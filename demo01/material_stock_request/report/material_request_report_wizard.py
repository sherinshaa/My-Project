# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
from odoo import api, fields, models


class MaterialRequestReportWizard(models.Model):
    _name = 'material.request.report.wizard'

    department_ids = fields.Many2many('hr.department', string='Department')
    division_id = fields.Many2one('hr.division', string='Division')
    from_date = fields.Date(string="From Date", required=True,
                            help="Choose the from date")
    to_date = fields.Date(string="To Date", required=True,
                          help="Choose the to date")
    partner_id = fields.Many2one('res.partner', string='Customer',
                                 domain="[('employee_ids','=', False)]", )
    user_id = fields.Many2one('res.users', string='Sales Person')
    issue_type_id = fields.Many2one('issue.type', string='Issue Type')
    state = fields.Selection([('draft', 'Draft'),
                              ('request_approve', 'Request Approve'),
                              ('approved', 'Approved'),
                              ('verified', 'Verified'),
                              ('done', 'Done'),
                              ('partially_returned', 'Partially Returned'),
                              ('fully_returned', 'Fully Returned'),
                              ('pending', 'Pending(Done&Partially Returned)'),
                              ('refuse', 'Refuse'),
                              ('cancel', 'Cancel')],
                             string='State', default='draft', )
    report_type = fields.Selection([('department', 'Department'),
                                    ('customer', 'Customer'),
                                    ('issue_type', 'Issue Type'),
                                    ('sales_person', 'Salesperson'), ],
                                   string='Report Type', default='department', )
    cost_type = fields.Selection([('with_cost', 'With Cost'),
                                  ('without_cost', 'Without Cost')],
                                 string="Cost Type")
    material_request_ids = fields.Many2many(
        'material.request', string="Material Request Domain",
        compute="_compute_material_request_ids")
    material_request_id = fields.Many2one(
        'material.request', string="Material Request",
        domain="[('id', 'in', material_request_ids)]")

    @api.depends('department_ids', 'from_date', 'to_date', 'partner_id',
                 'user_id', 'issue_type_id', 'state')
    def _compute_material_request_ids(self):
        result = None
        if self.from_date and self.to_date:
            query = """
                SELECT DISTINCT mr.id
                FROM material_request mr
                LEFT JOIN hr_department dept ON mr.department_id = dept.id
                LEFT JOIN hr_division div ON mr.division_id = div.id
                LEFT JOIN res_partner cust ON mr.customer_id = cust.id
                LEFT JOIN issue_type it ON mr.issue_type_id = it.id
                LEFT JOIN res_users sp ON mr.sales_person_id = sp.id
                LEFT JOIN res_partner partner ON sp.partner_id = partner.id
                LEFT JOIN material_request_line line ON mr.id = line.material_request_id
                LEFT JOIN product_product product ON line.product_id = product.id
                LEFT JOIN product_template tmpl ON product.product_tmpl_id = tmpl.id
                WHERE mr.date >= %s AND mr.date <= %s
            """
            params = [self.from_date, self.to_date]
            if self.department_ids:
                query += ' AND mr.department_id IN %s'
                params.append(tuple(self.department_ids.ids))
            if self.partner_id:
                query += ' AND mr.customer_id = %s'
                params.append(self.partner_id.id)
            if self.issue_type_id:
                query += ' AND mr.issue_type_id = %s'
                params.append(self.issue_type_id.id)
            if self.user_id:
                query += ' AND mr.sales_person_id = %s'
                params.append(self.user_id.id)
            if self.state:
                if self.state == 'pending':
                    query += " AND mr.state IN ('done', 'partially_returned')"
                else:
                    query += ' AND mr.state = %s'
                    params.append(self.state)
            self.env.cr.execute(query, tuple(params))
            result = self.env.cr.fetchall()
        if result:
            material_request_ids = [row[0] for row in result if row[0]]
            self.material_request_ids = [(6, 0, material_request_ids)]
        else:
            self.material_request_ids = None

    def action_material_request_report(self):
        unique_data = None
        request_data = None
        query = """SELECT 
                mr.id AS material_request_id,  -- Material request ID
                mr.department_id,  -- Selecting department_id (ID)
                dept.name AS department_name,  -- Selecting department_name
                div.name AS division_name,  -- Selecting division_name
                mr.name,  -- Material request name
                mr.state,  -- State
                TO_CHAR(mr.issue_date, 'DD/MM/YYYY') AS issue_date,  -- Format issue_date
                mr.customer_id,
                cust.name AS customer_name,  -- Customer name
                mr.issue_type_id,
                it.name AS issue_type_name,  -- Issue type name
                mr.sales_person_id,
                partner.name AS sales_person_name,  -- Salesperson name
                line.product_id,  -- Product ID
                tmpl.name AS product_name,  -- Product name from product_template
                product.default_code AS cat_code,
                line.product_uom_qty,
                line.approved_quantity,
                line.quantity,  -- Done quantity
                line.returned_quantity,  -- Returned quantity
                line.total_cost, -- Cost price
                line.unit_cost
            FROM 
                material_request mr
            LEFT JOIN hr_department dept ON mr.department_id = dept.id
            LEFT JOIN hr_division div ON mr.division_id = div.id
            LEFT JOIN res_partner cust ON mr.customer_id = cust.id
            LEFT JOIN issue_type it ON mr.issue_type_id = it.id
            LEFT JOIN res_users sp ON mr.sales_person_id = sp.id
            LEFT JOIN res_partner partner ON sp.partner_id = partner.id  -- Join to get sales person's name from res_partner
            LEFT JOIN material_request_line line ON mr.id = line.material_request_id  -- Corrected this line
            LEFT JOIN product_product product ON line.product_id = product.id  -- Join to get product details
            LEFT JOIN product_template tmpl ON product.product_tmpl_id = tmpl.id  -- Join with product_template to get product name
            WHERE
                mr.date >= %s AND mr.date <= %s
        """
        params = [self.from_date, self.to_date]
        if self.department_ids:
            query += ' AND mr.department_id IN %s'
            params.append(tuple(self.department_ids.ids))
        if self.partner_id:
            query += ' AND mr.customer_id = %s'
            params.append(self.partner_id.id)
        if self.issue_type_id:
            query += ' AND mr.issue_type_id = %s'
            params.append(self.issue_type_id.id)
        if self.user_id:
            query += ' AND mr.sales_person_id = %s'
            params.append(self.user_id.id)
        if self.state:
            if self.state == 'pending':
                query += " AND mr.state IN ('done', 'partially_returned')"
            else:
                query += ' AND mr.state = %s'
                params.append(self.state)
        if self.material_request_id:
            query += ' AND mr.id = %s'
            params.append(self.material_request_id.id)
        if self.report_type == 'department':
            query += '''
                GROUP BY 
                    mr.department_id, dept.name, div.name,  mr.id,
                    mr.name, mr.state, mr.issue_date, mr.customer_id,
                    cust.name,mr.issue_type_id, it.name, mr.sales_person_id, 
                    partner.name, line.product_id, tmpl.name,
                    product.default_code, line.product_uom_qty, 
                    line.approved_quantity, line.quantity, 
                    line.returned_quantity, line.total_cost ,line.unit_cost
            '''
            self.env.cr.execute(query, tuple(params))
            result = self.env.cr.fetchall()
            department_data = []
            request_data = []
            existing_mr_ids = set()
            for row in result:
                department_data.append({
                    'department_id':  row[1],
                    'department_name': row[2]['en_US'],
                    'division_name': row[3]
                })
                mr_id = row[0]
                if mr_id not in existing_mr_ids:
                    request_data.append({
                            'department_id': row[1],
                            'mr_id': row[0],
                            'mr': row[4],
                            'issue_date': row[6],
                            'sales_person': row[12],
                            'issue_type': row[10],
                            'customer': row[8],
                            'state': row[5],
                        })
                    existing_mr_ids.add(mr_id)
            unique_data = list(
                {(d['department_id'], d['department_name'], d['division_name']): d
                 for d in department_data}.values())
        elif self.report_type == 'customer':
            query += '''
               GROUP BY 
                    mr.customer_id,cust.name, mr.department_id, 
                    dept.name, div.name,  mr.id,mr.name, mr.state, 
                    mr.issue_date, mr.issue_type_id,
                    it.name, mr.sales_person_id, partner.name, line.product_id,
                     tmpl.name,product.default_code, line.product_uom_qty, 
                     line.approved_quantity, line.quantity, 
                     line.returned_quantity, line.total_cost,line.unit_cost
           '''
            self.env.cr.execute(query, tuple(params))
            result = self.env.cr.fetchall()
            customer_data = []
            request_data = []
            existing_mr_ids = set()
            for row in result:
                customer_data.append({
                    'customer_id': row[7], 'customer_name': row[8]
                })
                mr_id = row[0]
                if mr_id not in existing_mr_ids:
                    request_data.append({
                        'department': row[2]['en_US'],
                        'division': row[3],
                        'mr_id': row[0],
                        'mr': row[4],
                        'issue_date': row[6],
                        'sales_person': row[12],
                        'issue_type': row[10],
                        'customer_id': row[7],
                        'customer': row[8],
                        'state': row[5],
                    })
                    existing_mr_ids.add(mr_id)
            unique_data = list(
                {(d['customer_id'], d['customer_name']): d
                 for d in customer_data}.values())
        elif self.report_type == 'issue_type':
            query += '''
               GROUP BY 
                 mr.issue_type_id, it.name, mr.department_id, dept.name, 
                 div.name, mr.id, mr.name, mr.state, mr.issue_date, 
                 mr.customer_id,
                cust.name, mr.sales_person_id, partner.name,  line.product_id, 
                tmpl.name,product.default_code, line.product_uom_qty, 
                line.approved_quantity, line.quantity,
                 line.returned_quantity, line.total_cost,line.unit_cost
           '''
            self.env.cr.execute(query, tuple(params))
            result = self.env.cr.fetchall()
            issue_type_data = []
            request_data = []
            existing_mr_ids = set()
            for row in result:
                issue_type_data.append({
                    'issue_type_id': row[9], 'issue_type_name': row[10]
                })
                mr_id = row[0]
                if mr_id not in existing_mr_ids:
                    request_data.append({
                        'department': row[2]['en_US'],
                        'division': row[3],
                        'mr_id': row[0],
                        'mr': row[4],
                        'issue_date': row[6],
                        'sales_person': row[12],
                        'issue_type': row[10],
                        'customer_id': row[7],
                        'customer': row[8],
                        'state': row[5],
                        'issue_type_id': row[9],
                    })
                    existing_mr_ids.add(mr_id)
            unique_data = list(
                {(d['issue_type_id'], d['issue_type_name']): d
                 for d in issue_type_data}.values())
        else:
            query += '''
               GROUP BY
                    mr.sales_person_id, partner.name, mr.department_id, 
                    dept.name, div.name,  mr.id,
                    mr.name, mr.state, mr.issue_date, mr.customer_id,
                    cust.name,mr.issue_type_id, it.name, line.product_id, 
                    tmpl.name, product.default_code, line.product_uom_qty, 
                    line.approved_quantity, line.quantity, 
                    line.returned_quantity, line.total_cost,line.unit_cost
           '''
            self.env.cr.execute(query, tuple(params))
            result = self.env.cr.fetchall()
            sales_person_data = []
            request_data = []
            existing_mr_ids = set()
            for row in result:
                sales_person_data.append({
                    'sales_person_id': row[11], 'sales_person_name': row[12]
                })
                mr_id = row[0]
                if mr_id not in existing_mr_ids:
                    request_data.append({
                        'department': row[2]['en_US'],
                        'division': row[3],
                        'mr_id': row[0],
                        'mr': row[4],
                        'issue_date': row[6],
                        'sales_person': row[12],
                        'issue_type': row[10],
                        'sales_person_id': row[11],
                        'customer': row[8],
                        'state': row[5],
                    })
                    existing_mr_ids.add(mr_id)
            unique_data = list(
                {(d['sales_person_id'], d['sales_person_name']): d
                 for d in sales_person_data}.values())
        context = {
            'filter_data': unique_data,
            'data': result,
            'request_data': request_data,
            "from_date": self.from_date.strftime
            ('%d/%m/%Y') if self.from_date else '',
            "to_date": self.to_date.strftime
            ('%d/%m/%Y') if self.to_date else '',
            'report_type': self.report_type,
            'cost_type': self.cost_type,
        }
        return (self.env.ref('material_stock_request.'
                             'action_report_material_request_template').report_action(
            self, data=context))
