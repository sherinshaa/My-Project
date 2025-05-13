# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import models, fields


class ProductCostWarning(models.TransientModel):
    _name = 'stock.request.backorder'
    _description = 'Stock Request Backorder'

    stock_request_id = fields.Many2one('stock.request', string="Stock Request")

    def action_stock_request_backorder(self):
        stock_request = self.stock_request_id
        self.env['stock.request'].sudo().create({
            'from_department_id': stock_request.from_department_id.id,
            'to_department_id': stock_request.to_department_id.id,
            'date': stock_request.issued_date,
            'backorder_id': stock_request.id,
            'location_id': stock_request.location_id.id,
            'location_dest_id': stock_request.location_dest_id.id,
            'move_ids': [(fields.Command.create({
                'product_id': line.product_id.id,
                'remark': line.remark,
                'product_uom': line.product_uom.id,
                'product_uom_qty': line.quantity - line.issued_qty,
            })) for line in stock_request.move_ids if line.quantity !=
                                             line.issued_qty]
        })
        stock_request.state = 'transit'
        transfer = self.env['stock.picking'].sudo().create({
            'picking_type_id': stock_request.picking_type_id.id,
            'location_id': stock_request.location_id.id,
            'location_dest_id': self.env.ref(
                'material_stock_request.stock_request_transit_location').id,
            'origin': stock_request.name,
            'division_id': stock_request.to_division_id.id,
            'department_id': stock_request.to_department_id.id,
            'stock_request_id': stock_request.id,
            'scheduled_date': stock_request.issued_date,
            'date_done': stock_request.issued_date,
            'move_ids_without_package': [(fields.Command.create({
                'product_id': line.product_id.id,
                'product_uom_qty': line.issued_qty,
                'quantity': line.issued_qty,
                'product_uom': line.product_uom.id,
                'location_id': stock_request.location_id.id,
                'location_dest_id': self.env.ref(
                    'material_stock_request.stock_request_transit_location').id,
                'name': line.product_id.name
            })) for line in stock_request.move_ids]
        })
        # Assign the users responsible for the stock request from the
        # department to the picking record for the record rule.
        for from_store_head in stock_request.from_department_id.store_head_ids:
            transfer.write({
                'stock_request_user_ids': [(4, from_store_head.id)]
            })
        for from_product_manager in stock_request.from_department_id.issue_product_manager_ids:
            transfer.write({
                'stock_request_user_ids': [(4, from_product_manager.id)]
            })
        for to_store_head in stock_request.to_department_id.store_head_ids:
            transfer.write({
                'stock_request_user_ids': [(4, to_store_head.id)]
            })
        for to_product_manager in stock_request.to_department_id.issue_product_manager_ids:
            transfer.write({
                'stock_request_user_ids': [(4, to_product_manager.id)]
            })
        lot = 0
        for line in stock_request.move_ids:
            if line.product_id.mapped('tracking') == ['none']:
                lot = 0
            else:
                lot = 1
                break
        if lot == 1:
            stock_request.transfer_ids = [fields.Command.link(transfer.id)]
            transfer.sudo().action_confirm()
            return {
                'name': 'Invalid Operation',
                'type': 'ir.actions.act_window',
                'res_model': 'transfer.warning',
                'view_mode': 'form',
                'target': 'new',
            }
        else:
            stock_request.transfer_ids = [fields.Command.link(transfer.id)]
            transfer.sudo().button_validate()

    def action_no_stock_request_backorder(self):
        stock_request = self.stock_request_id
        stock_request.state = 'transit'
        transfer = self.env['stock.picking'].sudo().create({
            'picking_type_id': stock_request.picking_type_id.id,
            'location_id': stock_request.location_id.id,
            'location_dest_id': self.env.ref(
                'material_stock_request.stock_request_transit_location').id,
            'origin': stock_request.name,
            'division_id': stock_request.to_division_id.id,
            'department_id': stock_request.to_department_id.id,
            'stock_request_id': stock_request.id,
            'scheduled_date': stock_request.issued_date,
            'date_done': stock_request.issued_date,
            'move_ids_without_package': [(fields.Command.create({
                'product_id': line.product_id.id,
                'product_uom_qty': line.issued_qty,
                'quantity': line.issued_qty,
                'product_uom': line.product_uom.id,
                'location_id': stock_request.location_id.id,
                'location_dest_id': self.env.ref(
                    'material_stock_request.stock_request_transit_location').id,
                'name': line.product_id.name
            })) for line in stock_request.move_ids]
        })
        # Assign the users responsible for the stock request from the
        # department to the picking record for the record rule.
        for from_store_head in stock_request.from_department_id.store_head_ids:
            transfer.write({
                'stock_request_user_ids': [(4, from_store_head.id)]
            })
        for from_product_manager in stock_request.from_department_id.issue_product_manager_ids:
            transfer.write({
                'stock_request_user_ids': [(4, from_product_manager.id)]
            })
        for to_store_head in stock_request.to_department_id.store_head_ids:
            transfer.write({
                'stock_request_user_ids': [(4, to_store_head.id)]
            })
        for to_product_manager in stock_request.to_department_id.issue_product_manager_ids:
            transfer.write({
                'stock_request_user_ids': [(4, to_product_manager.id)]
            })
        lot = 0
        for line in stock_request.move_ids:
            if line.product_id.mapped('tracking') == ['none']:
                lot = 0
            else:
                lot = 1
                break
        if lot == 1:
            stock_request.transfer_ids = [fields.Command.link(transfer.id)]
            transfer.sudo().action_confirm()
            return {
                'name': 'Invalid Operation',
                'type': 'ir.actions.act_window',
                'res_model': 'transfer.warning',
                'view_mode': 'form',
                'target': 'new',
            }
        else:
            stock_request.transfer_ids = [fields.Command.link(transfer.id)]
            transfer.sudo().button_validate()
