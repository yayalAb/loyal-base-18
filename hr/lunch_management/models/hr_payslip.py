from odoo import models, fields, api

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def action_payslip_done(self):
        res = super(HrPayslip, self).action_payslip_done()

        lunch_logs_to_bill = self.env['lunch.log']
        for slip in self:
            domain = [
                ('employee_id', '=', slip.employee_id.id),
                ('date', '>=', slip.date_from),
                ('date', '<=', slip.date_to),
                ('state', '=', 'unbilled')
            ]

            found_logs = self.env['lunch.log'].sudo().search(domain)
            lunch_logs_to_bill |= found_logs

        if lunch_logs_to_bill:
            lunch_logs_to_bill.write({'state': 'billed'})

        return res