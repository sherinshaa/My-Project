from odoo import models, fields
from datetime import datetime


class HospitalAppointment(models.Model):
    _name = 'hospital.appointment'
    _description = 'Hospital Appointment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'patient_card_id'

    patient_card_id = fields.Many2one('hospital.management', string='Patient Card', required=True)
    patient_name = fields.Char(string='Patient Name', related='patient_card_id.patients_id.name')
    doctor_id = fields.Many2one('hr.employee', string='Doctor', domain=[('job_title', 'ilike', 'Doctor')],
                                required=True)
    department_id = fields.Many2one(string='Department', related='doctor_id.department_id', store=True)
    date = fields.Datetime(string='Date', default=datetime.today())
    state = fields.Selection(selection=[('draft', 'Draft'), ('appointment', 'Appointment'), ('op', 'OP')],
                             default='draft', string='state', copy=False, tracking=True)
    appointment_count = fields.Integer(compute='appointment_counts')

    def button_appointment(self):
        self.state = "appointment"

    def button_confirm(self):
        self.state = "op"
        return {
            'type': 'ir.actions.act_window',
            'target': 'new',
            'name': 'Op Creation',
            'view_mode': 'form',
            'res_model': 'hospital.op',
            'context': {'default_patient_card_id': self.patient_card_id.id, 'default_doctor_id': self.doctor_id.id,
                        'default_state': "op"}
        }

    def button_op(self):
        self.write({
            'state': "op"
        })
        return {
            'type': 'ir.actions.act_window',
            'target': 'new',
            'name': 'Op Creation',
            'view_mode': 'form',
            'res_model': 'hospital.op',
            'context': {'default_patient_card_id': self.patient_card_id.id, 'default_doctor_id': self.doctor_id.id,
                        'default_state': "op"},
        }

    def smart_button(self):
        return {
            'type': 'ir.actions.act_window',
            'target': 'new',
            'name': 'Op Creation',
            'view_mode': 'tree',
            'res_model': 'hospital.op',
            'domain': [('patient_card_id', '=', self.patient_card_id.id), ('state', '=', 'op'),
                       ('doctor_id', '=', self.doctor_id.id), ('date', '=', self.date)],
            'context': {'create': False}
        }

    def appointment_counts(self):
        self.appointment_count = 0
        if self.state == 'op':
            self.appointment_count = self.appointment_count + 1
