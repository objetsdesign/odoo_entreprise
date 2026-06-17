# -*- coding: utf-8 -*-
from odoo import fields, models


class MarketplaceOrderMixin(models.AbstractModel):
    """Champs partagés pour le suivi des commandes marketplace."""
    _name = 'marketplace.order.mixin'
    _description = 'Mixin commande marketplace'

    marketplace_account_id = fields.Many2one(
        'marketplace.account', string='Compte marketplace', index=True)
    marketplace_code = fields.Selection(
        related='marketplace_account_id.code', store=True, string='Marketplace')
    marketplace_order_ref = fields.Char(
        string='Référence commande marketplace', index=True, copy=False)
    marketplace_status = fields.Char(string='Statut marketplace', copy=False)
