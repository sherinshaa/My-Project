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
from odoo import models, fields


class IssueType(models.Model):
    """Create and record issue type for internal transfers done as
     material requests"""
    _name = 'issue.type'
    _description = 'Issue Type'
    _inherit = ['mail.thread']

    name = fields.Char(string="Name")
    expense_account_id = fields.Many2one('account.account',
                                         string="Expense Account",
                                         help="Choose account for "
                                              "stock transfer debit")
    company_id = fields.Many2one('res.company', string='Company',
                                 readonly=True,
                                 default=lambda self:
                                 self.env.user.company_id)
    note = fields.Text(string="Description",
                       help="Add a description for the issue type")
