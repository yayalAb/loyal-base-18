from odoo import models, fields, api, _
from odoo.exceptions import UserError

class StoreRequest(models.Model):
    _inherit = 'store.request'

    purchase_request_ids = fields.One2many(
        'purchase.request', 'store_request_id', string='Purchase Requests'
    )
    purchase_request_count = fields.Integer(
        compute='_compute_purchase_request_count', string='Purchase Request Count'
    )

    @api.depends('purchase_request_ids')
    def _compute_purchase_request_count(self):
        for rec in self:
            rec.purchase_request_count = len(rec.purchase_request_ids)

    def action_view_purchase_requests(self):
        self.ensure_one()
        return {
            'name': _('Purchase Requests'),
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'purchase.request',
            'domain': [('id', 'in', self.purchase_request_ids.ids)],
            'target': 'current',
        }

    def action_create_purchase_request(self):
        """Create a new purchase request from the store request and open its form view."""
        self.ensure_one()
        if self.state != 'approved':
            raise UserError(_("This action can only be performed on an approved store request."))

        # Prepare purchase request lines from store request lines
        purchase_request_lines = []
        for line in self.request_line_ids:
            # Find a product.product variant for the product.template
            product_variant = self.env['product.product'].search([
                ('product_tmpl_id', '=', line.product_id.id)
            ], limit=1)
            if not product_variant:
                raise UserError(
                    _("No product variant found for product template '%s'. Please ensure at least one variant exists.")
                    % line.product_id.name
                )

            purchase_request_lines.append((0, 0, {
                'product_id': product_variant.id,
                'description': line.description or product_variant.display_name,
                'product_uom_qty': line.product_uom_qty,
                'product_uom': line.product_uom.id,
                'serial_number': line.serial_number,
                'stock_number': line.stock_number,
                'remark': line.remark,
            }))

        # Create the purchase request
        purchase_request = self.env['purchase.request'].create({
            'store_request_id': self.id,
            'requested_by': self.requested_by.id,
            'department_id': self.department_id.id,
            'factory_id': self.factory_id,
            'purpose': self.purpose,
            'warehouse_id': self.warehouse_id.id,
            'request_line_ids': purchase_request_lines,
            'state': 'draft',
        })

        # Return the action to open the purchase request form
        return {
            'name': _('Purchase Request'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'purchase.request',
            'res_id': purchase_request.id,
            'target': 'current',
            'context': {'create': False},  # Prevent creating another record from the form
        }

    # Override the stock compute method if needed
    @api.depends('product_id', 'request_id.warehouse_id')
    def _compute_stock_available_qty_override(self):
        for line in self:
            if line.product_id and line.request_id.warehouse_id:
                variants = self.env['product.product'].search([('product_tmpl_id', '=', line.product_id.id)])
                if variants:
                    quants = self.env['stock.quant'].search([
                        ('product_id', 'in', variants.ids),
                        ('location_id', '=', line.request_id.warehouse_id.lot_stock_id.id)
                    ])
                    line.stock_available_qty = sum(quants.mapped('available_quantity'))
                else:
                    line.stock_available_qty = 0.0
            else:
                line.stock_available_qty = 0.0