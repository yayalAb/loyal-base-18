from odoo import fields, models, api
from odoo.exceptions import ValidationError


class VisitCase(models.Model):

    _name = 'visit.case'
    _description = 'visit Case'
    _rec_name = 'name'

    name = fields.Char(
        string="Visit Case",
        required=True,
    )
    description = fields.Html(
        string="Description",
        sanitize=True,
        sanitize_tags=True,
        sanitize_attributes=True,
        sanitize_style=False,
        strip_style=False,
        strip_classes=False,
    )


class PriceListMaping(models.Model):

    _name = 'price.patient.mapping'
    _description = 'price.patient.mapping'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = 'apply_on'

    description = fields.Html(
        string="Description",
    )
    apply_on = fields.Selection(
        selection=[
            ("pharmacist", "Pharmacist "),
            ("opd", "Out Patient Dept"),
            ("ipd", "In Patient Dept"),
        ],
        string="Apply On",
        required=True,
    )

    price_list_id = fields.Many2one(
        string="Price List",
        comodel_name="product.pricelist",
        required=True,
    )

    @api.constrains("name", "description")
    def _check_apply_on_unique(self):
        for record in self:
            existing_records = self.env['price.patient.mapping'].search([
                ('apply_on', '=', record.apply_on),
                ('id', '!=', record.id)
            ])
            if existing_records:
                raise ValidationError(
                    f"The apply_on value '{record.apply_on}' must be unique.")


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
