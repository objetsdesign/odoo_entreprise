# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MarketplaceAccount(models.Model):
    _name = 'marketplace.account'
    _description = 'Compte Marketplace'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(required=True, tracking=True)
    active = fields.Boolean(default=True)
    marketplace_id = fields.Many2one(
        'marketplace.marketplace', string='Marketplace',
        required=True, ondelete='restrict', tracking=True)
    code = fields.Selection(related='marketplace_id.code', store=True)
    company_id = fields.Many2one(
        'res.company', string='Société',
        default=lambda self: self.env.company, required=True)
    warehouse_id = fields.Many2one(
        'stock.warehouse', string='Entrepôt',
        help="Entrepôt utilisé pour calculer le stock exporté.")
    pricelist_id = fields.Many2one(
        'product.pricelist', string='Liste de prix',
        help="Liste de prix utilisée pour l'export des prix. "
             "Si vide, le prix de vente du produit est utilisé.")
    fiscal_position_id = fields.Many2one(
        'account.fiscal.position', string='Position fiscale')
    team_id = fields.Many2one('crm.team', string="Équipe commerciale")

    # --- Environnement ---------------------------------------------------
    environment = fields.Selection(
        selection=[('sandbox', 'Sandbox / Test'), ('production', 'Production')],
        default='sandbox', required=True, tracking=True)
    state = fields.Selection(
        selection=[('draft', 'Brouillon'), ('connected', 'Connecté'),
                   ('error', 'Erreur')],
        default='draft', tracking=True)

    # --- Identifiants génériques (utilisés différemment par connecteur) ---
    client_id = fields.Char(string='Client ID / App Key')
    client_secret = fields.Char(string='Client Secret')
    refresh_token = fields.Char(string='Refresh Token')
    access_token = fields.Char(string='Access Token', copy=False)
    token_expiry = fields.Datetime(string='Expiration token', copy=False)
    api_key = fields.Char(string='API Key (Mirakl / Cdiscount)')
    seller_id = fields.Char(string='Seller ID / Merchant ID')
    shop_id = fields.Char(string='Shop ID (Etsy)')
    region = fields.Char(string='Région / Endpoint',
                         help="Ex Amazon: eu-west-1 ; Mirakl: URL de la plateforme.")
    base_url = fields.Char(string='URL de base de l\'API')

    # --- Options de synchronisation --------------------------------------
    auto_export_stock = fields.Boolean(string='Export stock auto', default=True)
    auto_export_price = fields.Boolean(string='Export prix auto', default=True)
    auto_import_orders = fields.Boolean(string='Import commandes auto', default=True)
    last_order_import = fields.Datetime(string='Dernier import commandes', copy=False)

    listing_ids = fields.One2many(
        'marketplace.listing', 'account_id', string='Annonces')
    listing_count = fields.Integer(compute='_compute_counts')
    order_count = fields.Integer(compute='_compute_counts')

    @api.depends('listing_ids')
    def _compute_counts(self):
        listing_data = self.env['marketplace.listing'].read_group(
            [('account_id', 'in', self.ids)],
            ['account_id'], ['account_id'])
        listing_map = {d['account_id'][0]: d['account_id_count'] for d in listing_data}
        order_data = self.env['sale.order'].read_group(
            [('marketplace_account_id', 'in', self.ids)],
            ['marketplace_account_id'], ['marketplace_account_id'])
        order_map = {d['marketplace_account_id'][0]: d['marketplace_account_id_count']
                     for d in order_data}
        for rec in self:
            rec.listing_count = listing_map.get(rec.id, 0)
            rec.order_count = order_map.get(rec.id, 0)

    # --- Fabrique de connecteur ------------------------------------------
    def _get_connector(self):
        """Retourne l'instance du connecteur Python correspondant au code."""
        self.ensure_one()
        Connector = self.env['marketplace.connector.registry'].get_connector(self.code)
        if not Connector:
            raise UserError(_("Aucun connecteur disponible pour « %s ».") % self.code)
        return Connector(self)

    # --- Actions utilisateur ---------------------------------------------
    def action_test_connection(self):
        self.ensure_one()
        try:
            connector = self._get_connector()
            connector.test_connection()
            self.state = 'connected'
            self.message_post(body=_("Connexion réussie."))
        except Exception as exc:  # noqa: BLE001
            self.state = 'error'
            _logger.exception("Test de connexion échoué")
            raise UserError(_("Échec de connexion : %s") % exc)
        return self._notify(_("Connexion OK"), 'success')

    def action_export_listings(self):
        for account in self:
            account._get_connector().export_listings(account.listing_ids)
        return True

    def action_export_stock(self):
        for account in self:
            account._get_connector().export_stock(account.listing_ids)
        return True

    def action_export_price(self):
        for account in self:
            account._get_connector().export_price(account.listing_ids)
        return True

    def action_import_orders(self):
        for account in self:
            account._get_connector().import_orders()
        return True

    def action_view_listings(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Annonces'),
            'res_model': 'marketplace.listing',
            'view_mode': 'list,form',
            'domain': [('account_id', '=', self.id)],
            'context': {'default_account_id': self.id},
        }

    def action_view_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Commandes'),
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'domain': [('marketplace_account_id', '=', self.id)],
        }

    def _notify(self, message, msg_type='info'):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {'message': message, 'type': msg_type, 'sticky': False},
        }

    # --- Logging ---------------------------------------------------------
    def _log(self, operation, status, message, listing=None, order_ref=None):
        self.ensure_one()
        return self.env['marketplace.sync.log'].create({
            'account_id': self.id,
            'operation': operation,
            'status': status,
            'message': message[:4000] if message else False,
            'listing_id': listing.id if listing else False,
            'order_ref': order_ref,
        })

    # --- Crons -----------------------------------------------------------
    @api.model
    def _cron_export_stock(self):
        for account in self.search([('auto_export_stock', '=', True),
                                     ('state', '=', 'connected')]):
            try:
                account._get_connector().export_stock(account.listing_ids)
            except Exception:  # noqa: BLE001
                _logger.exception("Cron export stock échoué (%s)", account.name)

    @api.model
    def _cron_export_price(self):
        for account in self.search([('auto_export_price', '=', True),
                                     ('state', '=', 'connected')]):
            try:
                account._get_connector().export_price(account.listing_ids)
            except Exception:  # noqa: BLE001
                _logger.exception("Cron export prix échoué (%s)", account.name)

    @api.model
    def _cron_import_orders(self):
        for account in self.search([('auto_import_orders', '=', True),
                                    ('state', '=', 'connected')]):
            try:
                account._get_connector().import_orders()
            except Exception:  # noqa: BLE001
                _logger.exception("Cron import commandes échoué (%s)", account.name)
