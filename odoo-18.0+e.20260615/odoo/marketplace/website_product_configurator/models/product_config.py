from odoo import fields, models


class ProductConfigColor(models.Model):
    """Couleur disponible pour un produit configurable."""
    _name = 'product.config.color'
    _description = "Couleur du configurateur"
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    product_tmpl_id = fields.Many2one(
        'product.template', required=True, ondelete='cascade')
    name = fields.Char(string="Nom", required=True)
    html_color = fields.Char(
        string="Couleur", required=True, default='#cccccc',
        help="Code hexadécimal, ex : #e74c3c")
    extra_price = fields.Float(string="Supplément", default=0.0)


class ProductConfigPart(models.Model):
    """Partie recolorable du produit (zone de l'image SVG)."""
    _name = 'product.config.part'
    _description = "Partie configurable du produit"
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    product_tmpl_id = fields.Many2one(
        'product.template', required=True, ondelete='cascade')
    name = fields.Char(string="Nom", required=True,
                       help="Ex : Corps, Manches, Col")
    svg_target = fields.Char(
        string="Cible SVG", required=True,
        help="Sélecteur CSS de l'élément à recolorer dans le SVG, "
             "ex : #part_body ou .corps")
    default_color = fields.Char(string="Couleur par défaut", default='#cccccc')


class ProductConfigSize(models.Model):
    """Taille / dimension disponible."""
    _name = 'product.config.size'
    _description = "Taille du configurateur"
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    product_tmpl_id = fields.Many2one(
        'product.template', required=True, ondelete='cascade')
    name = fields.Char(string="Taille", required=True,
                       help="Ex : S, M, L ou 120x80 cm")
    extra_price = fields.Float(string="Supplément", default=0.0)


class ProductConfigOption(models.Model):
    """Option / proposition supplementaire (texte, choix, case a cocher)."""
    _name = 'product.config.option'
    _description = "Option du configurateur"
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    product_tmpl_id = fields.Many2one(
        'product.template', required=True, ondelete='cascade')
    name = fields.Char(string="Nom", required=True,
                       help="Ex : Texte a imprimer, Finition, Emballage cadeau")
    option_type = fields.Selection([
        ('text', "Texte libre"),
        ('select', "Liste de choix"),
        ('boolean', "Oui / Non"),
    ], string="Type", default='text', required=True)
    selection_options = fields.Char(
        string="Choix",
        help="Pour une liste de choix : valeurs separees par des virgules.")
    extra_price = fields.Float(
        string="Supplement", default=0.0,
        help="Ajoute au devis si l'option est remplie / cochee / choisie.")
    required = fields.Boolean(string="Obligatoire")
    help_text = fields.Char(string="Aide")
