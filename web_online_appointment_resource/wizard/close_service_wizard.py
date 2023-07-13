from odoo import models, fields, api
from datetime import timedelta
import pytz
import json

class CloseServiceWizard(models.TransientModel):
    _name='web.appointment.close.service.wizard'
    
    def _get_calendars(self):
        today = fields.Datetime.today().date()
        now = fields.Datetime.now()
        user = self.env['res.users'].browse(self.env.uid)
        tz_user = pytz.timezone(user.tz)
        now_time = pytz.utc.localize(now).astimezone(tz_user)
        now_float = now_time.hour + now_time.minute/60 + now_time.second/3600
        calendars = self.env['web.online.appointment'].search([
                ('start_date','<=',today),('start_time','<=',now_float),('end_time','>=',now_float)
            ]).filtered(lambda x: (x.start_date + timedelta(days=x.duration-1)) >= today)\
            .filtered(lambda x: today in {y.date() for y in x.calendar_line_ids.mapped('start_datetime')})
        return calendars
    
    name = fields.Char()
    calendars = fields.Many2many('web.online.appointment',default=_get_calendars)
    calendars_domain = fields.Char(compute='_compute_domain')
    
    @api.depends('name')
    def _compute_domain(self):
        calendars = self._get_calendars()
        for record in self:
            if calendars:
                record.calendars_domain = json.dumps([('id','in',calendars.ids)])
            else:
                record.calendars_domain = []

    def action_close_service(self):
#      buscar las web.online.appointment que con líneas hoy y que la hora actual esté entre la start de la primera línea
#      de hoy y la end de la última línea de hoy.
        min_time = fields.Datetime.today()
        max_time = min_time + timedelta(days=1)
        lines = self.env['web.online.appointment.line'].search([
                    ('line_id','in',self.calendars.ids),
                    ('start_datetime','>=',min_time),
                    ('start_datetime','<=',max_time)
            ])
        lines.is_open = False
        return  {
                    'type': 'ir.actions.client',
                    'tag': 'action_demo',
                    'params': {
                        'resources': lines.mapped('start_datetime'),
                    },
                    'target': 'new'
                }