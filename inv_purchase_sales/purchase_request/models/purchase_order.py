# purchase_order.py
from odoo import models, fields

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    purchase_request_id = fields.Many2one(
        'purchase.request',
        string='Purchase Request',
        readonly=True,
        copy=False
    )

    proforma_number = fields.Char(string='proforma Number')