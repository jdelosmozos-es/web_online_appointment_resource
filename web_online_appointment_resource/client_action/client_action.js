odoo.define('web_online_appointment_resource.action_demo', function (require) {
   'use strict';
   var AbstractAction = require('web.AbstractAction');
   var core = require('web.core');
   var calendar = require('calendar.CalendarRenderer')
   var ActionDemo = AbstractAction.extend({
       events: {
       },
       init: function(parent, action) {
           this.spaces = action.params.resources;
       },
       start: function() {
		   calendar.show()
           alert(this.spaces);
       },
   });
   core.action_registry.add("action_demo", ActionDemo);
   return ActionDemo;
});