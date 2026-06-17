# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MarketplaceMarketplace(models.Model):
    _name = 'marketplace.marketplace'
    _description = 'Marketplace'
    _order = 'sequence, name'

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    code = fields.Selection(
        selection=[
            ('amazon', 'Amazon'),
            ('etsy', 'Etsy'),
            ('laredoute', 'La Redoute (Mirakl)'),
            ('cdiscount', 'Cdiscount (Octopia)'),
        ],
        string='Type de connecteur',
        required=True,
        help="Détermine la classe technique de connecteur utilisée.",
    )
    active = fields.Boolean(default=True)
    account_ids = fields.One2many(
        'marketplace.account', 'marketplace_id', string='Comptes')
    account_count = fields.Integer(
        compute='_compute_account_count', string='Nb comptes')

    _sql_constraints = [
        ('code_uniq', 'unique(code)',
         "Un seul enregistrement par type de marketplace est autorisé."),
    ]

    @api.depends('account_ids')
    def _compute_account_count(self):
        for rec in self:
            rec.account_count = len(rec.account_ids)
