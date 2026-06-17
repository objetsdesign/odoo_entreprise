from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_3d = fields.Boolean(
        string="Aperçu 3D",
        help="Affiche un configurateur 3D sur la fiche produit du site web.")
    p3d_shape = fields.Selection([
        ('mug',      "Tasse / mug"),
        ('cylinder', "Cylindre"),
        ('box',      "Boîte"),
        ('handbag',  "Sac à main"),
        ('vase',     "Vase"),
    ], string="Forme 3D générée", default='mug',
        help="Forme géométrique générée automatiquement. "
             "Ignorée si un modèle .glb est importé ci-dessous.")
    p3d_glb = fields.Binary(
        string="Modèle 3D (.glb)", attachment=True,
        help="Fichier 3D au format glTF binaire (.glb). Quand il est présent, "
             "il remplace la forme générée et s'affiche tel quel sur le site "
             "(rotation à la souris, zoom à la molette).")
    p3d_glb_filename = fields.Char(string="Nom du fichier .glb")
    p3d_color_ids = fields.One2many(
        'product.p3d.color', 'product_tmpl_id', string="Couleurs de matière")
