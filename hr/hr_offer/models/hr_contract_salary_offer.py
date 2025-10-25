from odoo import models

class HrContractSalaryOffer(models.Model):
    _inherit = 'hr.contract.salary.offer'

    def action_send_by_email(self):
        action = super().action_send_by_email()
        custom_template_id = self.env.ref('hr_offer.email_template_custom_applicant_offer').id
        action['context']['default_template_id'] = custom_template_id
        return action