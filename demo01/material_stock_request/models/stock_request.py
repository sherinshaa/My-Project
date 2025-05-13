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
from odoo.exceptions import UserError, ValidationError


class StockRequest(models.Model):
    _name = 'stock.request'
    _inherit = ['mail.thread']
    _description = 'Stock Request'

    def get_domain(self):
        return [('id', 'in', self.env.user.department_ids.ids)]

    name = fields.Char(string='Name', default=_('New'), copy=False)
    date = fields.Date(string="Date", copy=False, required=True,
                       default=lambda self: fields.Date.today())
    issued_date = fields.Date(string="Issue Date", copy=False)
    received_date = fields.Date(string="Receive Date", copy=False,
                                tracking=True,
                                )
    from_department_id = fields.Many2one('hr.department',
                                         string="From Department",
                                         required=True,
                                         default=lambda
                                             self: self.env.user.department_id,
                                         domain=get_domain)
    from_division_id = fields.Many2one('hr.division',
                                       string='From Division',
                                       related='from_department_id.division_id',
                                       store=True)
    location_id = fields.Many2one('stock.location', string='Source Location')
    location_dest_id = fields.Many2one('stock.location',
                                       string='Destination Location',
                                       required=True)
    to_department_id = fields.Many2one('hr.department',
                                       string="To Department",
                                       required=True)
    to_division_id = fields.Many2one('hr.division',
                                     string='To Division',
                                     related='to_department_id.division_id',
                                     store=True)

    move_ids = fields.One2many('stock.request.line',
                               inverse_name='stock_request_id',
                               string="Stock move")
    state = fields.Selection([('draft', 'Draft'),
                              ('request_approve', 'Request Approve'),
                              ('approved', 'Approved'),
                              ('transit', 'In Transit'),
                              ('done', 'Done'),
                              ('refuse', 'Refuse'),
                              ('cancel', 'Cancel')
                              ],
                             string='State',
                             default='draft', copy=False,
                             tracking=True)
    request_by = fields.Many2one('res.users', string='Requested By',
                                 readonly=True, copy=False)
    approved_by = fields.Many2one('res.users', string='Approved By',
                                  readonly=True, copy=False)
    transfer_ids = fields.Many2many('stock.picking', string='Transfer',
                                    copy=False,
                                    compute="_compute_transfer_ids",
                                    search="_search_transfer_ids",
                                    )
    is_pos_stock_request = fields.Boolean(string="Is Stock Request from POS")
    domain_picking_ids = fields.Many2many('stock.picking.type',
                                          string="Department Operation Type",
                                          compute="_compute_domain_operation_type")
    picking_type_id = fields.Many2one('stock.picking.type',
                                      string='Operation Type',
                                      default=lambda
                                          self: self.env.user.department_id.location_id.warehouse_id.int_type_id,
                                      domain="[('id', 'in', domain_picking_ids)]",
                                      required=True)
    is_form_department = fields.Boolean(copy=False,
                                        string='From Department Person',
                                        compute='_compute_is_form_department')
    is_to_department = fields.Boolean(copy=False,
                                      string='To Department Person',
                                      compute='_compute_is_to_department')
    is_issue_store = fields.Boolean(string='Store Issue',
                                    compute='_compute_is_issue_store')
    is_issue_office = fields.Boolean(string='Office Issue',
                                     compute='_compute_is_issue_store')
    is_any_one = fields.Boolean(string='Any Department User',
                                compute='_compute_is_any_one')
    is_approve_visible = fields.Boolean(string='Is User in Approver List',
                                        compute='_compute_is_approve_visible')
    is_stock_receive_visible = fields.Boolean(
        string='Is User has Receive Stock',
        compute='_compute_is_stock_receive_visible')
    is_product_issue_manager = fields.Boolean(
        string='Is Product Issue Manger',
        compute='_compute_is_product_issue_manager')
    is_delivery_pending = fields.Boolean(string='Delivery Pending',
                                         copy=False,
                                         compute='_compute_delivery_pending')
    backorder_id = fields.Many2one('stock.request', string="Backorder Stock "
                                                           "Request", copy=False)
    pending_issue = fields.Boolean(string="Pending Issues",
                                   compute="_compute_pending_issue",
                                   store=True, copy=False)
    pending_receipts = fields.Boolean(string="Pending Receipts",
                                      compute="_compute_pending_issue",
                                      store=True, copy=False)
    lot_ids = fields.One2many('stock.request.lot', 'stock_request_id',
                              string="Lot/Serial Number")

    @api.depends('transfer_ids', 'transfer_ids.state',
                 'move_ids.balance_qty', 'state')
    def _compute_pending_issue(self):
        for rec in self:
            issue = rec.transfer_ids.filtered(lambda l:l.location_id.id ==
                                                       rec.location_id.id)
            receive = rec.transfer_ids.filtered(lambda
                                                    l:l.location_dest_id.id ==
                                               rec.location_dest_id.id)
            if issue and all(state == 'done' for state in issue.mapped(
                    'state')):
                rec.pending_issue = False
            else:
                if rec.state == 'transit':
                    rec.pending_issue = True
                else:
                    rec.pending_issue = False
            balance = rec.move_ids.filtered(lambda l:l.balance_qty != 0)
            if not rec.pending_issue:
                if receive and all(state == 'done' for state in
                                         receive.mapped('state')) and not balance:
                    rec.pending_receipts = False
                elif rec.state == 'transit' and not rec.pending_issue or \
                        balance:
                    if rec.state not in ['transit']:
                        rec.pending_receipts = False
                    else:
                        rec.pending_receipts = True
                else:
                    rec.pending_receipts = False
            else:
                rec.pending_receipts = False

    def action_backorder(self):
        """ To show corresponding Back order stock request."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Backorder Request',
            'res_model': 'stock.request',
            'view_mode': 'tree,form',
            'domain': [('id', '=', self.backorder_id.id)],
        }

    def _compute_transfer_ids(self):
        for rec in self:
            stock_picking_ids = self.env['stock.picking'].sudo().search([
                ('stock_request_id', '=', rec.id)
            ])
            if stock_picking_ids:
                rec.transfer_ids = stock_picking_ids.ids
            else:
                rec.transfer_ids = None

    def _search_transfer_ids(self, operator, value):
        domain = [('stock_request_id', operator, value)]
        matching_picking = self.env['stock.picking'].search(domain)
        return [('id', 'in', list(set(
            picking.stock_request_id.id for picking in matching_picking if
            picking.stock_request_id)))]

    @api.constrains('received_date')
    def constrain_received_date(self):
        for rec in self:
            if rec.issued_date > rec.received_date:
                raise ValidationError(
                    _(f'The date of issue must come before the date of receipt.'))

    @api.depends('is_pos_stock_request')
    def _compute_domain_operation_type(self):
        """function for computing the domain for the field operation type
        based on whether the user is pos cashier or normal user"""
        for rec in self:
            if rec.is_pos_stock_request:
                self.write({
                    'domain_picking_ids': [
                        (4,
                         self.env.user.department_id.location_id.warehouse_id.int_type_id.id)]
                })
            else:
                for dept in self.env['stock.picking.type'].sudo().search(
                        [('code', '=', 'internal')]):
                    self.write(({
                        'domain_picking_ids': [
                            (4, dept.id)
                        ]
                    }))

    def action_request_approve(self):
        """
            Request approval for the current record.
        """
        stock = []
        for line in self.move_ids:
            if line.product_uom_qty == 0.0:
                raise UserError(
                    _("Demand quantity changed must be greater than zero."))

            if line.location_available_qty >= line.product_uom_qty and \
                    line.location_available_qty != 0:
                stock.append(True)
            else:
                stock.append(False)
        self.request_by = self.env.user.id
        if all(stock):
            if self.move_ids:
                self.state = 'request_approve'
                mail_to = self.env.user.department_id.department_head_id.mapped(
                    'work_email')
                mail_cc = self.env.user.department_id.store_head_ids.mapped(
                    'work_email')
                message = (
                    f"Dear {self.env.user.department_id.department_head_id.name},<br/> "
                    f"An Stock Request- {self.name} - is created from the {self.to_department_id.name}"
                    f" department.<br/>"
                    f" Regards :-"
                    f" {self.env.user.name}")
                mail_values = {
                    'subject': f"Stock Request-  {self.name}",
                    'email_from': self.env.user.mapped('email')[0],
                    'author_id': self.env.user.partner_id.id,
                    'email_to': f'<{mail_to}>',
                    'email_cc': ', '.join(mail_cc),
                    'body_html': message,
                }
                self.env['mail.mail'].sudo().create(mail_values).send()
        else:
            raise UserError(
                _("Please check the stock. Some of the products are out of "
                  "stock."))

    def action_approve(self):
        """
            Approve the current record.
        """
        if sum(self.move_ids.mapped('quantity')) == 0.0:
            raise UserError(
                _("Approved quantity changed must be greater than zero."))
        out_of_stock = self.move_ids.filtered(lambda
                                                  l:l.location_available_qty <
                                        l.quantity)
        if not out_of_stock:
            for line in self.move_ids:
                line.issued_qty = line.quantity
                if line.quantity > 0.0:
                    stock = self.env['stock.quant'].sudo().search([
                        ('location_id', '=',
                         self.location_id.id),
                        ('product_id', '=',
                         line.product_id.id)
                    ])
                    if stock:
                        quantity = 0
                        for rec in stock:
                            quantity += rec.quantity
                        if quantity < line.quantity:
                            raise UserError(
                                _(" %s is not available in the specified "
                                  "source location.", line.product_id.name))
                        else:
                            self.state = 'approved'
                            self.approved_by = self.env.user.id
                            if line.product_id.tracking != 'none':
                                self.env['stock.request.lot'].sudo().create({
                                    'stock_request_id': self.id,
                                    'product_id': line.product_id.id,
                                    'qty': line.issued_qty,
                                })
                    else:
                        raise UserError(
                            _(" %s is not available in the specified "
                              "source location.", line.product_id.name))
        else:
            raise UserError(
                _("Please check the stock. Some of the products are out of "
                  "stock."))

    def button_transfer(self):
        if not self.issued_date:
            raise ValidationError(
                _(f'Please Enter Issue Date.'))
        decimal_qty = self.move_ids.filtered(lambda l: not l.issued_qty.is_integer())
        if decimal_qty:
            raise ValidationError(
                _(f'Please check the qty in lines.Quantity must be Integer.'))
        out_of_stock = self.move_ids.filtered(
            lambda l: l.location_available_qty < l.issued_qty)
        lot_product_stock_line = self.move_ids.filtered(
            lambda l: l.product_id.tracking != 'none').mapped(
            'product_id.id')
        lot_product = self.lot_ids.mapped('product_id.id')
        if not out_of_stock:
            lot_pending = self.lot_ids.filtered(
                lambda l: l.lot_qty_pending)
            if set(lot_product_stock_line) == set(lot_product) and not lot_pending:
                partially_issued = []
                for line in self.move_ids:
                    if line.quantity != line.issued_qty:
                        partially_issued.append(True)
                    else:
                        partially_issued.append(False)
                    if line.issued_qty > line.quantity and line.issued_qty != 0:
                        raise UserError(
                            _("Issued Qty must be Less than or equal "
                              "to  Approved"
                              "Qty."))
                    if sum(self.move_ids.mapped('issued_qty')) == 0.0:
                        raise UserError(
                            _("Issued Qty changed must be greater than zero."))
                if any(partially_issued):
                    return {
                        'name': 'BackOrder',
                        'type': 'ir.actions.act_window',
                        'res_model': 'stock.request.backorder',
                        'view_mode': 'form',
                        'target': 'new',
                        'context': {
                            'default_stock_request_id': self.id,
                        },
                    }
                else:
                    self.state = 'transit'
                    transfer = self.env['stock.picking'].sudo().create({
                        'picking_type_id': self.picking_type_id.id,
                        'location_id': self.location_id.id,
                        'location_dest_id': self.env.ref(
                            'material_stock_request.stock_request_transit_location').id,
                        'origin': self.name,
                        'division_id': self.to_division_id.id,
                        'department_id': self.to_department_id.id,
                        'stock_request_id': self.id,
                        'scheduled_date': self.issued_date,
                        'date_done': self.issued_date,
                        'move_ids': [(fields.Command.create({
                            'product_id': line.product_id.id,
                            'product_uom_qty': line.issued_qty,
                            'quantity': line.issued_qty,
                            'product_uom': line.product_uom.id,
                            'location_id': self.location_id.id,
                            'location_dest_id': self.env.ref(
                                'material_stock_request.stock_request_transit_location').id,
                            'name': line.product_id.name,
                            'move_line_ids': [fields.Command.create({
                                'product_id': line.product_id.id,
                                'lot_id': lot.lot_id.id,
                                'quantity': lot.qty,
                                'product_uom_id': line.product_uom.id,
                                'location_id': self.location_id.id,
                                'location_dest_id': self.env.ref('material_stock_request.stock_request_transit_location').id,
                            })
                            for lot in self.lot_ids.filtered(lambda l: l.product_id.id == line.product_id.id)]
                        })) for line in self.move_ids]
                    })
                    # Assign the users responsible for the stock request from the
                    # department to the picking record for the record rule.
                    for from_store_head in self.from_department_id.store_head_ids:
                        transfer.write({
                            'stock_request_user_ids': [(4, from_store_head.id)]
                        })
                    for from_product_manager in self.from_department_id.issue_product_manager_ids:
                        transfer.write({
                            'stock_request_user_ids': [(4, from_product_manager.id)]
                        })
                    for to_store_head in self.to_department_id.store_head_ids:
                        transfer.write({
                            'stock_request_user_ids': [(4, to_store_head.id)]
                        })
                    for to_product_manager in self.to_department_id.issue_product_manager_ids:
                        transfer.write({
                            'stock_request_user_ids': [(4, to_product_manager.id)]
                        })
                    self.transfer_ids = [fields.Command.link(transfer.id)]
                    transfer.sudo().action_confirm()
                    transfer.sudo().button_validate()
            else:
                raise ValidationError(
                    _('Please Add lot product in Lot/Serial Number lines or '
                      'Issued Qty is not Equal to Lot Qty.'))
        else:
            raise UserError(
                _("Please check the stock. Some of the products are out of "
                  "stock."))

    def button_receive(self):
        """
        The function used to initiate the transfer
        process for the current record.
        """
        if not self.received_date:
            raise ValidationError(
                _(f'Please Enter Receive Date. '))
        decimal_qty = self.move_ids.filtered(lambda l: not l.received_qty.is_integer())
        if decimal_qty:
            raise ValidationError(
                _(f'Please check the qty in lines.Quantity must be Integer.'))
        partially_receive = []
        for line in self.move_ids:
            if line.received_qty + line.already_received_qty + \
                    line.returned_qty != \
                    line.issued_qty and line.balance_qty != 0:
                partially_receive.append(True)
            else:
                partially_receive.append(False)
            if line.received_qty + line.already_received_qty + \
                    line.returned_qty > line.issued_qty and line.balance_qty != 0:
                raise UserError(
                    _("Received Qty must be Less than or equal "
                      "to  Issued"
                      "Qty."))
        if all(value is False for value in partially_receive):
            self.state = 'done'
        receive = self.env['stock.picking'].sudo().create({
            'picking_type_id': self.picking_type_id.id,
            'location_id': self.env.ref(
                'material_stock_request.stock_request_transit_location').id,
            'location_dest_id': self.location_dest_id.id,
            'origin': self.name,
            'division_id': self.from_division_id.id,
            'department_id': self.from_department_id.id,
            'stock_request_id': self.id,
            'scheduled_date': self.received_date,
            'date_done': self.received_date,
            'move_ids': [(fields.Command.create({
                'product_id': line.product_id.id,
                'product_uom_qty': line.received_qty,
                'quantity': line.received_qty,
                'product_uom': line.product_uom.id,
                'location_id': self.env.ref(
                    'material_stock_request.stock_request_transit_location').id,
                'location_dest_id': self.location_dest_id.id,
                'name': line.product_id.name,
                'move_line_ids': [fields.Command.create({
                    'product_id': line.product_id.id,
                    'lot_id': lot.lot_id.id,
                    'quantity': line.received_qty,
                    'product_uom_id': line.product_uom.id,
                    'location_id': self.env.ref(
                        'material_stock_request.stock_request_transit_location').id,
                    'location_dest_id': self.location_dest_id.id,
                })
                    for lot in self.lot_ids.filtered(
                        lambda l: l.product_id.id == line.product_id.id)]
            })) for line in self.move_ids if
                                             line.already_received_qty + line.returned_qty !=
                                          line.issued_qty]
        })
        # Assign the users responsible for the stock request from the
        # department to the picking record for the record rule.
        for from_store_head in self.from_department_id.store_head_ids:
            receive.write({
                'stock_request_user_ids': [(4, from_store_head.id)]
            })
        for from_product_manager in self.from_department_id.issue_product_manager_ids:
            receive.write({
                'stock_request_user_ids': [(4, from_product_manager.id)]
            })
        for to_store_head in self.to_department_id.store_head_ids:
            receive.write({
                'stock_request_user_ids': [(4, to_store_head.id)]
            })
        for to_product_manager in self.to_department_id.issue_product_manager_ids:
            receive.write({
                'stock_request_user_ids': [(4, to_product_manager.id)]
            })
        self.transfer_ids = [fields.Command.link(receive.id)]
        receive.sudo().action_confirm()
        receive.sudo().button_validate()

    def action_transfer(self):
        """
            The function is used to Open a window displaying
            the related stock pickings.
        """
        stock_picking_ids = self.env['stock.picking'].sudo().search([
            ('stock_request_id', '=', self.id)
        ])
        return {
            'name': 'Transfer',
            'type': 'ir.actions.act_window',
            'view_type': 'tree,form',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'domain': [('id', 'in', stock_picking_ids.ids)]
        }

    @api.onchange('from_department_id')
    def _onchange_from_department_id(self):
        """
            The onchange function used to update the location based
            on the selected department.
        """
        self.location_dest_id = self.from_department_id.location_id.id

    @api.onchange('to_department_id')
    def _onchange_to_department_id(self):
        """
            The onchange function used to update the location based
            on the selected department.
        """
        self.location_id = self.to_department_id.location_id.id

    @api.model_create_multi
    def create(self, vals_list):
        """
            Create records and assign names using a sequence.
        """
        res = super().create(vals_list)
        sequence = self.env.ref(
            'material_stock_request.stock_request_code')
        for val in vals_list:
            name = self.env.ref(
                'material_stock_request.stock_request_code').next_by_id(
                sequence_date=val.get('date'))
            name_list = [name[0:3]]
            if sequence.is_department and val.get('from_department_id',
                                                  False) \
                    and res.from_department_id.code:
                name_list.append(res.from_department_id.code)
            res.name = '-'.join(name_list) + name[3:]
            return res

    @api.depends('from_department_id')
    def _compute_is_form_department(self):
        """
            This method is triggered when the 'from_department_id'
            field changes.It sets the value of 'is_form_department'
            based on whether 'from_department_id' is in the user's
            department_ids.
        """
        for rec in self:
            rec.is_form_department = True if rec.from_department_id in self.env.user.department_ids else False

    @api.depends('to_department_id')
    def _compute_is_to_department(self):
        """
            This method is triggered when the 'to_department_id' field changes.
            It sets the value of 'is_to_department' based on whether
            'to_department_id' is in the user's department_ids.
        """
        for rec in self:
            rec.is_to_department = True if rec.to_department_id in self.env.user.department_ids else False

    def action_refuse(self):
        """
            The function used to cancel the current record.
        """
        self.state = 'refuse'

    def action_cancel(self):
        self.state = 'cancel'

    def action_draft(self):
        self.state = 'draft'

    def unlink(self):
        """
            This method allows the deletion of the current record
            if its state is not 'approved', 'transit', or 'done'. If the state
            is one of these, a UserError is raised, and the record is
            not deleted.
        """
        for rec in self:
            if rec.state in ('approved', 'transit', 'done'):
                raise UserError(
                    _("This record cannot be deleted because a Stock "
                      "request associated with it has already "
                      "been approved."))
            else:
                return super().unlink()

    def _compute_is_issue_store(self):
        for rec in self:
            rec.is_issue_office = False
            rec.is_issue_store = False
            if rec.location_id.warehouse_id.is_stock_request == False:
                rec.is_issue_store = True
                rec.is_issue_office = False
                if self.env.user.has_group(
                        'material_stock_request.inventory_store_manger'):
                    rec.is_issue_office = True

    def button_transfer_store_manger(self):
        return self.sudo().button_transfer()

    def _compute_is_any_one(self):
        for rec in self:
            rec.is_any_one = True if rec.from_department_id \
                                     in self.env.user.department_ids \
                                     or rec.to_department_id in \
                                     self.env.user.department_ids else False

    def _compute_is_approve_visible(self):
        for rec in self:
            rec.is_approve_visible = True if self.env.user in rec.to_department_id.store_head_ids else False

    def _compute_is_stock_receive_visible(self):
        for rec in self:
            rec.is_stock_receive_visible = True if self.env.user in rec.from_department_id.receive_product_manager_ids else False

    def _compute_is_product_issue_manager(self):
        for rec in self:
            rec.is_product_issue_manager = True if self.env.user in rec.to_department_id.issue_product_manager_ids else False

    @api.model
    def _compute_delivery_pending(self):
        """Function that check any transfer for this stock request is in
        under the pending and shows it on the transfer smart tab"""
        for rec in self:
            material_picking_ids_state = self.env[
                'stock.picking'].sudo().search([
                ('stock_request_id', '=', rec.id)]).mapped('state')
            if all(element == 'done' for element in
                   material_picking_ids_state):
                rec.is_delivery_pending = False
            else:
                rec.is_delivery_pending = True
