from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)


class StoreRequest(models.Model):
    _name = 'store.request'
    _description = 'Store Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'requested_date desc'

    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        default=lambda self: _('New'),
        readonly=True
    )
    requested_by = fields.Many2one(
        'res.users',
        string='Requested By',
        required=True,
        readonly=True,
        default=lambda self: self.env.user,
        tracking=True
    )
    department_id = fields.Many2one(
        'hr.department',
        related='requested_by.employee_id.department_id',
        string='Department',
        required=True,
        tracking=True
    )
    factory_id = fields.Char(
        string='Factory',
        tracking=True
    )
    purpose = fields.Char(
    string='Purpose of Request',
    tracking=True
    )

    project_id = fields.Many2one(
        'project.project',
        string='Contract/Project Reference',
        tracking=True
    )
    requested_date = fields.Datetime(
        string='Requested Date',
        required=True,
        default=fields.Datetime.now,
        tracking=True
    )
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warehouse',
        tracking=True
    )
    request_line_ids = fields.One2many(
        
        'store.request.line',
        'request_id',
        string='Request Lines',
        required=True
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('store_review', 'Received'),
        ('approved', 'Approved'),
        ('issue', 'Issued'),
        ('internal_transfer', 'Internal Transfer'),
        ('purchase_requested', 'Purchase Requested'),
        ('cancel', 'Cancelled')],
        string='State',
        default='draft',
        tracking=True
    )
    approved_by = fields.Many2one(
        'res.users',
        string='Approved By',
        tracking=True
    )
    storeman_id = fields.Many2one(
        'res.users',
        related='warehouse_id.storeman_id',
        string='Storeman',
    )
    note = fields.Html(string='Note')
    is_department_head = fields.Boolean(
        compute="_check_department_head", string="Is Department Head")
    is_storeman = fields.Boolean(
        compute="_check_is_storeman", string="Is Storeman")



    @api.constrains('warehouse_id', 'state')
    def _check_warehouse_required_after_approval(self):
        for rec in self:
            if rec.state == 'issue' and not rec.warehouse_id:
                raise ValidationError("You must select a warehouse.")

    @api.constrains('state', 'request_line_ids')
    def _check_request_lines(self):
        for rec in self:
            if rec.state not in ['draft', 'cancel'] and not rec.request_line_ids:
                raise ValidationError("You must add at least one item.")

    @api.depends("department_id")
    def _check_department_head(self):
        for rec in self:
            if rec.department_id.manager_id.id == self.env.user.employee_id.id:
                rec.is_department_head = True
            else:
                rec.is_department_head = False

    @api.depends("warehouse_id")
    def _check_is_storeman(self):
        for rec in self:
            if rec.storeman_id.id == self.env.user.id:
                rec.is_storeman = True
            else:
                rec.is_storeman = False

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'store.request') or _('New')
        res = super(StoreRequest, self).create(vals)
        return res

    def action_submit(self):
        if not self.request_line_ids:
            raise UserError("You must add at least one item before submitting.")
        self.state = 'submitted'

        # Auto-approve if requester is manager
        if self.department_id.manager_id.id == self.requested_by.employee_id.id:
            self.action_approve()


    def action_approve(self):
        self.write({
            'state': 'approved',
            'approved_by': self.env.user.id
        })

    def action_cancel(self):
        self.write({'state': 'cancel'})



class StoreRequestLine(models.Model):
    _name = 'store.request.line'
    _description = 'Store Request Line'

    request_id = fields.Many2one(
        'store.request',
        string='Request',
        required=True,
        ondelete='cascade'
    )
    product_id = fields.Many2one(
        'product.product',
        string='Description',
        required=True
    )
    serial_number = fields.Char(
        string='Serial Number',
        required=False
    )
    stock_number = fields.Char(
        string='Stock Number',
        required=False
    )
    product_uom_qty = fields.Float(
        string='Quantity',
        required=True,
        default=1.0
    )
    remark = fields.Text(
        string='Remark',
    )
    product_uom = fields.Many2one(
        'uom.uom',
        string='Unit of Measure',
        required=True
    )
    product_category_id = fields.Many2one(
        related='product_id.categ_id',
        string='Category',
        store=True
    )
    stock_available_qty = fields.Float(
        string='Available Quantity',
        compute='_compute_stock_available_qty',
        store=True,
        digits='Product Unit of Measure'
    )
    line_state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('issue', 'Issued'),
        ('transferred', 'Transferred'),
        ('tp_purchase', 'To Purchase'),
        ('cancel', 'Cancelled')],
        string='Line State',
        default='draft',
    )

    @api.depends('product_id', 'request_id.warehouse_id')
    def _compute_stock_available_qty(self):
        for line in self:
            if not line.product_id:
                line.stock_available_qty = 0.0
                continue

            domain = [('product_id', '=', line.product_id.id)]

            if line.request_id.warehouse_id:
                # Only this warehouse’s stock location
                domain.append(('location_id', '=', line.request_id.warehouse_id.lot_stock_id.id))
            else:
                # All internal locations across all warehouses
                internal_locations = self.env['stock.location'].search([('usage', '=', 'internal')]).ids
                domain.append(('location_id', 'in', internal_locations))

            quants = self.env['stock.quant'].search(domain)
            line.stock_available_qty = sum(quants.mapped('available_quantity'))



    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.product_uom = self.product_id.uom_id
            return {'domain': {
                'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]
            }}

    @api.constrains('product_uom_qty')
    def _check_positive_qty(self):
        for line in self:
            if line.product_uom_qty <= 0:
                raise ValidationError(_('Quantity must be positive!'))

    @api.constrains('product_uom')
    def _check_uom_category(self):
        for line in self:
            if line.product_id and line.product_uom.category_id != line.product_id.uom_id.category_id:
                raise ValidationError(
                    _('The unit of measure must be in the same category as the product unit of measure'))
