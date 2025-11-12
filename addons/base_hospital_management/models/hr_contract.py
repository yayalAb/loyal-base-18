from odoo.exceptions import ValidationError
from odoo import models, fields


class HrContractCommissionLine(models.Model):
    _name = 'hr.contract.commission.line'
    _description = 'Commission Line for HR Contract'

    contract_id = fields.Many2one(
        'hr.contract', string='Contract', ondelete='cascade')
    product_categ_id = fields.Many2one(
        'product.category', string='Product Category', required=True)
    percentage = fields.Float(string='Commission (%)', required=True)
    applied_for = fields.Selection(
        selection=[
            ("created", "Created"),
            ("department", "Department"),
        ],
        string="Applied for",
    )

    @api.constrains('percentage')
    def _check_positive_percentage(self):
        for rec in self:
            if rec.percentage <= 0:
                raise ValidationError(
                    "Commission percentage must be a positive number greater than 0.")
            if rec.percentage > 100:
                raise ValidationError(
                    "Commission percentage must no be  greater than 100.")


class HrContract(models.Model):
    _inherit = 'hr.contract'
    commission_line_ids = fields.One2many('hr.contract.commission.line',
                                          'contract_id',
                                          string='Commission Lines',
                                          help='Commission Lines')
