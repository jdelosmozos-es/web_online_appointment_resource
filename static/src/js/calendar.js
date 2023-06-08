odoo.define('web_online_web.online.appointmentViewKanak', function (require) {
"use strict";
    var CalendarView = require('web.CalendarView');
    var viewRegistry = require('web.view_registry');
    var CalendarViewKanak = CalendarView.extend({
        get_color: function(key) {
                if (this.name = 'Exception Calendar')
                    if (this.color_map[key]) {
                        return this.color_map[key];
                    }
                var index = (((_.keys(this.color_map).length + 1) *
                    5) % 24) + 1;
                if (key == 'appointment') {
                    index = 'green';
                } else if (key == 'exception') {
                    index = 'red';
                }
                this.color_map[key] = index
                return index;
            },
    });
    viewRegistry.add('calendar', CalendarViewKanak);
    return CalendarViewKanak
});
