import base64
import io
import zipfile
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class BankStatementWizard(models.TransientModel):
    _name = 'hr.payroll.bank.statement.wizard'
    _description = 'Bank Statement Wizard'

    bank_ids = fields.Many2many(
        'res.partner.bank',
        string='Banks',
        required=True,
        help="Select one or more banks to generate statements for."
    )

    payslip_ids = fields.Many2many('hr.payslip', string='Payslips')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get('active_model') == 'hr.payslip':
            res['payslip_ids'] = self.env.context.get('active_ids', [])
        return res

    # hr.payroll.bank.statement.wizard

    def action_generate_report(self):
        """
        Prepares data for all selected banks and generates a single, consolidated PDF report.
        Each bank's statement will start on a new page.
        """
        self.ensure_one()

        if not self.payslip_ids:
            raise UserError(_("You must select at least one payslip."))

        reports_data = []
        all_payslip_ids = self.env['hr.payslip']

        for bank in self.bank_ids:
            payslips_for_bank = self.payslip_ids.filtered(
                lambda p: p.employee_id.bank_account_id.bank_id == bank.bank_id
            )

            if not payslips_for_bank:
                continue

            all_payslip_ids |= payslips_for_bank

            total_net = sum(p._get_salary_line_total('NET')
                            for p in payslips_for_bank)

            # --- MODIFICATION START ---
            # Pass IDs instead of recordsets for robustness
            reports_data.append({
                'bank_id': bank.id,
                'branch_address': bank.branch_address,
                'payslip_ids': payslips_for_bank.ids,
                'total_net': total_net,
                'company_id': payslips_for_bank[0].company_id.id,
            })
            # --- MODIFICATION END ---

        if not reports_data:
            raise UserError(
                _("There are no payslips matching any of the selected banks in your selection."))

        data = {
            'reports': reports_data,
        }

        report_action = self.env.ref(
            'hr_payroll_bank_statement.action_report_bank_statement')

        return report_action.report_action(all_payslip_ids, data=data)
