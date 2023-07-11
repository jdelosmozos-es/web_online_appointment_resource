# -*- coding: utf-8 -*-
{
    'name': 'Web Online Appointment of Resources',
    'version': '15.0.1.0',
    'summary': 'Make reservations that create appointment reminders.',
    'description': """Make reservations that create appointment reminders.""",
    'license': 'Other proprietary',
    'author': 'Javier L. de los Mozos',
    'maintainer': 'Javier L. de los Mozos',
    'website': 'http://www.jdelosmozos.es',
    'live_test_url':'',
    'category': 'Website/Website',
    'depends': ['website', 'mail', 'calendar', 'contacts'], #, 'sale', 'stock', 'website_payment'],
    'data': [
        'data/appointment_data.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/web_online_appointment_view.xml',
        'views/resource_view.xml',
        'views/appointment.xml',
        'wizard/close_service_wizard_view.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'web_online_appointment_resource/static/src/css/appointment.css',
            'web_online_appointment_resource/static/src/js/appointment.js',
            'web/static/lib/fontawesome/css/font-awesome.css',
            'web_online_appointment_resource/static/lib/datetime/css/datepicker.css',
            'web_online_appointment_resource/static/lib/datetime/js/bootstrap-datepicker.js',
        ],
        'web.assets_backend': [
            'web_online_appointment_resource/client_action/client_action.js',
        ]
    },
    'installable': True,
    'auto_install': False,
}