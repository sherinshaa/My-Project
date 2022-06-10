from datetime import datetime, date

from odoo import models, fields, api


class HospitalOp(models.Model):
    _name = "hospital.op"
    _description = "Hospital Op"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "token_no"

    token_no = fields.Char(string="Token No", readonly=True, default=lambda self: 'New')
    patient_card_id = fields.Many2one("hospital.management", string="Patient Card", required=True)
    patients_id = fields.Many2one("res.partner", string="Patient Name",
                                  related='patient_card_id.patients_id')
    age = fields.Integer(related='patient_card_id.age', string="Age")
    gender = fields.Selection(related='patient_card_id.gender', string="Gender", store=True)
    blood_group = fields.Selection(related='patient_card_id.blood_group', string="Blood Group", store=True)
    doctor_id = fields.Many2one('hr.employee', string="Doctor", domain="[('job_title', 'ilike', 'doctor')]",
                                required=True)
    department_id = fields.Many2one(string='Department', related='doctor_id.department_id', store=True)

    date = fields.Datetime(string="Date", default=datetime.today())
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    fee = fields.Monetary(string="Fee", required=True, currency_field='currency_id', related='doctor_id.fee')
    state = fields.Selection(selection=[('draft', 'Draft'), ('op', 'OP')], string='State', copy=False,
                             default='draft', tracking=True)
    payment_count = fields.Integer(readonly=True)

    def button_op(self):
        self.write({
            'state': "op"
        })

    def button_payment(self):
        self.payment_count = self.payment_count + 1
        return {
            'type': 'ir.actions.act_window',
            'target': 'current',
            'name': 'Fee Payment',
            'view_mode': 'form',
            'res_model': 'fee.payment',
            'context': {'default_patient_card_id': self.patient_card_id.id, 'default_doctor_id': self.doctor_id.id,
                        'default_fee': self.fee, 'default_token_no': self.token_no},
        }

    @api.model
    def create(self, vals):
        vals['token_no'] = self.env['ir.sequence'].next_by_code(
            'hospital.op') or 'New'
        res = super(HospitalOp, self).create(vals)
        return res

    def action_done(self):
        sequence_id = self.env['ir.sequence'].search([('code', '=', 'hospital.op')])
        if sequence_id:
            if not sequence_id.use_date_range:
                sequence_id.use_date_range = True
            if sequence_id.date_range_ids:
                sequence_id.date_range_ids.date_from = sequence_id.date_range_ids.date_to = date.today()
                sequence_id.date_range_ids.number_next_actual = 1
            else:
                self.env['ir.sequence.date_range'].create(
                    {'sequence_id': sequence_id.id, 'date_from': date.today(),
                     'date_to': date.today(),
                     'number_next_actual': 1})
            # else:
            #     if sequence_id.date_range_ids:
            #         sequence_id.date_range_ids.date_from = sequence_id.date_range_ids.date_to = date.today()
            #         sequence_id.date_range_ids.number_next_actual = 1
            #     else:
            #         self.env['ir.sequence.date_range'].create(
            #             {'sequence_id': sequence_id.id, 'date_from': date.today(),
            #              'date_to': date.today(),
            #              'number_next_actual': 1})

    def payments(self):
        return {
            'type': 'ir.actions.act_window',
            'target': 'new',
            'name': 'Payment',
            'view_mode': 'tree',
            'res_model': 'fee.payment',
            'domain': [('patients_id', '=', self.patients_id.id),
                       ('fee', '=', self.fee),
                       ('doctor_id', '=', self.doctor_id.id),
                       ('token_no', '=', self.token_no)],
            'context': {'create': False},
        }
