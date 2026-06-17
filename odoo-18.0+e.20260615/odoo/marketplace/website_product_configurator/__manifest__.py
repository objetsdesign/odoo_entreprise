{
    'name': "Configurateur de produit visuel (canvas) - Devis",
    'version': '18.0.1.1.0',
    'category': 'Website/eCommerce',
    'summary': "Le client choisit couleurs (sur le produit en direct), tailles, "
               "etc. via un canvas interactif, puis envoie une demande de devis.",
    'description': """
Configurateur de produit visuel
===============================
- Marque un produit comme "configurable".
- Définit un dessin SVG du produit avec des parties recolorables
  (corps, manches, col...), des couleurs disponibles et des tailles.
- Sur le site, le client voit le produit dans un canvas : il clique sur une
  partie puis sur une couleur, et la couleur s'applique en direct sur le produit.
  Il choisit la taille, la quantité, puis clique sur "Demander un devis".
- Un devis (bon de commande en brouillon) est créé avec le détail de la
  configuration et un APERCU PNG du produit personnalisé (visible dans le
  fil de discussion du devis).
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
            'website_product_configurator/static/src/css/configurator.css',
            'website_product_configurator/static/src/js/configurator.js',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
