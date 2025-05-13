# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:Cybrosys Technologies(<https://www.cybrosys.com>)
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockRequestLine(models.Model):
    _name = 'stock.request.line'
    _description = 'Stock Request Line'

    sequence_number = fields.Integer(string='#',
                                     compute='_compute_sequence_number',
                                     help='Line Numbers')
    product_id = fields.Many2one('product.product', string='Product',
                                 required=True)
    product_uom_category_id = fields.Many2one(
        related='product_id.uom_id.category_id')
    product_uom_qty = fields.Float(string='Demand')
    product_uom = fields.Many2one('uom.uom', string='Unit',
                                  domain="[('category_id', '=', product_uom_category_id)]")
    stock_request_id = fields.Many2one('stock.request', string='Stock Request')
    remark = fields.Char(string='Description')
    issued_qty = fields.Float(string='Issued Qty')
    quantity = fields.Float(string='Approved Qty')
    received_qty = fields.Float(string='Received Qty')
    available_qty = fields.Float(string='Total Available Quantity',
                                 compute='_compute_available_qty')
    location_available_qty = fields.Float(string='Available Quantity',
                                          compute='_compute_available_qty')
    already_received_qty = fields.Float(string='Already Received Qty', compute="_compute_already_received_qty")
    balance_qty = fields.Float(string='Balance Qty')
    returned_qty = fields.Float(string="Returned Qty",
                                compute="_compute_returned_qty")

    @api.depends('stock_request_id.transfer_ids', 'already_received_qty', 'issued_qty')
    def _compute_returned_qty(self):
        for rec in self:
            stock_transfer = rec.stock_request_id.transfer_ids.filtered(
                lambda
                    l: l.location_dest_id.id ==
                       rec.stock_request_id.location_id.id)
            product = stock_transfer.move_ids.filtered(lambda
                                                                l: l.product_id.id ==
                                                                   rec.product_id.id)
            rec.returned_qty = sum(product.mapped('quantity'))
            rec.balance_qty = rec.issued_qty - rec.already_received_qty - rec.returned_qty

    def _compute_already_received_qty(self):
        for rec in self:
            stock_transfer = rec.stock_request_id.transfer_ids.filtered(
                lambda l:l.location_dest_id.id == rec.stock_request_id.location_dest_id.id)
            product = stock_transfer.move_ids.filtered(
                lambda l:l.product_id.id == rec.product_id.id)
            rec.already_received_qty = sum(product.mapped('quantity'))
            rec.balance_qty = rec.issued_qty - rec.already_received_qty - rec.returned_qty

    @api.depends('stock_request_id')
    def _compute_sequence_number(self):
        """Function to compute line numbers"""
        for order in self.mapped('stock_request_id'):
            sequence_number = 1
            for lines in order.move_ids:
                if lines:
                    lines.sequence_number = sequence_number
                    sequence_number += 1

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """
            The function used to update the product_uom field based on
            the selected product_id.
        """
        self.product_uom = self.product_id.uom_id.id

    @api.onchange('quantity')
    def _onchange_quantity(self):
        """
            The function used to validate the entered quantity.
        """
        if self.product_uom_qty < self.quantity:
            raise UserError(
                _("You can't transfer quantity more than demand quantity"))

    @api.depends('product_id', 'stock_request_id.location_id')
    def _compute_available_qty(self):
        for rec in self:
            rec.available_qty = rec.product_id.qty_available
            rec.location_available_qty = 0
            for stock in rec.product_id.stock_quant_ids:
                if stock.location_id == rec.stock_request_id.location_id:
                    rec.location_available_qty += stock.inventory_quantity_auto_apply

    def unlink_item(self):
        for rec in self:
            rec.unlink()
