{
    'name': "Configurateur 3D produit (style Zakeke) - Devis",
    'version': '18.0.1.0.0',
    'category': 'Website/eCommerce',
    'summary': "Aperçu 3D du produit (orbite à la souris) avec choix de couleur "
               "de matière, puis demande de devis.",
    'description': """
Configurateur 3D produit
========================
- Affiche le produit en 3D sur la fiche produit (three.js).
- Le client fait pivoter le produit librement (orbite) et zoome.
- Il choisit la couleur de la matière (appliquée en direct).
- "Demander un devis" -> un devis est créé avec un aperçu 3D (PNG).

Note : three.js est chargé depuis un CDN (cdnjs) et le chargeur de modèles
GLTFLoader depuis jsDelivr. Si votre site a une politique de sécurité (CSP)
stricte, autorisez 'cdnjs.cloudflare.com' et 'cdn.jsdelivr.net', ou hébergez
ces scripts en local dans static/lib/ et ajustez l'asset.

Modèle 3D réel : importez un fichier .glb dans l'onglet « Aperçu 3D » de la
fiche produit. Il remplace alors la forme générée et s'affiche tel quel.
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
            'website_product_3d/static/src/css/product_3d.css',
            'website_product_3d/static/src/js/product_3d.js',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
