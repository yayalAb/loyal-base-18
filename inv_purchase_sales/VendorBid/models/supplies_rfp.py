from odoo import models, fields, api
from odoo.exceptions import UserError
from ..utils.rfp_utils import rfp_state_flow
from ..utils.mail_utils import get_smtp_server_email, get_approver_emails, get_supplier_emails
from collections import defaultdict


class SuppliesRfp(models.Model):
    """
    Model: supplies.rfp (Request for Purchase)

    This model handles the lifecycle of a Request for Purchase (RFP) from creation to approval and final closure.
    It integrates with reviewers and suppliers, manages email notifications for different state transitions,
    and links with RFQs (Request for Quotations) and Purchase Orders.

    Key Features:
    - Tracks RFP states (Draft, Submitted, Rejected, Approved, Closed, Recommendation, Accepted).
    - Automatically generates unique RFP numbers using a sequence.
    - Allows adding multiple product lines and calculates total amount.
    - Sends email notifications to reviewers and suppliers during state transitions.
    - Supports user permission-based visibility (e.g., reviewer and requester access).
    - Provides actions to view RFQs and Purchase Orders related to the RFP.
    - Ensures only recommended RFQs can proceed to the recommendation stage.
    - Custom visibility logic using computed and searchable fields.
    - Integrates with external utilities: rfp_state_flow decorator, mail utilities.

    Linked Models:
    - `supplies.rfp.product.line`: Product lines added to the RFP.
    - `purchase.order`: RFQs linked to this RFP.
    - `res.partner`: Approved supplier.
    - `res.users`: Reviewers and submitters.

    Security Groups:
    - `group_supplies_requester`: Users who can submit RFPs.
    - `group_supplies_approver`: Users who can approve or reject RFPs.
    """

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
        """
        Determines if a record (RFP) is visible to the current user (reviewer) based on specific conditions.

        Conditions:
        - If the record was created by the current user, it is visible to the user.
        - If the record was created by a user in the 'requester' group and is in 'draft' state, it is visible to the user.
        - If the record was submitted by the current user, it is visible to the user.

        Args:
            record (recordset): The RFP record being checked for visibility.

        Returns:
            bool: True if the record is visible to the current user, False otherwise.
        """
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
        """
        Returns the domain for searching records based on visibility to the current user (reviewer).

        This method is used to build the search domain for filtering RFPs that are visible to the current user
        based on the following conditions:
        - The current user is the creator of the RFP.
        - The current user is part of the 'requester' group and the RFP is in 'draft' state or was submitted by the user.

        Args:
            operator (str): The operator used in the search (either '=' or '!=').
            value (bool): The value indicating whether to include or exclude records that are visible to the current user.

        Returns:
            list: A domain to be used in the search query. If `value` is `True`, it returns the domain for visible records;
                  if `value` is `False`, it returns the inverse domain for non-visible records.

        Raises:
            UserError: If the operator is not '=' or '!=' or if the `value` is not a boolean.
        """
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
        """
        Computes the total number of RFQs associated with the current RFP.
        This updates the 'total_rfq' field with the count of related RFQs.

        Args:
            self: The current instance of the RFP record.
        """
        
        for rec in self:
            recommended_rfq = rec.rfq_ids
            
            rec.total_rfq = len(recommended_rfq)
    def action_view_all_rfq(self):
        """
        Returns an action to open a list view of all RFQs related to the current RFP.

        Depending on the user's group and the RFQ state, the domain will filter the RFQs.
        If the user is an approver, it filters for RFQs with the same partner_id as the recommended RFQ.
        Otherwise, it shows all RFQs associated with the RFP (excluding draft state).

        Args:
            self: The current instance of the RFP record.

        Returns:
            dict: The action dictionary to open the RFQs in the appropriate view.
        """
        action = self.env.ref('purchase.purchase_rfq').read()[0]
        
        # Base domain to filter RFQs for the current RFP, excluding draft state
        domain = [('rfp_id', '=', self.id)]
        
        # Check if the user is in the approver group
       
        action['domain'] = domain
        return action
    def action_view_all_quotation(self):
        """
                Returns an action to open a list view of all RFQs related to the current RFP.

                Depending on the user's group and the RFQ state, the domain will filter the RFQs.

                If the user is an approver, it filters for recommended RFQs only.
                Otherwise, it shows all RFQs associated with the RFP.

                Args:
                    self: The current instance of the RFP record.

                Returns:
                    dict: The action dictionary to open the RFQs in the appropriate view.
        """
        action = self.env.ref('purchase.purchase_rfq').read()[0]
        
        action['domain'] = [('rfp_id', '=', self.id),('state','=','draft')]
        return action
    
    @api.depends('product_line_ids', 'product_line_ids.subtotal_price')
    def _compute_total_amount(self):
        """
            Computes the total amount for the current RFP by summing the 'subtotal_price'
                of all product lines associated with the RFP.

            Args:
                self: The current instance of the RFP record.
        """
        for rfp in self:
            rfp.total_amount = sum(rfp.product_line_ids.mapped('subtotal_price'))

    @api.model
    def _get_rfq_domain(self):
        """
        Returns the domain to filter RFQs based on the current user's group and the RFP's state.

        If the user is an approver, it returns a domain to filter RFQs where the recommendation is true,
        but only if the RFP's state allows it.

        Args:
            self: The current instance of the RFP record.

        Returns:
            list: A domain list for filtering RFQs.
        """
        domain=[]
        for rec in self:
         domain = [('rfp_id', '=', rec.id), ('is_final_po_from_rfp', '=', False)]
        # approver_states = ['recommendation', 'accepted']

        # if self.env.user.has_group('VendorBid.group_supplies_approver'):
        #     if self.state in approver_states:
        #         domain.append(('recommended', '=', True))
        #     else:
        #         # Hide everything for approvers when not in allowed states
        #         domain.append(('id', '=', -1))
        return domain

    @api.model_create_multi
    def create(self, vals_list):
        """
        Overrides the create method to assign a unique sequence number to the 'rfp_number' field if it's set to 'New'.

        Args:
            vals_list (list): List of dictionaries containing the RFP values to be created.

        Returns:
            recordset: The created RFP records.
        """
        for vals in vals_list:
            if vals.get('rfp_number', 'New') == 'New':
                vals['rfp_number'] = self.env['ir.sequence'].next_by_code('supplies.rfp.number') or 'New'
        return super(SuppliesRfp, self).create(vals_list)

    @api.depends('rfq_ids')
    def _compute_num_rfq(self):
        """
        Compute the number of RFQs associated with the current updates the 'num_rfq' field.
        Args:
            self: The current instance of the RFP record.
        """
        for rfp in self:
            rfp.num_rfq = len(rfp.rfq_ids)

    @rfp_state_flow('draft')
    def action_submit(self):
        """
        Submits the RFP, performs validation checks, and updates the RFP state to 'submitted'.
        Sends email notifications to the approvers and others involved in the submission process.

        Raises:
            UserError: If no product lines or invalid quantities are provided.

        Args:
            self: The current instance of the RFP record.
        """
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
        """
        Returns the RFP to the 'draft' state from 'rejected' or 'submitted' states.

        Args:
            self: The current instance of the RFP record.
        """
        self.state = 'draft'

    @rfp_state_flow('submitted')
    def action_approve(self):
        """
        Approves the RFP, updates the state to 'approved', and sends email notifications to the reviewer and suppliers.

        Args:
            self: The current instance of the RFP record.
        """
        self.write({'state': 'approved', 'date_approve': fields.Date.today(), 'review_by': self.env.user.id})

    @rfp_state_flow('submitted')
    def action_reject(self):
        """
        Rejects the RFP, updates the state to 'rejected', and sends email notifications to the reviewer.

        Args:
            self: The current instance of the RFP record.
        """
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
        """
        Closes the RFP, updating its state to 'closed'.

        Args:
            self: The current instance of the RFP record.
        """
        self.state = 'closed'

    @rfp_state_flow('closed')
    def action_recommendation(self):
        """
        Changes the RFP state to 'recommendation' after at least one RFQ is approved.
        Sends an email notification to the approvers.

        Raises:
            UserError: If no RFQs have been approved.

        Args:
            self: The current instance of the RFP record.
        """
        approved_rfqs = self.rfq_ids
        # if not approved_rfqs:
        #     raise UserError('Please approve at least one RFQ before recommending.')
        self.state = 'recommendation'
        self.rfq_ids.write({'recommended': False})

        # Select the RFQ with the lowest amount_total
        recommended_rfq = min(approved_rfqs, key=lambda rfq: rfq.amount_total)
        recommended_rfq.recommended = True
     
    
        email_values = {
            'email_from': get_smtp_server_email(self.env),
            'email_to': get_approver_emails(self.env),
            'subject': f'RFQ Recommendation for {self.rfp_number}',
           
        }
        contexts = {
            'rfp_number': self.rfp_number,
            'company_name': self.env.company.name,
            # 'recommended_rfq': recommended_rfq.name,
            # 'amount_total': recommended_rfq.amount_total,
        }
        template = self.env.ref('VendorBid.email_template_model_supplies_rfp_recommended').sudo()
        template.with_context(**contexts).send_mail(self.id, email_values=email_values)

    def action_view_purchase_order(self):
        """
        Returns an action to view the purchase order related to the current RFP.

        Args:
            self: The current instance of the RFP record.

        Returns:
            dict: The action dictionary to view the related purchase order.
        """
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
        """
        Returns RFP records using sudo access based on the provided domain and fields.

        Args:
            domain (list): A list of conditions for filtering the RFP records.
            fields (list): A list of fields to retrieve from the RFP records.

        Returns:
            list: A list of RFP records based on the specified domain and fields.
        """
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
            """
            Creates Purchase Orders for all recommended lines, grouping them by supplier.
            """
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
            self.write({
                'state': 'accepted',
                'date_accept': fields.Date.today(),
            })
