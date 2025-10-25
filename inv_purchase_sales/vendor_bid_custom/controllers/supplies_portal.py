from odoo import http, fields, _
from odoo.http import request, route
from odoo.exceptions import AccessDenied
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from operator import itemgetter
from odoo.tools import groupby as groupbyelem
from odoo.addons.VendorBid.utils import controller_utils as utils
from odoo.addons.VendorBid.utils import controller_utils as utils
from odoo.addons.VendorBid.utils import schemas
from odoo.addons.VendorBid.utils import mail_utils
from pydantic import ValidationError
from odoo.addons.VendorBid.utils.mail_utils import get_smtp_server_email, get_reviewers, get_reviewer_emails
from odoo.exceptions import AccessDenied
import base64
from ..utils.search_domain import get_rfp_general_search_domain


class SuppliesPortalInherit(CustomerPortal):

    @http.route(['/my/supplies', '/my/supplies/page/<int:page>'], auth='user', website=True)
    def supplies_portal(self, page=1, sortby=None, search=None, search_in=None, groupby=None, **kw):
        """
        Override supplier portal RFP list:
        Show only RFPs where the logged-in partner is in selected_suppliers.
        """
        partner_id = request.env.user.partner_id.id

        limit = 5
        searchbar_sortings = {
            'date': {'label': 'Newest', 'order': 'date_approve desc'},
            'name': {'label': 'Name', 'order': 'rfp_number'},
        }
        groupby_list = {
            'required_date': {'input': 'required_date', 'label': _('Required Date')},
            'state': {'input': 'state', 'label': _('Status')},
        }
        search_in = search_in or 'name'
        order = searchbar_sortings[sortby]['order'] if sortby else 'date_approve desc'
        groupby = groupby or 'state'
        search_list = {
            'all': {'label': _('All'), 'input': 'all', 'domain': []},
            'name': {'label': _('Name'), 'input': 'rfp_number', 'domain': [('rfp_number', 'ilike', search)]},
        }
        sortby = sortby or 'date'

        # original domain + restrict by selected_suppliers
        search_domain = get_rfp_general_search_domain(request.env)
        search_domain += search_list[search_in]['domain']
        search_domain.append(('selected_suppliers', 'in', [partner_id]))

        rfp_count = request.env['supplies.rfp'].sudo().search_count(search_domain)
        pager = portal_pager(
            url="/my/supplies",
            url_args={'sortby': sortby, 'search_in': search_in, 'search': search, 'groupby': groupby},
            total=rfp_count,
            page=page,
            step=limit
        )
        rfps = request.env['supplies.rfp'].sudo().search(search_domain, order=order, limit=limit,
                                                         offset=pager['offset'])
                                                         
        # rfps = rfps.filtered(lambda r: request.env.user.partner_id in r.selected_suppliers)

        group_by_rfp = groupby_list.get(groupby, {})
        if groupby_list[groupby]['input']:
            rfp_group_list = [{group_by_rfp['input']: i, 'rfps': list(j)} for i, j in
                              groupbyelem(rfps, itemgetter(group_by_rfp['input']))]
        else:
            rfp_group_list = [{'rfps': rfps}]

        return request.render(
            'VendorBid.portal_supplies_rfp_tree_view',
            {
                'rfps': rfps,
                'page_name': 'rfp_list',
                'pager': pager,
                'searchbar_sortings': searchbar_sortings,
                'searchbar_inputs': search_list,
                'sortby': sortby,
                'search_in': search_in,
                'search': search,
                'groupby': groupby,
                'searchbar_groupby': groupby_list,
                'default_url': '/my/supplies',
                'group_rfps': rfp_group_list
            }
        )

    @http.route('/my/supplies/<string:rfp_number>', auth='user', website=True)
    def supplies_portal_rfp(self, rfp_number, **kw):
        """
        Override supplier portal RFP detail:
        Supplier can only view if they're in selected_suppliers.
        """
        partner_id = request.env.user.partner_id.id
        search_domain = get_rfp_general_search_domain(request.env)
        search_domain += [('selected_suppliers', 'in', [partner_id])]
        all_rfps = request.env['supplies.rfp'].sudo().search(search_domain)
        search_domain.append(('rfp_number', '=', rfp_number))
        rfp = request.env['supplies.rfp'].sudo().search(search_domain, limit=1)
        rfp_index = all_rfps.ids.index(rfp.id)
        prev_record = all_rfps[rfp_index - 1].rfp_number if rfp_index > 0 else False
        next_record = all_rfps[rfp_index + 1].rfp_number if rfp_index < len(all_rfps) - 1 else False
        success_list = []
        error_list = []
        page_contexts = {}

        if request.httprequest.method == 'POST':
            try:
                partner_id = request.env.user.partner_id
                if partner_id.supplier_rank < 1:
                    raise AttributeError('You are not a supplier.')
                rfq_schema = schemas.PurchaseOrderSchema(
                    **dict(
                        request.httprequest.form.items(),
                        rfp_id=rfp.id,
                        partner_id=partner_id.id,
                        user_id=rfp.review_by.id
                    )
                )
            except ValidationError as e:
                errors = e.errors()
                for error in errors:
                    error_list.append(error['msg'])
            except AttributeError as e:
                error_list.append(str(e))
            else:
                data = rfq_schema.model_dump(exclude_none=True)
                order_line = data.pop('order_line')
                rfq = request.env['purchase.order'].sudo().create(data)
                for line in order_line:
                    line['order_id'] = rfq.id
                    # link taxes_id
                    tax_amount = line.pop('tax')
                    tax_id = False
                    if tax_amount:
                        if ac_tax := request.env['account.tax'].sudo().search([('amount', '=', tax_amount)], limit=1):
                            tax_id = ac_tax.id
                        else:
                            tax_data = {
                                "name": f"{tax_amount}%",
                                "amount": tax_amount,
                                "type_tax_use": "purchase",
                            }
                            ac_tax = request.env['account.tax'].sudo().create(tax_data)
                            tax_id = ac_tax.id
                    if tax_id:
                        line['taxes_id'] = [(4, tax_id)]
                    # create the PO line
                    request.env['purchase.order.line'].sudo().create(line)
                success_list.append('RFQ submitted successfully.')
                # send email to reviewer
                template = request.env.ref('VendorBid.email_template_model_purchase_order_rfq_submission').sudo()
                email_values = {
                    'email_from': mail_utils.get_smtp_server_email(request.env),
                    'email_to': rfp.create_uid.login,
                    'subject': f'New RFQ Submission for {rfp.rfp_number}',
                }
                contexts = {'rfp_number': rfp.rfp_number, 'company_name': rfq.company_id.name}
                template.with_context(**contexts).send_mail(rfq.id, email_values=email_values)
                page_contexts['submitted_rfq'] = rfq

        if request.env.user.has_group('VendorBid.group_supplies_requester'):
            template_name = "portal_supplies_rfp_form_view_requester"
        else:
            template_name = "portal_supplies_rfp_form_view"
        return request.render(
            f'VendorBid.{template_name}',
            {
                'rfp': rfp,
                'page_name': 'rfp_view',
                'success_list': success_list,
                'error_list': error_list,
                'prev_record': "/my/supplies/" + prev_record if prev_record else False,
                'next_record': "/my/supplies/" + next_record if next_record else False,
                **page_contexts
            }
        )
