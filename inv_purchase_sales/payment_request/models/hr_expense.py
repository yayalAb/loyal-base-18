from odoo import models, fields, api
from odoo.exceptions import ValidationError

class HrExpense(models.Model):
    _inherit = 'hr.expense'


    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order', domain="[('state', '=', 'purchase')]")
    foreign_purchase = fields.Boolean(string='Foreign Purchase Payments', default=False)
    lc_number = fields.Char(related='purchase_order_id.lc_number', string='LC Number')
    lc_amount = fields.Float(related='purchase_order_id.lc_amount', string='LC Amount', currency_field='currency_id')
    foreign_currency_amount = fields.Float(string='Foreign Currency Amount')
    narrative = fields.Text(string='Narrative')
    product_name = fields.Char(related='product_id.name', string='Product Name', readonly=True)

    @api.constrains('request_type')
    def _check_narrative(self):
        for record in self:
            if record.product_id == 'customs' and not record.narrative:
                raise ValidationError("Narrative is required for Customs Payment requests.")

    @api.constrains('lc_number', 'lc_amount', 'foreign_currency_amount', 'purchase_order_id')
    def _check_lc_and_foreign_currency(self):
        for record in self:
            if record.foreign_purchase:
                if not record.lc_number or not record.lc_amount:
                    raise ValidationError("LC Number and LC Amount are required for purchase expenses.")
                if not record.foreign_currency_amount:
                    raise ValidationError("Foreign Currency Amount is required for purchase expenses.")
                if not record.purchase_order_id:
                    raise ValidationError("Purchase Order is required for purchase expenses.")
