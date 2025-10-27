from odoo import models, fields, api


class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    max_balance = fields.Float(string='Maximum Balance')