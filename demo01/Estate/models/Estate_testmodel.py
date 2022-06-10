from odoo import fields, models
from datetime import datetime
from dateutil.relativedelta import relativedelta

class TestModel(models.Model):
    _name = "test.model"
    _description = "Test Model"

    name = fields.Char()
    tags = fields.Many2many("property.tag", string="tags")
    description = fields.Text()
    postcode = fields.Char()
    expected_price = fields.Float()
    selling_price = fields.Float(readonly=True, default=400)
    date_availability = fields.Date(default=datetime.today() + relativedelta(months=3), copy=False)
    sales_person = fields.Many2one("res.users", string="Salesperson", index=True, tracking=True, default=lambda self: self.env.user)
    buyer = fields.Char(copy=False)
    bedroom = fields.Integer(default=2, copy=False)
    living_area = fields.Integer()
    facades = fields.Integer()
    property_type = fields.Many2one("property.type", string="property")
    garage = fields.Boolean('Garage')
    garden = fields.Boolean('Garden')
    garden_orientation = fields.Selection(
        string="Garden Orientation",
        selection=[('north', 'North'), ('east', 'East'), ('west', 'West'), ('south', 'South')],)
    garden_area = fields.Integer()
    active = fields.Boolean('Active', default=True)
    status = fields.Selection(
        string="Status",
        selection=[('new', 'New'), ('offer received', 'Offer Received',)], default='new', copy=False)
    # offer = fields.Char()
    partner_ids = fields.One2many('property.offers', 'property_id')
    # price = fields.Float('price')
    # status = fields.Selection(string="status", copy=False,
    #                          selection=[('accepted', 'Accepted'), ('rejected', 'Rejected')])



class PropertyOffers(models.Model):
    _name = "property.offers"
    _description = "Property Offers"
    _rec_name = 'property_id'

    price = fields.Float()
    partner_ids = fields.Many2one('res.partner', string='partner_id', required=True)
    property_id = fields.Many2one('test.model', 'Name')
    status = fields.Selection(
        string='status',
        selection=[('accepted', 'Accepted'), ('rejected', 'Rejected')])