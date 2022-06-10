from odoo import models, fields, api


class ResusersInherit(models.Model):
    _inherit = 'res.users'

    commission_plan = fields.Many2one('crm.commission', string='Commission Plan')
    commission_amount = fields.Float(string='Commission Amount')

    def field_resets(self):
        field_reset = self.env['res.users'].search([('company_id', '=', self.env.company.id)])
        for record in field_reset:
            record.commission_amount = 0
            print(record.commission_amount)
