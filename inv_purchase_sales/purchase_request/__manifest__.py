{
    'name': 'purchase request',
    'version': '1.0',
    'category': 'Purchases',
    'description': 'A module to handle purchase requests',
    'depends': ['base', 'stock', 'purchase', 'store_request'],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'report/purchase_request_report_template.xml',
        'report/purchase_order_report_template.xml',
        'views/purchase_request_view.xml',
        'views/store_request_inherit_view.xml',
        'views/purchase_order_view.xml',

    ],
    'installable': True,
    'application': False,
}
