from odoo import models, fields, api

class TrainingRequisition(models.Model):
    _name = 'training.requisition'

    program_name = fields.Char(string='Program Name')
    training_participants = fields.One2many(
        'participant.lines', 'training_id', string='Training Participants')
    resource_line_ids = fields.One2many(
        'resource.lines', 'training_id', string='Resource Lines')
    estimated_budget = fields.Monetary(
        string='Estimated Budget', compute='_compute_estimated_budget', store=True)
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company)
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_review', 'In Review'),
        ('approve', 'Approve'),
        ('authorize', 'Authorize'),
        ('planned', 'Planned'),
        ('rejected', 'Rejected'),
    ], string='Status', default='draft', readonly=True, tracking=True)
    remark = fields.Html(string='Remark')
    creator_id = fields.Many2one(
        'res.users', string='Requestor', default=lambda self: self.env.user, readonly=True)
    requesting_department = fields.Many2one(
        'hr.department', default=lambda self: self.env.user.employee_id.department_id, string='Requesting Department', readonly=True)
    rejection_reason = fields.Text(string='Rejection Reason', readonly=True)
    approve_date = fields.Datetime(string='Approved On', readonly=True)

    @api.depends('resource_line_ids', 'resource_line_ids.cost')
    def _compute_estimated_budget(self):
        for record in self:
            record.estimated_budget = sum(line.cost for line in record.resource_line_ids)

    def action_submit(self):
        self.write({'state': 'in_review'})

    def action_approve(self):
        self.write({'state': 'approve'})

    def action_authorize(self):
        self.write({'state': 'authorize'})

    def action_set_to_draft(self):
        self.write({'state': 'draft', 'rejection_reason': ''})

    # In your TrainingRequisition model
    def action_plan(self):
        """
        This action updates the requisition state to 'approved', creates a new 'slide.channel' record,
        copies the resource lines, adds participants as enrolled attendees, and opens the new channel form.
        """
        self.ensure_one()

        # Update requisition state
        self.write({
            'state': 'planned',
            'approve_date': fields.Datetime.now()
        })

        # Prepare participant partner IDs
        partner_ids = [
            p.employee_id.related_partner_id.id for p in self.training_participants if p.employee_id.related_partner_id
        ]

        # Create the slide.channel record
        channel_vals = {
            'name': self.program_name,
            'description': self.remark,
            'user_id': self.env.user.id,
            'channel_type': 'training',
            'enroll': 'invite',
            'visibility': 'members',
            'date_start': self.start_date,
            'date_end': self.end_date,
        }
        channel = self.env['slide.channel'].create(channel_vals)

        for line in self.resource_line_ids:
            line.copy(default={'training_id': False, 'channel_id': channel.id})

        # Add participants as enrolled attendees
        if partner_ids:
            channel._action_add_members(
                target_partners=self.env['res.partner'].browse(partner_ids),
                member_status='joined'
            )

        return {
            'type': 'ir.actions.act_window',
            'name': 'eLearning Course',
            'res_model': 'slide.channel',
            'view_mode': 'form',
            'target': 'current',
            'res_id': channel.id,  # Open the newly created and fully populated channel
        }


class ParticipantLines(models.Model):
    _name = 'participant.lines'

    training_id = fields.Many2one('training.requisition')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    name = fields.Char(related='employee_id.name', string='Name')
    phone = fields.Char(related='employee_id.phone', string='Phone')
    department_id = fields.Many2one('hr.department', related='employee_id.department_id', string='Department')
    job_id = fields.Many2one('hr.job', related='employee_id.job_id', string='Job')
    company_id = fields.Many2one('res.company', related='employee_id.company_id', string='Company')

class ResourceLines(models.Model):
    _name = 'resource.lines'

    training_id = fields.Many2one('training.requisition', string='Training Requisition', ondelete='cascade')
    channel_id = fields.Many2one('slide.channel', string='Slide Channel', ondelete='cascade')
    name = fields.Char(string='Resource Name', required=True)
    cost = fields.Monetary(string='Cost', compute="_compute_cost")
    currency_id = fields.Many2one('res.currency', string='Currency', related='training_id.currency_id')
    description = fields.Text(string='Description')
    quantity = fields.Float(string='Quantity', default=1.0, required=True)
    unit_price = fields.Monetary(string='Unit Price', required=True)

    @api.depends('quantity', 'unit_price')
    def _compute_cost(self):
        for line in self:
            line.cost = line.quantity * line.unit_price