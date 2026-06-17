# -*- coding: utf-8 -*-
"""Classe de base commune à tous les connecteurs marketplace.

Toute la logique partagée (appels HTTP, gestion des erreurs, helpers
produit/stock/prix, création de commandes Odoo) est ici. Chaque connecteur
concret redéfinit les méthodes spécifiques à son API.
"""
import logging

from odoo import _
from odoo.exceptions import UserError

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

_logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30


class BaseConnector:
    """Interface commune. `account` est un recordset marketplace.account."""

    _code = None

    def __init__(self, account):
        if requests is None:
            raise UserError(_("La librairie Python « requests » est requise."))
        self.account = account
        self.env = account.env

    # ------------------------------------------------------------------ #
    #  HTTP helpers                                                       #
    # ------------------------------------------------------------------ #
    def _request(self, method, url, **kwargs):
        kwargs.setdefault('timeout', DEFAULT_TIMEOUT)
        _logger.debug("[%s] %s %s", self._code, method, url)
        try:
            resp = requests.request(method, url, **kwargs)
        except requests.RequestException as exc:
            raise UserError(_("Erreur réseau (%s) : %s") % (self._code, exc))
        if resp.status_code >= 400:
            raise UserError(_("Erreur API %s [%s] : %s") % (
                self._code, resp.status_code, resp.text[:500]))
        return resp

    def _json(self, method, url, **kwargs):
        resp = self._request(method, url, **kwargs)
        if not resp.content:
            return {}
        try:
            return resp.json()
        except ValueError:
            return {'_raw': resp.text}

    # ------------------------------------------------------------------ #
    #  Helpers métier partagés                                            #
    # ------------------------------------------------------------------ #
    def _get_stock_qty(self, listing):
        """Stock disponible (forecast) pour une annonce."""
        product = listing.product_id
        if self.account.warehouse_id:
            product = product.with_context(
                warehouse=self.account.warehouse_id.id)
        qty = product.free_qty if hasattr(product, 'free_qty') \
            else product.qty_available
        return max(0.0, qty)

    def _get_price(self, listing):
        """Prix à publier pour une annonce."""
        product = listing.product_id
        pricelist = self.account.pricelist_id
        if pricelist:
            return pricelist._get_product_price(product, 1.0)
        return product.list_price

    def _find_product_by_sku(self, sku):
        if not sku:
            return self.env['product.product']
        return self.env['product.product'].search(
            ['|', ('default_code', '=', sku), ('barcode', '=', sku)], limit=1)

    def _find_or_create_partner(self, vals):
        """Trouve/crée un client à partir d'un dict normalisé.

        vals attend au minimum: name, email; éventuellement street, city,
        zip, country_code, phone.
        """
        Partner = self.env['res.partner']
        domain = []
        if vals.get('email'):
            domain = [('email', '=ilike', vals['email'])]
        partner = Partner.search(domain, limit=1) if domain else Partner
        country = self.env['res.country'].search(
            [('code', '=', (vals.get('country_code') or '').upper())], limit=1)
        partner_vals = {
            'name': vals.get('name') or _('Client marketplace'),
            'email': vals.get('email'),
            'street': vals.get('street'),
            'street2': vals.get('street2'),
            'city': vals.get('city'),
            'zip': vals.get('zip'),
            'phone': vals.get('phone'),
            'country_id': country.id if country else False,
            'company_id': self.account.company_id.id,
        }
        if partner:
            partner.write({k: v for k, v in partner_vals.items() if v})
            return partner
        return Partner.create(partner_vals)

    def _create_sale_order(self, order_data):
        """Crée une sale.order Odoo à partir d'un dict normalisé.

        order_data = {
            'ref': '...', 'status': '...', 'date': datetime|None,
            'partner': {...},
            'lines': [{'sku', 'qty', 'price_unit', 'name', 'line_ref'}, ...],
        }
        Retourne le recordset créé (ou existant si déjà importé).
        """
        SaleOrder = self.env['sale.order']
        existing = SaleOrder.search([
            ('marketplace_account_id', '=', self.account.id),
            ('marketplace_order_ref', '=', order_data['ref']),
        ], limit=1)
        if existing:
            return existing

        partner = self._find_or_create_partner(order_data.get('partner', {}))
        order_vals = {
            'partner_id': partner.id,
            'company_id': self.account.company_id.id,
            'marketplace_account_id': self.account.id,
            'marketplace_order_ref': order_data['ref'],
            'marketplace_status': order_data.get('status'),
            'origin': '%s/%s' % (self.account.name, order_data['ref']),
            'order_line': [],
        }
        if self.account.team_id:
            order_vals['team_id'] = self.account.team_id.id
        if self.account.fiscal_position_id:
            order_vals['fiscal_position_id'] = self.account.fiscal_position_id.id
        if order_data.get('date'):
            order_vals['date_order'] = order_data['date']

        for line in order_data.get('lines', []):
            product = self._find_product_by_sku(line.get('sku'))
            if not product:
                # Produit inconnu : on journalise mais on continue
                self.account._log(
                    'import_order', 'warning',
                    _("SKU introuvable: %s (commande %s)") % (
                        line.get('sku'), order_data['ref']),
                    order_ref=order_data['ref'])
                continue
            order_vals['order_line'].append((0, 0, {
                'product_id': product.id,
                'name': line.get('name') or product.display_name,
                'product_uom_qty': line.get('qty', 1.0),
                'price_unit': line.get('price_unit', product.list_price),
                'marketplace_line_ref': line.get('line_ref'),
            }))

        order = SaleOrder.create(order_vals)
        self.account._log('import_order', 'success',
                          _("Commande %s importée.") % order_data['ref'],
                          order_ref=order_data['ref'])
        return order

    # ------------------------------------------------------------------ #
    #  Interface à implémenter par chaque connecteur                      #
    # ------------------------------------------------------------------ #
    def authenticate(self):
        """Rafraîchit/obtient un token d'accès si nécessaire."""
        raise NotImplementedError

    def test_connection(self):
        raise NotImplementedError

    def export_listings(self, listings):
        raise NotImplementedError

    def export_stock(self, listings):
        raise NotImplementedError

    def export_price(self, listings):
        raise NotImplementedError

    def import_orders(self):
        raise NotImplementedError
