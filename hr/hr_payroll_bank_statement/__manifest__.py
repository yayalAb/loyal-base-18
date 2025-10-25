{
    'name': 'Payroll Bank Statement Letter',
    'category': 'Human Resources/Payroll',
    'summary': 'Generate bank statement letters from selected payslips.',
    'depends': [
        'hr_payroll',
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'report/payroll_bank_statement_template.xml',
        'report/payroll_bank_report.xml',
        'views/payroll_statement_report_wizard_views.xml',
        'views/hr_payslip_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}