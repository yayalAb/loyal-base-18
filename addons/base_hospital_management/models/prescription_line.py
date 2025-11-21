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
    _name = 'hospital.prescription'
    _description = 'Prescription'
    _order = 'create_date desc'
    _rec_name = 'res_partner_id'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    name = fields.Char(string='Prescription Reference',
                       help='The reference of the prescription',
                       compute='prescription_name_compute', store=True)
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
                                     compute="compute_patient_id",
                                     help='The outpatient corresponds to the '
                                          'prescription line',)

    @api.depends('inpatient_id', 'outpatient_id')
    def compute_patient_id(self):
        """Compute patient id based on inpatient or outpatient"""
        for record in self:
            if record.inpatient_id:
                record.res_partner_id = record.inpatient_id.patient_id.id
            elif record.outpatient_id:
                record.res_partner_id = record.outpatient_id.patient_id.id
            else:
                record.res_partner_id = False
    patient_type = fields.Selection(
        selection=[
            ("opd", "OPD"),
            ("ipd", "IPD"),
        ],
        compute='_compute_patient_type',
        string="Patient Type",
    )
    state = fields.Selection(
        selection=[
            ("new", "New"),
            ("done", "Done"),
        ],
        string="State",
        default="new",
        help="State of the prescription line",
    )
    prescription_line_ids = fields.One2many(
        'prescription.line',
        'prescription_id',
        string='Prescription Lines',
        help='The prescription lines associated with this prescription'
    )

    number_of_lines = fields.Integer(
        string='Number of Lines',
        compute="compute_number_of_lines",
        help='The number of prescription lines associated with this ')

    @api.depends('inpatient_id', 'outpatient_id')
    def _compute_patient_type(self):
        """Compute patient type based on inpatient or outpatient"""
        for record in self:
            if record.inpatient_id:
                record.patient_type = 'ipd'
            elif record.outpatient_id:
                record.patient_type = 'opd'
            else:
                record.patient_type = False

    @api.depends('prescription_line_ids')
    def compute_number_of_lines(self):
        """Compute the number of prescription lines"""
        for record in self:
            record.number_of_lines = len(record.prescription_line_ids)

    @api.depends('prescription_line_ids')
    def prescription_name_compute(self):
        """Compute prescription name"""
        for record in self:
            names = record.prescription_line_ids.mapped("medication_name")
            record.name = ", ".join(names) if names else ""

    def action_create_sale_order(self):
        """Create sale order from prescription"""
        price_list_id = False
        if self.patient_type == 'opd':
            price_list = self.env['price.patient.mapping'].search(
                [('apply_on', '=', 'opd')], limit=1)
        else:
            price_list = self.env['price.patient.mapping'].search(
                [('apply_on', '=', 'ipd')], limit=1)
        if price_list:
            price_list_id = price_list.price_list_id.id

        return {
            'name': 'Create Sale Order',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_prescription_id': self.id,
                'default_partner_id': self.res_partner_id.id,
                'default_pricelist_id': price_list_id,
            },
        }


class PrescriptionLine(models.Model):
    """Class holding prescription line details"""
    _name = 'prescription.line'
    _description = 'Prescription Lines'
    _rec_name = 'medication_name'
    _order = 'create_date desc'

    prescription_id = fields.Many2one('hospital.prescription',
                                      string='Prescription',)

    medicine_id = fields.Many2one('product.template', domain=[
        '|', ('medicine_ok', '=', True), ('vaccine_ok', '=', True)],
        string='Medicine',
        help='Medicines or vaccines')
    medication_name = fields.Char(
        string='Medication Name',
        required=True,
        help="Start typing medication name for suggestions"
    )
    quantity = fields.Integer(string='Quantity',
                              help="The number of medicines for the time "
                                   "period")
    no_intakes = fields.Float(string='Intakes',
                              default=1.0,
                              help="How much medicine want to take")
    time = fields.Selection(
        [('once', 'Once in a day'), ('twice', 'Twice in a Day'),
         ('thrice', 'Thrice in a day'), ('morning', 'In Morning'),
         ('noon', 'In Noon'), ('evening', 'In Evening')], string='Time',
        help='The interval for medicine intake')
    note = fields.Selection(
        [('before', 'Before Food'), ('after', 'After Food')],
        string='Before/ After Food',
        help='Whether the medicine to be taken before or after food')

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
