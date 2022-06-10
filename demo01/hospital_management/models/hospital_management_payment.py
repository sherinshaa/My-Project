from odoo import models, fields, api
from datetime import datetime


class FeePayment(models.Model):
    _name = 'fee.payment'
    _description = 'Fee Payment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'payment_ref'

    payment_ref = fields.Char(string="Payment RefNo", readonly=True, default=lambda self: 'Ref-no')
    token_no = fields.Char(string="Token No")
    patient_card_id = fields.Many2one("hospital.management", string="Patient Card", required=True)
    patients_id = fields.Many2one("res.partner", string="Patient Name",
                                  related='patient_card_id.patients_id')
    doctor_id = fields.Many2one('hr.employee', string="Doctor", domain="[('job_title', 'ilike', 'doctor')]",
                                required=True)
    department_id = fields.Many2one(string='Department', related='doctor_id.department_id', store=True)

    bill_date = fields.Datetime(string="Date", default=datetime.today())
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    fee = fields.Monetary(stringfrom="Fee", required=True, currency_field='currency_id', related='doctor_id.fee')
    payment_count = fields.Integer(readonly=True)
    state = fields.Selection(selection=[('draft', 'Draft'), ('posted', 'Posted')], string='State', copy=False,
                             default='draft')

    @api.model
    def create(self, vals):
        vals['payment_ref'] = self.env['ir.sequence'].next_by_code(
            'fee.payment') or 'Ref-no'
        ref = super(FeePayment, self).create(vals)
        return ref

    def button_payment_confirm(self):
        self.write({
            'state': "posted"
        })
        print(self.payment_ref)
        fee_payment = self.env['account.payment'].create(
            {
                'amount': self.fee,
                'partner_id': self.patients_id.id,
                'ref': self.payment_ref
            })

        fee_payment.action_post()
        self.payment_count = 1

    def payments(self):
        return {
            'type': 'ir.actions.act_window',
            'target': 'new',
            'name': 'Fee Payment',
            'view_mode': 'tree',
            'res_model': 'account.payment',
            'domain': [('partner_id', '=', self.patients_id.id),
                       ('amount', '=', self.fee),
                       ('ref', '=', self.payment_ref)],
            'context': {'create': False},
        }
