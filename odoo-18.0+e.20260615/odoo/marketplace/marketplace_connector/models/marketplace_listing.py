# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MarketplaceListing(models.Model):
    _name = 'marketplace.listing'
    _description = 'Annonce Marketplace'
    _rec_name = 'display_name'

    account_id = fields.Many2one(
        'marketplace.account', string='Compte', required=True,
        ondelete='cascade', index=True)
    code = fields.Selection(related='account_id.code', store=True)
    product_id = fields.Many2one(
        'product.product', string='Variante produit',
        required=True, ondelete='cascade')
    product_tmpl_id = fields.Many2one(
        'product.template', related='product_id.product_tmpl_id', store=True)

    # Identifiants côté marketplace
    external_id = fields.Char(
        string='ID externe',
        help="Identifiant de l'annonce sur la marketplace (listing_id, offer_id...).")
    sku = fields.Char(string='SKU', help="Code vendeur côté marketplace.")
    ean = fields.Char(string='EAN/GTIN', related='product_id.barcode', store=True)

    # Données d'annonce
    title = fields.Char(string='Titre annonce')
    list_price = fields.Float(string='Prix publié')
    qty_available = fields.Float(string='Stock publié')

    state = fields.Selection(
        selection=[
            ('draft', 'À publier'),
            ('published', 'Publié'),
            ('error', 'Erreur'),
            ('inactive', 'Inactif'),
        ], default='draft', string='Statut')
    sync_enabled = fields.Boolean(string='Synchroniser', default=True)
    last_sync = fields.Datetime(string='Dernière synchro', copy=False)
    last_error = fields.Text(string='Dernière erreur', copy=False)

    _sql_constraints = [
        ('account_product_uniq',
         'unique(account_id, product_id)',
         "Ce produit possède déjà une annonce sur ce compte."),
    ]

    @api.depends('product_id', 'account_id')
    def _compute_display_name(self):
        for rec in self:
            mp = rec.account_id.marketplace_id.name or ''
            prod = rec.product_id.display_name or ''
            rec.display_name = ('[%s] %s' % (mp, prod)).strip()

    def action_export(self):
        for listing in self:
            listing.account_id._get_connector().export_listings(listing)
        return True
