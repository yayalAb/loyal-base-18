{
    "name": "Hr Leave Balance",
    "category": "Human Resources",
    "author": "Niyat ERP",
    "depends": ['base', 'hr_holidays'],
    "summary": "A module that adds a maximum leave balance for each leave types",
    "data": [
        'views/hr_leave_views.xml',
    ],  
    "installable": True,
    "application": False,
    "auto_install": True,
}