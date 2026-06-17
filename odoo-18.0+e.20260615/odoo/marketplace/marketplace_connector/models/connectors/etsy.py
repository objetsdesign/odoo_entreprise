# -*- coding: utf-8 -*-
"""Connecteur Etsy - Open API v3.

Authentification OAuth 2.0 (Authorization Code + PKCE). On suppose qu'un
refresh_token a déjà été obtenu (flux d'autorisation initial à faire une
fois, hors module ou via un wizard dédié). Le client_id est aussi la clé
'x-api-key' exigée par Etsy.

Champs marketplace.account utilisés :
  * client_id     -> keystring (= x-api-key)
  * client_secret -> shared secret
  * refresh_token -> OAuth2 refresh token
  * shop_id       -> identifiant de la boutique Etsy

Doc : https://developers.etsy.com/documentation/
"""
from datetime import datetime, timedelta

from odoo import _
from odoo.exceptions import UserError

from .base import BaseConnector
from .registry import register

BASE_URL = 'https://openapi.etsy.com/v3/application'
TOKEN_URL = 'https://api.etsy.com/v3/public/oauth/token'


@register('etsy')
class EtsyConnector(BaseConnector):

    def authenticate(self):
        acc = self.account
        if acc.access_token and acc.token_expiry and \
                acc.token_expiry > datetime.now() + timedelta(minutes=2):
            return acc.access_token
        data = {
            'grant_type': 'refresh_token',
            'client_id': acc.client_id,
            'refresh_token': acc.refresh_token,
        }
        res = self._json('POST', TOKEN_URL, data=data)
        token = res.get('access_token')
        if not token:
            raise UserError(_("Etsy : échec d'obtention du token."))
        vals = {
            'access_token': token,
            'token_expiry': datetime.now() + timedelta(
                seconds=res.get('expires_in', 3600)),
        }
        if res.get('refresh_token'):
            vals['refresh_token'] = res['refresh_token']
        acc.sudo().write(vals)
        return token

    def _headers(self):
        return {
            'x-api-key': self.account.client_id,
            'Authorization': 'Bearer %s' % self.authenticate(),
            'Content-Type': 'application/json',
        }

    def test_connection(self):
        url = '%s/shops/%s' % (BASE_URL, self.account.shop_id)
        self._json('GET', url, headers=self._headers())
        self.account._log('test', 'success', _("Etsy connecté."))
        return True

    def export_stock(self, listings):
        for listing in listings.filtered('sync_enabled'):
            if not listing.external_id:
                continue
            qty = int(self._get_stock_qty(listing))
            # Etsy gère le stock au niveau des "inventory" du listing.
            url = '%s/listings/%s/inventory' % (BASE_URL, listing.external_id)
            inv = self._json('GET', url, headers=self._headers())
            products = inv.get('products', [])
            for prod in products:
                for offering in prod.get('offerings', []):
                    offering['quantity'] = qty
            body = {'products': products}
            try:
                self._json('PUT', url, headers=self._headers(), json=body)
                listing.write({'qty_available': qty, 'last_sync': datetime.now(),
                               'last_error': False})
                self.account._log('export_stock', 'success',
                                  _("Stock Etsy %s -> %s") % (listing.external_id, qty),
                                  listing=listing)
            except Exception as exc:  # noqa: BLE001
                listing.write({'last_error': str(exc)})
                self.account._log('export_stock', 'error', str(exc), listing=listing)
        return True

    def export_price(self, listings):
        for listing in listings.filtered('sync_enabled'):
            if not listing.external_id:
                continue
            price = round(self._get_price(listing), 2)
            url = '%s/listings/%s/inventory' % (BASE_URL, listing.external_id)
            inv = self._json('GET', url, headers=self._headers())
            products = inv.get('products', [])
            for prod in products:
                for offering in prod.get('offerings', []):
                    offering['price'] = price
            try:
                self._json('PUT', url, headers=self._headers(),
                           json={'products': products})
                listing.write({'list_price': price, 'last_sync': datetime.now()})
                self.account._log('export_price', 'success',
                                  _("Prix Etsy %s -> %s") % (listing.external_id, price),
                                  listing=listing)
            except Exception as exc:  # noqa: BLE001
                self.account._log('export_price', 'error', str(exc), listing=listing)
        return True

    def export_listings(self, listings):
        # Création d'un listing draft Etsy (champs minimaux requis).
        shop_id = self.account.shop_id
        for listing in listings.filtered(lambda l: not l.external_id):
            body = {
                'quantity': int(self._get_stock_qty(listing)) or 1,
                'title': listing.title or listing.product_id.display_name,
                'description': listing.product_id.description_sale or '',
                'price': round(self._get_price(listing), 2),
                'who_made': 'i_did',
                'when_made': 'made_to_order',
                'taxonomy_id': 1,  # à adapter à la catégorie réelle
            }
            url = '%s/shops/%s/listings' % (BASE_URL, shop_id)
            try:
                res = self._json('POST', url, headers=self._headers(), json=body)
                listing.write({'external_id': str(res.get('listing_id')),
                               'state': 'published', 'last_sync': datetime.now()})
                self.account._log('export_listing', 'success',
                                  _("Listing créé: %s") % res.get('listing_id'),
                                  listing=listing)
            except Exception as exc:  # noqa: BLE001
                listing.write({'state': 'error', 'last_error': str(exc)})
                self.account._log('export_listing', 'error', str(exc), listing=listing)
        return True

    def import_orders(self):
        acc = self.account
        url = '%s/shops/%s/receipts' % (BASE_URL, acc.shop_id)
        params = {'limit': 100, 'was_paid': 'true'}
        if acc.last_order_import:
            params['min_created'] = int(acc.last_order_import.timestamp())
        res = self._json('GET', url, headers=self._headers(), params=params)
        for receipt in res.get('results', []):
            self._import_receipt(receipt)
        acc.sudo().write({'last_order_import': datetime.now()})
        return True

    def _import_receipt(self, receipt):
        lines = []
        for t in receipt.get('transactions', []):
            lines.append({
                'sku': t.get('sku'),
                'qty': t.get('quantity', 1),
                'price_unit': (t.get('price', {}) or {}).get('amount', 0) / 100.0,
                'name': t.get('title'),
                'line_ref': str(t.get('transaction_id')),
            })
        order_data = {
            'ref': str(receipt.get('receipt_id')),
            'status': receipt.get('status'),
            'partner': {
                'name': receipt.get('name'),
                'street': receipt.get('first_line'),
                'street2': receipt.get('second_line'),
                'city': receipt.get('city'),
                'zip': receipt.get('zip'),
                'country_code': receipt.get('country_iso'),
                'email': receipt.get('buyer_email'),
            },
            'lines': lines,
        }
        return self._create_sale_order(order_data)
