
from odoo import fields, models


class posConfig(models.Model):
    """ THe class ResUsers is used to inherit res.users """
    _inherit = "pos.config"

    pos_conf_imag = fields.Binary(string="POS Configuration Logo")
