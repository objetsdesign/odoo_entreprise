{
    'name': "Visual Product Customizer (style Zakeke) - Devis",
    'version': '18.0.2.0.0',
    'category': 'Website/eCommerce',
    'summary': "Personnalisation visuelle en direct : texte, logo, couleurs, "
               "déplacement/redimensionnement sur le produit, puis devis.",
    'description': """
Visual Product Customizer
=========================
Inspiré de la structure de Zakeke (Visual Product Customizer) :
- Produit affiché en direct (dessin SVG recolorable).
- Le client choisit la couleur du produit.
- Il ajoute du TEXTE (police, couleur, taille, rotation).
- Il téléverse un LOGO / une IMAGE.
- Il déplace, redimensionne et fait pivoter chaque élément sur le produit.
- Aperçu en temps réel.
- "Demander un devis" -> un devis est créé avec le visuel personnalisé (PNG)
  et le détail de la composition.
""",
    'author': "Votre société",
    'depends': ['website_sale', 'sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_views.xml',
        'views/website_templates.xml',
        'data/demo_product.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'website_visual_customizer/static/src/css/customizer.css',
            'website_visual_customizer/static/src/js/customizer.js',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
