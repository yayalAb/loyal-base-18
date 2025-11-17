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
    patient_lead = fields.Float(string='Result Within',
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

    @api.model
    def create(self, vals):
        """Method for creating lab sequence number"""
        if vals.get('lab_code', 'New') == 'New':
            vals['lab_code'] = self.env['ir.sequence'].next_by_code(
                'lab.test') or 'New'
        return super().create(vals)
