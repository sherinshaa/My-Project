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
from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError


class MaterialRequest(models.Model):
    _name = 'material.request'
    _inherit = ['mail.thread']
    _description = 'Material Request'

    def get_domain(self):
        return [('id', 'in', self.env.user.department_ids.ids)]

    name = fields.Char(string='Name', default=_('New'), copy=False)
    date = fields.Date(string="Date", copy=False, required=True,
                       default=lambda self: fields.Date.today())
    issue_date = fields.Date(string="Issue Date", copy=False)
    company_id = fields.Many2one('res.company', string='Company',
                                 readonly=True,
                                 default=lambda self:
                                 self.env.user.company_id)
    state = fields.Selection([('draft', 'Draft'),
                              ('request_approve', 'Request Approve'),
                              ('approved', 'Approved'),
                              ('verified', 'Verified'),
                              ('done', 'Done'),
                              ('partially_returned', 'Partially Returned'),
                              ('fully_returned', 'Fully Returned'),
                              ('refuse', 'Refuse'),
                              ('cancel', 'Cancel')],
                             string='State', default='draft', copy=False,
                             tracking=True)
    customer_id = fields.Many2one('res.partner', string='Customer',
                                  domain="[('employee_ids','=', False)]",
                                  required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee',
                                  required=False, default=
                                  lambda self: self.env.user.employee_id)
    sales_person_id = fields.Many2one('res.users', string='Sales Person',
                                      default=lambda self: self.env.user)
    department_id = fields.Many2one('hr.department',
                                    string="Department",
                                    required=True,
                                    default=lambda
                                        self: self.env.user.department_id,
                                    domain=get_domain)
    division_id = fields.Many2one('hr.division',
                                  string='Division', store=True,
                                  related='department_id.division_id')
    location_id = fields.Many2one('stock.location', string='Source Location',
                                  related='department_id.location_id')
    issue_type_id = fields.Many2one('issue.type', string='Type',
                                    required=True)
    move_ids = fields.One2many('material.request.line',
                               inverse_name='material_request_id',
                               string="Material move")
    transfer_ids = fields.Many2many('stock.picking', string='Transfer',
                                    copy=False)
    picking_type_id = fields.Many2one('stock.picking.type',
                                      string='Operation Type', readonly=True,
                                      related='location_id.warehouse_id'
                                              '.out_type_id')
    journal_id = fields.Many2one('account.journal', string="Journal",
                                 compute='_compute_material_request_journal_id')
    is_material_department_approval_requested = fields.Boolean(
        string="Is material department approval requested", copy=False)
    requested_approvals_ids = fields.Many2many('approval.request',
                                               string='Approval Requested',
                                               copy=False)
    is_department_approved = fields.Boolean(string='Is department approved',
                                            copy=False)
    is_finance_approved = fields.Boolean(string='Is finance approved',
                                         copy=False)
    is_qty_verified = fields.Boolean(string="Is done qty verified", copy=False)
    is_done_qty_readonly = fields.Boolean(string="Is done qty readonly",
                                          copy=False,
                                          compute="_compute_is_is_done_qty_readonly")
    is_approval_active = fields.Boolean(string="Is approval active",
                                        copy=False)
    is_qty_approved = fields.Boolean(string="Is quantity approved",
                                     copy=False)
    show_entries = fields.Boolean(string="Show Entries", copy=False)
    is_contract = fields.Boolean(string="Is Contract Request",
                                 compute="_compute_is_contract_request")
    total_cost_amount = fields.Float(
        string="Total Amount",
        compute='_compute_total_cost_amount',
        store=True)
    is_delivery_pending = fields.Boolean(string='Delivery Pending',
                                         copy=False,
                                         compute='_compute_delivery_pending')
    remarks = fields.Text(string="Remarks", help='Add the Internal Remarks')
    is_partial_or_full_returned = fields.Boolean(string="Is fully or partial return",
                                                 store=True,
                                                 compute='_compute_is_partially_or_fully_returned')

    @api.onchange('sales_person_id')
    def _onchange_sale_person_id(self):
        for rec in self:
            rec.employee_id = rec.sales_person_id.employee_id.id

    @api.depends('move_ids.returned_quantity')
    def _compute_is_partially_or_fully_returned(self):
        """Check the quantities of the returned products and
         changed the state accordingly"""
        for rec in self:
            for line in rec.move_ids:
                if rec.state in ('done','partially_returned') and line.quantity > 0 and line.returned_quantity != 0:
                    if line.quantity > line.returned_quantity:
                        line.full_or_partial_return = False
                        rec.is_partial_or_full_returned = True
                    elif line.quantity == line.returned_quantity:
                        line.full_or_partial_return = True
                        rec.is_partial_or_full_returned =True
                    else:
                        line.full_or_partial_return = False
                        rec.is_partial_or_full_returned = False
                else:
                    line.full_or_partial_return = False
                    rec.is_partial_or_full_returned = False
            return_products = self.move_ids.mapped('full_or_partial_return')
            if all(return_products) and rec.state in ('done','partially_returned'):
                rec.state = 'fully_returned'
            elif any(not item for item in return_products) and rec.state in ('done','partially_returned'):
                if any(qty > 0 for qty in self.move_ids.mapped('returned_quantity')):
                    rec.state = 'partially_returned'

    @api.depends('issue_type_id')
    def _compute_is_contract_request(self):
        for rec in self:
            if (rec.issue_type_id.id == rec.env.ref(
                    'material_stock_request'
                    '.material_stock_request_warranty_contract').id or
                    rec.issue_type_id.id == rec.env.ref(
                        'material_stock_request'
                        '.material_stock_request_service_contract').id or
                    rec.issue_type_id.id == rec.env.ref(
                        'material_stock_request'
                        '.material_stock_request_installation').id or
                    rec.issue_type_id.id == rec.env.ref(
                        'material_stock_request'
                        '.material_stock_request_service_inquiry').id):
                rec.is_contract = True
            else:
                rec.is_contract = False

    @api.depends('company_id')
    def _compute_material_request_journal_id(self):
        """For taking the default value to the journal id"""
        for rec in self:
            rec.journal_id = rec.company_id.material_request_journal_id.id
            if (self.env.ref('material_stock_request.material_request_'
                             'department_approvals').active or
                    self.env.ref('material_stock_request.material_request_'
                                 'finance_approvals').active):
                self.is_approval_active = True

    @api.model
    def _compute_delivery_pending(self):
        """Function that check any transfer for this material request is in
        under the pending and shows it on the transfer smart tab"""
        for rec in self:
            material_picking_ids_state = self.env[
                'stock.picking'].sudo().search([
                ('material_request_id', '=', rec.id)]).mapped('state')
            if all(element == 'done' for element in
                   material_picking_ids_state):
                rec.is_delivery_pending = False
            else:
                rec.is_delivery_pending = True

    @api.depends('state')
    def _compute_is_is_done_qty_readonly(self):
        """compute function for making done qty readonly"""
        for rec in self:
            if ((not self.env.ref('material_stock_request.material_request_'
                                  'department_approvals').active or
                 self.env.ref('material_stock_request.material_request_'
                              'finance_approvals').active) and
                    self.state == 'approved'):
                rec.is_done_qty_readonly = True
            else:
                rec.is_done_qty_readonly = False

    def action_request_approve(self):
        """Request approval for the current record
            (department and finance approval)."""
        if not self.issue_type_id.expense_account_id:
            raise ValidationError(_('Kindly ensure that the expense account'
                                    ' is selected within the designated issue'
                                    ' type.'))
        for rec in self.move_ids:
            if not rec.product_uom_qty:
                raise ValidationError(_('Ensure that the demanded quantity'
                                        ' field is filled with a'
                                        ' valid value.'))
        material_request_department_approval_type = (
            self.env.ref('material_stock_request.material_request_'
                         'department_approvals'))
        department_manager = (
            self.department_id.department_head_id.employee_id)
        # Approval for the department head
        if (self.move_ids and material_request_department_approval_type.active
                and not self.is_material_department_approval_requested and
                self.department_id in material_request_department_approval_type.approval_department_ids):
            self.state = 'request_approve'
            material_department_approval = self.env[
                'approval.request'].sudo().create({
                'name': self.name + ' - Material Request Department'
                                    ' Approval',
                'material_stock_id': self.id,
                'request_owner_id': self.env.user.id,
                'partner_id': self.customer_id.id,
                'department_id': self.department_id.id,
                'division_id': self.division_id.id,
                'category_id': material_request_department_approval_type.id,
                'date_start': fields.Datetime.now(),
                'date_end': fields.Datetime.now(),
                'is_material_request_approval': True,
                'reason': 'This Approval Request is Created'
                          ' for the Material Request"' + self.name,
                'approver_ids': [(0, 0, {
                    'user_id': department_manager.alternative_person_id.id
                    if department_manager.is_absent
                       and department_manager.alternative_person_id
                    else self.department_id.department_head_id.id,
                })]
            })
            for approver in material_department_approval.approver_ids:
                for line in material_department_approval.category_id.approver_ids:
                    if line.user_id.id != approver.user_id.id:
                        material_department_approval.sudo().write({
                            'approver_ids': [(0, 0, {
                                'user_id': line.user_id.employee_id.alternative_person_id.id
                                if line.user_id.employee_id.alternative_person_id
                                   and line.user_id.employee_id.is_absent else line.user_id.id,
                                'required': line.required,
                            })],
                        })
            material_department_approval.sudo().action_confirm()
            self.is_material_department_approval_requested = True
            self.write({
                'requested_approvals_ids': [
                    (4, material_department_approval.id)]
            })
            # Approval for the finance department
        elif (self.is_department_approved or
              self.env.ref(
                  'material_stock_request.material_request_finance_'
                  'approvals').active) and not self.is_finance_approved:
            self.state = 'request_approve'
            material_finance_approval = self.env[
                'approval.request'].sudo().create({
                'name': self.name + ' - Material Request Finance Approval',
                'material_stock_id': self.id,
                'request_owner_id': self.env.user.id,
                'partner_id': self.customer_id.id,
                'department_id': self.department_id.id,
                'division_id': self.division_id.id,
                'category_id': self.env.ref('material_stock_request.material_'
                                            'request_finance_approvals').id,
                'date_start': fields.Datetime.now(),
                'date_end': fields.Datetime.now(),
                'is_material_request_approval': True,
                'reason': 'This Approval Request is Created'
                          ' for the Material Request"' + self.name,
            })
            material_finance_approval.sudo().action_confirm()
            self.is_material_department_approval_requested = True
            self.write({
                'requested_approvals_ids': [
                    (4, material_finance_approval.id)]
            })
        elif not self.move_ids:
            self.state = 'draft'
        else:
            self.state = 'approved'

    def action_verify_done_quantity(self):
        """Check whether the product is available in the source location"""
        for line in self.move_ids:
            if line.approved_quantity == 0.0:
                raise UserError(
                    _("Done quantity changed must be greater than zero."))
            else:
                product_qty = []
                stock = self.env['stock.quant'].sudo().search([
                    ('location_id', '=', self.location_id.id),
                    ('product_id', '=', line.product_id.id)
                ])
                if stock or line.product_id.detailed_type == 'consu':
                    quantity = 0
                    for rec in stock:
                        quantity += rec.quantity
                    if quantity < line.quantity and not line.product_id.detailed_type == 'consu':
                        raise UserError(
                            _(" %s is not available in the specified "
                              "source location.", line.product_id.name))
                    else:
                        product_qty.append(line)
                        self.is_qty_verified = True
                        self.state = 'verified'
                else:
                    raise UserError(
                        _(" %s is not available in the specified "
                          "source location.", line.product_id.name))

    def action_approve(self):
        """
            Approve the material request.
        """
        self.is_qty_verified = True
        self.is_qty_approved = True
        self.state = 'approved'

    def button_transfer(self):
        """Function for creating the picking for the products and
        create a return {
                        'name': 'Invalid Operation',
                        'type': 'ir.actions.act_window',
                        'res_model': 'transfer.warning',
                        'view_mode': 'form',
                        'target': 'new',
                    } and journal entry"""
        self.state = 'done'
        # create picking
        if self.company_id.material_request_journal_id:
            transfer = self.env['stock.picking'].sudo().create({
                'picking_type_id': self.picking_type_id.id,
                'location_id': self.location_id.id,
                'location_dest_id': self.env.ref(
                    'stock.stock_location_customers').id,
                'origin': self.name,
                'material_request_id': self.id,
                'department_id': self.department_id.id,
                'scheduled_date': self.issue_date,
                'date_done': self.issue_date,
                'user_id': self.sales_person_id.id,
                'material_transfer': True,
                'move_ids_without_package': [(fields.Command.create({
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.approved_quantity,
                    'quantity': line.quantity,
                    'product_uom': line.product_uom.id,
                    'location_id': self.location_id.id,
                    'location_dest_id': self.env.ref(
                        'stock.stock_location_customers').id,
                    'name': line.product_id.name
                })) for line in self.move_ids]
            })
            lot = 0
            for line in self.move_ids:
                if line.product_id.mapped('tracking') == ['none']:
                    lot = 0
                else:
                    lot = 1
                    break
            if lot == 1:
                self.transfer_ids = [fields.Command.link(transfer.id)]
                transfer.sudo().action_confirm()
                transfer.write({'date_done': self.issue_date})
                for move in transfer:
                    debit_vals = []
                    credit_vals = []
                    if move.material_request_id and not transfer.backorder_id:
                        debit_entries = [(0, 0, debit) for debit in
                                         debit_vals]
                        credit_entries = [(0, 0, credit) for credit in credit_vals]
                        for line in move.move_ids_without_package:
                            amount = line.product_id.standard_price * line.quantity
                            debit_entries.append((0, 0, {
                                'ref': f"{move.name}",
                                'name': f"{self.name} - "f"{line.product_id.name} ",
                                'account_id': move.material_request_id.issue_type_id.expense_account_id.id,
                                'journal_id':
                                    move.material_request_id.journal_id.id,
                                'date': move.date_done,
                                'debit': amount if amount > 0.0 else 0.0,
                                'credit': -amount if amount < 0.0 else 0.0,
                            }))
                            credit_entries.append((0, 0, {
                                'ref': f"{move.name}",
                                'name': f"{self.name} - "f"{line.product_id.name} ",
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
                            'account_move_material_request_id': self.id,
                            'line_ids': debit_entries + credit_entries,
                        }
                        if not move.stock_entry:
                            # Create the move
                            account_move = self.env[
                                'account.move'].sudo().create(
                                vals)
                            account_move.sudo()._compute_name()
                            account_move.sudo().action_post()
                            self.show_entries = True
                transfer.write({
                    'date_done': self.issue_date
                })
                return {
                    'name': 'Invalid Operation',
                    'type': 'ir.actions.act_window',
                    'res_model': 'transfer.warning',
                    'view_mode': 'form',
                    'target': 'new',
                }
            else:
                self.transfer_ids = [fields.Command.link(transfer.id)]
                transfer.write({
                    'date_done': self.issue_date
                })
                transfer.sudo().button_validate()
                # additional journal entry for picking
                for move in transfer:
                    debit_vals = []
                    credit_vals = []
                    if move.material_request_id and not transfer.backorder_id:
                        debit_entries = [(0, 0, debit) for debit in
                                         debit_vals]
                        credit_entries = [(0, 0, credit) for credit in credit_vals]
                        for line in move.move_ids_without_package:
                            amount = line.product_id.standard_price * line.quantity
                            debit_entries.append((0, 0, {
                                'ref': f"{move.name}",
                                'name':f"{self.name} - "f"{line.product_id.name} ",
                                'account_id': move.material_request_id.issue_type_id.expense_account_id.id,
                                'journal_id':
                                    move.material_request_id.journal_id.id,
                                'date': move.date_done,
                                'debit': amount if amount > 0.0 else 0.0,
                                'credit': -amount if amount < 0.0 else 0.0,
                            }))
                            credit_entries.append((0, 0, {
                                'ref': f"{move.name}",
                                'name': f"{self.name} - "f"{line.product_id.name} ",
                                'account_id':  self.env.ref('account.1_stock_out').id,
                                'journal_id':
                                    move.material_request_id.journal_id.id,
                                'date': move.date_done,
                                'debit': -amount if amount > 0.0 else 0.0,
                                'credit': amount if amount < 0.0 else 0.0,
                            }))
                        # Values for creating record in account_move
                        vals = {
                            'narration': self.name,
                            'ref': move.name,
                            'journal_id': move.material_request_id.journal_id.id,
                            'date': move.date_done,
                            'picking_id': move.id,
                            'department_id': move.department_id.id,
                            'account_move_material_request_id': self.id,
                            'line_ids': debit_entries + credit_entries,
                        }
                        if not move.stock_entry:
                            # Create the move
                            account_move = self.env[
                                'account.move'].sudo().create(
                                vals)
                            account_move.sudo()._compute_name()
                            account_move.sudo().action_post()
                            self.show_entries = True
        else:
            raise ValidationError(_('Kindly Ensure that the Default '
                                    'Journal for Material Request is '
                                    'Selected within the Configuration '
                                    'Settings.'))

    def product_transfer(self):
        """Function that check whether the products have cost and return
        the warning popup"""
        costless_products = self.move_ids.filtered(
            lambda line: line.product_id.standard_price == 0).mapped(
            'product_id')
        if costless_products:
            return {
                'name': 'Warning: Product Cost Missing',
                'type': 'ir.actions.act_window',
                'res_model': 'product.cost.warning',
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_material_request_id': self.id},
            }
        elif not self.issue_date:
            raise UserError(_("Provide Issue Date"))
        else:
            self.button_transfer()

    def action_transfer(self):
        """
            The function is used to Open a window displaying
            the related stock pickings.
        """
        material_picking_ids = self.env['stock.picking'].sudo().search([
            ('material_request_id', '=', self.id)
        ])
        return {
            'name': 'Transfer',
            'type': 'ir.actions.act_window',
            'view_type': 'tree,form',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'domain': [('id', 'in', material_picking_ids.ids)]
        }

    def action_requested_approvals(self):
        """ To show corresponding approval requests for this material
        request"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Approval Request',
            'res_model': 'approval.request',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.requested_approvals_ids.ids)],
        }

    @api.model_create_multi
    def create(self, vals_list):
        """
            Create records and assign names using a sequence.
        """
        res = super().create(vals_list)
        sequence = self.env.ref(
            'material_stock_request.material_request_code')
        for val in vals_list:
            name = self.env.ref(
                'material_stock_request.material_request_code').next_by_id(
                sequence_date=val.get('date'))
            name_list = [name[0:3]]
            if sequence.is_department and val.get('department_id',
                                                  False) \
                    and res.department_id.code:
                name_list.append(res.department_id.code)
            res.name = '-'.join(name_list) + name[3:]
            return res

    def action_view_journal_entries(self):
        """External link for account_move"""
        domain = []
        for rec in self.env['stock.picking'].search(
                [('material_request_id', '=', self.id)]):
            for line in self.env['account.move'].search(
                    [('picking_id', '=', rec.id)]):
                domain.append(line.id)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Entries'),
            'res_model': 'account.move',
            'view_mode': 'tree',
            'views': [(False, 'list'), (False, 'form')],
            'domain': [('id', 'in', domain)],
        }

    @api.depends('move_ids.total_cost')
    def _compute_total_cost_amount(self):
        for rec in self:
            total_cost = 0
            for line in rec.move_ids:
                total_cost += line.total_cost
            self.total_cost_amount = total_cost
