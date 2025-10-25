{
    'name': "Purchase Guarantee",
    'version': '1.0',
    'category': 'Purchases',
    'summary': "Manage purchase guarantees",
    'description': """
        This module allows users to manage purchase guarantees, including
        the creation and tracking of guarantees for purchased products.
    """,
    "author": "Niyat ERP",
    'depends': ['base', 'product', 'purchase', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'security/user_groups.xml',
        'data/mail_activity_type_data.xml',
        'data/guarantee_reminder.xml',
        'views/purchase_guarante_views.xml',
        'views/purchase_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}