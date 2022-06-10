from odoo import models, fields


class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'

    dob = fields.Date(string="DOB")
    gender = fields.Selection(
        string="Gender",
        selection=[('female', 'Female'), ('male', 'Male'), ('other', 'Other')])


class EmployeeInherit(models.Model):
    _inherit = 'hr.employee'

    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    fee = fields.Monetary(stringfrom="Fee", required=True, currency_field='currency_id')
