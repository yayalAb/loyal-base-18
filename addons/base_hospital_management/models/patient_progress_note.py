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
from odoo.exceptions import ValidationError


class PatientProgressNote(models.Model):
    """Class holding Patient room details"""
    _name = 'patient.progress.note'
    _description = 'patient progress note'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_recorded desc"

    patient_id = fields.Many2one('res.partner', string='Patient',
                                 help='Patient')
    patient_type = fields.Selection(
        selection=[
            ("opd", "OPD"),
            ("ipd", "IPD"),
        ], string="Type", default="opd", required=True,)
    problem = fields.Html(string="Problem")
    subjective = fields.Html(string="subjective")
    objective = fields.Html(string="Objective")
    investigation_result = fields.Html(string="Investigation Result")
    assessment = fields.Html(string="Assessment")
    plan = fields.Html(string="Plan")
    date_recorded = fields.Datetime(
        string='Date', default=fields.Datetime.now)

    @api.constrains("problem", "subjective", "objective", "investigation_result",
                    "assessment", "plan")
    def _check_name_description(self):
        for record in self:
            if not record.problem and not record.subjective and not record.objective and not record.investigation_result and not record.assessment and not record.plan:
                raise ValidationError(
                    "You cannot create a progress note without any details.")
