{

    'name': 'Hospital Management',
    'application': True,
    'version': '15.0.1.0.0',
    'description': "Hospital Management",
    'sequence': 2,
    'depends': ['base',
                'hr',
                'contacts',
                'mail'],
    'data': [
        'security/hospital_management_security.xml',
        'security/ir.model.access.csv',
        'views/hospital_management_views.xml',
        'views/hospital_management_main.xml',
        'views/hospital_management_op.xml',
        'views/hospital_management_consultation.xml',
        'views/hospital_management_desease.xml',
        'views/hospital_management_treatment.xml',
        'views/hospital_management_medicine.xml',
        'views/hospital_management_appointment.xml',
        'views/hospital_management_payment.xml',
        'views/menu.xml',
    ]

}
