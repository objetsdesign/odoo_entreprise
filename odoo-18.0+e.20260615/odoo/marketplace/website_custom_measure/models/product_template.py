from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_custom_measure = fields.Boolean(
        string="Produit sur mesure",
        help="Si coché, le client pourra saisir des mesures sur la fiche "
             "produit du site web et envoyer une demande de devis.")
    measure_field_ids = fields.One2many(
        'product.measure.field', 'product_tmpl_id',
        string="Champs de mesure")
