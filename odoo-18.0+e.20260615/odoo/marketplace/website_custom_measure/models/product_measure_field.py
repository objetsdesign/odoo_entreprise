from odoo import fields, models


class ProductMeasureField(models.Model):
    """Définition d'un champ de mesure pour un produit sur mesure.

    Ex : "Largeur" (cm), "Hauteur" (cm), "Type de tissu" (liste de choix)...
    """
    _name = 'product.measure.field'
    _description = "Champ de mesure d'un produit sur mesure"
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    product_tmpl_id = fields.Many2one(
        'product.template', string="Produit",
        required=True, ondelete='cascade')
    name = fields.Char(string="Libellé", required=True)
    field_type = fields.Selection([
        ('float', "Nombre décimal"),
        ('integer', "Nombre entier"),
        ('char', "Texte"),
        ('selection', "Liste de choix"),
    ], string="Type", default='float', required=True)
    unit = fields.Char(string="Unité", help="ex : cm, mm, m")
    min_value = fields.Float(string="Valeur min.")
    max_value = fields.Float(string="Valeur max.")
    selection_options = fields.Char(
        string="Options",
        help="Pour une liste de choix : valeurs séparées par des virgules. "
             "Ex : Coton, Lin, Velours")
    required = fields.Boolean(string="Obligatoire", default=True)
    help_text = fields.Char(string="Texte d'aide")
