from odoo import models, fields
from datetime import datetime


class HospitalConsultation(models.Model):
    _name = "hospital.consultation"
    _description = "Hospital Consultation"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "consultation"

    patient_card_id = fields.Many2one('hospital.management', string='Patient Card', required=True)
    consultation = fields.Selection(string='Consultation Type', selection=[('op', 'OP'), ('ip', 'IP')])
    doctor_id = fields.Many2one('hr.employee', string="Doctor", domain=[('job_title', 'ilike', 'doctor')],
                                required=True)
    department_id = fields.Many2one(string='Department', related='doctor_id.department_id', store=True)
    disease_id = fields.Many2one('hospital.disease', string="Disease", required=True)
    date = fields.Datetime(string='Date', default=datetime.today())
    diagnose = fields.Text(string='Diagnose')
    treatment_ids = fields.One2many('hospital.treatment', 'consultation_id', string='Treatment')
