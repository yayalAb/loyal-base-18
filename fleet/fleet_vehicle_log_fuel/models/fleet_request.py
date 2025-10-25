# Copyright 2022 ForgeFlow S.L.  <https://www.forgeflow.com>
# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class FleetVehicleRequest(models.Model):
    _name = "fleet.vehicle.request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Fuel log for vehicles"

    active = fields.Boolean(default=True)
    user_id = fields.Many2one(
        "res.users",
        "Requester",
        required=True,
        default=lambda self: self.env.user,

    )
    vehicle_id = fields.Many2one(
        "fleet.vehicle",
        "Vehicle",
        help="Vehicle concerned by this log",
    )
    amount = fields.Monetary("Cost")
    description = fields.Char()
    odometer_id = fields.Many2one(
        "fleet.vehicle.odometer",
        "Odometer",
        help="Odometer measure of the vehicle at the moment of this log",
    )
    odometer = fields.Float(
        compute="_compute_odometer",
        store=True,
        inverse="_inverse_odometer",
        string="Odometer Value",
        help="Odometer measure of the vehicle at the moment of this log",
    )
    odometer_unit = fields.Selection(
        related="vehicle_id.odometer_unit", string="Unit")
    date = fields.Date(
        help="Date when the cost has been executed",
        default=fields.Date.context_today,
    )
    company_id = fields.Many2one(
        "res.company", "Company", default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(
        "res.currency", related="company_id.currency_id")
    purchaser_id = fields.Many2one(
        "res.partner",
        string="Driver",
        compute="_compute_purchaser_id",
        store=True,
    )
    inv_ref = fields.Char("Vendor Reference")
    vendor_id = fields.Many2one("res.partner", "Vendor")
    notes = fields.Text()
    source_location = fields.Char("Pick up location")
    destruction_location = fields.Char("Destruction Location")
    date_from = fields.Datetime(string="From")
    date_to = fields.Datetime(string="To")
    service_type_id = fields.Many2one(
        "fleet.service.type",
        "Service Type",
        default=lambda self: self.env.ref(
            "fleet.type_service_refueling", raise_if_not_found=False
        ),
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("in_review", "In Review"),
            ("approved", "Approved"),
            ("authorize", "Authorize"),
            ("cancel", "Cancel"),
            ("rejected", "Rejected"),
        ],
        default="draft",
        string="Stage",
    )
    liter = fields.Float()
    price_per_liter = fields.Float()
    service_id = fields.Many2one(
        comodel_name="fleet.vehicle.log.services", readonly=True, copy=False
    )

    def button_draft(self):
        self.state = "draft"
        return True

    def button_in_review(self):
        self.state = "in_review"
        return True

    def button_approved(self):
        self.state = "approved"
        return True

    def button_authorize(self):
        self.state = "authorize"
        return True

    def button_cancel(self):
        self.state = "cancel"
        return True

    def button_rejected(self):
        self.state = "rejected"
        return True
