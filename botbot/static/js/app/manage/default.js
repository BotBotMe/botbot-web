$(document).ready(function () {

    $('form#chatbot input[name^="cb-irc"]')
        .parent().show()
        .siblings('.errorlist').show();

    //Autocomplete
    $("#backbone-user-search").autocomplete({
        source: $("#backbone-user-search").data('url'),
        minLength: 2,
        select: function (event, ui) {
            event.preventDefault();
            var user = new $$.Models.User({
                'email': ui.item.label,
                'id': ui.item.value
            });
            if ($$.manager.user_view.collection.indexOf(user) === -1) {
                $$.manager.user_view.collection.add(user);
            }
            $('#backbone-user-search').val('');
        },
        focus: function (event, ui) { event.preventDefault(); }
    });

});
