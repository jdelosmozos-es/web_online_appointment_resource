# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import pytz

TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

class WebOnlineAppointment(models.Model):
    _name = 'web.online.appointment'
    _description = 'Web Online Appointment'

    name = fields.Char(required=True)
    space = fields.Many2one(comodel_name='appointment.space', required=True)
    capacity = fields.Integer(related='space.capacity')
    minutes_slot = fields.Char("Slot in mins.", required=True)
    lunch_start = fields.Float("Lunch Start")
    lunch_end = fields.Float("Lunch End")
    start_date = fields.Date(string='Start Date', required=True, default=fields.Datetime.now)
    start_time = fields.Float("Start Time", required=True)
    end_time = fields.Float("End TIme", required=True)
    duration = fields.Integer('Duration in days', required=True)
    calendar_line_ids = fields.One2many('web.online.appointment.line', 'line_id', 'Calendar Lines')
    holiday_ids = fields.One2many('web.online.appointment.holidays', 'jt_calendar_id', 'Holidays')
    alarm_ids = fields.Many2many(
        'calendar.alarm', 'web_online_appointment_alarm_calendar_event_rel',
        string='Reminders', ondelete="restrict")
    weekoff_ids = fields.Many2many("web.online.appointment.weekoff", string="Weekoff Days")
    event_duration_minutes = fields.Integer('Event duration (minutes)', help="If not set the duration is all available")
    instructions = fields.Text()
    
    def get_last_time_in_date(self, date):
        dates_lines = self.calendar_line_ids.filtered(lambda x: x.start_datetime.date() == date)
        last_date_line = dates_lines.sorted(key=lambda x: x.end_datetime.time(),reverse=True)[0]
        return last_date_line.end_datetime + timedelta(minutes=int(self.minutes_slot))
        
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = dict(default or {})
        default.update({'calendar_line_ids': False, 'duration': 0})
        return super(WebOnlineAppointment, self).copy(default)
    
    @api.model
    def get_tz_date(self, date=None, timezone=None):
        to_zone = pytz.timezone(timezone)
        from_zone = pytz.timezone('UTC')
        return from_zone.localize(date).astimezone(to_zone)
    
    @api.model
    def get_utc_date(self, date=None, timezone=None):
        to_zone = pytz.timezone('UTC')
        from_zone = pytz.timezone(timezone)
        return from_zone.localize(date).astimezone(to_zone)
    
    @api.model
    def generate_calendar(self):
        user = self.env['res.users'].browse(self.env.uid)
        tz = pytz.timezone(user.tz)
        for appointment in self:
            start_date = datetime(
                                    year=appointment.start_date.year,
                                    month=appointment.start_date.month,
                                    day=appointment.start_date.day,
#                                    hour=0,
#                                    minute=0,
#                                    second=0,
#                                    tzinfo=tz
                                )
            start_date = tz.localize(start_date).astimezone(pytz.utc)
