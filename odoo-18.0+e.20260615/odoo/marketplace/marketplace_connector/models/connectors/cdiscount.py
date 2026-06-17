# -*- coding: utf-8 -*-
"""Connecteur Cdiscount - Octopia Marketplace API.

Cdiscount opère désormais sa marketplace via Octopia. L'API est REST/JSON
et s'authentifie par token (OAuth2 client credentials) ou clé API selon le
contrat vendeur. On gère ici un flux client_credentials générique.

Champs marketplace.account utilisés :
  * client_id     -> identifiant client API
  * client_secret -> secret client API
  * base_url      -> base de l'API Octopia (ex: https://api.octopia-io.net)
  * seller_id     -> identifiant vendeur

Doc : https://dev.octopia-io.net/ (selon accès vendeur)
NB : les chemins exacts varient selon la version de l'API Octopia ;
adapter `_PATHS` à la documentation fournie par votre compte.
"""
from datetime import datetime, timedelta

from odoo import _
from odoo.exceptions import UserError

from .base import BaseConnector
from .registry import register

TOKEN_PATH = '/auth/oauth2/token'

_PATHS = {
    'offers': '/marketplace/offers',
    'orders': '/marketplace/orders',
}


@register('cdiscount')
class CdiscountConnector(BaseConnector):

    def _url(self, path):
        base = (self.account.base_url or 'https://api.octopia-io.net').rstrip('/')
        return base + path

    def authenticate(self):
        acc = self.account
        if acc.access_token and acc.token_expiry and \
                acc.token_expiry > datetime.now() + timedelta(minutes=2):
            return acc.access_token
        data = {
            'grant_type': 'client_credentials',
            'client_id': acc.client_id,
            'client_secret': acc.client_secret,
        }
        res = self._json('POST', self._url(TOKEN_PATH), data=data)
        token = res.get('access_token')
        if not token:
            raise UserError(_("Cdiscount/Octopia : échec d'authentification."))
        acc.sudo().write({
            'access_token': token,
            'token_expiry': datetime.now() + timedelta(
                seconds=res.get('expires_in', 3600)),
        })
        return token

    def _headers(self):
        headers = {
            'Authorization': 'Bearer %s' % self.authenticate(),
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        if self.account.seller_id:
            headers['SellerId'] = self.account.seller_id
        return headers

    def test_connection(self):
        self.authenticate()
        self.account._log('test', 'success', _("Cdiscount/Octopia connecté."))
        return True

    def _push_offers(self, listings, with_stock, with_price):
        offers = []
        for listing in listings.filtered('sync_enabled'):
            if not listing.sku:
                continue
            offer = {'sellerProductId': listing.sku, 'ean': listing.ean}
            if with_stock:
                offer['stock'] = int(self._get_stock_qty(listing))
            if with_price:
                offer['price'] = round(self._get_price(listing), 2)
            offers.append((listing, offer))
        if not offers:
            return True
        body = {'offers': [o for _l, o in offers]}
        try:
            self._json('POST', self._url(_PATHS['offers']),
                       headers=self._headers(), json=body)
            now = datetime.now()
            for listing, offer in offers:
                vals = {'last_sync': now, 'last_error': False}
                if 'stock' in offer:
                    vals['qty_available'] = offer['stock']
                if 'price' in offer:
                    vals['list_price'] = offer['price']
                listing.write(vals)
            self.account._log(
                'export_stock' if with_stock else 'export_price', 'success',
                _("%d offre(s) Cdiscount mise(s) à jour.") % len(offers))
        except Exception as exc:  # noqa: BLE001
            self.account._log('export_stock', 'error', str(exc))
            raise
        return True

    def export_stock(self, listings):
        return self._push_offers(listings, with_stock=True, with_price=False)

    def export_price(self, listings):
        return self._push_offers(listings, with_stock=False, with_price=True)

    def export_listings(self, listings):
        return self._push_offers(listings, with_stock=True, with_price=True)

    def import_orders(self):
        acc = self.account
        params = {'orderStateFilter': 'CreatedByCustomer,AcceptedBySeller'}
        if acc.last_order_import:
            params['beginCreationDate'] = acc.last_order_import.strftime(
                '%Y-%m-%dT%H:%M:%SZ')
        res = self._json('GET', self._url(_PATHS['orders']),
                         headers=self._headers(), params=params)
        for order in res.get('orders', res.get('data', [])):
            self._import_single_order(order)
        acc.sudo().write({'last_order_import': datetime.now()})
        return True

    def _import_single_order(self, order):
        ship = order.get('shippingAddress', {})
        lines = []
        for line in order.get('orderLines', order.get('lines', [])):
            lines.append({
                'sku': line.get('sellerProductId') or line.get('sku'),
                'qty': line.get('quantity', 1),
                'price_unit': line.get('unitPrice', line.get('price', 0)),
                'name': line.get('productName'),
                'line_ref': line.get('orderLineId'),
            })
        order_data = {
            'ref': order.get('orderNumber') or order.get('orderId'),
            'status': order.get('orderState'),
            'date': order.get('creationDate'),
            'partner': {
                'name': ship.get('fullName') or '%s %s' % (
                    ship.get('firstName', ''), ship.get('lastName', '')),
                'street': ship.get('address1'),
                'street2': ship.get('address2'),
                'city': ship.get('city'),
                'zip': ship.get('zipCode'),
                'country_code': ship.get('country'),
                'phone': ship.get('phone'),
                'email': order.get('customerEmail'),
            },
            'lines': lines,
        }
        return self._create_sale_order(order_data)
