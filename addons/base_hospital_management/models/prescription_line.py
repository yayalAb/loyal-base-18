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


class PrescriptionLine(models.Model):
    """Class holding prescription line details"""
    _name = 'prescription.line'
    _description = 'Prescription Lines'
    _rec_name = 'prescription_id'

    prescription_id = fields.Many2one('hospital.prescription',
                                      string='Prescription',
                                      help='Name of the prescription')

    medicine_id = fields.Many2one('product.template', domain=[
        '|', ('medicine_ok', '=', True), ('vaccine_ok', '=', True)],
        string='Medicine',
        help='Medicines or vaccines')
    medication_name = fields.Char(
        string='Medication Name',
        required=True,
        help="Start typing medication name for suggestions"
    )
    quantity = fields.Integer(string='Quantity', required=True,
                              help="The number of medicines for the time "
                                   "period")
    no_intakes = fields.Float(string='Intakes', required=True,
                              help="How much medicine want to take")
    time = fields.Selection(
        [('once', 'Once in a day'), ('twice', 'Twice in a Day'),
         ('thrice', 'Thrice in a day'), ('morning', 'In Morning'),
         ('noon', 'In Noon'), ('evening', 'In Evening')], string='Time',
        required=True,
        help='The interval for medicine intake')
    note = fields.Selection(
        [('before', 'Before Food'), ('after', 'After Food')],
        string='Before/ After Food',
        help='Whether the medicine to be taken before or after food')
    inpatient_id = fields.Many2one('hospital.inpatient',
                                   string='Inpatient',
                                   help='The inpatient corresponds to the '
                                        'prescription line')
    outpatient_id = fields.Many2one('hospital.outpatient',
                                    string='Outpatient',
                                    help='The outpatient corresponds to the '
                                         'prescription line')
    res_partner_id = fields.Many2one('res.partner',
                                     string='Patient',
                                     help='The outpatient corresponds to the '
                                          'prescription line',
                                     related='outpatient_id.patient_id')

    @api.model
    def get_medication_suggestions(self, search_term):
        """Return medication suggestions for auto-complete"""
        print(f"Searching for: {search_term}")
        if not search_term or len(search_term) < 2:
            return []

        # Search in existing prescription lines for common medications
        existing_medications = self.search_read(
            [('medication_name', 'ilike', search_term)],
            ['medication_name'],
            limit=10,
            order='medication_name'
        )

        # Remove duplicates and format suggestions
        suggestions = list(set([med['medication_name']
                           for med in existing_medications]))
        return suggestions[:10]
