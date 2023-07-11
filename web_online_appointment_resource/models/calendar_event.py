from odoo import fields, models, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime, timedelta

class CalendarEvent(models.Model):
    _inherit = "calendar.event"
    
    STATE_SELECTION = [
        ('needsAction', 'Needs Action'),
        ('tentative', 'Uncertain'),
        ('declined', 'Declined'),
        ('accepted', 'Accepted'),
    ]

    resource = fields.Many2one(
        comodel_name="appointment.space",
        string="Space",
    )
    num_persons = fields.Integer('Num. persons')
    state = fields.Selection(STATE_SELECTION, string='Status', compute='_compute_state')
    
    @api.depends('attendee_ids')
    def _compute_state(self):
        management_user = self.env.ref('web_online_appointment_resource.appointment_manager_user') #.sudo()
        attendee_id = self.attendee_ids.filtered(lambda x: x.partner_id.id == management_user.partner_id.id)
        if attendee_id:
            self.state = attendee_id.state
        else:
            self.state = False
             
    def change_attendee_status(self, status, recurrence_update_setting):
        super(CalendarEvent, self).change_attendee_status(status, recurrence_update_setting)
        changer = self.attendee_ids.filtered(lambda x: x.partner_id == self.env.user.partner_id)
        mail_template = self.env.ref('web_online_appointment_resource.calendar_template_change_attendee_status', raise_if_not_found=False)
        (self.attendee_ids - changer)._send_mail_to_attendees(mail_template, force_send=False)
    
    def unlink(self):
        for record in self:
            if not 'resource' in record:
                continue
            if not 'calendar_id' in record.resource:
                continue
            if not record.resource.calendar_id:
                continue
            booking_calendar = record.resource.calendar_id
            domain = [('line_id', '=', booking_calendar.id), ('start_datetime', '>=', self.start), ('start_datetime', '<',self.stop)]
            lines = self.env['web.online.appointment.line'].search(domain)
            for line in lines:
                new_occupancy = line.occupancy - self.num_persons
                line.occupancy = new_occupancy
        return super(CalendarEvent, self).unlink()