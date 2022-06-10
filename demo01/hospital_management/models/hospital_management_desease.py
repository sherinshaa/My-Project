from odoo import models, fields


class Desease(models.Model):
    _name = 'hospital.disease'
    _description = 'Disease'
    _rec_name = 'disease'

    disease = fields.Char(string='Diseases', required=True)
