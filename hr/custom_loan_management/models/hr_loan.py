from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
import math

class HrLoan(models.Model):
    _inherit = 'hr.loan'

    # --- REQUIREMENT 1: FIELDS ---
    # The new field for the user to input the desired payment amount.
    installment_amount = fields.Float(
        string="Amount Per Installment",
        tracking=True,
        help="The amount the employee will pay per installment. This will be used to calculate the number of installments."
    )
    
    # We are not changing the original 'installment' field in Python,
    # as its value will now be set by our new logic. We will make it
    # readonly in the XML view.

    # --- REQUIREMENT 2: FIELDS ---
    is_employee_manager = fields.Boolean(
        string="Is Manager?",
        compute='_compute_is_manager',
        help="Checked if the employee has direct reports."
    )
    manager_loan_type = fields.Selection(
        [
            ('emergency', 'Emergency Loan'),
            ('fixed_asset', 'Fixed Asset Loan'),
        ],
        string="Manager Loan Type",
        tracking=True
    )
    
    has_grace_period = fields.Boolean(
        string="Add Grace Period",
        tracking=True,
        help="Check this box to define a period where no installments will be scheduled."
    )
    grace_period_start_date = fields.Date(
        string="Grace Period Start Date",
        tracking=True
    )
    grace_period_end_date = fields.Date(
        string="Grace Period End Date",
        tracking=True
    )
    
    is_special_loan = fields.Boolean(
        string="Special Loan (Bypass Policy)",
        tracking=True,
        default=False,
        help="If checked, the standard loan amount policies will be ignored for this request. This should only be used in exceptional cases and requires manager approval."
    )
    
    adjust_installment_amount = fields.Boolean(
        string="Adjust Amount Per Installment",
        default=False,
        tracking=True,
        help="Check this box to calculate the schedule based on a fixed payment amount. Uncheck to calculate based on a fixed number of installments."
    )

    @api.depends('employee_id')
    def _compute_is_manager(self):
        """A simple check to see if an employee is a manager."""
        for loan in self:
            loan.is_employee_manager = bool(loan.employee_id and loan.employee_id.child_ids)

    def _recompute_installments(self):
        """
        Master method to re-compute installments based on the user's chosen method.
        It respects paid installments and handles grace periods.
        """
        for loan in self:
            # --- PRE-CHECKS ---
            if loan.loan_amount <= 0 or not loan.payment_date:
                continue
            if loan.has_grace_period and (not loan.grace_period_start_date or not loan.grace_period_end_date):
                continue

            # --- INITIAL CALCULATION ---
            paid_lines = loan.loan_line_ids.filtered(lambda line: line.paid)
            paid_amount = sum(paid_lines.mapped('amount'))
            balance_amount = loan.loan_amount - paid_amount

            # --- CLEAR UNPAID LINES ---
            unpaid_lines = loan.loan_line_ids.filtered(lambda line: not line.paid)
            if unpaid_lines:
                unpaid_lines.unlink()

            # --- DUAL LOGIC FOR INSTALLMENT CALCULATION ---
            new_lines_vals = []
            
            # Logic Branch 1: Calculate based on a fixed NUMBER of installments
            if not loan.adjust_installment_amount:
                if loan.installment <= len(paid_lines):
                    # User reduced the number of installments to something already paid. Do nothing.
                    continue
                
                remaining_installments = loan.installment - len(paid_lines)
                if remaining_installments <= 0:
                    continue # Avoid division by zero
                
                amount_per_installment = balance_amount / remaining_installments
                
                # We will create exactly 'remaining_installments' lines.
                for i in range(remaining_installments):
                    # For the last installment, assign the remaining balance to avoid float errors
                    amount_to_pay = amount_per_installment if i < remaining_installments - 1 else balance_amount
                    new_lines_vals.append({
                        'amount': amount_to_pay,
                    })
                    balance_amount -= amount_to_pay # Decrement balance for the last line calculation

            # Logic Branch 2: Calculate based on a fixed AMOUNT per installment
            else:
                if loan.installment_amount <= 0:
                    continue # Cannot calculate if amount is zero
                
                temp_balance = balance_amount
                while temp_balance > 0.01:
                    amount_to_pay = min(loan.installment_amount, temp_balance)
                    new_lines_vals.append({
                        'amount': amount_to_pay,
                    })
                    temp_balance -= amount_to_pay

            # --- DATE SCHEDULING & FINAL WRITE (Common for both logics) ---
            if not new_lines_vals:
                continue

            next_installment_date = loan.payment_date
            if paid_lines:
                last_paid_date = max(paid_lines.mapped('date'))
                if next_installment_date <= last_paid_date:
                    next_installment_date = last_paid_date + relativedelta(months=1)
            
            # Add the dates to our calculated lines
            for vals in new_lines_vals:
                if loan.has_grace_period and \
                   loan.grace_period_start_date <= next_installment_date <= loan.grace_period_end_date:
                    next_installment_date = loan.grace_period_end_date + relativedelta(months=1)
                
                vals['date'] = next_installment_date
                vals['employee_id'] = loan.employee_id.id
                next_installment_date += relativedelta(months=1)

            if new_lines_vals:
                loan.with_context(bypass_write_trigger=True).write({
                    'loan_line_ids': [(0, 0, vals) for vals in new_lines_vals],
                    'installment': len(paid_lines) + len(new_lines_vals)
                })

    # You also need to add 'has_grace_period' and its date fields to the write trigger
    def write(self, vals):
        """ On save/write, call the original write, then re-compute if necessary. """
        if self.env.context.get('bypass_write_trigger'):
            return super(HrLoan, self).write(vals)

        res = super(HrLoan, self).write(vals)
        if 'loan_amount' in vals or 'installment_amount' in vals or \
           'payment_date' in vals or 'has_grace_period' in vals or \
           'grace_period_start_date' in vals or 'grace_period_end_date' in vals or \
           'installment' in vals or 'adjust_installment_amount' in vals:
            self._recompute_installments()
        return res
                
    # --- MODIFIED ORIGINAL METHOD ---
    def action_compute_installment(self):
        """ The button now simply calls our new helper method. """
        if self.installment_amount <= 0 and self.adjust_installment_amount :
            raise ValidationError(_("Amount Per Installment must be greater than zero."))
        self._recompute_installments()
        return True

    # --- OVERRIDE CREATE AND WRITE METHODS ---
    @api.model
    def create(self, vals):
        """ On creation, call the original create, then compute installments. """
        loan = super(HrLoan, self).create(vals)
        if loan.installment_amount > 0:
            loan._recompute_installments()
        return loan

    # def write(self, vals):
    #     """ On save/write, call the original write, then re-compute if necessary. """
    #     res = super(HrLoan, self).write(vals)
    #     # We only recompute if one of the key values has been changed.
    #     if 'loan_amount' in vals or 'installment_amount' in vals or 'payment_date' in vals:
    #         self._recompute_installments()
    #     return res


    # --- REQUIREMENT 2: VALIDATION LOGIC ---
    @api.constrains('loan_amount', 'state', 'manager_loan_type')
    def _check_loan_amount_policy(self):
        """
        This server-side validation enforces the company's loan policy limits.
        It now reads its values from the system configuration.
        """
        # Get the configuration parameter reading function
        get_param = self.env['ir.config_parameter'].sudo().get_param

        # Load all the policy values from the configuration at once
        emp_months = int(get_param('custom_loan_management.loan_policy_emp_months', default=4))
        emp_service_years_active = get_param('custom_loan_management.loan_policy_emp_service_years', default='True').lower() == 'true'

        mgr_em_months = int(get_param('custom_loan_management.loan_policy_mgr_emergency_months', default=6))
        mgr_em_service_years_active = get_param('custom_loan_management.loan_policy_mgr_emergency_service_years', default='True').lower() == 'true'

        mgr_fa_months = int(get_param('custom_loan_management.loan_policy_mgr_fixed_asset_months', default=24))

        for loan in self:
            
            if loan.is_special_loan:
                continue
            # We only run the check when the user tries to move it to the approval stage.
            if loan.state == 'waiting_approval_1' and loan.employee_id and loan.loan_amount > 0:
                contract = self.env['hr.contract'].search([
                    ('employee_id', '=', loan.employee_id.id),
                    ('state', '=', 'open')
                ], limit=1)

                if not contract:
                    raise ValidationError(_("The employee does not have a running contract."))

                monthly_salary = contract.wage
                service_years = 0
                if contract.date_start:
                    service_years = relativedelta(fields.Date.today(), contract.date_start).years

                max_loan_amount = 0
                policy_msg = ""

                if loan.is_employee_manager:
                    if not loan.manager_loan_type:
                        raise ValidationError(_("You must select a 'Manager Loan Type' for this employee."))
                    
                    if loan.manager_loan_type == 'emergency':
                        limit_by_salary = mgr_em_months * monthly_salary
                        # Only calculate service year limit if the setting is active
                        limit_by_service = service_years * monthly_salary if mgr_em_service_years_active and service_years > 0 else 0
                        max_loan_amount = max(limit_by_salary, limit_by_service)
                        policy_msg = _("For a Manager Emergency Loan, the maximum amount is the greater of %(months)s months' salary (%(salary_limit)s) or service years x salary (%(service_limit)s).") % {
                            'months': mgr_em_months,
                            'salary_limit': f"{limit_by_salary:,.2f}",
                            'service_limit': f"{limit_by_service:,.2f}"
                        }
                    
                    elif loan.manager_loan_type == 'fixed_asset':
                        max_loan_amount = mgr_fa_months * monthly_salary
                        policy_msg = _("For a Manager Fixed Asset Loan, the maximum amount is %(months)s months' salary (%(salary_limit)s).") % {
                            'months': mgr_fa_months,
                            'salary_limit': f"{max_loan_amount:,.2f}"
                        }
                
                else: # Is a regular employee
                    limit_by_salary = emp_months * monthly_salary
                    # Only calculate service year limit if the setting is active
                    limit_by_service = service_years * monthly_salary if emp_service_years_active and service_years > 0 else 0
                    max_loan_amount = max(limit_by_salary, limit_by_service)
                    policy_msg = _("For an Employee Loan, the maximum amount is the greater of %(months)s months' salary (%(salary_limit)s) or service years x salary (%(service_limit)s).") % {
                        'months': emp_months,
                        'salary_limit': f"{limit_by_salary:,.2f}",
                        'service_limit': f"{limit_by_service:,.2f}"
                    }

                if loan.loan_amount > max_loan_amount:
                    raise ValidationError(_(
                        "Loan amount ({:,.2f}) exceeds company policy.\n\n"
                        "The maximum allowed is {:,.2f}.\n"
                        "Reason: {}"
                    ).format(loan.loan_amount, max_loan_amount, policy_msg))
                    
class HrLoanLine(models.Model):
    _inherit = 'hr.loan.line'

    # By default, Odoo doesn't trigger parent recomputations when a one2many line changes.
    # We need to explicitly tell it to do so.
    # The 'auto_join=True' is an optimization.
    loan_id = fields.Many2one(
        'hr.loan', string='Loan Ref.',
        help="Loan Reference", auto_join=True)

    # We override the 'write' method, which is called every time a record is saved.
    def write(self, vals):
        """
        When an installment line is changed (e.g., 'paid' is checked),
        this method will trigger the re-computation of the parent loan's totals.
        """
        # Store the parent loan records before the change happens
        loans_to_recompute = self.mapped('loan_id')
        
        # Call the original Odoo write method to save the changes
        res = super(HrLoanLine, self).write(vals)
        
        # If the 'paid' field was part of the update, recompute the totals
        if 'paid' in vals and loans_to_recompute:
            loans_to_recompute._compute_loan_amount()
            
        return res