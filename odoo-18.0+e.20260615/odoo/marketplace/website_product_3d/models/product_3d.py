from odoo import fields, models


class ProductP3dColor(models.Model):
    """Couleur de matiere disponible pour le produit 3D."""
    _name = 'product.p3d.color'
    _description = "Couleur (configurateur 3D)"
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    product_tmpl_id = fields.Many2one(
        'product.template', required=True, ondelete='cascade')
    name = fields.Char(string="Nom", required=True)
    html_color = fields.Char(string="Couleur", required=True, default='#cccccc')
    extra_price = fields.Float(string="Supplément", default=0.0)
