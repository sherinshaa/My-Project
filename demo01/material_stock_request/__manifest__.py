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
{
    'name': 'Material Request or Issue Type',
    'version': '16.19.1',
    'summary': 'This module is for creating material request or issue type',
    'description': 'This module manage the issue type created by the user and '
                   'also the material request',
    'author': "Cybrosys Techno Solutions",
    'company': "Cybrosys Techno Solutions",
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['stock', 'hr_division_department', 'expiration_alert',
                'delivery', 'approvals', 'account', 'stock_extends'],
    'data': [
        'data/material_request_approval_data.xml',
        'data/stock_location_data.xml',
        'data/ir_sequence_data.xml',
        'data/paper_format_data.xml',
        'security/ir.model.access.csv',
        'security/store_manger_group.xml',
        'security/stock_request_rule.xml',
        'security/stock_picking_rule.xml',
        'security/material_request_rule.xml',
        'wizard/transfer_warning_views.xml',
        'wizard/product_cost_warning_views.xml',
        'report/material_request_report_wizard.xml',
        'report/material_request_report_template.xml',
        'report/stock_request_report_template.xml',
        'report/ir_actions_report.xml',
        'report/report_stockpicking_operations.xml',
        'report/material_request_report.xml',
        'report/material_request_report_without_cost.xml',
        'views/material_stock_request_views.xml',
        'views/stock_picking_views.xml',
        'views/res_company_views.xml',
        'views/approval_request_views.xml',
        'views/issue_type_views.xml',
        'views/hr_department_views.xml',
        'views/account_move_views.xml',
        'views/stock_location.xml',
        'views/stock_request_views.xml',
        'views/stock_ware_house_views.xml',
        'views/res_config_settings_views.xml',
        'wizard/stock_request_backorder_views.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
