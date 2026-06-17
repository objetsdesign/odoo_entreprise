from markupsafe import Markup

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_visual_customizer = fields.Boolean(
        string="Personnalisation visuelle (canvas)",
        help="Active le customizer visuel (texte + logo) sur la fiche produit.")
    vc_svg = fields.Text(
        string="Dessin SVG du produit",
        help="SVG du produit. La zone recolorée par les couleurs est celle "
             "ciblée par 'Cible couleur'.")
    vc_svg_html = fields.Html(
        string="Aperçu", compute='_compute_vc_svg_html', sanitize=False)
    vc_color_target = fields.Char(
        string="Cible couleur", default='#part_body',
        help="Sélecteur SVG recoloré par les couleurs produit, ex : #part_body")
    vc_fonts = fields.Char(
        string="Polices proposées",
        default="Arial, Helvetica, Georgia, Times New Roman, Courier New, "
                "Verdana, Impact, Comic Sans MS",
        help="Liste de polices séparées par des virgules.")
    vc_area = fields.Char(
        string="Zone de personnalisation",
        help="Optionnel. Rectangle indicatif 'x,y,w,h' en coordonnées du "
             "viewBox SVG (affiche un cadre en pointillés).")
    vc_color_ids = fields.One2many(
        'product.vc.color', 'product_tmpl_id', string="Couleurs produit")
    vc_dimension_ids = fields.One2many(
        'product.vc.dimension', 'product_tmpl_id', string="Dimensions")

    @api.depends('vc_svg')
    def _compute_vc_svg_html(self):
        for rec in self:
            rec.vc_svg_html = Markup(rec.vc_svg) if rec.vc_svg else False
