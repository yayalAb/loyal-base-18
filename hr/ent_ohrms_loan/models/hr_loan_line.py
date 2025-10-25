# -*- coding: utf-8 -*-
################################################################################
#
#    A part of OpenHRMS Project <https://www.openhrms.com>
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
################################################################################
from odoo import fields, models


class HrLoanLine(models.Model):
    """Inherits the model hr.loan.line for creating installment details"""
    _name = "hr.loan.line"
    _description = "Installment Line"

    date = fields.Date(string="Payment Date", required=True,
                       help="Date of the payment")
    employee_id = fields.Many2one(comodel_name='hr.employee', string="Employee",
                                  help="Employee of Loan Line")
    amount = fields.Float(string="Amount", required=True, help="Loan Amount")
    paid = fields.Boolean(string="Paid", help="Loan is Paid")
    loan_id = fields.Many2one(comodel_name='hr.loan', string="Loan Ref.",
                              help="Loan Reference")
    payslip_id = fields.Many2one(comodel_name='hr.payslip',
                                 string="Payslip Ref.",
                                 help="Payslip Reference")
