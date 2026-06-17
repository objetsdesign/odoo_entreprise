{
    'name': "Produits sur mesure - Demande de devis",
    'version': '18.0.1.0.0',
    'category': 'Website/eCommerce',
    'summary': "Le client saisit ses mesures sur la fiche produit et envoie une "
               "demande de devis (sans passer par le paiement).",
    'description': """
Produits sur mesure (made-to-measure)
=====================================
Permet de marquer un produit comme "sur mesure" et de définir les champs de
mesure (largeur, hauteur, etc.). Sur le site e-commerce, le client remplit ces
mesures et clique sur "Demander un devis". Un devis (bon de commande en
brouillon) est alors créé automatiquement avec les mesures détaillées.
""",
    'author': "Votre société",
    'depends': ['website_sale', 'sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_views.xml',
        'views/website_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'website_custom_measure/static/src/css/custom_measure.css',
            'website_custom_measure/static/src/js/custom_measure.js',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
