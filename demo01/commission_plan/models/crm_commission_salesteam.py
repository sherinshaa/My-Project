from odoo import models, fields


class Team(models.Model):
    _inherit = 'crm.team'

    commission_plan = fields.Many2one('crm.commission', string='Commission Plan')
    commission_amount = fields.Float(string='Commission Amount')

    def field_reset(self):
        reset = self.env['crm.team'].search([])
        for commission in reset:
            print(commission.commission_amount)
            print(commission.commission_plan)
            commission.commission_amount = 0
            print(commission.commission_amount)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    commission_amount_team = fields.Float(string='Commission Amount (Team)')
    commission_amount_person = fields.Float(string='Commission Amount (Person)')

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        if self.team_id.commission_plan.commission_type == "revenue_wise":
            fetched_data_revenue = self.env['crm.commission'].search(
                [('commission_type', '=', 'revenue_wise')])
            if self.team_id.commission_plan.straight:
                commission = self.amount_total * (self.team_id.commission_plan.straight_percentage / 100)
                self.commission_amount_team = self.team_id.commission_amount = self.team_id.commission_amount + commission
                self.commission_amount_person = self.user_id.commission_amount = self.user_id.commission_amount + commission
            if not self.team_id.commission_plan.straight:
                total_amount = self.amount_total
                graduated_commission_total = 0
                commission_list = []
                for graduated in fetched_data_revenue.graduated_commission_ids:
                    if self.amount_total > graduated.to_amount:
                        graduated_commission = graduated.to_amount * (graduated.commission_percentage / 100)
                        total_amount = self.amount_total - graduated.to_amount
                        commission_list.append(graduated_commission)
                    else:
                        graduated_commission = total_amount * (graduated.commission_percentage / 100)
                        commission_list.append(graduated_commission)
                        break
                for commission in commission_list:
                    graduated_commission_total = graduated_commission_total + commission
                self.commission_amount_team = self.team_id.commission_amount = self.team_id.commission_amount + graduated_commission_total
                self.commission_amount_person = self.user_id.commission_amount = self.user_id.commission_amount + graduated_commission_total
        else:
            fetched_data_productwise = self.env['crm.commission'].search(
                [('commission_type', '=', 'product_wise')])
            productwises = fetched_data_productwise.productwise_commission_ids
            for product_wise in productwises:
                productwise = product_wise.product_id.id
                rate = product_wise.rate_percentage
                max_commission = product_wise.max_commission
                for sale_order in self.order_line:
                    prdt = sale_order.product_id
                    price = sale_order.price_subtotal
                    if prdt.id == productwise:
                        commission_product = price * (rate / 100)
                        self.commission_amount_team = self.team_id.commission_amount = self.team_id.commission_amount + commission_product
                        self.commission_amount_person = self.user_id.commission_amount = self.user_id.commission_amount + commission_product
                        if commission_product >= max_commission:
                            commission_product = max_commission
                            self.commission_amount_team = self.team_id.commission_amount = self.team_id.commission_amount + commission_product
                            self.commission_amount_person = self.user_id.commission_amount = self.user_id.commission_amount + commission_product
        return res
        # # today = fields.date.today()
        # today = datetime.now()
        # print(today.month)
        # print("hey")
        # print(self.date_order.month)
        # print(type(today))
        # print(date_utils.start_of(today, "month").day)
        # print(today.day)
        # print(date_utils.end_of(today, "month"))
        # print(type(date_utils.end_of(today, "month")))
        # print(date_utils.start_of(today, "month").day)
        # if today.month == self.date_order.month:
        #     print("success")

        # else:
        #     self.commission_amount_team = self.team_id.commission_amount = 0
        #     self.commission_amount_person = self.user_id.commission_amount = 0

# commission = self.amount_total * (graduated.commission_percentage / 100)
# print(commission)
# print(self.amount_total)
# if self.amount_total < graduated.to_amount:
#     print(self.amount_total)
#     graduated_commission = self.amount_total * (graduated.commission_percentage / 100)
#     self.commission_amount_team = self.team_id.commission_amount = self.team_id.commission_amount + graduated_commission
#     self.commission_amount_person = self.user_id.commission_amount = self.user_id.commission_amount + graduated_commission
#     break
# elif self.amount_total >= graduated.to_amount:
#

