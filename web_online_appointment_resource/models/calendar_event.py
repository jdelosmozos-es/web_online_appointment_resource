from odoo import fields, models, api


class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    resource = fields.Many2one(
        comodel_name="appointment.space",
        string="Space",
    )
    num_persons = fields.Integer('Num. persons')
    
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