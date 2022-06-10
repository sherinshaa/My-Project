from odoo import fields, models


class HospitalMedicine(models.Model):

    _name = 'hospital.medicine'
    _rec_name = 'medicine'

    medicine = fields.Char(string='Medicine')