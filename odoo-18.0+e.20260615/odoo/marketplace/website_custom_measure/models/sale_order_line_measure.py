from odoo import fields, models


class SaleOrderLineMeasure(models.Model):
    """Valeur d'une mesure saisie par le client, rattachée à une ligne de devis."""
    _name = 'sale.order.line.measure'
    _description = "Mesure d'une ligne de devis"
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    order_line_id = fields.Many2one(
        'sale.order.line', string="Ligne de commande",
        required=True, ondelete='cascade')
    measure_field_id = fields.Many2one(
        'product.measure.field', string="Champ de mesure")
    name = fields.Char(string="Libellé", required=True)
    unit = fields.Char(string="Unité")
    value_display = fields.Char(string="Valeur")
