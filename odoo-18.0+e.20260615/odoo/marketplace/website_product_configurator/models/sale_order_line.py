from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    config_summary = fields.Text(string="Configuration choisie")
    config_preview = fields.Binary(string="Aperçu personnalisé")
