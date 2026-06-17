# -*- coding: utf-8 -*-
from odoo import fields, models


class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = ['sale.order', 'marketplace.order.mixin']

    _sql_constraints = [
        ('marketplace_order_ref_uniq',
         'unique(marketplace_account_id, marketplace_order_ref)',
         "Cette commande marketplace a déjà été importée."),
    ]


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    marketplace_line_ref = fields.Char(
        string='Réf. ligne marketplace', copy=False)
