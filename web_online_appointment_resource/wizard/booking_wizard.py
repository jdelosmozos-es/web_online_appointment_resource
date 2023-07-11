from odoo import models, fields
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

class BookingWizard(models.TransientModel):
    _name = 'web.appointment.booking.wizard'
        
    def _space_domain(self):
        import sys;sys.path.append(r'/home/javier/eclipse/jee-2021/eclipse/plugins/org.python.pydev.core_10.1.4.202304151203/pysrc')
        import pydevd;pydevd.settrace('127.0.0.1',port=9999)
        start_date = self.date
        end_date = start_date + timedelta(days=1)
        Line = self.env['web.online.appointment.line']
        calendar_lines = Line.search([('start_datetime', '>=', start_date),
                                       ('end_datetime','<',end_date),
                                             ('is_open','=',True)])
        return [('id','in',calendar_lines.mapped('space').ids)]
        
    def _slot_domain(self):
        import sys;sys.path.append(r'/home/javier/eclipse/jee-2021/eclipse/plugins/org.python.pydev.core_10.1.4.202304151203/pysrc')
        import pydevd;pydevd.settrace('127.0.0.1',port=9999)
        Line = self.env['web.online.appointment.line']
        date = Line.get_tz_date(datetime.strptime(self.date, DEFAULT_SERVER_DATETIME_FORMAT), self.context['tz'])
        slots = self.env['web.online.appointment'].get_time_slots(date, self.num_persons, self.space.id)
        return [('id','in',slots.ids)]
        
    date = fields.Date()
    space = fields.Many2one(comodel_name='appointment.space',domain=_space_domain)
    num_persons = fields.Integer()
    slot = fields.Many2one(comodel_name='web.online.appointment.line',domain=_slot_domain)
    
    def action_book(self):
        pass
        