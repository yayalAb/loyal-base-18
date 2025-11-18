from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # ---------------------------------------------------
    # 🔧 Ministry of Revenue API Configuration
    # ---------------------------------------------------
    client_id = fields.Char(string="Client ID")
    client_secret = fields.Char(string="Client Secret")
    api_key = fields.Char(string="API Key")
    tin = fields.Char(string="TIN")
    base_url = fields.Char(
        string="Base URL",
        default="http://core.mor.gov.et",
        help="Base URL for the Ministry of Revenue API"
    )

    # ---------------------------------------------------
    # 💾 Save values to ir.config_parameter
    # ---------------------------------------------------
    def set_values(self):
        super().set_values()
        ICP = self.env['ir.config_parameter'].sudo()
        ICP.set_param('pos_mor.client_id', self.client_id or '')
        ICP.set_param('pos_mor.client_secret', self.client_secret or '')
        ICP.set_param('pos_mor.api_key', self.api_key or '')
        ICP.set_param('pos_mor.tin', self.tin or '')
        ICP.set_param('pos_mor.base_url', self.base_url or '')

    # ---------------------------------------------------
    # 📤 Load values from ir.config_parameter
    # ---------------------------------------------------
    @api.model
    def get_values(self):
        res = super().get_values()
        ICP = self.env['ir.config_parameter'].sudo()
        res.update(
            client_id=ICP.get_param('pos_mor.client_id', default=''),
            client_secret=ICP.get_param('pos_mor.client_secret', default=''),
            api_key=ICP.get_param('pos_mor.api_key', default=''),
            tin=ICP.get_param('pos_mor.tin', default=''),
            base_url=ICP.get_param(
                'pos_mor.base_url', default='http://core.mor.gov.et'),
        )
        return res
