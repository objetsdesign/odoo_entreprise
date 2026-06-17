# -*- coding: utf-8 -*-
{
    'name': 'Marketplace Connector',
    'version': '18.0.1.0.0',
    'category': 'Sales/Sales',
    'summary': 'Connecteur multi-marketplace : Amazon, Etsy, La Redoute (Mirakl), Cdiscount (Octopia)',
    'description': """
Marketplace Connector
======================
Module de connexion d'Odoo 18 vers plusieurs marketplaces.

Fonctionnalités :
  * Architecture commune (couche d'abstraction) + un connecteur par marketplace
  * Comptes / instances multiples par marketplace (multi-boutiques)
  * Export et mise à jour des annonces (listings) produits
  * Synchronisation du stock et des prix
  * Import des commandes vers sale.order
  * Mise à jour du statut d'expédition / numéro de suivi
  * Journal de synchronisation et tâches planifiées (cron)

Marketplaces fournis :
  * Amazon (Selling Partner API / SP-API + LWA)
  * Etsy (Open API v3, OAuth2)
  * La Redoute (plateforme Mirakl)
  * Cdiscount (Octopia Marketplace API)
""",
    'author': 'Custom',
    'website': 'https://www.example.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'sale_management',
        'stock',
        'product',
    ],
    'external_dependencies': {
        'python': ['requests'],
    },
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/marketplace_data.xml',
        'data/cron.xml',
        'views/marketplace_views.xml',
        'views/marketplace_account_views.xml',
        'views/marketplace_listing_views.xml',
        'views/marketplace_order_views.xml',
        'views/sync_log_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
