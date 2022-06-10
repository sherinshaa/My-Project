from odoo import fields, models


class HospitalTreatment(models.Model):
    _name = 'hospital.treatment'
    _description = 'Hospital Treatment'
    _rec_name = 'medicine_id'

    consultation_id = fields.Many2one('hospital.consultation', string='consultation')
    medicine_id = fields.Many2one('hospital.medicine', string='Medicine')
    dose = fields.Char(string='Dose')
    day = fields.Integer(string='Days')
    description = fields.Text(string='Description')

