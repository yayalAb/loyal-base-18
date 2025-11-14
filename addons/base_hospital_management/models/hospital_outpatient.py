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
import base64
from odoo import api, fields, models
from odoo.exceptions import ValidationError
from datetime import timedelta


class HospitalOutpatient(models.Model):
    """Class holding Outpatient details"""
    _name = 'hospital.outpatient'
    _description = 'Hospital Outpatient'
    _rec_name = 'op_reference'
    _inherit = 'mail.thread'
    _order = 'op_date desc'

    op_reference = fields.Char(string="OP Reference", readonly=True,
                               default='New',
                               help='Op reference number of the patient')
    patient_id = fields.Many2one('res.partner',
                                 domain=[('patient_seq', 'not in',
                                          ['New', 'Employee', 'User'])],
                                 string='Patient ID', help='Id of the patient',
                                 required=True)
    doctor_id = fields.Many2one('doctor.allocation',
                                string='Doctor',
                                help='Select the doctor',
                                # required=True,
                                domain=[('slot_remaining', '>', 0),
                                        ('date', '=', fields.date.today()),
                                        ('state', '=', 'confirm')])
    department_id = fields.Many2one(
        string="Department",
        comodel_name="hr.department",
        required=True,
    )
    card_fee = fields.Float(
        string="Card Fee",
        compute="_compute_registration_fee",
        digits=(10, 2),
    )

    op_date = fields.Date(default=fields.Date.today(), string='Date',
                          help='Date of OP')
    reason = fields.Text(string='Reason', help='Reason for visiting hospital')
    test_count = fields.Integer(string='Test Created',
                                help='Number of tests created for the patient',
                                compute='_compute_test_count')
    test_ids = fields.One2many('lab.test.line', 'op_id',
                               string='Tests',
                               help='Tests for the patient')
    state = fields.Selection(
        [('draft', 'Draft'), ('op', 'OP'), ('inpatient', 'In Patient'),
         ('invoice', 'Invoiced'), ('cancel', 'Canceled')],
        default='draft', string='State', help='State of the outpatient')
    prescription_ids = fields.One2many('prescription.line',
                                       'outpatient_id',
                                       string='Prescription',
                                       help='Prescription for the patient')
    invoiced = fields.Boolean(default=False, string='Invoiced',
                              help='True for invoiced')
    invoice_id = fields.Many2one('account.move', copy=False,
                                 string='Invoice',
                                 help='Invoice of the patient')
    attachment_id = fields.Many2one('ir.attachment',
                                    string='Attachment',
                                    help='Attachments related to the'
                                         ' outpatient')
    active = fields.Boolean(string='Active', help='True for active patients',
                            default=True)
    slot = fields.Float(string='Slot', help='Slot for the patient',
                        copy=False, readonly=True)
    is_sale_created = fields.Boolean(string='Sale Created',
                                     help='True if sale order created')
    day_type = fields.Selection([
        ('working', 'Working Day'),
        ('night', 'Night/Weekend'),
        ('holiday', 'Holiday'),
        ('repeat', 'Repeat'),
    ], string="Day Type", compute="_compute_daytype", default="working",)
    product_id = fields.Many2one(
        comodel_name="product.template",
        compute="_compute_registration_fee"
    )

    def _compute_daytype(self):
        for rec in self:
            rec.day_type = "working"

    @api.depends("department_id", "day_type")
    def _compute_registration_fee(self):
        for rec in self:
            fee = 0.0
            department = rec.department_id
            product_id = False
            today = fields.Datetime.now()
            if (rec.department_id == rec.patient_id.department_id) and (rec.patient_id.card_fee > 0 and rec.patient_id.valid_untill and rec.patient_id.valid_untill >= today):
                rec.card_fee = 0.0
                product_id = False
            else:
                if not department:
                    rec.card_fee = 0.0
                    continue
                if rec.day_type == "working" and department.reg_fee_new_id:
                    fee = department.reg_fee_new_id.list_price
                    product_id = department.reg_fee_new_id.id,
                elif rec.day_type == "repeat" and department.reg_fee_repeat_id:
                    fee = department.reg_fee_repeat_id.list_price
                    product_id = department.reg_fee_repeat_id.id
                elif rec.day_type == "night" and department.reg_fee_weekend_id:
                    fee = department.reg_fee_weekend_id.list_price
                    product_id = department.reg_fee_weekend_id.id
                elif rec.day_type == "holiday" and department.reg_fee_holiday_id:
                    fee = department.reg_fee_holiday_id.list_price
                    product_id = department.reg_fee_holiday_id.id

            rec.card_fee = fee
            rec.product_id = product_id

    def action_create_invoice(self, record):
        today = fields.Datetime.now()
        if (record.department_id == record.patient_id.department_id) and (record.patient_id.card_fee > 0 and record.patient_id.valid_untill and record.patient_id.valid_untill >= today):
            print("invoice  free: ")
        else:
            days = int(self.env['ir.config_parameter'].sudo().get_param(
                'hospital.patient_validity_days', default=10))

            valid_untill = fields.Date.context_today(
                record) + timedelta(days=days)
            record.patient_id.write({
                'card_fee': record.card_fee,
                'department_id': record.department_id,
                'valid_untill': valid_untill

            })
            invoice_vals = {
                'move_type': 'out_invoice',  # customer invoice
                'partner_id': record.patient_id.id,
                'invoice_date': fields.Date.context_today(self),
                'invoice_line_ids': [(0, 0, {
                    'product_id': record.product_id.id,
                    'quantity': 1.0,
                    'price_unit': record.card_fee,
                    'name': record.product_id.name or 'Registration Fee',
                })],
            }
            invoice = self.env['account.move'].create(invoice_vals)

    @api.model
    def create(self, vals):
        """Op number generator"""

        if vals.get('op_reference', 'New') == 'New':
            last_op = self.search([
                ('doctor_id', '=', vals.get('department_id')),
                ('op_reference', '!=', 'New'),
            ], order='create_date desc', limit=1)
            if last_op:
                last_number = int(last_op.op_reference[2:])
                new_number = last_number + 1
                vals['op_reference'] = f'OP{str(new_number).zfill(3)}'
            else:
                vals['op_reference'] = 'OP001'
        # if self.search([
        #     ('patient_id', '=', vals['patient_id']),
        #     ('department_id', '=', vals['department_id'])
        # ]):
        #     raise ValidationError(
        #         'An OP already exists for this patient under the specified'
        #         'allocation')
        record = super().create(vals)
        if record.card_fee > 0:
            self.action_create_invoice(record)
        record.patient_id.write({
            "state": "opd"


        })
        return record

    @api.depends('test_ids')
    def _compute_test_count(self):
        """Computes the value of test count"""
        self.test_count = len(self.test_ids.ids)

    @api.onchange('op_date')
    def _onchange_op_date(self):
        """Method for updating the doamil of doctor_id"""
        self.doctor_id = False
        return {'domain': {'doctor_id': [('slot_remaining', '>', 0),
                                         ('date', '=', self.op_date),
                                         ('state', '=', 'confirm'), (
                                             'patient_type', 'in',
                                             [False, 'outpatient'])]}}

    @api.model
    def action_row_click_data(self, op_reference):
        """Returns data to be displayed on clicking op row"""
        op_record = self.env['hospital.outpatient'].sudo().search(
            [('op_reference', '=', op_reference),
             ('active', 'in', [True, False])])
        op_data = [op_reference, op_record.patient_id.patient_seq,
                   op_record.patient_id.name, str(op_record.op_date),
                   op_record.slot, op_record.reason,
                   op_record.doctor_id.doctor_id.name,
                   op_record.is_sale_created]
        medicines = []
        for rec in op_record.prescription_ids:
            medicines.append(
                [rec.medicine_id.name, rec.no_intakes, rec.time, rec.note,
                 rec.quantity, rec.medicine_id.id])
        return {
            'op_data': op_data,
            'medicines': medicines
        }

    @api.model
    def create_medicine_sale_order(self, order_id):
        """Method for creating sale order for medicines"""
        order = self.sudo().search([('op_reference', 'ilike', order_id)])
        sale_order = self.env['sale.order'].sudo().create({
            'partner_id': order.patient_id.id,
        })
        for i in order.prescription_ids:
            self.env['sale.order.line'].sudo().create({
                'product_id': i.medicine_id.id,
                'product_uom_qty': i.quantity,
                'order': sale_order.id,
            })
            self.create_invoice()

    @api.model
    def create_file(self, rec_id):
        """Method for creating prescription"""
        record = self.env['hospital.outpatient'].sudo().browse(rec_id)
        p_list = []
        data = False
        for rec in record.prescription_ids:
            p_list.append({
                'medicine': rec.medicine_id.name,
                'intake': rec.no_intakes,
                'time': rec.time.capitalize(),
                'quantity': rec.quantity,
                'note': rec.note.capitalize() if rec.note else '',
            })
            data = {
                'datas': p_list,
                'date': record.op_date,
                'patient_name': record.patient_id.name,
                'doctor_name': record.doctor_id.doctor_id.name,
            }
        pdf = self.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'base_hospital_management.action_report_patient_prescription',
            rec_id, data=data)
        record.attachment_id = self.env['ir.attachment'].sudo().create({
            'datas': base64.b64encode(pdf[0]),
            'name': "Prescription",
            'type': 'binary',
            'res_model': 'hospital.outpatient',
            'res_id': rec_id,
        })
        return {
            'url': f'/web/content'
            f'/{record.attachment_id.id}?download=true&amp'
            f';access_token=',
        }

    @api.model
    def create_new_out_patient(self, kw):
        """Create out patient from receptionist dashboard"""
        if kw['id']:
            partner = self.env['res.partner'].sudo().search(
                ['|', ('barcode', '=', kw['id']),
                 ('phone', '=', kw['op_phone'])])
            self.sudo().create({
                'patient_id': partner.id,
                'op_date': kw['date'],
                'reason': kw['reason'],
                'slot': kw['slot'],
                'doctor_id': kw['doctor'],
            })

    def action_create_lab_test(self):
        """Button action for creating a lab test"""
        return {
            'name': 'Create Lab Test',
            'res_model': 'lab.test.line',
            'view_mode': 'form',
            'views': [[False, 'form']],
            'target': 'current',
            'type': 'ir.actions.act_window',
            'context': {
                'default_patient_id': self.patient_id.id,
                'default_doctor_id': self.doctor_id.id,
                'default_patient_type': 'outpatient',
                'default_op_id': self.id
            }
        }

    def action_view_test(self):
        """Method for viewing all lab tests"""
        return {
            'name': 'Created Tests',
            'res_model': 'lab.test.line',
            'view_mode': 'list,form',
            'target': 'current',
            'type': 'ir.actions.act_window',
            'domain': [
                ('patient_type', '=', 'outpatient'),
                ('op_id', '=', self.id)
            ]
        }

    def action_convert_to_inpatient(self):
        """Converts an outpatient to inpatient"""
        self.state = 'inpatient'
        return {
            'name': 'Convert to Inpatient',
            'res_model': 'hospital.inpatient',
            'view_mode': 'form',
            'target': 'current',
            'type': 'ir.actions.act_window',
            'context': {
                'default_patient_id': self.patient_id.id,
                'default_attending_doctor_id': self.doctor_id.doctor_id.id,
            }
        }

    def action_op_cancel(self):
        """Button action for cancelling an op"""
        self.state = 'cancel'

    def action_confirm(self):
        """Button action for confirming an op"""
        if self.doctor_id.latest_slot == 0:
            self.slot = self.doctor_id.work_from
        else:
            self.slot = self.doctor_id.latest_slot + self.doctor_id.time_avg
        self.doctor_id.latest_slot = self.slot
        self.state = 'op'

    def create_invoice(self):
        """Method for creating invoice"""
        self.state = 'invoice'
        self.invoice_id = self.env['account.move'].sudo().create({
            'move_type': 'out_invoice',
            'date': fields.Date.today(),
            'invoice_date': fields.Date.today(),
            'partner_id': self.patient_id.id,
            'invoice_line_ids': [(
                0, 0, {
                    'name': 'Consultation fee',
                    'quantity': 1,
                    'price_unit': self.doctor_id.doctor_id.consultancy_charge,
                }
            )]
        })
        self.invoiced = True

    def action_view_invoice(self):
        """Method for viewing invoice"""
        return {
            'name': 'Invoice',
            'domain': [('id', '=', self.invoice_id.id)],
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'context': {'create': False},
        }

    def action_print_prescription(self):
        """Method for printing prescription"""
        data = False
        p_list = []
        for rec in self.prescription_ids:
            datas = {
                'medicine': rec.medicine_id.name,
                'intake': rec.no_intakes,
                'time': rec.time.capitalize(),
                'quantity': rec.quantity,
                'note': rec.note.capitalize(),
            }
            p_list.append(datas)
            data = {
                'datas': p_list,
                'date': self.op_date,
                'patient_name': self.patient_id.name,
                'doctor_name': self.doctor_id.doctor_id.name,
            }
        return self.env.ref(
            'base_hospital_management.action_report_patient_prescription'). \
            report_action(self, data=data)
