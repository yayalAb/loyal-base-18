# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Subina P (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import api, fields, models


class LabTestResult(models.Model):
    """Class holding lab test result"""
    _name = 'lab.test.result'
    _description = 'Lab Test Result'
    _rec_name = 'test_id'
    _order = 'create_date desc'

    patient_id = fields.Many2one('res.partner', string='Patient',
                                 domain=[('patient_seq', 'not in',
                                          ['New', 'Employee', 'User'])],
                                 help='Patient for whom the test has been done')
    result = fields.Html(
        string='Result', compute="_compute_display_result", help='Result of the test')
    normal = fields.Char(string='Normal', help="The normal rate of the test")

    parent_id = fields.Many2one('patient.lab.test', string='Tests',
                                help='The tests for which the result'
                                     ' corresponds to')
    test_id = fields.Many2one('lab.test', string="Test Name",
                              help='Name of the test')
    uom_id = fields.Many2one('uom.uom', string='Unit',
                             related='test_id.uom_id',
                             help='Unit of the normal and result value')
    attachment = fields.Binary(string='Attachment', help='Result document')
    currency_id = fields.Many2one('res.currency',
                                  related='test_id.currency_id',
                                  string='Currency',
                                  help='Currency in which payments to be done')
    price = fields.Monetary(string='Cost', help='Cost for the test',
                            related='test_id.price')
    tax_ids = fields.Many2many('account.tax', string='Tax',
                               help='Tax for the test')
    state = fields.Selection(selection=[('processing', 'Processing'),
                                        ('published', 'Published')],
                             string='State', help='State of the result',
                             default='processing', compute='_compute_state')
    result_type = fields.Selection(
        selection=[
            ("yes", "Yes/No"),
            ("number", "Number"),
            ("range", "Range"),
            ("text", "Text"),
            ("selection", "Selection"),
        ],
        related='test_id.result_type',
        default="range",
        string="Result Type",
        required=True,
    )
    upper_panic_value = fields.Float(string='Upper Panic',
                                     help='Upper panic value for the test')
    lower_panic_value = fields.Float(string='Lower Panic',
                                     help='Lower panic value for the test')
    upper_limit = fields.Float(string='Upper Limit',
                               help='Upper limit for the test')
    lower_limit = fields.Float(string='Lower Limit',
                               help='Lower limit for the test')
    man_upper_limit = fields.Float(string="Man Upper Limit")
    man_upper_lower = fields.Float(string="Man Lower Limit")

    women_upper_limit = fields.Float(string="Women Upper Limit")
    women_upper_lower = fields.Float(string="Women Upper Limit")

    qc_uppern__limit = fields.Float(string="QC-Upper(N)")
    qc_lower_n_limit = fields.Float(string="QC-Lower(N)")

    qc_upper_ab_limit = fields.Float(string="QC-Upper(AB)")
    qc_lower_ab_limit = fields.Float(string="QC-Lower(AB)")

    mu_normal = fields.Float(string="MU-Normal")
    mu_abnormal = fields.Float(string="MU-Abnormal")

    uom_id = fields.Many2one('uom.uom', string='Unit of Measure',
                             help='Unit of Measure for the test')
    consult = fields.Html(string='Consult', help='Consult')
    result_htm = fields.Html(
        string="Default Result",
        sanitize=True,
        sanitize_tags=True,
        sanitize_attributes=True,
        sanitize_style=False,
        strip_style=False,
        strip_classes=False,
    )

    yes_or_no = fields.Selection(
        selection=[
            ("yes", "Yes"),
            ("no", "No"),
        ],
        default="yes",
        string="Defualt Result",
    )

    result_number = fields.Integer(
        string="Result Number",
    )
    result_selection = fields.Many2one(
        string="Result",
        comodel_name="lab.test.option",
    )

    @api.depends('result_number', 'result_htm', 'yes_or_no', 'result_selection')
    def _compute_display_result(self):
        for rec in self:
            if rec.result_type == 'yes':
                rec.result = rec.yes_or_no
            elif rec.result_type == 'text':
                rec.result = rec.result_htm
            elif rec.result_type == 'number' or rec.result_type == 'range':
                rec.result = str(rec.result_number)
            elif rec.result_type == 'selection':
                rec.result = rec.result_selection.name
            else:
                rec.result = ""

    @api.depends('attachment')
    def _compute_state(self):
        """Method for computing the state of result based on attachment"""
        for rec in self:
            if rec.attachment:
                rec.state = 'published'
            else:
                rec.state = 'processing'

    @api.model
    def print_test_results(self):
        """Method for printing rest result"""
        data = self.sudo().search([])
        context = []
        for rec in data:
            self.env.cr.execute(
                f"""SELECT id FROM ir_attachment WHERE res_id = {rec.id} 
                                            and res_model='lab.test.result' """)
            attachment_id = False
            attachment = self.env.cr.dictfetchall()
            if attachment:
                attachment_id = attachment[0]['id']
            context.append({
                'id': rec.id,
                'parent_id': rec.parent_id.test_id.name,
                'patient_id': [rec.parent_id.patient_id.id,
                               rec.parent_id.patient_id.name],
                'test_id': rec.test_id.name,
                'attachment_id': attachment_id,
                'normal': rec.normal,
                'result': rec.result,
                'unit': rec.uom_id.name if rec.uom_id else ''
            })
        return context
