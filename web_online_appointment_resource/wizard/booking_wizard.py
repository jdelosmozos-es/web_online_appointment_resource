from odoo import models, fields, api
from datetime import datetime, timedelta
import json

class BookingWizard(models.TransientModel):
    _name = 'web.appointment.booking.wizard'
        
    date = fields.Date(required=True)
    space = fields.Many2one(comodel_name='appointment.space',required=True)
    space_domain = fields.Char(compute='_compute_space_domain')
    num_persons = fields.Integer(required=True)
    slot = fields.Many2one(comodel_name='web.online.appointment.line',required=True)
    slot_domain = fields.Char(compute='_compute_slot_domain')
    partner = fields.Many2one(comodel_name='res.partner',required=True)
    comments = fields.Char()
    
    @api.depends('date')
    def _compute_space_domain(self):
        self.ensure_one()
        if self.date:
            start_date = self.date
            end_date = start_date + timedelta(days=1)
            Line = self.env['web.online.appointment.line']
            calendar_lines = Line.search([('start_datetime', '>=', start_date),
                                           ('end_datetime','<',end_date),
                                                 ('is_open','=',True)])
            self.space_domain = json.dumps([('id','in',calendar_lines.mapped('space').ids)])
        else:
            self.space_domain = json.dumps([])
    
    @api.depends('date','space','num_persons')   
    def _compute_slot_domain(self):
        self.ensure_one()
        if self.date and self.space and self.num_persons != 0:
            Appointment = self.env['web.online.appointment']
            date = Appointment.get_tz_date(datetime(self.date.year, self.date.month, self.date.day), self.env.context['tz'])
            slots = Appointment.get_time_slots(date.strftime("%d-%m-%Y"), self.num_persons, self.space.id)
            self.slot_domain = json.dumps([('id','in',slots.ids)])
        else:
            self.slot_domain = json.dumps([])
    
    def action_book(self):
        import sys;sys.path.append(r'/home/javier/eclipse/jee-2021/eclipse/plugins/org.python.pydev.core_10.1.4.202304151203/pysrc')
        import pydevd;pydevd.settrace('127.0.0.1',port=9999)
        line = self.slot
        start_date = line.start_datetime
        calendar_id = line.line_id
        if calendar_id.event_duration_minutes:
            stop_date = start_date + timedelta(minutes=int(calendar_id.event_duration_minutes))
        else:
            stop_date = calendar_id.get_last_time_in_date(start_date.date())
        management_user = self.env.ref('web_online_appointment_resource.appointment_manager_user').sudo()
        event = {
            'name': '%s %spax %s' % (self.partner.name.split(" ")[0],self.num_persons,self.space.name),
            'partner_ids': [(6, 0, [self.partner.id,management_user.partner_id.id])],
#            'duration': duration,
            'start': fields.Datetime.to_string(start_date),
            'stop': fields.Datetime.to_string(stop_date),
            'alarm_ids': [(6, 0, calendar_id.alarm_ids.ids)],
            'resource': self.space.id,
            'description': self.comments,
            'num_persons': self.num_persons,
            'location': self.space.name,
        }
        user = self.env.ref('web_online_appointment_resource.appointment_system_user').sudo()
        self.env['calendar.event'].sudo().with_user(user).create(event)
        domain = [('line_id', '=', calendar_id.id), ('start_datetime', '>=', fields.Datetime.to_string(start_date)), ('start_datetime', '<', fields.Datetime.to_string(stop_date))]
        lines = self.env['web.online.appointment.line'].sudo().search(domain)
        for line in lines:
            new_occupancy = line.occupancy + self.num_persons
            line.occupancy = new_occupancy
        
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',  }