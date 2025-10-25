from odoo import models, fields

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    expense_id = fields.One2many('hr.expense', 'purchase_order_id', string='Expense Account')

    def action_open_payment_request(self):
        return {
            'name': 'Payment Request',
            'type': 'ir.actions.act_window',
            'view_mode': 'list',
            'res_model': 'hr.expense',
            'domain': [('purchase_order_id', '=', self.id)],
            'target': 'current',
        }