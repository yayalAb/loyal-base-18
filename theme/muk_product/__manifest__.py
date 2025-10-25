{
    'name': 'MuK Product', 
    'summary': 'Centralize your product views',
    'description': '''
        This module gives you a quick view of all your products, 
        accessible from your home menu.
    ''',
    'version': '18.0.1.1.5',
    'category': 'Sales/Product',
    'license': 'LGPL-3', 
    'author': 'MuK IT',
    'website': 'http://www.mukit.at',
    'live_test_url': 'https://my.mukit.at/r/f6m',
    'contributors': [
        'Mathias Markl <mathias.markl@mukit.at>',
    ],
    'depends': [
        'base_setup',
        'product',
        'uom',
        'muk_web_utils',
    ],
    'data': [
        'data/ir_sequence.xml',
        'security/ir.model.access.csv',
        'views/product_template.xml',
        'views/product_product.xml',
        'views/product_document.xml',
        'views/product_pricelist_item.xml',
        'views/product_search.xml',
        'views/menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'muk_product/static/src/views/**/*.*',
        ],
    },
    'images': [
        'static/description/banner.png',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
