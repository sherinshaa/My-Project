from odoo import fields, models


class PropertyType(models.Model):
    _name = "property.type"
    _description = "property"

    property = fields.Char()
    _rec_name = "property"


class PropertyTag(models.Model):
    _name = "property.tag"
    _description = "property_tag"

    tags = fields.Char()
    _rec_name = "tags"


