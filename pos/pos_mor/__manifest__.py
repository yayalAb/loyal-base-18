{
    'name': 'POS MOR Integration',
    'version': '18.0.1.0.0',
    'category': 'pos',
    'summary': 'POS MOR Integration',
    'description': '''POS MOR Integration''',
    'author': 'Niyat Consultancy',
    'company': 'Niyat Consultancy',
    'maintainer': 'Niyat Consultancy',
    'website': 'https://niyatconsultancy.com/',
    'depends': ['base', 'point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/view_pos_mor_config.xml',
        'views/mor_api_view.xml',
        'views/mor_responses.xml',
        'views/payment_view.xml',
        'views/mor_receipt_api.xml',
        'views/invoice_inher_view.xml'
    ],
    'assets': {

    },
    'images': [

    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
