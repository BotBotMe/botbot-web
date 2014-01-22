//
// Subscribe form
//
$('#subscribe-form').submit(function (event) {
    var $form = $(this),
        $button = $form.find('button');
    event.preventDefault();
    $.post(this.action, {
        email: $('#id_email').val(),
        csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val()
    },
    function (data) {
        $button.attr('disabled', 'disabled');
        $button.text('Working');

        if (data.success) {
            if (document.location.hostname === 'botbot.me') {
                _gaq.push(['_trackEvent', 'Prelaunch', 'Signup']);
            }
            $('.failure, .request').hide();
            $form.removeClass('error');

            $('.success').show();


        } else {
            $form.addClass('shake animated error');

            $('.success').hide();
            $('.failure').show();

            $button.removeAttr('disabled');
            $button.text('Subscribe');
        }
    });
});