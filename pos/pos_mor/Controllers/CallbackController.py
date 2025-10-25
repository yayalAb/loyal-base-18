# controllers/mor_callback.py
from odoo import http
from odoo.http import request
import logging
import json


_logger = logging.getLogger(__name__)


class MorCallbackController(http.Controller):

    # @http.route('/api/callback', type='http', auth='public', methods=['POST'], csrf=False)
    # def mor_callback(self, **kw):
    #     """Handle callback from external system"""
    #     _logger.info("Callback received: %s", kw)
    #     return request.make_response(json.dumps({'status': 'ok'}), headers={'Content-Type': 'application/json'})

    @http.route('/api/callback', type='http', auth='public', methods=['GET', 'POST'], csrf=False)
    def mor_callback(self, **kw):
        """Handle callback from external system"""
        # _logger.info("Callback received: %s", kw)
        return request.make_response(json.dumps({'status': 'ok'}), headers={'Content-Type': 'application/json'})
