from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SuppliesRFP(models.Model):
    _inherit = 'supplies.rfp'

    purchase_type = fields.Selection([
        ('bid', 'Bid'),
        ('direct', 'Direct'),
        ('proforma', 'Proforma Invoice'),
    ], string='Purchase Method', default='direct')

    purchase_origin = fields.Selection([
        ('local', 'Local'),
        ('foreign', 'Foreign')],
        string='Purchase Origin', default='local'
    )
    bid_type = fields.Selection([
        ('open', 'Open'),
        ('closed', 'Restricted')],
        string='Bid Type', default='open'
    )
    
    store_request_id = fields.Many2one(
        'store.request', string='Store Request', readonly=True, copy=False
    )
    purpose = fields.Char(string='Purpose of Request', tracking=True)
    requested_date = fields.Datetime(
        string='Requested Date', required=True, default=fields.Datetime.now, tracking=True
    )

    start_date = fields.Date(
        string='Start Date', default=fields.Datetime.now, tracking=True)
    end_date = fields.Date(string='End Date', tracking=True)

    selected_suppliers = fields.Many2many(
        'res.partner', string='Selected Suppliers'
    )
    project_id = fields.Many2one(
        'project.project',
        string='Contract/Project Reference',
        tracking=True
    )

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.end_date and record.start_date and record.end_date <= record.start_date:
                raise ValidationError("End Date must be after Start Date.")
            if record.start_date and record.start_date < fields.Date.today():
                raise ValidationError("Start Date must be today or in the future.")
            if record.end_date and record.end_date < fields.Date.today():
                raise ValidationError("End Date must be today or in the future.")
            if record.purchase_type in ['bid', 'proforma']:
                if not record.start_date and not record.end_date:
                    raise ValidationError("Start Date and End Date must be set for Bid and Proforma requests.")



    def action_create_purchase_order(self):
        self.ensure_one()

        order_lines = []
        for line in self.product_line_ids:
            line_vals = {
                'product_id': line.product_id.id,
                'name': line.product_name, 
                'product_qty': line.product_qty,
                'product_uom': line.product_uom.id,
                'price_unit': line.unit_price,
                'date_planned': fields.Date.today(),
            }
            order_lines.append((0, 0, line_vals))
            
        self.write({'state': 'accepted'})

        return {
            'name': 'New Purchase Order',
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                # Pre-fill these fields on the new PO form
                'default_origin': self.rfp_number,
                'default_user_id': self.env.user.id,
                'default_supplies_rfp_id': self.id,
                'default_order_line': order_lines,
                'default_rfp_id': self.id,
                'default_state': 'draft',
                'default_purchase_origin': self.purchase_origin,
                'default_project_id': self.project_id.id
            }
        }

