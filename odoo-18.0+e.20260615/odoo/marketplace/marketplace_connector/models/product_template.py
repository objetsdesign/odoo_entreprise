# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    marketplace_listing_ids = fields.One2many(
        'marketplace.listing', 'product_tmpl_id', string='Annonces marketplace')
    marketplace_listing_count = fields.Integer(
        compute='_compute_marketplace_listing_count')

    def _compute_marketplace_listing_count(self):
        for tmpl in self:
            tmpl.marketplace_listing_count = len(tmpl.marketplace_listing_ids)

    def action_view_marketplace_listings(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Annonces marketplace',
            'res_model': 'marketplace.listing',
            'view_mode': 'list,form',
            'domain': [('product_tmpl_id', '=', self.id)],
        }
