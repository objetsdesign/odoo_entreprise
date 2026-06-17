from odoo import fields, models


class ProductVcColor(models.Model):
    """Couleur de produit disponible dans le customizer."""
    _name = 'product.vc.color'
    _description = "Couleur (visual customizer)"
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    product_tmpl_id = fields.Many2one(
        'product.template', required=True, ondelete='cascade')
    name = fields.Char(string="Nom", required=True)
    html_color = fields.Char(string="Couleur", required=True, default='#cccccc')
    extra_price = fields.Float(string="Supplément", default=0.0)


class ProductVcDimension(models.Model):
    """Dimension saisissable par le client (largeur, hauteur, diametre...)."""
    _name = 'product.vc.dimension'
    _description = "Dimension (visual customizer)"
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    product_tmpl_id = fields.Many2one(
        'product.template', required=True, ondelete='cascade')
    name = fields.Char(string="Nom", required=True, help="Ex : Largeur, Hauteur")
    unit = fields.Char(string="Unité", default='cm')
    min_value = fields.Float(string="Min")
    max_value = fields.Float(string="Max")
    default_value = fields.Float(string="Valeur par défaut")
    required = fields.Boolean(string="Obligatoire", default=True)
    price_per_unit = fields.Float(
        string="Prix / unité", default=0.0,
        help="Optionnel : montant ajouté au devis = valeur saisie x ce prix.")
