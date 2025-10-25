from odoo import fields, models, api
from odoo.exceptions import UserError, ValidationError

class HrPromotion(models.Model):
    _name = 'hr.promotion'

    name = fields.Char(string='Promotion Reference', required=True, copy=False, readonly=True, default=lambda self: self.env['ir.sequence'].next_by_code('hr.promotion'))
    employee_id = fields.Many2one('hr.employee', string='Employees', required=True)
    creator_id = fields.Many2one('res.users', string='Requestor', default=lambda self: self.env.user, readonly=True)
    appraisal_id = fields.Many2one('hr.appraisal', string='Appraisal')
    appraisal_final_rating = fields.Many2one('hr.appraisal.note',
        related='appraisal_id.assessment_note',
        string="Appraisal Final Rating",
        readonly=True,
        store=True
    )

    reason = fields.Html(string ='Promotion Reason', required=True)
    request_date = fields.Date(string='Request Date', default=fields.Date.today)
    approval_date = fields.Date(string='Approve Date', readonly=True)
    rejection_reason = fields.Html(string='Rejection Reason')

    promotion_type = fields.Selection(
        [('salary_promotion', 'Salary Promotion'), ('position_promotion', 'Position Promotion'), ('position_demotion', 'Position Demotion')],
        string='Promotion Type',
        required=True
    )

    new_department_id = fields.Many2one('hr.department', string='New Department')
    new_job_id = fields.Many2one('hr.job', string='New Job Position')

    state = fields.Selection([
        ('draft', 'Draft'), ('in_review', 'In Review'), ('approved', 'Approved'), ('done', 'Applied'), ('rejected', 'Rejected'),],
         string="Status", default='draft')



    @api.constrains('new_job_id', 'new_department_id', 'promotion_type')
    def _check_job_in_department(self):
        for record in self:
            if record.promotion_type in ('position_promotion', 'position_demotion') and record.new_job_id and record.new_department_id:

                if record.new_job_id.department_id != record.new_department_id:
                    raise ValidationError(_(
                        "Job and Department Mismatch: The job '%(job)s' does not belong to the department '%(dept)s'. "
                        "Please select a job that is part of the chosen department."
                    ))


    def action_submit(self):
        for record in self:
            if record.reason:
                record.write({'state': 'in_review'})
            else:
                raise UserError('Please provide a reason for this request')
    
    def action_draft(self):
        for record in self:
            record.write({'state': 'draft'})
    
    def action_approve(self):
        for record in self:
            record.write({'state': 'approved', 'approval_date': fields.Date.today()})


    def action_done(self):
        for record in self:
            record.write({'state': 'done'})


    

