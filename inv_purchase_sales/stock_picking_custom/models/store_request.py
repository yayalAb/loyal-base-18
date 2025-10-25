from odoo import models, fields, _
from odoo.exceptions import UserError

class StoreRequest(models.Model):
    _inherit = "store.request"

    transfer_id = fields.Many2one(
        'stock.picking',
        string='Transfer',
        readonly=True,
        copy=False,
    )

    issued_by = fields.Many2one(
        'res.users',
        string='Issued By',
        readonly=True,
        copy=False,
    )

    def action_store_issue(self):
        for rec in self:
            # Create stock picking
            if not rec.warehouse_id:
                raise UserError(_("You must select a warehouse before issuing the request."))
            picking_type = rec.warehouse_id.out_type_id
            if not picking_type:
                raise UserError(
                    _("No outgoing picking type found for the warehouse!"))

            customer_location = self.env.ref('stock.stock_location_customers')

            # Prepare move lines
            move_lines = []
            for line in rec.request_line_ids:
                move_lines.append((0, 0, {
                    'name': line.product_id.name,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.product_uom_qty,
                    'product_uom': line.product_uom.id,
                    'location_id': picking_type.default_location_src_id.id,
                    'location_dest_id': customer_location.id,
                }))

            # Create the picking
            picking = self.env['stock.picking'].create({
                'picking_type_id': picking_type.id,
                'location_id': picking_type.default_location_src_id.id,
                'location_dest_id': customer_location.id,
                'origin': rec.name,
                'move_ids_without_package': move_lines,
                'store_request_id': rec.id,
            })

            rec.write({
                'state': 'issue',
                'transfer_id': picking.id,
                'issued_by': self.env.user.id
            })

        return True

    def action_open_transfer(self):
        self.ensure_one()  # Ensures this method works on a single record
        if not self.transfer_id:
            raise UserError(_("No transfer is linked to this request!"))

        return {
            'name': _('Stock Transfer'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'stock.picking',
            'res_id': self.transfer_id.id,
            'target': 'current',
            'context': {
                'create': False,
                'edit': False,
            }
        }