# -*- coding: utf-8 -*-
{
    'name': "Vendor Bid Custom",
    'summary': "Customization to the Vendor Bid module",
    'author': "Niyat Consultancy",
    'category': 'Purchases',
    'version': '0.1',
    'depends': ['VendorBid', 'store_request'],
    'data': [
        'security/ir.model.access.csv',
        'security/user_group.xml',
        'report/purchase_request_report_template.xml',
        'report/purchase_order_report_template.xml',
        'views/supplies_wizard_views.xml',
        'views/supplies_rfp_views.xml',
        'views/store_request_inherit_view.xml',
        'views/purchase_order_views.xml',
        'views/product_price_view.xml',
    ],
    'application': False,
    'installable': True,
}
