from odoo import models, fields


class ProductwiseCommission(models.Model):
    _name = 'productwise.commission'

    commission_id = fields.Many2one('crm.commission', string='Name')
    product_category_id = fields.Many2one('product.category', string='Product Category', related='product_id.categ_id')
    product_id = fields.Many2one('product.product', string='Product')
    rate_percentage = fields.Float(string='Rate in percentage')
    max_commission = fields.Float(string='Max Commission')
