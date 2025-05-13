from odoo import api, models, fields, _
from odoo.exceptions import ValidationError


class StockRequestLot(models.Model):
    _name = 'stock.request.lot'
    _description = 'Stock Request Lot'

    stock_request_id = fields.Many2one('stock.request', string="Stock Request")
    product_id = fields.Many2one('product.product', string="Product")
    issued_qty = fields.Float(string='Issued Qty',
                              compute="_compute_issues_qty")
    qty = fields.Float(string='Quantity')
    lot_ids = fields.Many2many('stock.lot', compute="_compute_lot_ids")
    lot_id = fields.Many2one(
        'stock.lot', 'Lot/Serial Number', domain="[('id', 'in',lot_ids)]")
    available_qty_lot = fields.Float(string="Available Quantity In Lot")
    is_expired = fields.Boolean(related='lot_id.product_expiry_alert')
    lot_qty_pending = fields.Boolean(string="Pending Lot Qty",
                                     compute="_compute_lot_qty_pending")

    @api.depends('qty', 'product_id')
    def _compute_lot_qty_pending(self):
        for rec in self:
            product = rec.stock_request_id.lot_ids.filtered(
                lambda l: l.product_id.id == rec.product_id.id)
            if rec.issued_qty != sum(product.mapped('qty')):
                rec.lot_qty_pending = True
            else:
                rec.lot_qty_pending = False

    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        for rec in self:
            quant = self.env['stock.quant'].sudo().search([
                ('product_id', '=', rec.product_id.id),
                ('location_id', '=', rec.stock_request_id.location_id.id),
                ('lot_id', '=', rec.lot_id.id)])
            rec.available_qty_lot = quant.quantity
            if rec.available_qty_lot < rec.qty and rec.lot_id:
                raise ValidationError(
                    _('This lot only available qty is %f')% rec.available_qty_lot)

    @api.onchange('qty')
    def _onchange_qty(self):
        for rec in self:
            product = rec.stock_request_id.lot_ids.filtered(
                lambda l: l.product_id.id == rec.product_id.id)
            if rec.issued_qty < sum(product.mapped('qty')):
                raise ValidationError(
                    _('Quantity must be equal to Issued qty'))

    @api.depends('product_id')
    def _compute_lot_ids(self):
        for rec in self:
            quant = self.env['stock.quant'].sudo().search([
                ('product_id', '=', rec.product_id.id),
                ('location_id', '=', rec.stock_request_id.location_id.id),
                ('quantity', '>', 0), ('lot_id', '!=', False)])
            rec.lot_ids = quant.mapped('lot_id')

    @api.depends('product_id', 'stock_request_id.move_ids.issued_qty')
    def _compute_issues_qty(self):
        for rec in self:
            if rec.product_id:
                issued_qty = rec.stock_request_id.move_ids.filtered(
                    lambda l: l.product_id.id == rec.product_id.id)
                rec.issued_qty = sum(issued_qty.mapped('issued_qty'))
            else:
                rec.issued_qty = 0
