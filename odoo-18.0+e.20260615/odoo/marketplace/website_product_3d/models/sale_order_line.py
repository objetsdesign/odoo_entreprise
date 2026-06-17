from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    p3d_preview = fields.Binary(string="Aperçu 3D")
