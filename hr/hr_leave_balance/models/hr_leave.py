from odoo import models, fields, api
from odoo.exceptions import ValidationError

class HrleaveRequest(models.Model):
    _inherit = 'hr.leave'

    @api.constrains('request_date_from', 'request_date_to', 'holiday_status_id', 'number_of_days')
    def _check_leave_balance(self):
        for record in self:
            if record.holiday_status_id.requires_allocation == 'no':
                leaves = record.env['hr.leave'].search(
                    [('id', '!=', record.id), ('employee_id', '=', record.employee_id.id), ('state', 'in', ['confirm', 'validate1', 'validate']), ('holiday_status_id', '=', record.holiday_status_id.id)])
                
                days_taken = sum(leaves.mapped('number_of_days'))
                new_total_days = days_taken + record.number_of_days
                max_balance = record.holiday_status_id.max_balance
                if new_total_days > max_balance:
                    raise ValidationError(
                        f"This leave request exceeds the maximum balance of {max_balance} days "
                        f"for the '{record.holiday_status_id.name}' leave type. "
                        f"You have already taken {days_taken} day(s)."
                    )