# @api.model
# def _snailmail_cron(self, autocommit=True):
#     letters_send = self.search([
#         '|',
#         ('state', '=', 'pending'),
#         '&',
#         ('state', '=', 'error'),
#         ('error_code', 'in', ['TRIAL_ERROR', 'CREDIT_ERROR', 'ATTACHMENT_ERROR', 'MISSING_REQUIRED_FIELDS'])
#     ])
#     for letter in letters_send:
#         letter._snailmail_print()
#         # Commit after every letter sent to avoid to send it again in case of a rollback
#         if autocommit:
#             self.env.cr.commit()

# @api.model
# def write(self, vals):
#     print(vals)

# @api.onchange('order_line')
# def get_value(self):
#     # fetched_data_revenue = self.env['crm.commission'].search(
#     #     [('commission_type', '=', 'revenue_wise')])
#     # print(fetched_data_revenue)
#     # print(self.team_id.commission_plan.straight)
#     # if self.team_id.commission_plan.straight:
#     #     print("do")
#     #     commission = self.amount_total * (self.team_id.commission_plan.straight_percentage / 100)
#     #     print(commission)
#     #     self.commission_amount_team = self.team_id.commission_amount = self.team_id.commission_amount + commission
#     # if not self.team_id.commission_plan.straight:
#     #     print("done")
#     fetched_data_productwise = self.env['crm.commission'].search(
#         [('commission_type', '=', 'product_wise')])
#     print("Hello")
#     print(fetched_data_productwise)
#     productwises = fetched_data_productwise.productwise_commission_ids
#     print(productwises)
#     print("productwise")
#     for product_wise in productwises:
#         productwise = product_wise.product_id.id
#         rate = product_wise.rate_percentage
#         max_commission = product_wise.max_commission
#         print(rate)
#         print(productwise)
#         print(max_commission)
#     # product = self.order_line.product_id
#         print("after")
#         print(self.order_line.product_id)
#     # print(product)
#         for sale_order in self.order_line:
#             print("hai odoo")
#             prdt = sale_order.product_id
#             price = sale_order.price_subtotal
#             print(price)
#             print(prdt)
#             if prdt.id == productwise:
#                 print(productwise)
#                 print("do it")
#                 print(rate)
#                 print(max_commission)
#             # print(self.order_line.price_subtotal)
#                 print(price)
#                 commission_product = price * (rate / 100)
#                 print(commission_product)
#                 self.commission_amount_team = self.team_id.commission_amount = self.team_id.commission_amount + commission_product
#                 if commission_product >= max_commission:
#                     commission_product = max_commission
#                     print(commission_product)
#                     self.commission_amount_team = self.team_id.commission_amount = self.team_id.commission_amount + commission_product

# return super(SaleorderInherit, self).create(vals)
# for products in product:
#     # if productwise == product:
#     print(products)
#     print("do it ")

# if self.order_line.product_id in fetched_data_productwise.productwise_commission_ids.product_id:

# if fetched_data_productwise.productwise_commission_ids.product_id.id == self.order_line.product_id.id:
# fetched_data_graduated = self.env['crm.commission'].search(
#     [('commission_type', '=', 'revenue_wise'), ('graduated', '=', 'True')])
# print("success")
# print(fetched_data_graduated)
# for graduated in fetched_data_graduated:
#     print(graduated.name)
#     print("oky")
#     if self.team_id.commission_plan.name == graduated.name:
#         print(graduated.name)
#         print("Done it")
#         print(self.team_id.commission_plan)
#         for graduated_commission in graduated.graduated_commission_ids:
#             print(graduated_commission.to_amount)
#         break

# print(values)
# print()
# print(fetched_data.team_id)
# print(fetched_data.tax_totals_json)

# override_create = super(SalesteamInherit, self).create(values)
# return override_create
# @api.depends('model')
#     def _compute_model_id(self):
#         for action in self:
#             action.model_id = self.env['ir.model']._get(action.model).id

# class SaleorderInherit(models.Model):
#     _inherit = 'sale.order'
#
#     @api.model
#     def commission_amount_calculation(self):
#         # print(self.commission_plan)
#         print(self.user_id)
#         print(self.user_id.commission_plan)

#     # , compute = 'commission_amount_calculation'
# @api.depends(tax_totals_)
# def commission_amount_calculation(self):
#     print(self.commission_plan)
#     print(self.commission_amount)
#     print(self.order_line.price_subtotal)
