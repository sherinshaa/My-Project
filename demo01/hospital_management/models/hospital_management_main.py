from odoo import models, fields, api
from datetime import date


class HospitalManagement(models.Model):
    _name = 'hospital.management'
    _description = 'Hospital Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'patient_id'

    patient_id = fields.Char(string='Patient ID', readonly=True, default='New')
    patients_id = fields.Many2one("res.partner", string="Patient Name", required=True)
    mobile = fields.Char(related='patients_id.mobile', string='Mobile')
    dob = fields.Date(related='patients_id.dob', string='DOB')
    age = fields.Integer(string='Age', readonly=True)
    gender = fields.Selection(related='patients_id.gender', string='Gender', store=True)
    telephone = fields.Char(related='patients_id.phone', string='Telephone')
    blood_group = fields.Selection(string='Blood Group', required=True,
                                   selection=[('O+ve', 'O+ve'), ('O-ve', 'O-ve'), ('A+ve', 'A+ve'), ('A-ve', 'A-ve'),
                                              ('B+ve', 'B+ve'), ('B-ve', 'B-ve'), ('AB+ve', 'AB+ve'),
                                              ('AB-ve', 'AB-ve')], tracking=True, store=True)
    history_ids = fields.One2many('hospital.op', 'patient_card_id', string='History')

    @api.model
    def create(self, vals):
        vals['patient_id'] = self.env['ir.sequence'].next_by_code(
            'hospital.management') or 'New'
        res = super(HospitalManagement, self).create(vals)
        return res

    @api.onchange('dob')
    def set_age(self):
        if self.dob:
            self.age = date.today().year - self.dob.year
