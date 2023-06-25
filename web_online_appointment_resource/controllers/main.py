# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from odoo import fields, http
from odoo.http import request
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class MemberAppointment(http.Controller):

    @http.route('/appointment', auth="public", website=True)
    def show_persons_input(self, **post):
        availabilities = request.env['web.online.appointment.line'].search([]).sorted(lambda x:x.availability,reverse=True)
        if availabilities:
            max_capacity = availabilities[0].availability
        else:
            pass
            # decir que no hay fechas disponibles
        return request.render('web_online_appointment_resource.appointment_intro_persons', {'max_capacity': max_capacity})
            
    @http.route('/appointment/member', auth="public", website=True)
    def team_list(self, **post):
        if not post.get('max_capacity') or not post.get('num_persons'):
            return self.show_persons_input()
            #TODO : debería monstrarse algún mensaje
        max_capacity = int(post.get('max_capacity'))
        num_persons = int(post.get('num_persons'))
        if num_persons > max_capacity:
            return self.show_persons_input()
        lines = request.env['web.online.appointment.line'].sudo().search([('availability', '>', num_persons)])
        spaces = lines.mapped('space')
        return request.render('web_online_appointment_resource.appointment_select_space', {'spaces': spaces, 'num_persons': num_persons})

    @http.route('/appointment/member/<int:space_id>/<int:num_persons>', auth="public", website=True)
    def calendar(self, space_id=None, day=None, calendar_id=None, selectedDate=None, num_persons=None, **post):
#        calendars = request.env['web.online.appointment'].sudo().browse(int(calendar_id))
        today = datetime.now()
        cal_lines = request.env['web.online.appointment.line'].sudo().search([('space', '=', space_id),
                                                                              ('start_datetime','>',today),
                                                                              ('availability','>',int(num_persons))])
        today.strftime("%B")
        month_year = '%s  %s' % (today.strftime("%B"), today.year)
#        minutes_slot = calendar.minutes_slot
        days = []
        for c in cal_lines:
            s_date = c.start_datetime
            if s_date.day not in days:
                days.append(s_date.day)
        #FIXME: values no se utiliza para nada en la página pero sí en el js, revisar y eliminar lo que no se use.
        values = {
#            'cal_lines': cal_lines,
            'days': days,
#            'calendar_id': calendar.id,
            'space_id': space_id,
            'month_year': month_year,
#            'minutes_slot': minutes_slot,
            'num_persons': num_persons
        }
        return request.render('web_online_appointment_resource.appointment_member_calendar', values)

    @http.route('/appointment/book', auth="public", website=True)
    def book_time(self, **post):
        if post.get('selectedDate') and post.get('selectedTime'):
            date_time = '%s %s' % (post.get('selectedDate'), post.get('selectedTime'))
            start_date = datetime.strptime(date_time, '%d-%m-%Y %H:%M')
#            minutes_slot = post.get('minutes_slot')
            space = request.env['appointment.space'].sudo().browse(int(post.get('space_id')))
