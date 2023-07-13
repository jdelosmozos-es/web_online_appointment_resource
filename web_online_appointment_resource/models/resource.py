from odoo import models, fields, api, _

class Space(models.Model):
    _name = "appointment.space"
    _inherit = ["resource.mixin", "image.mixin"]
    
    name = fields.Char("Space", related='resource_id.name', store=True, readonly=False)
    capacity = fields.Integer(required=True)
    note = fields.Text(
        'Description',
        help="Description of the space.")
    active = fields.Boolean('Active', related='resource_id.active', default=True, store=True, readonly=False)
    color = fields.Integer('Color')
    calendar_ids = fields.Many2many('web.online.appointment', string='Booking Calendar', compute='_compute_calendar_id')
    #TODO: reservas One2many
    
    def _compute_calendar_id(self):
        import sys;sys.path.append(r'/home/javier/eclipse/jee-2021/eclipse/plugins/org.python.pydev.core_10.1.4.202304151203/pysrc')
        import pydevd;pydevd.settrace('127.0.0.1',port=9999)
        for record in self:
            record.calendar_ids = record.env['web.online.appointment'].search([('space','=',record.id)])