#            start_date = tz.normalize(start_date).astimezone(pytz.utc)
            start_minutes = float(appointment.start_time) * 60
            end_minutes = float(appointment.end_time) * 60
            min_slot = appointment.minutes_slot
            lunch_start_min = float(appointment.lunch_start) * 60
            lunch_end_min = float(appointment.lunch_end) * 60
            if lunch_start_min and lunch_end_min:
                appointment.get_exception_slots()
            start = start_date + timedelta(minutes=start_minutes)
            stop = start_date + timedelta(minutes=end_minutes)
            for days in range(appointment.duration):
                start = start_date + timedelta(minutes=start_minutes)
                stop = start_date + timedelta(minutes=end_minutes)
                while start <= stop:
                    t1 = start
                    if appointment.event_duration_minutes:
                        t2 = t1 + timedelta(minutes=int(min_slot))
                        duration = appointment.minutes_slot
                    else:
                        #Si no hay duración la reserva es para el servicio completo
                        t2 = stop
                        duration = False
                    lines = {
                        'line_id': appointment.id,
                        'duration': duration,
                        'start_datetime': fields.Datetime.to_string(t1),
                        'end_datetime': fields.Datetime.to_string(t2),
                        'space': appointment.space.id
                    }
                    already_line = self.env['web.online.appointment.line'].sudo().search([('start_datetime', '=', fields.Datetime.to_string(t1)), ('end_datetime', '=', fields.Datetime.to_string(t2)), ('line_id', '=', appointment.id)])
                    if not already_line:
                        if appointment.holiday_ids:
                            create_line = False
                            lst = []
                            for holiday in appointment.holiday_ids:
                                sdrange = [holiday.jt_start_date+timedelta(days=x) for x in range((holiday.jt_end_date-holiday.jt_start_date).days + 1)]
                                lst += sdrange
                            if t1.date() not in lst:
                                if appointment.weekoff_ids:
                                    weekoffdays = appointment.weekoff_ids.mapped('dayofweek')
                                    if not str(t1.date().weekday()) in weekoffdays:
                                        create_line = True
                                else:
                                    create_line = True
                            else:
                                create_line = False
                            if create_line:
                                self.env['web.online.appointment.line'].sudo().create(lines)
                        elif appointment.weekoff_ids:
                            weekoffdays = appointment.weekoff_ids.mapped('dayofweek')
                            if str(t1.date().weekday()) not in weekoffdays:
                                self.env['web.online.appointment.line'].sudo().create(lines)
                        else:
                            self.env['web.online.appointment.line'].sudo().create(lines)
#                    start = t2
                    start = t1 + timedelta(minutes=int(min_slot))
                if days == 0:
                    start_date = start_date + timedelta(days=days + 1)
                else:
                    start_date = start_date + timedelta(days=1)
                days = days + 1
        return True

    def get_exception_slots(self):
        start_date = datetime.strptime(self.start_date, '%Y-%m-%d')
        min_slot = self.minutes_slot
        lunch_start_min = float(self.lunch_start) * 60
        lunch_end_min = float(self.lunch_end) * 60
        ex_slots = []
        for appointment in self:
            for days in range(appointment.duration):
                if lunch_start_min and lunch_end_min:
                    ex_start = start_date + timedelta(minutes=lunch_start_min)
                    ex_stop = start_date + timedelta(minutes=lunch_end_min)
                    while ex_start < ex_stop:
                        ex_t1 = ex_start
                        ex_t2 = ex_t1 + timedelta(minutes=int(min_slot))
                        ex_slots.append(ex_t1)
                        ex_slots.append(ex_t2)
                        ex_start = ex_t2
                if days == 0:
                    start_date = start_date + timedelta(days=days + 1)
                else:
                    start_date = start_date + timedelta(days=1)
                days = days + 1
        return ex_slots

    @api.model
    def create(self, vals):
        appointment = super(WebOnlineAppointment, self).create(vals)
        appointment.generate_calendar()
        return appointment

    def write(self, values):
        appointment = super(WebOnlineAppointment, self).write(values)
        lst = ['minutes_slot', 'start_date', 'start_time', 'end_time', 'duration', 'holiday_ids', 'weekoff_ids']
        if any(key in values for key in lst):
            for rec in self:
                rec.calendar_line_ids.unlink()
                rec.generate_calendar()
        return appointment

    @api.model
    def get_time_slots(self, date, num_persons, space_id):
        str_date = str(date)
        sel_date = str_date.split("-")
        day = sel_date[0]
        month = sel_date[1]
        year = sel_date[2]
        end_date = datetime(int(year), int(month), int(day), 0,0,0)
        end_date = end_date + timedelta(days=1)

        Line = self.env['web.online.appointment.line']
        calendar_lines = Line.sudo().search([('start_datetime', '>=', datetime.now()),
                                             ('end_datetime','<',end_date),
                                             ('space','=',int(space_id)),
                                             ('is_open','=',True)])
        available_lines = Line
        for line in calendar_lines:
            event_duration_minutes = line.line_id.event_duration_minutes
            if event_duration_minutes:
                event_end_time = line.start_datetime + timedelta(minutes=event_duration_minutes)
            else:
                event_end_time = line.end_datetime
            event_lines = Line.sudo().search([
                                        ('start_datetime','>=', line.start_datetime),
                                        ('start_datetime','<=',event_end_time)
                                    ])
            if event_lines and min(event_lines.mapped('availability')) >= int(num_persons):
                available_lines |= line
        slots = Line
        for line in available_lines:
            start_datetime = fields.Datetime.to_string(line.start_datetime)
            date = line.line_id.get_tz_date(datetime.strptime(start_datetime, DEFAULT_SERVER_DATETIME_FORMAT), self.env.context['tz'])
            if int(date.day) == int(day) and int(date.month) == int(month) and int(date.year) == int(year):
                slots += line
        return slots
    
