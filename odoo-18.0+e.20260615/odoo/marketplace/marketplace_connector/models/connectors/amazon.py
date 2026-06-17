# -*- coding: utf-8 -*-
"""Connecteur Amazon - Selling Partner API (SP-API).

Authentification : Login With Amazon (LWA). Depuis 2023, la signature AWS
SigV4 n'est plus obligatoire pour la plupart des appels : un access token LWA
suffit. On échange le refresh_token contre un access_token.

Champs marketplace.account utilisés :
  * client_id      -> LWA client id
  * client_secret  -> LWA client secret
  * refresh_token  -> LWA refresh token
  * seller_id      -> Marketplace ID (ex: A13V1IB3VIYZZH pour la France)
  * region         -> 'eu' | 'na' | 'fe'  (zone des endpoints)

Doc : https://developer-docs.amazon.com/sp-api/
"""
from datetime import datetime, timedelta

from odoo import _
from odoo.exceptions import UserError

from .base import BaseConnector
from .registry import register

LWA_TOKEN_URL = 'https://api.amazon.com/auth/o2/token'

ENDPOINTS = {
    'eu': 'https://sellingpartnerapi-eu.amazon.com',
    'na': 'https://sellingpartnerapi-na.amazon.com',
    'fe': 'https://sellingpartnerapi-fe.amazon.com',
}


@register('amazon')
class AmazonConnector(BaseConnector):

    def _endpoint(self):
        region = (self.account.region or 'eu').lower()
        return ENDPOINTS.get(region, ENDPOINTS['eu'])

    # --- Auth ------------------------------------------------------------
    def authenticate(self):
        acc = self.account
        if acc.access_token and acc.token_expiry and \
                acc.token_expiry > datetime.now() + timedelta(minutes=2):
            return acc.access_token
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': acc.refresh_token,
            'client_id': acc.client_id,
            'client_secret': acc.client_secret,
        }
        res = self._json('POST', LWA_TOKEN_URL, data=data)
        token = res.get('access_token')
        if not token:
            raise UserError(_("Amazon : aucun access_token retourné."))
        acc.sudo().write({
            'access_token': token,
            'token_expiry': datetime.now() + timedelta(
                seconds=res.get('expires_in', 3600)),
        })
        return token

    def _headers(self):
        return {
            'x-amz-access-token': self.authenticate(),
            'Content-Type': 'application/json',
        }

    def test_connection(self):
        token = self.authenticate()
        # Appel léger : liste des participations marketplace du vendeur.
        url = self._endpoint() + '/sellers/v1/marketplaceParticipations'
        self._json('GET', url, headers=self._headers())
        self.account._log('test', 'success', _("Amazon connecté (LWA OK)."))
        return True

    # --- Stock (Listings Items API patch quantity) -----------------------
    def export_stock(self, listings):
        marketplace_id = self.account.seller_id
        for listing in listings.filtered('sync_enabled'):
            if not listing.sku:
                continue
            qty = int(self._get_stock_qty(listing))
            url = '%s/listings/2021-08-01/items/%s/%s' % (
                self._endpoint(), self.account.seller_id, listing.sku)
            body = {
                'productType': 'PRODUCT',
                'patches': [{
                    'op': 'replace',
                    'path': '/attributes/fulfillment_availability',
                    'value': [{
                        'fulfillment_channel_code': 'DEFAULT',
                        'quantity': qty,
                    }],
                }],
            }
            params = {'marketplaceIds': marketplace_id}
            try:
                self._json('PATCH', url, headers=self._headers(),
                           params=params, json=body)
                listing.write({'qty_available': qty,
                               'last_sync': datetime.now(), 'last_error': False})
                self.account._log('export_stock', 'success',
                                  _("Stock %s -> %s") % (listing.sku, qty),
                                  listing=listing)
            except Exception as exc:  # noqa: BLE001
                listing.write({'last_error': str(exc), 'state': 'error'})
                self.account._log('export_stock', 'error', str(exc),
                                  listing=listing)
        return True

    # --- Prix ------------------------------------------------------------
    def export_price(self, listings):
        marketplace_id = self.account.seller_id
        for listing in listings.filtered('sync_enabled'):
            if not listing.sku:
                continue
            price = round(self._get_price(listing), 2)
            url = '%s/listings/2021-08-01/items/%s/%s' % (
                self._endpoint(), self.account.seller_id, listing.sku)
            body = {
                'productType': 'PRODUCT',
                'patches': [{
                    'op': 'replace',
                    'path': '/attributes/purchasable_offer',
                    'value': [{
                        'currency': self.account.company_id.currency_id.name,
                        'our_price': [{'schedule': [{'value_with_tax': price}]}],
                    }],
                }],
            }
            params = {'marketplaceIds': marketplace_id}
            try:
                self._json('PATCH', url, headers=self._headers(),
                           params=params, json=body)
                listing.write({'list_price': price, 'last_sync': datetime.now()})
                self.account._log('export_price', 'success',
                                  _("Prix %s -> %s") % (listing.sku, price),
                                  listing=listing)
            except Exception as exc:  # noqa: BLE001
                listing.write({'last_error': str(exc)})
                self.account._log('export_price', 'error', str(exc),
                                  listing=listing)
        return True

    def export_listings(self, listings):
        # Sur Amazon, la création d'annonce passe par la Listings Items API
        # (PUT) avec un productType + attributs spécifiques à la catégorie.
        # On délègue par défaut à l'export stock + prix sur des SKU existants.
        self.export_stock(listings)
        self.export_price(listings)
        return True

    # --- Commandes (Orders API v0) ---------------------------------------
    def import_orders(self):
        acc = self.account
        since = acc.last_order_import or (datetime.now() - timedelta(days=7))
        url = self._endpoint() + '/orders/v0/orders'
        params = {
            'MarketplaceIds': acc.seller_id,
            'CreatedAfter': since.strftime('%Y-%m-%dT%H:%M:%SZ'),
        }
        res = self._json('GET', url, headers=self._headers(), params=params)
        orders = res.get('payload', {}).get('Orders', [])
        for amz_order in orders:
            self._import_single_order(amz_order)
        acc.sudo().write({'last_order_import': datetime.now()})
        return True

    def _import_single_order(self, amz_order):
        order_id = amz_order.get('AmazonOrderId')
        # Récupération des lignes de commande
        url = '%s/orders/v0/orders/%s/orderItems' % (self._endpoint(), order_id)
        items_res = self._json('GET', url, headers=self._headers())
        items = items_res.get('payload', {}).get('OrderItems', [])
        ship = amz_order.get('ShippingAddress', {})
        lines = []
        for it in items:
            price = it.get('ItemPrice', {}).get('Amount', 0)
            qty = it.get('QuantityOrdered', 1)
            lines.append({
                'sku': it.get('SellerSKU'),
                'qty': qty,
                'price_unit': float(price) / qty if qty else float(price),
                'name': it.get('Title'),
                'line_ref': it.get('OrderItemId'),
            })
        order_data = {
            'ref': order_id,
            'status': amz_order.get('OrderStatus'),
            'date': amz_order.get('PurchaseDate'),
            'partner': {
                'name': ship.get('Name'),
                'street': ship.get('AddressLine1'),
                'street2': ship.get('AddressLine2'),
                'city': ship.get('City'),
                'zip': ship.get('PostalCode'),
                'country_code': ship.get('CountryCode'),
                'phone': ship.get('Phone'),
            },
            'lines': lines,
        }
        return self._create_sale_order(order_data)
