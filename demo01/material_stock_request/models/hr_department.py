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
from odoo import fields, models


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    account_id = fields.Many2one('account.account',
                                 string="Inventory Valuation Account",
                                 help="Choose account for "
                                      "inventory valuation")
    store_head_ids = fields.Many2many('res.users', 'depart_store_head_rel',
                                      column1="store_head_id",
                                      column2="res_user_id",
                                      string="Store Head's",
                                      help="Choose the store head for approving the stock request from"
                                           " department")
    issue_product_manager_ids = fields.Many2many('res.users', 'depart_issue_product_manager_rel',
                                      column1="issue_product_manager_id",
                                      column2="res_issue_product",
                                      string="Product Issue Manger's",
                                      help="Choose the product manager for issuing the product for stock request"
                                           )
    receive_product_manager_ids = fields.Many2many(
        'res.users', 'depart_received_product_manager_rel',
        column1="received_product_manager_id",
        column2="res_received_product",
        string="Product Receive Manger's",
        help="Choose the product manager for receiving the product for "
             "stock request")
