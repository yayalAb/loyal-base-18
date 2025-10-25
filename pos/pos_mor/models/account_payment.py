from odoo.exceptions import UserError
from odoo import models, fields, api, _


class AccountPaymentInh(models.Model):
    _inherit = 'account.payment'

    def action_send_to_mor(self):
        for payment in self:
            try:
                self.env['mor.api.receipt'].register_single_receipt(
                    payment)
            except UserError as e:
                raise UserError(
                    _("Error sending receipt to MoR: %s") % e)
        return True

    def action_post(self):
        res = super(AccountPaymentInh, self).action_post()
        for payment in self:

            # irn = self.env['mor.api.invoice'].search(
            #     [('move_id', '=', self.id), ('move_id', '=', self.id)], limit=1)
            # if irn:
            try:
                self.env['mor.api.receipt'].register_single_receipt(
                    payment)
            except UserError as e:
                raise UserError(
                    _("Error sending receipt to MoR: %s") % e)
            return res
