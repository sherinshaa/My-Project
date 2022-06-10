from odoo import models, fields, api


class GraduatedCommission(models.Model):
    _name = 'graduated.commission'
    _description = 'Graduated Commission'

    commission_plan_id = fields.Many2one('crm.commission', string='Name')
    graduation_no = fields.Char(string="Graduation No", readonly=True, default=lambda self: 'New')
    currency_id = fields.Many2one('res.currency', string='Currency_id',
                                  default=lambda self: self.env.company.currency_id)
    from_amount = fields.Monetary(string='From Amount', currency_field='currency_id')
    to_amount = fields.Monetary(string='To Amount', currency_field='currency_id')
    commission_percentage = fields.Integer(string='Rate')

    @api.model
    def create(self, vals):
        vals['graduation_no'] = self.env['ir.sequence'].next_by_code('graduated.commission') or 'New'
        res = super(GraduatedCommission, self).create(vals)
        return res
