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


class SalesOrder(models.Model):
    """Inherited to prevent creating patients while creating users"""
    _inherit = 'sale.order'

    prescription_id = fields.Many2one(
        string="Prescription",
        comodel_name="hospital.prescription",
        help="Link to the prescription associated with this sales order.",
        readonly=True
    )

    prescription_detail = fields.Html(
        string="Prescription Detail",
        compute="_compute_prescription_detail",
        store=True,
        readonly=True)

    def create(self, vals):
        order = super().create(vals)

        # If sale order has a prescription
        if order.prescription_id:
            order.prescription_id.write({'state': 'done'})

        return order

    @api.depends('prescription_id')
    def _compute_prescription_detail(self):
        """Fill HTML field with formatted table of prescription lines."""
        for rec in self:
            if not rec.prescription_id.prescription_line_ids:
                rec.prescription_detail = "<p>No prescription lines added.</p>"
                continue

            table_html = """
                <table border="1" cellspacing="0" cellpadding="4"
                       style="border-collapse: collapse; width: 100%;">
                    <thead>
                        <tr style="background-color:#f2f2f2;">
                            <th>Prescription</th>
                            <th>No. Intakes</th>
                            <th>Time</th>
                            <th>Note</th>
                            <th>Quantity</th>
                        </tr>
                    </thead>
                    <tbody>
            """

            for line in rec.prescription_id.prescription_line_ids:
                table_html += f"""
                    <tr>
                        <td>{line.medication_name or ''}</td>
                        <td>{line.no_intakes or ''}</td>
                        <td>{line.time or ''}</td>
                        <td>{line.note or ''}</td>
                        <td>{line.quantity or ''}</td>
                    </tr>
                """

            table_html += """
                    </tbody>
                </table>
            """

            rec.prescription_detail = table_html
