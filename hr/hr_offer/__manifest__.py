{
    'name': 'Hr Offer',
    'category': 'Human Resources',
    'depends': [
        'hr_recruitment', 'hr_contract_salary'
    ],
    'data': [
        'report/custom_mail_template.xml',
        'report/salary_offer_template.xml',
        'report/welcome_letter_template.xml',
        'report/report_actions.xml',
        'views/hr_contract_salary_offer_view.xml',
    ],
    'installable': True,
    'auto_install': False
}