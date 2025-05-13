# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
from odoo import fields, models


class StockPicking(models.Model):
    """
    This model is inherited for adding the
    """
    _inherit = 'stock.picking'

    request_type = fields.Selection(
        [('material_request', 'Material Request'),
         ('stock_request', 'Stock Request')], string='Request Type')
    state = fields.Selection(selection_add=[
        ('request_approval', 'Requested Approval'), ('approved', 'Approved'),
        ('waiting', 'Waiting Another Operation')])
    issue_type_id = fields.Many2one('issue.type',
                                    string='Issue Type',
                                    help="Choose an issue type for the "
                                         "material_request")
    return_date = fields.Date(string="Return Date", help="Return date for the "
                                                         "requested material")
    to_department_id = fields.Many2one('hr.department',
                                       string="To Department")
    to_division_id = fields.Many2one('hr.division',
                                     string="To Division",
                                     related='to_department_id.division_id')
    journal_id = fields.Many2one('account.journal',
                                 string="Journal",
                                 help="Choose a journal type for entries",
                                 domain="[('company_id', '=', company_id)]")
    show_action_validate = fields.Boolean(
        help='Technical field used to compute whether the button '
             '"Request Approval" should be displayed.', copy=False)
    show_entries = fields.Boolean(string="Show Entries", copy=False)
    stock_entry = fields.Boolean(string="Stock Entries", copy=False)
    material_request_id = fields.Many2one('material.request',
                                          string='Material Request')
    stock_request_id = fields.Many2one('stock.request',
                                          string='Stock Request')
    material_transfer = fields.Boolean(string="Is Material Transferred",
                                       copy=False)
    backorder_journal = fields.Boolean(string="Back order Jornal", copy=False)
    stock_request_user_ids = fields.Many2many('res.users',string="Stock Request User's'",
                                              help='It shows the users who can see '
                                                   'te record of stock request picking')

    def button_validate(self):
        """Function that create additional journal entry for the picking"""
        result = super().button_validate()
        if self.return_id and self.return_id.stock_request_id:
            no_balance = self.return_id.stock_request_id.move_ids\
                .filtered(
                lambda l:l.balance_qty != 0)
            if not no_balance and self.return_id.stock_request_id.state not in ['draft', 'request_approve', 'approved']:
                self.return_id.stock_request_id.state = 'done'
        if self.material_request_id:
            for move in self.move_ids:
                for journal in move.account_move_ids:
                    for line in journal.line_ids:
                        line.write({
                            'ref': f"{self.name}",
                            'name': f"{self.material_request_id.name} - "f"{move.product_id.name} "
                        })
        if self.material_request_id or self.return_id or self.backorder_id:
            if self.date_done:
                scraps = self.env['stock.scrap'].search([('picking_id', '=', self.id)])
                move_id = (self.move_ids + scraps.move_ids).stock_valuation_layer_ids.account_move_id
                move_id.write({'date': self.date_done})
            else:
                self.date_done = self.scheduled_date
        if self.material_request_id and (
                (self.backorder_id and not self.backorder_journal) or (
                self.return_id)):
            if self.date_done:
                scraps = self.env['stock.scrap'].search([('picking_id', '=', self.id)])
                move_id = (self.move_ids + scraps.move_ids).stock_valuation_layer_ids.account_move_id
                move_id.write({'date': self.date_done})
            else:
                self.date_done = self.scheduled_date
            # additional journal entry for backorder
            for move in self:
                debit_vals = []
                credit_vals = []
                if move.material_request_id and move.backorder_id:
                    debit_entries = [(0, 0, debit) for debit in debit_vals]
                    credit_entries = [(0, 0, credit) for credit in credit_vals]
                    for line in move.move_ids_without_package:
                        amount = line.account_move_ids.amount_total
                        debit_entries.append((0, 0, {
                            'ref': f"{self.name}",
                            'name': f"{self.material_request_id.name} - "f"{line.product_id.name} ",
                            'account_id': move.material_request_id.issue_type_id.expense_account_id.id,
                            'journal_id':
                                move.material_request_id.journal_id.id,
                            'date': move.date_done,
                            'debit': amount if amount > 0.0 else 0.0,
                            'credit': -amount if amount < 0.0 else 0.0,
                        }))
                        credit_entries.append((0, 0, {
                            'ref': f"{self.name}",
                            'name': f"{self.material_request_id.name} - "f"{line.product_id.name} ",
                            'account_id': self.env.ref('account.1_stock_out').id,
                            'journal_id':
                                move.material_request_id.journal_id.id,
                            'date': move.date_done,
                            'debit': -amount if amount > 0.0 else 0.0,
                            'credit': amount if amount < 0.0 else 0.0,
                        }))
                    # Values for creating record in account_move
                    vals = {
                        'narration': move.name,
                        'ref': move.name,
                        'journal_id': move.material_request_id.journal_id.id,
                        'date': move.date_done,
                        'picking_id': move.id,
                        'department_id': move.department_id.id,
                        'line_ids': debit_entries + credit_entries,
                    }
                    # Create the move
                    account_move = self.env['account.move'].sudo().create(vals)
                    account_move._compute_name()
                    account_move.action_post()
                    self.backorder_journal = True
                    for request in self.material_request_id.move_ids:
                        for product in self.move_ids_without_package:
                            if request.product_id == product.product_id:
                                request.quantity += product.quantity
                # Journal entry for the return
                if self.return_id:
                    debit_entries = [(0, 0, debit) for debit in debit_vals]
                    credit_entries = [(0, 0, credit) for credit in credit_vals]
                    for line in move.move_ids_without_package:
                        amount = line.account_move_ids.amount_total
                        debit_entries.append((0, 0, {
                            'ref': f"{self.name}",
                            'name': f"{self.material_request_id.name} - "f"{line.product_id.name} ",
                            'account_id': self.env.ref(
                                'account.1_stock_out').id,
                            'journal_id':
                                move.material_request_id.journal_id.id,
                            'date': move.date_done,
                            'debit': amount if amount > 0.0 else 0.0,
                            'credit': -amount if amount < 0.0 else 0.0,
                        }))
                        credit_entries.append((0, 0, {
                            'ref': f"{self.name}",
                            'name': f"{self.material_request_id.name} - "f"{line.product_id.name} ",
                            'account_id': move.material_request_id.issue_type_id.expense_account_id.id,
                            'journal_id':
                                move.material_request_id.journal_id.id,
                            'date': move.date_done,
                            'debit': -amount if amount > 0.0 else 0.0,
                            'credit': amount if amount < 0.0 else 0.0,
                        }))
                    # Values for creating record in account_move
                    vals = {
                        'narration': move.name,
                        'ref': move.name,
                        'journal_id': move.material_request_id.journal_id.id,
                        'date': move.date_done,
                        'picking_id': move.id,
                        'department_id': move.department_id.id,
                        'line_ids': debit_entries + credit_entries,
                    }
                    account_move = self.env['account.move'].sudo().create(vals)
                    account_move._compute_name()
                    account_move.action_post()
                    # update the returned qty in the material move line while return th eproduct
                    for return_prdt in self.move_line_ids:
                        product = self.material_request_id.move_ids.filtered(
                            lambda l: l.product_id.id == return_prdt.product_id.id)
                        if len(product) > 1:
                            return_qty = return_prdt.quantity
                            for rec in product:
                                if rec.returned_quantity < rec.quantity:
                                    balance_return = rec.quantity - rec.returned_quantity
                                    if balance_return >= return_qty:
                                        rec.returned_quantity += return_qty
                                        return_qty = 0
                                    elif balance_return < return_qty:
                                        rec.returned_quantity += balance_return
                                        return_qty = return_qty - balance_return
                        else:
                            product.returned_quantity += return_prdt.quantity

        return result
