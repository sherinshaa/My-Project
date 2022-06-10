from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    milestone = fields.Integer(string='Milestone')


class ProjectInherit(models.Model):
    _inherit = 'project.project'

    ref_id = fields.Many2one('sale.order', string='Reference')


class TaskInherit(models.Model):
    _inherit = 'project.task'

    milestone = fields.Integer(string='Milestone')


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    project = fields.Integer(string='Project', default=0)

    def project_smart(self):
        return {
            'type': 'ir.actions.act_window',
            'target': 'current',
            'name': 'Project smart',
            'view_mode': 'tree',
            'res_model': 'project.project',
            'domain': [('name', '=', self.name),
                       ('partner_id', '=', self.partner_id.id),
                       ],
            'context': {'create': False}
        }

    def action_project(self):
        project = self.env['project.project'].create(
            {
                'name': self.name,
                'partner_id': self.partner_id.id,
                'ref_id': self.id,
            }
        )
        project_id = project.id
        self.project = 1
        mapped = self.order_line.mapped('milestone')
        mapped = set(mapped)
        for milestone in mapped:
            print(type(milestone))
            milestones = str(milestone)
            task = self.env['project.task'].create(
                {
                    'name': "Milestone" + milestones,
                    'project_id': project.id,
                    'milestone': milestone,
                    'child_ids': [(0, 0, {'name': line.product_id.name}) for line in self.order_line if
                                  milestone == line.milestone]
                }
            )

    def action_update_project(self):
        update = self.env['project.task'].search([('project_id', '=', self.name)]).filtered('child_ids')
        # print(update)
        # start = self.order_line.product_id.name
        # for started in start:
        #     print(started)
        print(self.order_line.filtered(lambda x: x.product_id.name not in update.mapped('child_ids').mapped('name')),
              "xfhhhhhhhhh")
        sale_order = self.order_line.filtered(
            lambda x: x.product_id.name not in update.mapped('child_ids').mapped('name'))
        print(sale_order)
        for order_line in sale_order:
            for val in update:
                if order_line.milestone == val.milestone:
                    print(val.milestone)
                    # for lines in self.order_line:
                    #     if val.child_ids.milestone == lines.milestone:
                    #         print()
                    val.write(
                        {
                            'child_ids': [(0, 0, {'name': sale_orders.product_id.name})for sale_orders in order_line]
                        }
                    )
                # for val in update:
                #     print(val)
                #     print(val.id)
                #     print(val.name)
                #     print(val.child_ids)
                #     # for child in val.child_ids.filtered():
                #     #     print(child.name)
                #     for child in val.child_ids:
                #         print(child)
                #         print(child.name)
                #         check = child.name in new
                #         print(check)
                #         if check:
                #             new.remove(child.name)
                #             print(new)
                # for prdt in new:
                #     print(prdt)
                #     for lines in self.order_line:
                #         if lines.product_id.name == prdt:
                #             print(lines.product_id.name)
                #
                #             val.create(
                #                 {
                #                     'child_ids': [(0, 0, {'name': lines.product_id.name}) for lines in self.order_line
                #                                   if val.child_ids.milestone == lines.milestone]
                #                 }
                #             )

                # and prdt == lines.product_id.name
                # .filtered(
                #     lambda x: x.name in self.order_line.mapped('product_id').mapped('name')):
                # print("hey")
                # print(new)
                # old = child.name not in new
                # print(type(old))
                # print(old, "SGGGGGGGGGGGGGG")
                # print(child.name)
                # print(child.name, "ghgh")
                # for lines in self.order_line:
                #     if lines.milestone == val.milestone:
                #         print(lines.product_id.name)
                # print(child.name)

                # for milestone in mapped:
                #     val.write(
                #         {
                #             'child_ids': [(0, 0, {'name': lines.product_id.name}) for lines in self.order_line if
                #                           milestone == lines.milestone]
                #         }
                #     )
                # for lines in self.order_line:
                #     if milestone == lines.milestone:
                #         print(milestone)
                #         for child in line.child_ids:
                #             print(child.name)
                #             if lines.product_id.name != child.name:
                #                 print(lines.product_id.name)
                #
                #         # if lines.product_id.name != child.name:
                #                 print("hello")

                # mapped = self.order_line.mapped('milestone')
                # print(mapped)
                # mapped = set(mapped)
                # print(mapped)
                # for milestone in mapped:
                #     print(milestone)
                #     for line in update:
                #         print(line)
                #         print(line.name)
                #         for lines in self.order_line:
                #             print(lines.milestone)
                #             if milestone == lines.milestone:
                #                 print("hey")
                # print(child.name)
                # print("done")

                # mapped = self.order_line.mapped('milestone')
                # mapped = set(mapped)
                # for milestone in mapped:
                #     milestones = str(milestone)
                #     task = self.env['project.task'].create(
                #         {
                #             'name': "Milestone" + milestones,
                #             'project_id': project_id,
                #             'child_ids': [(0, 0, {'name': line.product_id.name}) for line in self.order_line if
                #                           milestone == line.milestone]
                #         }
                #     )
                # sub_task = self.env['project.task'].create(
                #     {
                #         'name': "Milestone" + milestones,
                #
                #     }
                # )
                #     for product in self.order_line:
                #         print(product.milestone)
                #         print(product.product_id.name)
                #         if product.milestone == milestone:
                #             print(product.product_id)
                #             sub_task = self.env['project.task'].create(
                #                 {
                #                     'name': "task" + milestones,
                #                     'project_id': project.id,
                #                     # 'parent_id': [(4, milestone)],
                #                     'child_ids': [(4, product.product_id.id)],
                #                 }
                #             )
                #             print("done")
                #             print(sub_task.id)
