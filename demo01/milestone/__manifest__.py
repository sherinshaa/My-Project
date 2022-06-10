{
    'name': 'Milestone',
    'application': True,
    'version': '15.0.1.0.0',
    'description': "Milestone",
    'sequence': 4,
    'installable': True,

    'depends': ['base', 'sale_management', 'project'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/milestone.xml',
    ]
}