from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.addons.VendorBid.utils.mail_utils import get_smtp_server_email

class SuppliesWizard(models.TransientModel):
    _name = 'supplies.wizard'
    _description = 'Supplies Wizard'

    supplies_rfp_id = fields.Many2one('supplies.rfp', string='Supplies RFP', required=True)
    selected_suppliers = fields.Many2many(
        'res.partner',
        string='Suppliers',
        required=True,
        domain="[('supplier_rank', '>', 0)]",
        
        help="Select the suppliers who will receive the RFP notification."
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        rfp_id = self.env.context.get('default_supplies_rfp_id')
        if rfp_id:
            suppliers = self.env['res.partner'].search([('supplier_rank', '>', 0)])
            res['selected_suppliers'] = [(6, 0, suppliers.ids)]
        return res


    def action_send(self):
        self.ensure_one()

        self.supplies_rfp_id.selected_suppliers = self.selected_suppliers

        email_values = {
            'email_from': get_smtp_server_email(self.env),
            'email_to': self.create_uid.login,
            'subject': f'RFP Approved {self.supplies_rfp_id.rfp_number}',
        }
        contexts = {
            'rfp_number': self.supplies_rfp_id.rfp_number,
            'company_name': self.env.company.name,
        }
        template = self.env.ref('VendorBid.email_template_model_supplies_rfp_approved_reviewer').sudo()
        template.with_context(**contexts).send_mail(self.supplies_rfp_id.id, email_values=email_values)

        if not self.selected_suppliers:
            raise UserError("Please select at least one supplier to notify for this RFP.")

        # Send email to each selected supplier
        template_supplier = self.env.ref('VendorBid.email_template_model_supplies_rfp_approved_supplier').sudo()
        email_values_supplier = {
            'email_from': get_smtp_server_email(self.env),
            'subject': f"New Request for Purchase Available {self.supplies_rfp_id.rfp_number}",
        }
        for partner in self.selected_suppliers:
            if partner.email:
                email_values_supplier['email_to'] = partner.email
                template_supplier.with_context(**contexts).send_mail(self.supplies_rfp_id.id, email_values=email_values_supplier)
            else:
                self.env.logger.warning(f"Supplier {partner.name} (ID: {partner.id}) has no email address. Skipping notification.")