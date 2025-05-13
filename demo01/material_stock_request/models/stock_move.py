# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
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
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockMove(models.Model):
    _inherit = 'stock.move'

    approved_quantity = fields.Integer(string="Approved Quantity")
    product_cost = fields.Float(string="Item Cost")
    total_cost = fields.Float(string="Sub Total", compute="_compute_cost",
                              store=True)

    @api.constrains('quantity', 'approved_quantity')
    def _constrains_quantity(self):
        """Check the quantity received with approved and demanded quantity"""
        for each in self:
            if (each.picking_id.request_type == 'stock_request' and
                    each.quantity > each.approved_quantity):
                raise UserError(_("Quantity Exceeds the Approved Quantity"))
            elif (each.picking_id.backorder_id and
                  each.quantity > each.product_uom_qty):
                raise UserError(_(
                    "Quantity Exceeds the Remaining Approved Quantity"))

    @api.depends('product_uom_qty', 'product_cost', 'quantity')
    def _compute_cost(self):
        """Compute the amount of material products in order_line."""
        for line in self:
            line.total_cost = line.product_uom_qty * line.product_cost \
                if line.picking_id.state == 'draft' \
                else line.quantity * line.product_cost
