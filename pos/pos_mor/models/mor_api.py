import requests
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta


class MorApi(models.Model):
    _name = 'mor.api'
    _description = 'Ministry of Revenue API Integration'
    _order = 'create_date desc'

    access_token = fields.Char(string="Access Token")
    refresh_token = fields.Char(string="Refresh Token")
    encryption_key = fields.Char(string="Encryption Key")
    token_expiry = fields.Datetime(string="Token Expiry")
    status = fields.foo = fields.Selection(
        selection=[
            ("active", "active"),
            ("expired", "expired"),],
        string="Status",
        compute="_compute_token_status"
    )

    @api.depends("token_expiry")
    def _compute_token_status(self):
        now = datetime.now()
        for rec in self:
            if rec.token_expiry > now:
                rec.status = "active"
            else:
                rec.status = "expired"

            # ----------------------------------------------------------------------
            # 🔹 Get stored credentials from configuration
            # ----------------------------------------------------------------------

    @api.model
    def get_credentials(self):
        ICP = self.env['ir.config_parameter'].sudo()
        return {
            "base_url": ICP.get_param('pos_mor.base_url'),
            "client_id": ICP.get_param('pos_mor.client_id'),
            "client_secret": ICP.get_param('pos_mor.client_secret'),
            "api_key": ICP.get_param('pos_mor.api_key'),
            "tin": ICP.get_param('pos_mor.tin'),
        }

    def ensure_valid_token(self):
        # Get latest token record
        now = datetime.now()
        token_record = self.env['mor.api'].search(
            [('token_expiry', '>', now)], order='create_date desc', limit=1)
        if not token_record or not token_record.access_token:
            # No token exists, authenticate
            token_record = self.env['mor.api'].authenticate()
        elif token_record.token_expiry and token_record.token_expiry < datetime.now():
            # Token expired, refresh
            token_record = self.env['mor.api'].refresh_access_token()
        return token_record

    # ----------------------------------------------------------------------
    # 🔹 Authenticate with the Ministry of Revenue (Login)
    # ----------------------------------------------------------------------

    @api.model
    def authenticate(self):
        creds = self.get_credentials()

        # Check all credentials are provided
        missing = [k for k, v in creds.items() if not v]
        if missing:
            raise UserError(_("Missing configuration fields: %s") %
                            ", ".join(missing))
        url = f"{creds['base_url'].rstrip('/')}/auth/login"
        payload = {
            "clientId": creds["client_id"],
            "clientSecret": creds["client_secret"],
            "apikey": creds["api_key"],
            "tin": creds["tin"],
        }
        try:
            response = requests.post(url, json=payload, timeout=25)
        except requests.exceptions.RequestException as e:
            raise UserError(_("Connection Error: %s") % str(e))

        # Parse JSON safely
        try:
            result = response.json()
        except Exception:
            raise UserError(_("Invalid response format from MoR server."))

        # ---------------------------------------------------------------
        # ✅ SUCCESS RESPONSE HANDLING
        # ---------------------------------------------------------------
        if response.ok and result.get('status') == 'SUCCESS':
            data = result.get('data', {})

            # Store tokens securely
            ICP = self.env['ir.config_parameter'].sudo()
            ICP.set_param('pos_mor.access_token', data.get('accessToken', ''))
            ICP.set_param('pos_mor.refresh_token',
                          data.get('refreshToken', ''))
            ICP.set_param('pos_mor.encryption_key',
                          data.get('encryptionKey', ''))

            # Optional: compute expiry time
            if data.get('expiresIn'):
                expiry = datetime.now() + timedelta(seconds=data.get('expiresIn'))
                ICP.set_param('pos_mor.token_expiry', expiry.isoformat())
                self.create({
                    "access_token": data.get('accessToken', ''),
                    "refresh_token": data.get('refreshToken', ''),
                    "encryption_key": data.get('encryptionKey', ''),
                    "token_expiry": expiry,

                })

            # Update record fields
            self.access_token = data.get('accessToken')
            self.refresh_token = data.get('refreshToken')
            self.encryption_key = data.get('encryptionKey')

            return {
                "status": "success",
                "message": _("Login successful!"),
                "access_token": data.get("accessToken"),
                "expires_in": data.get("expiresIn"),
            }

        # ---------------------------------------------------------------
        # ❌ INVALID CREDENTIALS (401)
        # ---------------------------------------------------------------
        elif result.get('statusCode') == 401 or result.get('code') == '4400':
            details = result.get('details', [])
            detail_msg = details[0].get(
                'errorMessage') if details else 'Invalid credentials.'
            raise UserError(_("Authentication failed: %s") % detail_msg)

        # ---------------------------------------------------------------
        # ❌ MISSING FIELD OR BAD REQUEST (400)
        # ---------------------------------------------------------------
        elif result.get('statusCode') == 400 or result.get('code') == '4001':
            details = result.get('details', [])
            field_errors = ", ".join(
                [f"{d.get('field')}: {d.get('errorMessage')}" for d in details]
            )
            raise UserError(_("Missing or invalid field(s): %s") %
                            field_errors)

        # ---------------------------------------------------------------
        # ❌ GATEWAY OR SERVER ERROR
        # ---------------------------------------------------------------
        else:
            msg = result.get('message', response.text)
            raise UserError(_("Login failed: %s") % msg)

    @api.model
    def refresh_access_token(self):
        """Refresh MoR access token using stored refresh token."""
        # Get the last saved token record (latest by create_date)
        token_record = self.search([], order='create_date desc', limit=1)
        if not token_record or not token_record.refresh_token:
            raise UserError(_("No refresh token found. Please login first."))

        creds = self.env['ir.config_parameter'].sudo()
        base_url = creds.get_param(
            'pos_mor.base_url', 'http://core.mor.gov.et')

        url = f"{base_url}/refresh"
        payload = {"refreshToken": token_record.refresh_token}

        response = requests.post(url, json=payload)
        if not response.ok:
            # Handle invalid refresh token
            try:
                data = response.json()
                code = data.get("code")
                msg = data.get("message", "Refresh token failed")
                raise UserError(f"MoR refresh token failed ({code}): {msg}")
            except Exception:
                raise UserError(
                    f"MoR refresh token request failed: {response.text}")

        # Success response
        data = response.json().get("data", {})
        token_record.write({
            "access_token": data.get("accessToken"),
            "refresh_token": data.get("refreshToken"),
            "encryption_key": data.get("encryptionKey"),
            "token_expiry": datetime.now() + timedelta(seconds=data.get("expiresIn", 3600)),
            "status": "active",
        })
        return token_record
