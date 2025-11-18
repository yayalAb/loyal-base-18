import requests
from odoo import models, fields, api


class PosOrder(models.Model):
    _inherit = 'pos.order'

    def action_pos_order_invoice(self):
        res = super().action_pos_order_invoice()
        for order in self:
            order.send_to_mor()
        return res

    def send_to_mor(self):
        api = self.env['mor.api'].sudo().search([], limit=1)
        url = "https://mor.gov.et/api/receipt"
        headers = {"Authorization": f"Bearer {api.access_token}"}
        data = {
            "invoice_number": self.name,
            "customer_name": self.partner_id.name,
            "total": self.amount_total,
            "items": [{
                "description": line.product_id.name,
                "quantity": line.qty,
                "price": line.price_unit
            } for line in self.lines]
        }
        requests.post(url, json=data, headers=headers)