class WebOnlineAppointmentLine(models.Model):
    _name = 'web.online.appointment.line'
    _description = 'Web Online Appointment Line'

    line_id = fields.Many2one('web.online.appointment', 'Lines', ondelete='cascade')
    space = fields.Many2one(comodel_name="appointment.space")
    start_datetime = fields.Datetime()
    end_datetime = fields.Datetime()
    duration = fields.Float('Duration in mins')
    capacity = fields.Integer(related='space.capacity')
    occupancy = fields.Integer(readonly=True)
    availability = fields.Integer(compute='_compute_availability', store=True)
    is_open = fields.Boolean('Open', default=True)
    is_past = fields.Boolean('Past', compute='_compute_availability')
                            
    _sql_constraints = [
                            ('slot_uniq', 'unique (space,start_datetime)','There cannot be two slots at the same time for the same space.')
                        ]
    
    def name_get(self):
        result = []
        Appointment = self.env['web.online.appointment']
        for record in self:
            date = Appointment.get_tz_date(record.start_datetime, self.env.context['tz'])
            result.append((record.id, '%s - %s [%d]' % (date.time(), date.date(), record.availability)))
        return result
    
    @api.depends('occupancy')
    def _compute_availability(self):
        for record in self:
            if record.start_datetime < fields.Datetime.now():
                record.is_past = True
            else:
                record.is_past = False
            record.availability = record.capacity - record.occupancy

    @api.constrains('start_datetime', 'end_datetime')
    def _check_closing_date(self):
        for line in self:
            if line.start_datetime and line.end_datetime < line.start_datetime:
                line.duration = 0.0
                raise ValidationError(_('Ending datetime cannot be set before starting datetime.'))
            if line.start_datetime and line.end_datetime < line.start_datetime:
                line.duration = 0.0
                raise ValidationError(_('Ending date cannot be set before starting date.'))

    @api.onchange('start_datetime', 'end_datetime')
    def onchange_start_end_time(self):
        if self.start_datetime and self.end_datetime:
            if self.start_datetime < self.end_datetime:
                self.duration = self._get_duration()
            else:
                self.duration = 0.0
                raise ValidationError(_('Ending date cannot be set before starting date or equal to starting date.'))

#    @api.model
#    def create(self, vals):
#        # compute duration, if not given
#        if not vals.get('duration'):
#            vals['duration'] = self._get_duration(vals['start_datetime'], vals['end_datetime'])
#        return super(WebOnlineAppointmentLine, self).create(vals)

    @api.model
    def _get_duration(self):
        """ Get the duration value between the 2 given dates. """
        start = self.start_datetime
        stop = self.end_datetime
        if start and stop:
            diff = fields.Datetime.from_string(stop) - fields.Datetime.from_string(start)
            if diff:
                duration = (float(diff.days) * 24 + (float(diff.seconds) / 3600)) * 60.0
                return round(duration, 2)
            return 0.0


class WebOnlineAppointmentHolidays(models.Model):
    _name = 'web.online.appointment.holidays'
    _description = 'Web Online Appointment Holidays'

    name = fields.Char("Reason", required=True)
    jt_start_date = fields.Date("Start Date")
    jt_end_date = fields.Date("End Date")
    jt_calendar_id = fields.Many2one('web.online.appointment', 'Web Online Appointment', ondelete='cascade')


class WebOnlineAppointmentWeekoff(models.Model):
    _name = 'web.online.appointment.weekoff'
    _description = 'Web Online Appointment Weekoff'

    name = fields.Char(required=True)
    dayofweek = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')
        ], 'Day of Week', required=True, index=True, default='6')
