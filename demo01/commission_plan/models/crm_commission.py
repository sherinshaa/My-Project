from odoo import models, fields


class CrmCommission(models.Model):
    _name = 'crm.commission'
    _description = 'Crm Commission'

    name = fields.Char(string='Name')
    active = fields.Boolean(string='Active')
    from_date = fields.Date(string='From Date', required=True)
    to_date = fields.Date(string='To Date')
    commission_type = fields.Selection(string='Commission Type',
                                       selection=[('product_wise', 'Product Wise'), ('revenue_wise', 'Revenue Wise')])
    straight = fields.Boolean(string='Straight')
    graduated = fields.Boolean(string='Graduated')
    productwise_commission_ids = fields.One2many('productwise.commission', 'commission_id', string='Commission Plan')
    graduated_commission_ids = fields.One2many('graduated.commission', 'commission_plan_id', string='Graduated Plan')
    straight_percentage = fields.Float(string='Straight Commission Percentage')
