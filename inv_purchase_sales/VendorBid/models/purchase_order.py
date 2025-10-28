from logging import exception

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PurchaseOrder(models.Model):
    """
    Inherits the 'purchase.order' model to integrate with the RFP (Request for Purchase)
    process, extend functionality for evaluating supplier proposals, and provide
    recommendation and scoring mechanisms.

    Enhancements include:
    ---------------------
    - Link to an RFP via `rfp_id`
    - Additional evaluation fields like `warrenty_period`, `score`, `system_score`, and `recommended`
    - Computation of a `system_score` based on price, delivery charge, and warranty period
    - Constraint to ensure only one recommendation per supplier per RFP
    - Automation for accepting an RFQ and updating related RFP and other RFQs
    - Tracking when the RFQ status last changed

    Fields
    ------
    rfp_id : Many2one
        Reference to the related RFP (supplies.rfp).

    warrenty_period : Integer
        Warranty period offered by the supplier, measured in months.

    score : Float
        Manual score for evaluation purposes, default is 0.

    system_score : Float (computed)
        Computed score based on normalized price, delivery charge, and warranty.

    recommended : Boolean
        Flag to mark the purchase order as recommended.

    last_changed_status_date : Datetime (computed & stored)
        Records the last date when the RFQ status changed.

    Methods
    -------
    _compute_last_changed_status_date()
        Sets the last_changed_status_date to today's date whenever the RFQ state changes.

    action_accept()
        Accepts the RFQ, confirms the PO, updates the RFP product lines,
        and cancels competing RFQs for the same RFP.

    _check_recommended()
        Ensures that a supplier is not recommended more than once for the same RFP.

    get_purchase_order_sudo(domain, fields)
        Sudo-enabled method to fetch purchase orders with specified domain and fields.

    write(vals)
        Overrides write to ensure that score cannot be set to a negative value.

    _compute_system_score()
        Calculates a weighted system score:
        - 40% weight for normalized price (lower is better),
        - 30% for normalized delivery charge (lower is better),
        - 30% for normalized warranty period (higher is better).

    Raises
    ------
    UserError:
        If a supplier is marked as recommended more than once for a given RFP.

    ValidationError:
        If an attempt is made to write a negative score.
    """
    _inherit = 'purchase.order'

    rfp_id = fields.Many2one('supplies.rfp', string='RFP', index=True, copy=False)
    warrenty_period = fields.Integer(string='Warrenty Period (in months)')
    score = fields.Float(string='Score', default=0)
    system_score = fields.Float(string='System Score', compute='_compute_system_score')
    # recommended = fields.Boolean(string='Recommended', default=False)
    last_changed_status_date = fields.Datetime(
        string='Last Updated Date of RFQ Status',
        compute='_compute_last_changed_status_date',
        store=True
    )

    is_final_po_from_rfp = fields.Boolean(
        string="Is Final PO from RFP",
        default=False,
        copy=False,
        help="Check this if the Purchase Order was created from a recommendation in an RFP, "
             "as opposed to being an initial RFQ from a supplier."
    )

    


    @api.depends('state')
    def _compute_last_changed_status_date(self):
        for rfq in self:
            rfq.last_changed_status_date = fields.Date.today()

    def action_accept(self):
        self.rfp_id.write({
            'state': 'accepted',
            'approved_supplier_id': self.partner_id.id,
            'date_accept': fields.Date.today()
        })
        self.button_confirm()
        # updating RFP product line prices
        for line in self.rfp_id.product_line_ids:
            rfq_line = self.order_line.filtered(lambda x: x.product_id == line.product_id)
            line.write({
                'unit_price': rfq_line.price_unit,
                'delivery_charge': rfq_line.delivery_charge,
            })
        # cancelling other RFQs
        other_rfqs = self.env['purchase.order'].search([
            ('rfp_id', '=', self.rfp_id.id),
            ('id', '!=', self.id),
        ])
        other_rfqs.button_cancel()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'supplies.rfp',
            'view_mode': 'form',
            'res_id': self.rfp_id.id,
            'target': 'current',
        }


    @api.model
    def get_purchase_order_sudo(self, domain, fields):
        return self.sudo().search_read(domain, fields)

    @api.model
    def write(self, vals):
        if 'score' in vals and vals['score'] is not None and vals['score'] < 0:
            raise ValidationError(_("Score of this RFQ can not be negative"))
        return super(PurchaseOrder, self).write(vals)

    @api.depends('order_line.price_unit', 'order_line.delivery_charge', 'warrenty_period')
    def _compute_system_score(self):
        for order in self:
            if not order.order_line:
                order.system_score = 0
                continue

            price = [line.price_unit for line in order.order_line]
            deliveries = [line.delivery_charge for line in order.order_line]
            warranty = order.warrenty_period or 0

            sum_price = sum(price)
            sum_delivery = sum(deliveries)

            max_price, max_delivery, max_warranty = 100000000, 1000000, 100

            normalized_price = min(sum_price / max_price, 1.0)
            normalized_delivery = min(sum_delivery / max_delivery, 1.0)
            normalized_warranty = min(warranty / max_warranty, 1.0)

            order.system_score = 100 * round(
                0.4 * (1 - normalized_price) +
                0.3 * (1 - normalized_delivery) +
                0.3 * normalized_warranty, 3)
