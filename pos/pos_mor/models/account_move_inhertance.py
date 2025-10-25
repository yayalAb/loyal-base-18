from odoo.exceptions import UserError
from odoo import models, fields, api, _


class AccountMoveInherit(models.Model):
    _inherit = 'account.move'
    irn = fields.Char(
        string="IRN", readonly=True)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
        ('error', 'Error')], default='draft', string="MOR Status",  readonly=True)
    signed_qr = fields.Binary("Signed QR",  readonly=True)
    signed_invoice = fields.Text("Signed Invoice", readonly=True)
    mor_respons_ids = fields.One2many(
        comodel_name='mor.api.invoice',
        inverse_name='move_id',
        string='MOR API Communications'
    )

    # @api.model
    # def create(self, vals):
    #     invoice = super(AccountMoveInherit, self).create(vals)
    #     try:
    #         if len(invoice.invoice_line_ids) > 0:
    #             print("pppppppppppppppppppppppp")
    #             result = self.env['mor.api.invoice'].register_single_invoice(
    #                 invoice)

    #     except UserError as e:
    #         raise ValueError("error occured on session start", e)

    #     return invoice
    def send_invoice_single_to_mor(self):
        for rec in self:
            try:
                result = self.env['mor.api.invoice'].register_single_invoice(
                    rec)
            except UserError as e:
                raise UserError(
                    _("Error sending multi invoice to MoR: %s") % e)
        return True

    def send_invoice_multi_to_mor(self):
        try:
            result = self.env['mor.api.invoice'].register_multi_invoice(
                self)
        except UserError as e:
            raise UserError(
                _("Error sending multi invoice to MoR: %s") % e)
        return True

    def button_cancel(self):
        res = super(AccountMoveInherit, self).button_cancel()
        for invoice in self:
            irn = self.env['mor.api.invoice'].search(
                [('move_id', '=', self.id), ('status', '=', 'done')], limit=1)
            if irn:
                try:
                    self.env['mor.api.invoice'].cancel_single_invoice(
                        irn.irn, '1', "test")
                except UserError as e:
                    raise UserError(
                        _("Error sending invoice cancel to MoR: %s") % e)
        return res

    def cancel_multi_invoice_mor(self):
        try:
            result = self.env['mor.api.invoice'].cancel_bulk_invoice(
                self, '1', "test")
        except UserError as e:
            raise UserError(
                _("Error sending multi invoice cancel to MoR: %s") % e)
        return True

    def action_post(self):
        res = super(AccountMoveInherit, self).action_post()
        for invoice in self:
            irn = self.env['mor.api.invoice'].search(
                [('move_id', '=', self.id), ('move_id', '=', self.id)], limit=1)
            if irn:
                try:
                    self.env['mor.api.invoice'].verify_invoice(
                        irn.irn)
                except UserError as e:
                    raise UserError(
                        _("Error sending invoice verify to MoR: %s") % e)
        return res
