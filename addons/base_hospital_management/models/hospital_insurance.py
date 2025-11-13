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


class HospitalInsurance(models.Model):
    """Class holding insurance details"""
    _name = 'hospital.insurance'
    _description = 'Hospital Insurance'

    name = fields.Char(string='Provider',
                       help='Name of the insurance provider', required=True,)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  help='Currency in which insurance will be '
                                       'calculated',
                                  default=lambda self: self.env.user.company_id
                                  .currency_id.id,
                                  required=True)
    total_coverage = fields.Monetary(string='Total Coverage',
                                     help='Total coverage of the insurance')
    fixed_amount = fields.Boolean(string="Fixed Amount Coverage",)
    item_based = fields.Boolean(string="is item based",)
    coverage_ids = fields.One2many('insurance.coverage.line',
                                   'insurance_id',
                                   string='coverage Lines',
                                   help='coverage Lines')
    price_ids = fields.One2many('insurance.pricing.line',
                                'insurance_id',
                                string='Price Lines',
                                help='Agreed Price List per product Lines')
    date_from = fields.Datetime(
        string="Date From",
        required=True
    )
    date_to = fields.Datetime(
        string="Date To",
        required=True
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("active", "Active"),
            ("reject", "Reject"),
            ("expired", "Expired"),
            ("canceled", "Canceled"),
        ],
        string="state",
        default="draft",
    )

    def action_approve(self):
        for rec in self:
            rec.state = "state"

    def action_cancel(self):
        for rec in self:
            rec.state = "canceled"

    def action_reject(self):
        for rec in self:
            rec.state = "reject"


class InsuranceCoverageLine(models.Model):
    _name = 'insurance.coverage.line'
    _description = 'insurance.coverage.line'

    insurance_id = fields.Many2one(
        'hospital.insurance', string='insurance', ondelete='cascade')
    is_fixed = fields.Boolean(related="insurance_id.fixed_amount",)
    is_item = fields.Boolean(related="insurance_id.item_based",)

    product_categ_id = fields.Many2one(
        'product.category', string='Item Category')
    product_id = fields.Many2one(
        'product.template', string='Item')
    percentage = fields.Float(string='percentage (%)', default=100)
    amount = fields.Float(string='Amount')


class InsurancePricingLine(models.Model):
    _name = 'insurance.pricing.line'
    _description = 'insurance.pricing.line'

    insurance_id = fields.Many2one(
        'hospital.insurance', string='insurance', ondelete='cascade')
    product_id = fields.Many2one(
        'product.template', string='Item', required=True)
    amount = fields.Float(string='Amount', required=True,)

    @api.onchange("product_id")
    def handle_product_price(self):
        for rec in self:
            rec.amount = rec.product_id.list_price
