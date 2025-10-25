# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Project by Phases',
    'version': '18.0.0.0',
    'category': 'Project',
    'license': 'OPL-1',
    'summary': 'This apps helps to manage Project and Task Phases',
    'description': """
        Project Phases.
        Task phases.
        Project by Phases
        Task by Project phases
        Task by Phases
        Project with phases
        Task with phases

""",
    'author': 'BROWSEINFO',
    'website': 'https://www.browseinfo.com/demo-request?app=bi_odoo_project_phases&version=18&edition=Community',
    'depends': ['project'],
    'data': [
        'security/ir.model.access.csv',
        'views/project_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    "live_test_url":'https://www.browseinfo.com/demo-request?app=bi_odoo_project_phases&version=18&edition=Community',
    "images":['static/description/Banner.gif'],
}
