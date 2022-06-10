{
    'name': 'CRM Commission',
    'application': True,
    'version': '15.0.1.0.0',
    'description': "CRM Commission",
    'sequence': 3,
    'installable': True,

    'depends': ['base', 'product', 'sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/crm_commission.xml',
        'views/crm_commission_productwise.xml',
        'views/crm_commission_graduated.xml',
        'views/crm_commission_saleperson.xml',
        'views/crm_commission_saleteam.xml',
        'views/menu.xml'
    ]
}
