from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    vc_design = fields.Text(string="Composition (JSON)")
    vc_preview = fields.Binary(string="Aperçu personnalisé")
