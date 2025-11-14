from odoo import api, fields, models
from odoo.exceptions import ValidationError
import math


class HospitalVitalSigns(models.Model):
    _name = 'hospital.vital.signs'
    _description = 'Patient Vital Signs'
    _order = 'date_recorded desc'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "patient_id"

    patient_id = fields.Many2one(
        'res.partner', string='Patient', track_visibility="always", required=True)
    mode_of_arrival = fields.Selection(
        selection=[
            ("walking", "walking"),
            ("wheelchair", "wheelchair"),
            ("stretcher", "Stretcher"),
        ],
        string="MOA",
        track_visibility="always",
        default="walking")
    is_reffered = fields.Boolean(
        string="Refferal",
        track_visibility="always",
    )
    Status = fields.Selection(
        selection=[
            ("alert", "Alert"),
            ("verbal", "verbal"),
            ("pain", "Pain"),
            ("unresponsive", "Unresponsive"),
        ],
        track_visibility="always",
        string="status",
        default="alert"
    )
    allergy = fields.Html(
        string="Allergy",
        track_visibility="always",
    )

    date_recorded = fields.Datetime(
        string='Date', default=fields.Datetime.now)
    temperature = fields.Float(string='Temperature', default=37)
    pulse = fields.Integer(string='Pulse', default=72)
    respiration_rate = fields.Integer(string='Respiration Rate', default=16)
    blood_pressure = fields.Char(string='Blood Pressure', default='120/80')
    systolic = fields.Float(string='Oxygen Saturation', default=120)
    diastolic = fields.Float(string='Oxygen Saturation', default=80)
    oxygen_saturation = fields.Float(string='Oxygen Saturation', default=98)

    weight = fields.Float(string='Weight', default=0.0)
    height = fields.Float(string='Height', default=0.0)
    bmi = fields.Float(string='BMI', compute='_compute_bmi', store=True)
    bsa = fields.Float(string='BSA', compute='_compute_bsa', store=True)
    current_medication = fields.Html(
        string="Current Medication",
    )
    reason_for_visit = fields.Html(
        string="Reason For Visit",
    )
    pain_level = fields.Selection(
        selection=[
            ("no", "No Pain"),
            ("mild", "Mild"),
            ("moderate", "Moderate"),
            ("severe", "Severe"),
            ("very", "Very severe"),
            ("worest", "Worest Pain"),
        ],
        string="Pain Leavel",
        default="no"
    )
    is_emergency = fields.Boolean(
        string="Emergency Patient(Please Give Priority)",
    )

    @api.onchange('systolic', 'diastolic')
    def _onchange_sys_dia(self):
        """Sync blood_pressure when systolic or diastolic changes."""
        if self.systolic and self.diastolic:
            self.blood_pressure = f"{int(self.systolic)}/{int(self.diastolic)}"

    @api.depends('height', 'weight')
    def _compute_bsa(self):
        for record in self:
            if record.height > 0 and record.weight > 0:
                record.bsa = math.sqrt(
                    (record.height * record.weight) / 3600)
            else:
                record.bsa = 0.0

    @api.depends('weight', 'height')
    def _compute_bmi(self):
        """Compute BMI based on weight and height."""
        for record in self:
            if record.height and record.weight:
                record.bmi = record.weight / ((record.height / 100) ** 2)
            else:
                record.bmi = 0

    # ----------------------------
    # VALIDATIONS
    # ----------------------------
    @api.constrains('temperature', 'pulse', 'respiration_rate', 'oxygen_saturation', 'weight', 'height')
    def _check_vital_sign_ranges(self):
        """Basic validation for realistic human vital sign values."""
        for rec in self:
            if rec.temperature and (rec.temperature < 0 or rec.temperature > 45):
                raise ValidationError(
                    "Temperature must be between 30°C and 45°C.")

            if rec.pulse and (rec.pulse < 0 or rec.pulse > 200):
                raise ValidationError(
                    "Pulse rate must be between 30 and 200 bpm.")

            if rec.respiration_rate and (rec.respiration_rate < 5 or rec.respiration_rate > 60):
                raise ValidationError(
                    "Respiration rate must be between 3 and 60 breaths/min.")

            if rec.oxygen_saturation and (rec.oxygen_saturation < 0 or rec.oxygen_saturation > 100):
                raise ValidationError(
                    "Oxygen saturation must be between 00% and 100%.")

            if rec.weight and rec.weight <= 0:
                raise ValidationError("Weight must be greater than zero.")

            if rec.height and rec.height <= 0:
                raise ValidationError("Height must be greater than zero.")

    @api.constrains('blood_pressure')
    def _check_blood_pressure_format(self):
        """Ensure blood pressure follows a valid 'systolic/diastolic' format, e.g., 120/80."""
        import re
        pattern = re.compile(r'^\d{2,3}/\d{2,3}$')
        for rec in self:
            if rec.blood_pressure and not pattern.match(rec.blood_pressure):
                raise ValidationError(
                    "Blood pressure must be in the format '120/80' (systolic/diastolic).")
