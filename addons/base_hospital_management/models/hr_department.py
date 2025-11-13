from odoo import api, fields, models


class Department(models.Model):
    """
    department.
    """
    _inherit = "hr.department"

    reg_fee_new_id = fields.Many2one(
        string="Registration Fee New",
        comodel_name="product.template",
        domain=[('categ_id.name', '=', 'Registration Fee')]
    )

    reg_fee_repeat_id = fields.Many2one(
        string="Registration Fee reapted",
        comodel_name="product.template",
        domain=[('categ_id.name', '=', 'Registration Fee')]
    )
    reg_fee_weekend_id = fields.Many2one(
        string="Registration Fee weekend/Night",
        comodel_name="product.template",
        domain=[('categ_id.name', '=', 'Registration Fee')]
    )
    reg_fee_holiday_id = fields.Many2one(
        string="Registration Fee Holiday",
        comodel_name="product.template",
        domain=[('categ_id.name', '=', 'Registration Fee')]
    )
    # is_default = fields.Boolean(
    #     string="Is default Department",
    # )
