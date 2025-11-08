from odoo import fields, models


class AddressCountry(models.Model):

    _name = 'address.country'
    _description = 'country'
    _rec_name = 'name'

    name = fields.Char(
        string="Country",
        required=True,
    )
    code = fields.Char(
        string="Code",
    )


class AddressRegion(models.Model):

    _name = 'address.region'
    _description = 'Region'
    _rec_name = 'name'
    country_id = fields.Many2one(
        string="country",
        comodel_name="address.country",
    )
    name = fields.Char(
        string="Region",
        required=True,
    )


class AddressCity(models.Model):

    _name = 'address.city'
    _description = 'Region'
    _rec_name = 'name'
    region_id = fields.Many2one(
        string="Region",
        comodel_name="address.region",
    )
    name = fields.Char(
        string="City",
        required=True,
    )


class AddressWoreda(models.Model):

    _name = 'address.woreda'
    _description = 'woreda'
    _rec_name = 'name'
    city_id = fields.Many2one(
        string="City/Zone",
        comodel_name="address.city",
    )
    name = fields.Char(
        string="Woreda",
        required=True,
    )


class AddressKebele(models.Model):

    _name = 'address.kebele'
    _description = 'Kebele'
    _rec_name = 'name'
    woreda_id = fields.Many2one(
        string="Woreda",
        comodel_name="address.woreda",
    )
    name = fields.Char(
        string="Kebele",
        required=True,
    )
