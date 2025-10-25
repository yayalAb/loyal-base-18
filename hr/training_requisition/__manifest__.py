{
    'name': 'Training Requisition',
    'category': 'Human Resources',
    'summary': 'A module for making training requests',
    'depends': [
         'base', 'hr', 'website_slides'
    ],
    'data': [
        'security/requisition_security.xml',
        'security/ir.model.access.csv',
        'security/users_groups.xml',
        'views/training_requisition_wizard_views.xml',
        'views/training_request_views.xml',
        'views/view_slide_channel_inherited_form.xml'

    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}