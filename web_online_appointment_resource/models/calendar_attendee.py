import logging

from odoo import models, _
import base64

_logger = logging.getLogger(__name__)

class Attendee(models.Model):
    _inherit = 'calendar.attendee'
    
    def do_decline(self):
        import sys;sys.path.append(r'/home/javier/eclipse/jee-2021/eclipse/plugins/org.python.pydev.core_10.1.4.202304151203/pysrc')
        import pydevd;pydevd.settrace('127.0.0.1',port=9999)
        system_user = self.env.ref('web_online_appointment_resource.appointment_system_user')
        management_user = self.env.ref('web_online_appointment_resource.appointment_manager_user')
        mail_template = self.env.ref('web_online_appointment_resource.calendar_template_change_attendee_status', raise_if_not_found=False)
        (self.event_id.attendee_ids - self)._send_mail_to_attendees(mail_template, force_send=True)
        self.flush()
        if self.partner_id == management_user.partner_id and \
            system_user == self.event_id.user_id:
            self.event_id.unlink()
        else:
            super(Attendee, self).do_decline()