from odoo import models, api
from odoo.exceptions import UserError


class PosSession(models.Model):
    _inherit = 'pos.session'

    @api.model
    def create(self, vals):
        # 1️⃣ Create the POS session as usual
        session = super(PosSession, self).create(vals)

        # 2️⃣ Trigger MoR login automatically
        try:
            mor_api = self.env['mor.api'].sudo()
            result = mor_api.ensure_valid_token()
            # Optional: log success

        except UserError as e:
            raise ValueError("error occured on session start")

        return session
