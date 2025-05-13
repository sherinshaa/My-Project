# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import fields, models, _
from odoo.exceptions import ValidationError


class RequestApproval(models.Model):
    """Inherits the model approval. request for approve the requests"""
    _inherit = "approval.request"

    material_stock_id = fields.Many2one("material.request",
                                        string="Material Request")
    is_material_request_approval = fields.Boolean(string="Check whether the "
                                                         "approval is created "
                                                         "for the material "
                                                         "request",copy=False)

    def action_approve(self):
        """Function for approving the request and change the
        corresponding state"""
        result = super().action_approve()
        if self.material_stock_id:
            for qty in self.material_stock_id.move_ids:
                if not qty.quantity:
                    raise ValidationError(
                        _('Kindly ensure that the done quantity is filled '
                          'for all the products.'))
            if (self.request_status == 'approved' and
                    self.category_id ==
                    self.env.ref('material_stock_request.material_request'
                                 '_department_approvals')):
                self.material_stock_id.is_department_approved = True
                self.material_stock_id.action_request_approve()
                message = (f"The Approval Request ' {self.name} ' having the "
                           f"category '{self.category_id.name} ' has been "
                           f"approved by '{self.env.user.name}. "
                           f"Now need the Finance Approval.")
                self.material_stock_id.message_post(body=message)
            if (self.request_status == 'approved' and
                    self.category_id == self.env.ref(
                        'material_stock_request.material_request_finance_'
                        'approvals')):
                self.material_stock_id.is_finance_approved = True
                self.material_stock_id.action_approve()
                message = (f"The Approval Request ' {self.name} ' having the "
                           f"category '{self.category_id.name} ' has been "
                           f"approved by '{self.env.user.name}")
                self.material_stock_id.message_post(body=message)
        return result

    def action_material_request(self):
        """ To show corresponding material request that are requested
        for approval."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Material Request',
            'res_model': 'material.request',
            'view_mode': 'tree,form',
            'domain': [('id', '=', self.material_stock_id.id)],
        }

    def action_refuse(self):
        """When refuse the approval then the material request become
         refuse state"""
        result = super(RequestApproval, self).action_refuse()
        if self.material_stock_id:
            self.material_stock_id.state = 'refuse'
            message = (f"The Approval Request ' {self.name} ' having the "
                       f"category '{self.category_id.name} ' has been refused."
                       f" Check it and do needful.")
            self.material_stock_id.message_post(body=message)
            return result
