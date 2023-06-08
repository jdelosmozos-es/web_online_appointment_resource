odoo.define('web_online_appointment_resource.appointment', function(require) {
    "use strict";

    // var Model = require('web.Model');
    var ajax = require('web.ajax');
    $(document).ready(function() {
        var $datePicker = $("div.date");
        var $datePicker = $("div");
        $("#done_button").hide();
        $('.date_time_set_customer').datepicker({
				minDate: moment().calendar(),
				locale : moment.locale(),
                startView: 0,
                dateFormat: 'yy-mm-dd',
                icon: {
                    next: 'glyphicon glyphicon-chevron-right',
                    previous: 'glyphicon glyphicon-chevron-left'
                }
            })
            .on('changeDate', function(e) {
                var date = $(this).datepicker('getDate');
                var day = e.date.getDate()
                var month = e.date.getMonth() + 1
                var year = e.date.getFullYear()
                var selectedDate = day + '-' + month + '-' + year
                var calendar_id = $('#calendar_id').val();
                var num_persons = $('#num_persons').val();
                $("#done_button").hide();
                $("#selectedTime1").text('');
                $("#selectedDate1").text(selectedDate);
                ajax.jsonRpc('/calendar/timeslot', 'call', {
                    calendar_id: calendar_id,
                    selectedDate: selectedDate,
                    num_persons: num_persons
                    }).then(function (event_list) {
                        var HTML = '';
                        for (var i in event_list['slots']) {
                            HTML += '<span class="js-time-slot" id="js_slot">' + event_list['slots'][i] + '</span>';
                        }
                        $("#time").html(HTML);
                        $('.datepicker.datepicker-dropdown.dropdown-menu').remove();

                        $("#time .js-time-slot").click(function() {
                            $("#time .js-time-slot").removeClass("js-time-slot selected");
                            $(this).addClass('js-time-slot selected');
                            $("#done_button").show();
                            $("#selectedTime1").text($(this).text());
                            $("#selectedDate1").text(selectedDate);
                            $("#selectedTime").val($(this).text());
                            $("#selectedDate").val(selectedDate);
                        });
                    });
            });
    });

});
