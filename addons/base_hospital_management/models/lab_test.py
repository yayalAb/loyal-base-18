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
from odoo import fields, models, api


class LabTest(models.Model):
    """Class holding lab test details"""
    _name = 'lab.test'
    _description = 'Laboratory Test'

    lab_code = fields.Char(string='Code')
    name = fields.Char(string='Test', help='Name of the test')
    patient_lead = fields.Float(string='Time taken',
                                help='Time taken to get the result')
    price = fields.Monetary(string='Price', help="The cost for the test")
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self:
                                  self.env.user.company_id.currency_id.id,
                                  required=True, help='Currency in which '
                                                      'payments will be done')
    tax_ids = fields.Many2many('account.tax', string='Tax',
                               help='Tax for the test')
    medicine_ids = fields.One2many('lab.medicine.line',
                                   'test_id',
                                   string='Medicines',
                                   help='Medicines used for the test')
    test_type = fields.Selection(
        [('range', 'Range'), ('objective', 'Objective')],
        string='Type', required=True, help='Type of test')
    category_id = fields.Many2one('lab.test.category',
                                  string='Category',
                                  help='Category of the test')
    sample_type_id = fields.Many2one('lab.sample.type',
                                     string='Sample Type',
                                     help='Sample type for the test')
    result_type = fields.Selection(
        selection=[
            ("yes", "Yes/No"),
            ("number", "Number"),
            ("range", "Range"),
            ("text", "Text"),
            ("selection", "Selection"),
        ],
        default="range",
        string="Result Type",
        required=True,
    )
    lab_id = fields.Many2one('hospital.laboratory', string='Lab',
                             help='Lab in which test is doing')

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
    option_ids = fields.One2many('lab.test.option',
                                 'lab_test_id',
                                 string='Options',
                                 help='Option List')

    @api.model
    def create(self, vals):
        """Method for creating lab sequence number"""
        if vals.get('lab_code', 'New') == 'New':
            vals['lab_code'] = self.env['ir.sequence'].next_by_code(
                'lab.test') or 'New'
        return super().create(vals)


class SelectionList(models.Model):
    _name = 'lab.test.option'
    _description = 'lab.test.option'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    lab_test_id = fields.Many2one(
        string="Lab Test",
        comodel_name="lab.test",
    )
    name = fields.Char(
        string="Options",
    )
