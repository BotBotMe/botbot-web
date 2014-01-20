$$.Models.User = Backbone.Model.extend({});

$$.Collections.Users = Backbone.Collection.extend({
    model: $$.Models.User
});

$$.Views.UserListView = Backbone.View.extend({
    template_source: "#user-list-template",
    input_source: "#user-input-template",

    events: {
        'click .delete-user': 'deleteUser'
    },

    initialize: function (options) {
        _.bindAll(this, "render", "deleteUser");

        this.template = Handlebars.compile($(this.template_source).html());
        this.input = Handlebars.compile($(this.input_source).html());

        this.collection.on("add remove", this.render, this);
        this.render();
    },

    render: function () {
        // Load the compiled HTML into the Backbone "el"
        this.$('#backbone-user-list').html(
            this.template({'users': this.collection.toJSON()})
        );
        this.$('#input-el').html(this.input({'users': this.collection.toJSON()}));
    },

    deleteUser: function (event) {
        event.preventDefault();
        this.collection.remove($(event.target).data('id'));
    }

});


$(document).ready(function () {

    $$.manager = (function () {

        var initial_users = new $$.Collections.Users($.parseJSON($('#initial-users').html()));

        return {
            user_view: new $$.Views.UserListView({
                el: $("#backbone-users"),
                collection: initial_users
            })
        };

    }());

});
