from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    patient_validity_days = fields.Integer(
        string='Patient Card Validity Period (Days)',
        default=10,
        config_parameter='hospital.patient_validity_days',
        help='Number of days before the patient record or ID expires.'
    )
