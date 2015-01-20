$$.Views.Glob = Backbone.View.extend({
    $globEl: $('#Glob'),

    initialize: function (options) {
        log('Glob:initialize');
        this.eventSourceUrl = options.source;
        this.setupEventSource();
    },

    setupEventSource: function () {
        log('Glob:setupEventSource');
        var self = this;
        if (this.source) {
            return;
        }
        this.source = new EventSource(this.eventSourceUrl);
        log('Creating event source');
        this.source.addEventListener('loc', function (e) {
            //log('received');
            //log(e);
            //log(this);
            //log('end');

            log(JSON.parse(e.data))

        }, false);
    }
});

$(document).ready(function () {
    new $$.Views.Glob({
        el: $('#Glob'),
        source: 'http://localhost:3000/push/glob'
    })
})
