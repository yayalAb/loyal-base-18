# purchase_order.py
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    supplies_rfp_id = fields.Many2one(
        'supplies.rfp',
        string='Purchase Request',
        readonly=True,
        copy=False
    )

    container_ids = fields.One2many(
        'purchase.container',
        'purchase_id',
        string='Containers',
        copy=True
    )
    proforma_number = fields.Char(string='Proforma Number')
    purchase_origin = fields.Selection([
        ('local', 'Local'),
        ('foreign', 'Foreign')],
        string='Purchase Origin', default='local'
    )

    @api.constrains('date_planned')
    def _check_date_planned(self):
        today = fields.Date.context_today(self)
        for order in self:
            for line in order.order_line:
                if line.date_planned and line.date_planned.date() < today:
                    raise ValidationError("The planned date cannot be in the past.")


    @api.constrains('order_line')
    def _check_order_line(self):
        for order in self:
            if not order.order_line:
                raise ValidationError("Purchase Order must have at least one product line.")


class PurchaseContainer(models.Model):
    _name = 'purchase.container'

    purchase_id = fields.Many2one('purchase.order', string='Purchase Order', required=True)
    container_number = fields.Char(string='Container Number', required=True)
    current_location = fields.Char(string='Current Location', required=True)
    delivered_to = fields.Char(string='Delivered To', required=True)
    status = fields.Selection([
        ('lc_1_opened', 'LC-1 Opened'),
        ('shipped_from_supplier', 'Shipped from Supplier'),
        ('lc_2_opened', 'LC-2 Opened'),
        ('custom_departed', 'Custom Departed'),
        ('custom_process', 'Custom Process'),
        ('custom_release', 'Custom Release'),
        ('warehouse_arrived', 'Warehouse Arrived')],
        string='Status', default='lc_1_opened'
    )

