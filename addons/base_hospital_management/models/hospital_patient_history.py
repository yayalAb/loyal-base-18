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


class HospitalPateintHistory(models.Model):
    """Class holding insurance details"""
    _name = 'hospital.patient.history'
    _description = 'hospital.patient.history'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    history_type = fields.Selection(
        selection=[
            ("history", "Patient History"),
            ("physical", "Physical Findings"),
            ("chronic", "Chronic Disease Assessment"),
        ],
        default="history",
        string="History Type",
        required=True,
    )
    result_type = fields.Selection(
        selection=[
            ("yes", "Yes/No"),
            ("text", "Text"),
            ("number", "Number"),
            ("long", "Long Text"),
            ("selection", "Selection"),
        ],
        default="yes",
        string="Result Type",
        required=True,
    )
    name = fields.Char(
        string="Name",
        required=True,
    )
    default_value_htm = fields.Html(
        string="Default Value",
        default="Blank"
    )
    default_value_char = fields.Char(
        string="Default Value",
        default="Blank"
    )
    default_value_float = fields.Float(
        string="Default Value",
        default=0.0
    )
    default_value_boolean = fields.Boolean(
        string="Default Value",
        default=True
    )
    default_value_yes_no = fields.Selection(
        selection=[
            ("yes", "Yes"),
            ("no", "No"),
        ],
        default="no",
        string="Default Value",
    )
    option_ids = fields.One2many('patient.history.option',
                                 'history_id',
                                 string='Options',
                                 help='Option List')


class SelectionList(models.Model):
    _name = 'patient.history.option'
    _description = 'patient.history.option'
    history_id = fields.Many2one(
        string="History",
        comodel_name="hospital.patient.history",
    )
    name = fields.Char(
        string="Options",
    )


class PhysicalFinding(models.Model):
    _name = 'patient.history'
    _description = 'patient.history'

    patient_id = fields.Many2one(
        'res.partner', string='Patient', ondelete='cascade')
    physical_patient_id = fields.Many2one(
        'res.partner', string='Patient', ondelete='cascade')
    cronic_patient_id = fields.Many2one(
        'res.partner', string='Patient', ondelete='cascade')
    history_datetime = fields.Datetime(
        string="Date",
        default=lambda self: fields.Datetime.now()
    )

    history_id = fields.Many2one(
        'hospital.patient.history', string='History')
    hist_type = fields.Selection(
        selection=[
            ("history", "Patient History"),
            ("physical", "Physical Findings"),
            ("chronic", "Chronic Disease Assessment"),
        ],
        default="history",
        related="history_id.history_type",
        store=True
    )
    result_type = fields.Selection(
        selection=[
            ("yes", "Yes/No"),
            ("text", "Text"),
            ("number", "Number"),
            ("long", "Long Text"),
            ("selection", "Selection"),

        ],
        related="history_id.result_type",
        default="yes",
        string="Result Type",
    )

    result_htm = fields.Html(
        string="Result",
    )
    result_char = fields.Char(
        string="Result",
    )
    result_float = fields.Float(
        string="Result",
    )
    result_boolean = fields.Boolean(
        string="Result",
    )
    history_date = fields.Date(
        string="Date",
        compute='_compute_history_date',
        store=True
    )
    result_selection = fields.Many2one(
        string="Option",
        comodel_name="patient.history.option",
        domain="[('id', '=', history_id)]"

    )
    default_value_yes_no = fields.Selection(
        selection=[
            ("yes", "Yes"),
            ("no", "No"),
        ],
        string="Result",

    )

    display_result = fields.Char(
        string="Result",
        compute="_compute_display_result"
    )
    selection = [
        ("yes", "Yes/No"),
        ("text", "Text"),
        ("number", "Number"),
        ("long", "Long Text"),
        ("selection", "Selection"),

    ],

    @api.onchange('history_id')
    def _onchange_history_id(self):
        if self.result_type == "long":
            self.result_htm = self.history_id.default_value_html
        elif self.result_type == "text":
            self.result_char = self.history_id.default_value_char
        elif self.result_type == "number":
            self.result_float = self.history_id.default_value_float
        elif self.result_type == "yes":
            self.default_value_yes_no = self.history_id.default_value_yes_no

    @api.depends('result_boolean', 'result_char', 'result_float', 'result_htm', 'result_selection')
    def _compute_display_result(self):
        for rec in self:
            if rec.result_boolean:
                rec.display_result = "Yes" if rec.result_boolean else "No"
            elif rec.result_char:
                rec.display_result = rec.result_char
            elif rec.result_float:
                rec.display_result = str(rec.result_float)
            elif rec.result_htm:
                rec.display_result = rec.result_htm
            elif rec.result_selection:
                rec.display_result = rec.result_selection.name
            else:
                rec.display_result = ""

    @api.depends('history_datetime')
    def _compute_history_date(self):
        for rec in self:
            rec.history_date = rec.history_datetime.date() if rec.history_datetime else False
