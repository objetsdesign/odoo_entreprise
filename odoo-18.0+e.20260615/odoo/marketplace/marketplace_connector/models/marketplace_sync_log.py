# -*- coding: utf-8 -*-
from odoo import fields, models


class MarketplaceSyncLog(models.Model):
    _name = 'marketplace.sync.log'
    _description = 'Journal de synchronisation marketplace'
    _order = 'create_date desc'
    _rec_name = 'operation'

    account_id = fields.Many2one(
        'marketplace.account', string='Compte', ondelete='cascade', index=True)
    listing_id = fields.Many2one('marketplace.listing', string='Annonce')
    order_ref = fields.Char(string='Réf. commande')
    operation = fields.Selection(
        selection=[
            ('test', 'Test connexion'),
            ('export_listing', 'Export annonce'),
            ('export_stock', 'Export stock'),
            ('export_price', 'Export prix'),
            ('import_order', 'Import commande'),
            ('update_order', 'MAJ commande'),
            ('auth', 'Authentification'),
        ], string='Opération', required=True)
    status = fields.Selection(
        selection=[('success', 'Succès'), ('warning', 'Avertissement'),
                   ('error', 'Erreur')],
        string='Statut', required=True)
    message = fields.Text(string='Message')
