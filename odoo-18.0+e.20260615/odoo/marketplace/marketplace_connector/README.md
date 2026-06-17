# Marketplace Connector — Odoo 18

Connecteur multi-marketplace pour Odoo 18 : **Amazon**, **Etsy**,
**La Redoute (Mirakl)** et **Cdiscount (Octopia)**.

## Ce que fait le module

- Une couche d'abstraction commune (`BaseConnector`) + un connecteur par marketplace.
- Comptes multiples par marketplace (multi-boutiques, multi-sociétés).
- Export / mise à jour des annonces (listings).
- Synchronisation **stock** et **prix** (manuelle ou par cron).
- Import des **commandes** vers `sale.order`.
- Journal de synchronisation et tâches planifiées désactivées par défaut.

## Architecture

```
marketplace_connector/
├── __manifest__.py
├── models/
│   ├── marketplace.py            # catalogue des marketplaces
│   ├── marketplace_account.py    # credentials + orchestration + crons
│   ├── marketplace_listing.py    # lien product.product <-> annonce
│   ├── marketplace_order.py      # mixin de suivi commande
│   ├── marketplace_sync_log.py   # journal
│   ├── product_template.py       # extension produit
│   ├── sale_order.py             # extension commande
│   └── connectors/
│       ├── registry.py           # registre code -> classe
│       ├── base.py               # logique commune (HTTP, commandes...)
│       ├── amazon.py             # SP-API + LWA
│       ├── etsy.py               # Open API v3 (OAuth2)
│       ├── laredoute.py          # Mirakl
│       └── cdiscount.py          # Octopia
├── views/  •  security/  •  data/
```

Pour ajouter une 5e marketplace : créer une classe qui hérite de
`BaseConnector`, la décorer avec `@register('mon_code')`, l'importer dans
`connectors/__init__.py` et ajouter l'option dans le `Selection` du modèle
`marketplace.marketplace`.

## Installation

1. Copier le dossier `marketplace_connector` dans votre répertoire d'addons.
2. `pip install requests` (dépendance Python).
3. Mettre à jour la liste des applications puis installer
   **Marketplace Connector**.

## Configuration

1. Menu **Marketplaces > Comptes > Créer**.
2. Choisir la marketplace, l'environnement (sandbox/production) et renseigner
   les identifiants API dans l'onglet *Identifiants API*.
3. Cliquer **Tester la connexion**.
4. Créer des annonces (onglet *Annonces*) en liant un produit Odoo et son SKU.
5. Activer les crons souhaités dans **Paramètres > Technique > Planificateurs**.

## ⚠️ Important — état de livraison

C'est une **base solide et structurée**, pas un produit certifié clé en main.
Avant la production, pour chaque marketplace il faut :

- Obtenir et tester les **credentials** (clés API, refresh tokens, etc.).
- **Vérifier/ajuster les chemins d'endpoints et les payloads** selon la version
  exacte de l'API et de votre contrat vendeur (surtout Octopia et Mirakl, dont
  les chemins varient). Les schémas de création d'annonce Amazon dépendent du
  `productType` et des attributs de catégorie.
- Tester en environnement **sandbox** avant la production.
- Gérer les spécificités : flux d'autorisation OAuth initial (Etsy/Amazon),
  pagination, limites de débit (rate limits), confirmation d'expédition.

Le code est volontairement commenté aux endroits à adapter.
