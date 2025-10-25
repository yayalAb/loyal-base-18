{
    "name": "Payment Request",
    "version": "1.0",
    "category": "Purchases",
    "author": "Niyat ERP",
    "description": "Module for managing payment requests.",
    "summary": "Manage payment requests efficiently",
    "depends": ["base", "account", "purchase", 'purchase_guarante', 'hr_expense'],
    "data": [
        "views/hr_expense_views.xml",
        "views/purchase_order_views.xml",
        
    ],
    "installable": True,
    "application": False
}