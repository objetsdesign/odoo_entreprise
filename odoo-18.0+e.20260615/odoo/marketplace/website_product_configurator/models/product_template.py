from markupsafe import Markup

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_configurable = fields.Boolean(
        string="Produit configurable (canvas)",
        help="Si coché, un configurateur visuel s'affiche sur la fiche produit "
             "du site web.")
    config_svg = fields.Text(
        string="Dessin SVG du produit",
        help="Code SVG du produit. Chaque partie recolorable doit avoir un id "
             "(ex : id=\"part_body\") référencé dans l'onglet Parties.")
    config_svg_html = fields.Html(
        string="Aperçu du dessin",
        compute='_compute_config_svg_html', sanitize=False)
    config_color_ids = fields.One2many(
        'product.config.color', 'product_tmpl_id', string="Couleurs")
    config_part_ids = fields.One2many(
        'product.config.part', 'product_tmpl_id', string="Parties")
    config_size_ids = fields.One2many(
        'product.config.size', 'product_tmpl_id', string="Tailles")
    config_option_ids = fields.One2many(
        'product.config.option', 'product_tmpl_id', string="Options")

    @api.depends('config_svg')
    def _compute_config_svg_html(self):
        for rec in self:
            rec.config_svg_html = Markup(rec.config_svg) if rec.config_svg else False
