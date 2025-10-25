# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'
    duplicate_bank_partner_ids = fields.Many2many(
        'res.partner')


class PayslipWithCustomColumns(models.Model):
    _inherit = 'hr.payslip'
    hr_contract_start = fields.Date(
        string="Start Date", related='contract_id.date_start', store=True, readonly=True)
    hr_contract_end = fields.Date(
        string="End Date", related='contract_id.date_end', store=True, readonly=True)

    attachment_salary = fields.Monetary(
        string="Attachment of Salary", compute='_calculate_all_rule_amounts', store=True)
    assignment_salary = fields.Monetary(
        string="Assignment of Salary", compute='_calculate_all_rule_amounts', store=True)
    child_support = fields.Monetary(
        string="Child Support", compute='_calculate_all_rule_amounts', store=True)
    deduction = fields.Monetary(
        string="Deduction", compute='_calculate_all_rule_amounts', store=True)
    pension = fields.Monetary(
        string="Pension", compute='_calculate_all_rule_amounts', store=True)
    income_tax = fields.Monetary(
        string="Income Tax", compute='_calculate_all_rule_amounts', store=True)
    reimbursement = fields.Monetary(
        string="Reimbursement", compute='_calculate_all_rule_amounts', store=True)
    house_rent_allowance = fields.Monetary(
        string="House Rent Allowance", compute='_calculate_all_rule_amounts', store=True)
    dearness_allowance = fields.Monetary(
        string="Dearness Allowance", compute='_calculate_all_rule_amounts', store=True)
    travel_allowance = fields.Monetary(
        string="Travel Allowance", compute='_calculate_all_rule_amounts', store=True)
    meal_allowance = fields.Monetary(
        string="Meal Allowance", compute='_calculate_all_rule_amounts', store=True)
    medical_allowance = fields.Monetary(
        string="Medical Allowance", compute='_calculate_all_rule_amounts', store=True)
    position_allowance = fields.Monetary(
        string="Position Allowance", compute='_calculate_all_rule_amounts', store=True)
    transport_home_allowance = fields.Monetary(
        string="Transport Home Allowance", compute='_calculate_all_rule_amounts', store=True)
    transport_work_allowance = fields.Monetary(
        string="Transport Work Allowance", compute='_calculate_all_rule_amounts', store=True)
    fuel_allowance = fields.Monetary(
        string="Fuel Allowance", compute='_calculate_all_rule_amounts', store=True)
    cash_indemnity_allowance = fields.Monetary(
        string="Cash Indemnity Allowance", compute='_calculate_all_rule_amounts', store=True)
    professional_allowance = fields.Monetary(
        string="Professional Allowance", compute='_calculate_all_rule_amounts', store=True)
    other_allowance = fields.Monetary(
        string="Other Allowance", compute='_calculate_all_rule_amounts', store=True)
    agreed_deduction = fields.Monetary(
        string="Agreed Deduction", compute='_calculate_all_rule_amounts', store=True)
    social_commite = fields.Monetary(
        string="Social Committee", compute='_calculate_all_rule_amounts', store=True)
    none_taxiable_transport_allowance = fields.Monetary(
        string="Non-Taxiable Transport Allowance", compute='_calculate_all_rule_amounts',
        store=True)

    employee_bank_id = fields.Many2one(
        'res.bank',
        string="Bank",
        related='employee_id.bank_account_id.bank_id',
        store=True,
        readonly=True
    )

    calculate_active_rate = fields.Float(
        string="active rate ",
        compute='_calculate_active_rate',
    )

    @api.depends('employee_id', 'date_from', 'date_to', 'contract_id.date_start', 'contract_id.date_end')
    def _calculate_active_rate(self):
        for record in self:
            rate = 0.0
            if record.contract_id and record.date_from and record.date_to:
                # contract dates
                start_date = record.contract_id.date_start
                end_date = record.contract_id.date_end or record.date_to

                # period dates
                period_start = record.date_from
                period_end = record.date_to

                # find overlap between contract and payslip period
                overlap_start = max(start_date, period_start)
                overlap_end = min(end_date, period_end)

                if overlap_start <= overlap_end:
                    total_days = (period_end - period_start).days + 1
                    active_days = (overlap_end - overlap_start).days + 1
                    rate = active_days / total_days if total_days > 0 else 0.0

            record.calculate_active_rate = rate

    @api.depends('line_ids.code', 'line_ids.total')
    def _calculate_all_rule_amounts(self):
        target_rule_codes = [
            'ATTACH_SALARY', 'ASSIG_SALARY', 'CHILD_SUPPORT', 'DEDUCTION', 'PENSION', 'INTAX', 'REIMBURSEMENT',
            'HRA', 'DA', 'TRA', 'MEA', 'MEDA', 'POSA', 'THA', 'TWA', 'FUEL', 'CIA', 'PROA','OTHA', 'AGREEDDED', 'TNONTAX', 'SOCC'
        ]

        for payslip in self:
            rule_amounts = {
                line.code: line.total
                for line in payslip.line_ids
                if line.code in target_rule_codes
            }
            payslip.attachment_salary = rule_amounts.get('ATTACH_SALARY', 0.0)
            payslip.assignment_salary = rule_amounts.get('ASSIG_SALARY', 0.0)
            payslip.child_support = rule_amounts.get('CHILD_SUPPORT', 0.0)
            payslip.deduction = rule_amounts.get('DEDUCTION', 0.0)
            payslip.pension = rule_amounts.get('PENSION', 0.0)
            payslip.income_tax = rule_amounts.get('INTAX', 0.0)
            payslip.reimbursement = rule_amounts.get('REIMBURSEMENT', 0.0)
            payslip.house_rent_allowance = rule_amounts.get('HRA', 0.0)
            payslip.dearness_allowance = rule_amounts.get('DA', 0.0)
            payslip.travel_allowance = rule_amounts.get('TRA', 0.0)
            payslip.meal_allowance = rule_amounts.get('MEA', 0.0)
            payslip.medical_allowance = rule_amounts.get('MEDA', 0.0)
            payslip.position_allowance = rule_amounts.get('POSA', 0.0)
            payslip.transport_home_allowance = rule_amounts.get('THA', 0.0)
            payslip.transport_work_allowance = rule_amounts.get('TWA', 0.0)
            payslip.fuel_allowance = rule_amounts.get('FUEL', 0.0)
            payslip.cash_indemnity_allowance = rule_amounts.get('CIA', 0.0)
            payslip.professional_allowance = rule_amounts.get('PROA', 0.0)
            payslip.other_allowance = rule_amounts.get('OTHA', 0.0)
            payslip.agreed_deduction = rule_amounts.get('AGREEDDED', 0.0)
            payslip.none_taxiable_transport_allowance = rule_amounts.get(
                'TNONTAX', 0.0)
            payslip.social_commite = rule_amounts.get(
                'SOCC', 0.0)
