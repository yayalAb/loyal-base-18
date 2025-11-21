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


class OrderSheet(models.Model):
    """Class holding Patient lab test details"""
    _name = 'order.sheet'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = 'Order Sheet'

    patient_id = fields.Many2one(
        'res.partner', string='Patient')
    out_patient_id = fields.Many2one(
        'hospital.outpatient', string='Outpatient')
    in_patient_id = fields.Many2one(
        'hospital.inpatient', string=' Inpatient')
    order = fields.Html(string='Order Details',  required=True,)
    date = fields.Datetime(string='Date', default=fields.Datetime.now)
    status = fields.Selection(
        [('draft', 'Draft'), ('seen', 'Seen')], string='Status', default='draft')

    def action_seen(self):
        """Method to archive the order sheet"""
        for record in self:
            record.status = 'seen'

    def action_done(self):
        """Method to mark the order sheet as done"""
        for record in self:
            record.status = 'done'
