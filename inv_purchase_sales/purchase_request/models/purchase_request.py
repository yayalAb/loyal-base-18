# purchase_request.py
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

# purchase_request.py

# ... (imports and most of the class definition are the same) ...

class PurchaseRequest(models.Model):
    _name = 'purchase.request'
    # ... (all fields from before are the same) ...
    _description = 'Purchase Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Reference', required=True, copy=False,
        default=lambda self: _('New'), readonly=True
    )

    requested_by = fields.Many2one(
        'res.users', string='Requested By', required=True,
        default=lambda self: self.env.user, tracking=True
    )
    department_id = fields.Many2one(
        'hr.department', string='Department', required=True, tracking=True,
        compute='_compute_department_id', store=True, readonly=False
    )
    requested_date = fields.Datetime(
        string='Requested Date', required=True, default=fields.Datetime.now, tracking=True
    )
    warehouse_id = fields.Many2one(
        'stock.warehouse', string='Deliver To', required=True, tracking=True
    )
    purpose = fields.Char(string='Purpose of Request', tracking=True)
    factory_id = fields.Char(string='Factory', tracking=True)
    approved_by = fields.Many2one('res.users', string='Approved By', tracking=True, readonly=True)
    authorized_by = fields.Many2one('res.users', string='Authorized By', tracking=True, readonly=True)
    purchase_type = fields.Selection([
        ('local', 'Local'),
        ('foreign', 'Foreign')],
        string='Purchase Type', default='local'
    )
    store_request_id = fields.Many2one(
        'store.request', string='Store Request', readonly=True, copy=False
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('authorized', 'Authorized'),
        ('ordered', 'Ordered'),
        ('cancel', 'Cancelled')],
        string='Status', default='draft', tracking=True
    )
    request_line_ids = fields.One2many(
        'purchase.request.line',
        'request_id',
        string='Request Lines',
        required=True
    )
    purchase_order_ids = fields.One2many(
        'purchase.order', 'purchase_request_id', string='Purchase Orders'
    )
    purchase_order_count = fields.Integer(
        compute='_compute_purchase_order_count', string='PO Count'
    )
    
    @api.depends('purchase_order_ids')
    def _compute_purchase_order_count(self):
        for request in self:
            request.purchase_order_count = len(request.purchase_order_ids)


    @api.depends('requested_by')
    def _compute_department_id(self):
        for rec in self:
            if rec.requested_by and not rec.department_id:
                rec.department_id = rec.requested_by.employee_id.department_id

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('purchase.request') or _('New')
        res = super(PurchaseRequest, self).create(vals)
        return res

    def action_submit(self):
        self.write({'state': 'submitted'})

    def action_approve(self):
        self.write({'state': 'approved', 'approved_by': self.env.user.id})
    
    def action_authorize(self):
        self.write({'state': 'authorized', 'authorized_by': self.env.user.id})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    # --- === THIS METHOD IS NOW CORRECTED === ---
    def action_create_purchase_order(self):
        self.ensure_one()
        
        # Prepare the lines for the PO
        order_lines = []
        for line in self.request_line_ids:
            line_vals = {
                'product_id': line.product_id.id,
                'name': line.description,
                'product_qty': line.product_uom_qty,
                'product_uom': line.product_uom.id,
                'price_unit': 0, # Let the Purchase Manager set the price
                'date_planned': fields.Date.today(),
            }
            order_lines.append((0, 0, line_vals))

        # Return an action to open the PO form, with values pre-filled
        return {
            'name': _('New Purchase Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                # Pre-fill these fields on the new PO form
                'default_origin': self.name,
                'default_user_id': self.requested_by.id,
                'default_picking_type_id': self.warehouse_id.in_type_id.id,
                'default_purchase_request_id': self.id,
                'default_order_line': order_lines,
            }
        }

    def action_view_purchase_orders(self):
        self.ensure_one()
        # In Odoo 16, this is the correct way to get the action
        action = self.env['ir.actions.act_window']._for_xml_id('purchase.purchase_rfq')
        action['domain'] = [('id', 'in', self.purchase_order_ids.ids)]
        if self.purchase_order_count == 1:
            action['view_mode'] = 'form,tree' # Allow switching back to tree
            action['res_id'] = self.purchase_order_ids.id
        return action

# --- The PurchaseRequestLine model remains the same ---
class PurchaseRequestLine(models.Model):
    # ... (no changes needed here) ...
    _name = 'purchase.request.line'
    _description = 'Purchase Request Line'

    request_id = fields.Many2one(
        'purchase.request', string='Request', required=True, ondelete='cascade'
    )
    product_id = fields.Many2one(
        'product.product', string='Product', required=True,
        domain="[('purchase_ok', '=', True)]"
    )
    serial_number = fields.Char(string='Serial Number')
    stock_number = fields.Char(string='Stock Number')
    description = fields.Text(string='Description', required=True)
    product_uom_qty = fields.Float(string='Quantity', required=True, default=1.0)
    remark = fields.Text(string='Remark')
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', required=True)
    product_category_id = fields.Many2one(
        related='product_id.categ_id', string='Category', store=True
    )
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.product_uom = self.product_id.uom_po_id or self.product_id.uom_id
            self.description = self.product_id.get_product_multiline_description_sale()
            return {'domain': {
                'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]
            }}

    @api.constrains('product_uom_qty')
    def _check_positive_qty(self):
        for line in self:
            if line.product_uom_qty <= 0:
                raise ValidationError(_('Quantity must be positive!'))