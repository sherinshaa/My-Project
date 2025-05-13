# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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


class MaterialRequestLine(models.Model):
    _name = 'material.request.line'
    _description = 'Material Request Line'

    sequence_number = fields.Integer(string='#',
                                     compute='_compute_sequence_number',
                                     help='Line Numbers')

    product_id = fields.Many2one('product.product', string='Product',
                                 required=True)
    product_uom_category_id = fields.Many2one(
        related='product_id.uom_id.category_id')
    product_uom_qty = fields.Float(string='Demand', default=1)
    product_uom = fields.Many2one('uom.uom', string='Unit',
                                  domain="[('category_id', '=', "
                                         "product_uom_category_id)]")
    material_request_id = fields.Many2one('material.request',
                                          string='Material Request')
    remark = fields.Char(string='Description',
                         related='product_id.display_name')
    approved_quantity = fields.Float(string='Approved Qty',
                                     default=lambda self: self.product_uom_qty)
    quantity = fields.Float(string='Done',
                            default=lambda self: self.approved_quantity)
    returned_quantity = fields.Float(string="Returned Qty")
    available_qty = fields.Float(string='Warehouse Qty',
                                 compute='_compute_available_qty')
    location_available_qty = fields.Float(string='Location Qty',
                                          compute='_compute_available_qty')
    unit_cost = fields.Float(
        string="Unit Cost",
        compute='_compute_price_unit',
        store=True)
    total_cost = fields.Float(
        string="Total Cost",
        compute='_compute_total_cost',
        store=True)
    full_or_partial_return = fields.Boolean(string='Return',
                                            help='Check whether the product '
                                                 'is fully or partially returned')

    @api.depends('material_request_id')
    def _compute_sequence_number(self):
        """Function to compute line numbers"""
        for order in self.mapped('material_request_id'):
            sequence_number = 1
            for lines in order.move_ids:
                if lines:
                    lines.sequence_number = sequence_number
                    sequence_number += 1

    @api.onchange('product_uom_qty', 'approved_quantity')
    def onchange_done_quantity(self):
        """Function that compute the value of the done qty"""
        if self.material_request_id.state == 'draft':
            self.approved_quantity = self.product_uom_qty
        if self.material_request_id.state == 'request_approve':
            self.quantity = self.approved_quantity
        if (not self.env.ref('material_stock_request.material_request_'
                             'department_approvals').active or
                self.env.ref('material_stock_request'
                             '.material_request_finance_approvals').active):
            self.quantity = self.approved_quantity

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """
            The function used to update the product_uom field based on
            the selected product_id.
        """
        self.product_uom = self.product_id.uom_id.id

    @api.onchange('approved_quantity')
    def _onchange_approved_quantity(self):
        """
            The function used to validate the entered quantity.
        """
        if self.product_uom_qty < self.approved_quantity:
            raise UserError(
                _("You can't transfer quantity more than demand quantity"))

    @api.onchange('quantity')
    def _onchange_quantity(self):
        """
            The function used to validate the entered quantity.
        """
        if self.approved_quantity < self.quantity:
            raise UserError(
                _("You can't transfer quantity more than approved quantity"))

    @api.depends('product_id', 'material_request_id.location_id')
    def _compute_available_qty(self):
        for rec in self:
            rec.available_qty = rec.product_id.qty_available
            rec.location_available_qty = 0
            for stock in rec.product_id.stock_quant_ids:
                if stock.location_id == rec.material_request_id.location_id:
                    rec.location_available_qty += stock.inventory_quantity_auto_apply

    @api.depends('product_id')
    def _compute_price_unit(self):
        for rec in self:
            rec.unit_cost = rec.product_id.standard_price

    @api.depends('product_id', 'product_uom_qty', 'approved_quantity')
    def _compute_total_cost(self):
        for rec in self:
            unit_price = rec.product_id.standard_price
            rec.total_cost = unit_price * rec.quantity
