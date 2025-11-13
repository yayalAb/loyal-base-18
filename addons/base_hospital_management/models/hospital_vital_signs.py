from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HospitalVitalSigns(models.Model):
    _name = 'hospital.vital.signs'
    _description = 'Patient Vital Signs'
    _order = 'date_recorded desc'

    patient_id = fields.Many2one(
        'res.partner', string='Patient', required=True)
    date_recorded = fields.Datetime(
        string='Date', default=fields.Datetime.now)
    temperature = fields.Float(string='Temperature')
    pulse = fields.Integer(string='Pulse')
    respiration_rate = fields.Integer(string='Respiration Rate')
    blood_pressure = fields.Char(string='Blood Pressure')
    oxygen_saturation = fields.Float(string='Oxygen Saturation')
    weight = fields.Float(string='Weight')
    height = fields.Float(string='Height')
    bmi = fields.Float(string='BMI', compute='_compute_bmi', store=True)

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
            if rec.temperature and (rec.temperature < 30 or rec.temperature > 45):
                raise ValidationError(
                    "Temperature must be between 30°C and 45°C.")

            if rec.pulse and (rec.pulse < 30 or rec.pulse > 200):
                raise ValidationError(
                    "Pulse rate must be between 30 and 200 bpm.")

            if rec.respiration_rate and (rec.respiration_rate < 5 or rec.respiration_rate > 60):
                raise ValidationError(
                    "Respiration rate must be between 5 and 60 breaths/min.")

            if rec.oxygen_saturation and (rec.oxygen_saturation < 50 or rec.oxygen_saturation > 100):
                raise ValidationError(
                    "Oxygen saturation must be between 50% and 100%.")

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
