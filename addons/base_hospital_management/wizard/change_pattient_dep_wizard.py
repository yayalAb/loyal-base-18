# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import date, datetime
from odoo.exceptions import UserError, ValidationError


class ChangePatientDepartment(models.TransientModel):
    _name = 'patient.department.change'
    _description = 'patient'

    patient_id = fields.Many2one(
        string="",
        comodel_name="res.partner",
    )

    old_department_id = fields.Many2one(
        string="Old Department",
        comodel_name="hr.department",
    )
    new_department_id = fields.Many2one(
        string="New Department",
        comodel_name="hr.department",
        required=True,
        domain="[('id', '!=', old_department_id)]"
    )

    def change_patient_department(self):
        for rec in self:
            rec.patient_id.write({
                "department_id": rec.new_department_id.id
            })
            rec.patient_id.action_create_invoice(rec.patient_id)