#            calendar_id = post.get('calendar_id')
#            stop_date = start_date + timedelta(minutes=int(minutes_slot))
            values = ({
                'booking_time': '%s | %s %s , %s' % (post.get('selectedTime'), start_date.strftime('%B'), start_date.day, start_date.year),
                'start_datetime': fields.Datetime.to_string(start_date),
                'start': fields.Datetime.to_string(start_date),
#                'stop': fields.Datetime.to_string(stop_date),
#                'duration': round((float(minutes_slot) / 60.0), 2),
#                'calendar_id': int(calendar_id),
#                'minutes_slot': int(post.get('minutes_slot')),
                'space': space,
                'num_persons': post.get('num_persons'),
                'phone': False,
                'name': False,
                'email': False
            })
            if request.uid != 4: #TODO: Comprobar bien que es el Public User
                partner = request.env['res.users'].browse(request.uid).partner_id
                values['name'] = partner.name
                if partner.email:
                    values['email'] = partner.email
                if partner.phone:
                    values['phone'] = partner.phone
                elif partner.mobile:
                    values['phone'] = partner.mobile
            return request.render('web_online_appointment_resource.appointment_book', values)

    @http.route('/appointment/book/confirm', auth="public", website=True)
    def confirm_booking(self, **post):
        Partner = request.env['res.partner'].sudo()
        Space = request.env['appointment.space'].sudo()
        partner = Partner.search([('email', '=', post.get('email'))], limit=1)
        start_date = datetime.strptime(post.get('start_datetime'), '%Y-%m-%d %H:%M:%S')
        utc_date = request.env['web.online.appointment'].get_utc_date(start_date, request.context['tz'])
        line = request.env['web.online.appointment.line'].search([('start_datetime','=',utc_date),('space','=',int(post.get('space_id')))])
        space = Space.browse(int(post.get('space_id')))
        calendar_id = line.line_id
        if calendar_id.event_duration_minutes:
            stop_date = utc_date + timedelta(minutes=int(calendar_id.event_duration_minutes))
        else:
            stop_date = line.end_datetime
        post['space'] = space
        post['comments'] = post.get('comments')
        if not partner:
            partner = Partner.create({
#                    'name': "%s %s" % (post.get('first_name'), post.get('last_name') and post.get('last_name') or ''),
                'name': post.get('name'),
                'email': post.get('email'),
                'phone': post.get('phone'),
                'tz': post.get('timezone'),
            })
        event = {
#                'name': '%s-%s' % (post.get('first_name'), post.get('start_datetime')),
            'name': '%s %s %spax %s' % (post.get('name').split(" ")[0], post.get('start_datetime'),post.get('num_persons'),space.name),
            'partner_ids': [(6, 0, [partner.id])],
            # 'start_datetime': fields.Datetime.to_string(utc_date),
#            'duration': duration,
            'start': fields.Datetime.to_string(utc_date),
            'stop': fields.Datetime.to_string(stop_date),
            'alarm_ids': [(6, 0, calendar_id.alarm_ids.ids)],
            'resource': space.id,
            'description': post.get('comments'),
            'num_persons': post.get('num_persons')
        }
        #TODO: ¿no_mail? si es false envía email de confirmación
        user = request.env.ref('web_online_appointment_resource.appointment_system_user').sudo()
        #app = request.env['calendar.event'].sudo().with_context({'no_mail': True}).with_user(user).create(event)
        app = request.env['calendar.event'].sudo().with_user(user).create(event)
        #TODO: el state podría ser otro y acepted cuando esté confirmado.
        # app.attendee_ids.write({'state': 'accepted'})
        # domain = [('line_id', '=', int(post.get('calendar_id'))), ('start_datetime', '=', fields.Datetime.to_string(utc_date)), ('end_datetime', '=', fields.Datetime.to_string(stop_date))]
        domain = [('line_id', '=', calendar_id.id), ('start_datetime', '>=', fields.Datetime.to_string(utc_date)), ('start_datetime', '<', fields.Datetime.to_string(stop_date))]
        lines = request.env['web.online.appointment.line'].sudo().search(domain)
        for line in lines:
            #if str(line.start_datetime) == fields.Datetime.to_string(utc_date) and str(line.end_datetime) == fields.Datetime.to_string(stop_date):
            #    line.unlink()
            new_occupancy = line.occupancy + int(post.get('num_persons'))
            line.occupancy = new_occupancy
        post['event_id'] = app
        # mail_ids = []
        # Mail = request.env['mail.mail'].sudo()
        # template = request.env.ref('jupical_appointment_advanced.jupical_calendar_booking')
        # for attendee in app.attendee_ids:
        #     Mail.browse(template.sudo().send_mail(attendee.id)).send()
        # post['date'] = date_appointment
        return request.render('web_online_appointment_resource.appointment_thankyou', post)

    @http.route('/calendar/timeslot', type='json', auth='public')
    def get_time_slots(self, selectedDate, num_persons):
        str_date = str(selectedDate)
        sel_date = str_date.split("-")
        day = sel_date[0]
        month = sel_date[1]
        year = sel_date[2]
        end_date = datetime(int(year), int(month), int(day) + 1, 0,0,0)

        Line = request.env['web.online.appointment.line']
        calendar_lines = Line.sudo().search([('start_datetime', '>=', datetime.now()),('end_datetime','<',end_date)])
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
            if event_lines and min(event_lines.mapped('availability')) > int(num_persons):
                available_lines |= line
        slots = []
        for line in available_lines:
            start_datetime = fields.Datetime.to_string(line.start_datetime)
            date = line.line_id.get_tz_date(datetime.strptime(start_datetime, DEFAULT_SERVER_DATETIME_FORMAT), request.context['tz'])
            if int(date.day) == int(day) and int(date.month) == int(month) and int(date.year) == int(year):
                slots.append(str(date.time())[0:5])
        mylst = [s.replace(':', '') for s in slots]
        sorted_slots = [my_hash[:2] + ':' + my_hash[2:] for my_hash in sorted(mylst, key=int)]
        return {'slots': sorted_slots}
