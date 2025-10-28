from odoo import models, fields, api
from odoo.exceptions import UserError
from ..utils.rfp_utils import rfp_state_flow
from ..utils.mail_utils import get_smtp_server_email, get_approver_emails, get_supplier_emails
from collections import defaultdict


class SuppliesRfp(models.Model):

    _name = 'supplies.rfp'
    _inherit = ['mail.thread']
    _description = 'Request for Purchase'
    _rec_name = 'rfp_number'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('rejected', 'Rejected'),
        ('approved', 'Approved'),
        ('closed', 'Closed'),
        ('recommendation', 'Recommendation'),
        ('accepted', 'Accepted'),
    ], string='Status', readonly=True, copy=False, index=True, tracking=True, default='draft')
    rfp_number = fields.Char(string='RFP Number', readonly=True, index=True, copy=False, default='New')
    required_date = fields.Date(string='Required Date', tracking=True,
                                default=lambda self: fields.Date.add(fields.Date.today(), days=7))
    approved_supplier_id = fields.Many2one('res.partner', string='Approved Supplier')
    product_line_ids = fields.One2many('supplies.rfp.product.line', 'rfp_id', string='Product Lines')
    rfq_ids = fields.One2many('purchase.order', 'rfp_id', string='RFQs', domain=lambda self: self._get_rfq_domain())
    rfq_line_ids = fields.One2many('purchase.order.line', compute='_compute_rfq_line_ids', string='RFQ Lines')
    num_rfq = fields.Integer(string='Number of RFQs', compute='_compute_num_rfq', store=True)
    total_amount = fields.Monetary(string='Total Amount', compute='_compute_total_amount', store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    date_approve = fields.Date(string='Reviewed On', readonly=True)  # when an approver either approves or rejects
    review_by = fields.Many2one('res.users', string='Review By',
                                readonly=True)  # an approver either approves or rejects
    date_accept = fields.Date(string='Accepted On', readonly=True)
    product_category_id = fields.Many2one('product.category', string="Product Category", store=True)
    total_rfq = fields.Integer(string='Number of RFQs', compute='_compute_total_rfq', store=False)
    visible_to_reviewer = fields.Boolean(compute='_compute_visible_to_reviewer', search='_search_visible_to_reviewer')
    submitted_by = fields.Many2one('res.users', string='Submitted By', readonly=True)

    recommendations_made = fields.Boolean(compute='_compute_recommendations_made', store=True)

    @api.depends('rfq_line_ids.recommended')
    def _compute_recommendations_made(self):
        for rfp in self:
            rfp.recommendations_made = any(rfp.rfq_line_ids.mapped('recommended'))


    @api.depends('rfq_ids.order_line')
    def _compute_rfq_line_ids(self):
        for rfp in self:
            rfp.rfq_line_ids = rfp.rfq_ids.mapped('order_line')


    def _compute_visible_to_reviewer(self):
        for rec in self:
            rec.visible_to_reviewer = self._is_visible_to_reviewer(rec)

    def _is_visible_to_reviewer(self, record):

        requester_group = self.env.ref('VendorBid.group_supplies_requester')
        user = self.env.user

        # Check if the record was created by the current user
        if record.create_uid == user:
            return True

        # Check if the record was created by a user in the requester group and is in draft state or was submitted by the user
        if record.create_uid.has_group('VendorBid.group_supplies_requester'):
            if record.state == 'draft' or record.submitted_by == user:
                return True

        return False

    @api.model
    def _search_visible_to_reviewer(self, operator, value):

        # Ensure the operator is either '=' or '!=' and the value is a boolean
        if operator not in ['=', '!='] or not isinstance(value, bool):
            raise UserError("Unsupported search operation for visible_to_reviewer")

        requester_group = self.env.ref('VendorBid.group_supplies_requester')
        user = self.env.user

        # Construct the domain for the search query based on visibility conditions
        domain = ['|',
                  ('create_uid', '=', user.id),  # Record created by the current user
                  '&',
                  ('create_uid.groups_id', 'in', requester_group.id),
                  # Record created by someone in the requester group
                  '|',
                  ('state', '=', 'draft'),  # Record is in 'draft' state
                  ('submitted_by', '=', user.id)  # Record was submitted by the current user
                  ]

        # Return the domain depending on the value of the operator
        return domain if value else ['!', domain]

    def _compute_total_rfq(self):
        
        for rec in self:
            recommended_rfq = rec.rfq_ids
            
            rec.total_rfq = len(recommended_rfq)
    def action_view_all_rfq(self):

        action = self.env.ref('purchase.purchase_rfq').read()[0]
        
        # Base domain to filter RFQs for the current RFP, excluding draft state
        domain = [('rfp_id', '=', self.id), ('is_final_po_from_rfp', '=', False)]
        
        # Check if the user is in the approver group
       
        action['domain'] = domain
        return action
    
    def action_view_all_quotation(self):

        action = self.env.ref('purchase.purchase_rfq').read()[0]
        
        action['domain'] = [('rfp_id', '=', self.id),('state','=','draft')]
        return action
    
    @api.depends('product_line_ids', 'product_line_ids.subtotal_price')
    def _compute_total_amount(self):

        for rfp in self:
            rfp.total_amount = sum(rfp.product_line_ids.mapped('subtotal_price'))

    @api.model
    def _get_rfq_domain(self):

        domain=[]
        for rec in self:
         domain = [('rfp_id', '=', rec.id), ('is_final_po_from_rfp', '=', False)]

        return domain

    @api.model_create_multi
    def create(self, vals_list):

        for vals in vals_list:
            if vals.get('rfp_number', 'New') == 'New':
                vals['rfp_number'] = self.env['ir.sequence'].next_by_code('supplies.rfp.number') or 'New'
        return super(SuppliesRfp, self).create(vals_list)

    @api.depends('rfq_ids')
    def _compute_num_rfq(self):

        for rfp in self:
            rfp.num_rfq = len(rfp.rfq_ids)

    @rfp_state_flow('draft')
    def action_submit(self):

        if not self.product_line_ids:
            raise UserError('Please add product lines before submitting.')

        if not all(self.product_line_ids.mapped('product_qty')):
            raise UserError('Product quantity must be greater than 0')

        self.write({'state': 'submitted', 'submitted_by': self.env.user.id,
                    'product_category_id': self.product_category_id.id, })

        email_values = {
            'email_from': get_smtp_server_email(self.env),
            'email_to': get_approver_emails(self.env),
            'subject': f'New RFP Submitted {self.rfp_number}',
        }
        contexts = {
            'reviwer_name': self.env.user.name,
            'company_name': self.env.company.name,
        }
        template = self.env.ref('VendorBid.email_template_model_supplies_rfp_submission').sudo()
        template.with_context(**contexts).send_mail(self.id, email_values=email_values)

    @rfp_state_flow('rejected', 'submitted')
    def action_return_to_draft(self):

        self.state = 'draft'

    @rfp_state_flow('submitted')
    def action_approve(self):

        self.write({'state': 'approved', 'date_approve': fields.Date.today(), 'review_by': self.env.user.id})

    @rfp_state_flow('submitted')
    def action_reject(self):

        self.write({'state': 'rejected', 'review_by': self.env.user.id, 'date_approve': fields.Date.today()})
        email_values = {
            'email_from': get_smtp_server_email(self.env),
            'email_to': self.create_uid.login,
            'subject': f'RFP Rejected {self.rfp_number}',
        }
        contexts = {
            'rfp_number': self.rfp_number,
            'company_name': self.env.company.name,
            'approver_name': self.env.user.name,
        }
        template = self.env.ref('VendorBid.email_template_model_supplies_rfp_rejected_reviewer').sudo()
        template.with_context(**contexts).send_mail(self.id, email_values=email_values)

    @rfp_state_flow('approved')
    def action_close(self):

        self.state = 'closed'

    @rfp_state_flow('closed')
    def action_recommendation(self):

        self.write({'state': 'recommendation'})

    def action_view_purchase_order(self):

        self.ensure_one()
        return {
            'name': 'Purchase Orders',
            'view_mode': 'list,form',
            'res_model': 'purchase.order',
            'domain': [('rfp_id', '=', self.id), ('is_final_po_from_rfp', '=', True)],
            'type': 'ir.actions.act_window',
        }


    @api.model
    def get_rfp_sudo(self, domain, fields):

        return self.sudo().search_read(domain, fields)

 

    def action_recommend_best_prices(self):
            self.ensure_one()

            # First, un-recommend all lines to allow re-running the process
            self.rfq_line_ids.write({'recommended': False})
            
            # Group lines by product
            lines_by_product = defaultdict(lambda: self.env['purchase.order.line'])
            for line in self.rfq_line_ids:
                lines_by_product[line.product_id] |= line

            if not lines_by_product:
                raise UserError("There are no RFQ lines to recommend.")

            # Find the best price for each product
            recommended_lines = self.env['purchase.order.line']
            for product, lines in lines_by_product.items():
                # Find the line with the minimum price_unit
                best_line = min(lines, key=lambda l: l.price_subtotal)
                recommended_lines |= best_line
            
            # Mark the best lines as recommended
            if recommended_lines:
                recommended_lines.write({'recommended': True})


    def action_create_purchase_orders(self):

            self.ensure_one()
            recommended_lines = self.rfq_line_ids.filtered(lambda l: l.recommended)
            
            if not recommended_lines:
                raise UserError("There are no recommended lines to create Purchase Orders from. Please run the 'Recommend Best Prices' action first.")

            # Group recommended lines by supplier (partner_id on the purchase.order)
            lines_by_supplier = defaultdict(lambda: self.env['purchase.order.line'])
            for line in recommended_lines:
                lines_by_supplier[line.order_id.partner_id] |= line

            created_pos = self.env['purchase.order']
            for supplier, lines in lines_by_supplier.items():
                po_vals = {
                    'partner_id': supplier.id,
                    'rfp_id': self.id,
                    'origin': self.rfp_number,
                    'order_line': [],
                    'currency_id': self.currency_id.id,
                    'purchase_origin': self.purchase_origin,
                    'project_id': self.project_id.id,
                    'is_final_po_from_rfp': True,
                }
                for line in lines:
                    line_vals = {
                        'product_id': line.product_id.id,
                        'name': line.name,
                        'product_qty': line.product_qty,
                        'product_uom': line.product_uom.id,
                        'price_unit': line.price_unit,
                        'date_planned': line.date_planned,
                    }
                    po_vals['order_line'].append((0, 0, line_vals))
                
                new_po = self.env['purchase.order'].create(po_vals)
                created_pos |= new_po

            if self.rfq_ids:
                self.rfq_ids.write({'state': 'done'})

            self.write({'state': 'accepted', 'date_accept':  fields.Date.today()})
