# -*- coding: utf-8 -*-
"""Connecteur La Redoute - plateforme Mirakl.

La place de marché La Redoute fonctionne sur Mirakl. L'authentification se
fait par une clé API passée dans l'en-tête `Authorization`.

Champs marketplace.account utilisés :
  * base_url -> URL de la plateforme Mirakl de La Redoute
                (ex: https://laredoute-prod.mirakl.net)
  * api_key  -> clé API du compte vendeur (front API key)

Sur Mirakl, stock et prix sont deux attributs d'une même "offer" : on les
met à jour via le même endpoint (OF21/OF24 selon version). Les commandes
sont récupérées via OR11 et acceptées via OR21.

Doc : https://help.mirakl.net/ (API operator/shop)
"""
from datetime import datetime, timedelta

from odoo import _
from odoo.exceptions import UserError

from .base import BaseConnector
from .registry import register


@register('laredoute')
class LaRedouteConnector(BaseConnector):

    def authenticate(self):
        # Mirakl utilise une clé statique, rien à rafraîchir.
        if not self.account.api_key or not self.account.base_url:
            raise UserError(_("La Redoute : base_url et api_key sont requis."))
        return self.account.api_key

    def _headers(self):
        return {
            'Authorization': self.authenticate(),
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    def _url(self, path):
        return self.account.base_url.rstrip('/') + path

    def test_connection(self):
        # P11 : informations du compte vendeur connecté.
        self._json('GET', self._url('/api/account'), headers=self._headers())
        self.account._log('test', 'success', _("La Redoute (Mirakl) connecté."))
        return True

    def _update_offers(self, listings, operation):
        """Mise à jour des offres (OF21). Met à jour stock ET/OU prix."""
        offers = []
        for listing in listings.filtered('sync_enabled'):
            if not listing.sku:
                continue
            offer = {
                'shop_sku': listing.sku,
                'update_delete': 'update',
            }
            if operation in ('stock', 'all'):
                offer['quantity'] = int(self._get_stock_qty(listing))
            if operation in ('price', 'all'):
                offer['price'] = round(self._get_price(listing), 2)
            offers.append((listing, offer))

        if not offers:
            return True
        body = {'offers': [o for _l, o in offers]}
        try:
            self._json('POST', self._url('/api/offers'),
                       headers=self._headers(), json=body)
            now = datetime.now()
            for listing, offer in offers:
                vals = {'last_sync': now, 'last_error': False}
                if 'quantity' in offer:
                    vals['qty_available'] = offer['quantity']
                if 'price' in offer:
                    vals['list_price'] = offer['price']
                listing.write(vals)
            op = 'export_stock' if operation == 'stock' else 'export_price'
            self.account._log(op, 'success',
                              _("%d offre(s) mise(s) à jour.") % len(offers))
        except Exception as exc:  # noqa: BLE001
            self.account._log('export_stock', 'error', str(exc))
            raise
        return True

    def export_stock(self, listings):
        return self._update_offers(listings, 'stock')

    def export_price(self, listings):
        return self._update_offers(listings, 'price')

    def export_listings(self, listings):
        return self._update_offers(listings, 'all')

    def import_orders(self):
        acc = self.account
        params = {'order_state_codes': 'WAITING_ACCEPTANCE,SHIPPING',
                  'max': 100}
        if acc.last_order_import:
            params['start_date'] = acc.last_order_import.strftime(
                '%Y-%m-%dT%H:%M:%SZ')
        res = self._json('GET', self._url('/api/orders'),
                         headers=self._headers(), params=params)
        for order in res.get('orders', []):
            self._import_single_order(order)
        acc.sudo().write({'last_order_import': datetime.now()})
        return True

    def _import_single_order(self, order):
        cust = order.get('customer', {})
        ship = cust.get('shipping_address', {})
        lines = []
        for line in order.get('order_lines', []):
            offer = line.get('offer', {})
            lines.append({
                'sku': offer.get('shop_sku') or line.get('offer_sku'),
                'qty': line.get('quantity', 1),
                'price_unit': line.get('price_unit', line.get('price', 0)),
                'name': line.get('product_title'),
                'line_ref': line.get('order_line_id'),
            })
        order_data = {
            'ref': order.get('order_id'),
            'status': order.get('order_state'),
            'date': order.get('created_date'),
            'partner': {
                'name': '%s %s' % (ship.get('firstname', ''),
                                   ship.get('lastname', '')),
                'street': ship.get('street_1'),
                'street2': ship.get('street_2'),
                'city': ship.get('city'),
                'zip': ship.get('zip_code'),
                'country_code': ship.get('country_iso_code'),
                'phone': ship.get('phone'),
                'email': cust.get('email'),
            },
            'lines': lines,
        }
        return self._create_sale_order(order_data)
