$$.Templates = {
    DateHeader: _.template(
        '<h3 id="date-<%= flatDate %>" data-date="<%= flatDate %>"><span><%= dateString %></span></h3>'
    ),
    ImagePreview: _.template(
        '<a class="preview-img" href="<%= link %>"><img src="<%= link %>" height="200" /></a>'
    ),
    ImageToggle: _.template(
        '<a href="<%= link %>" class="toggle-preview" title="Preview"><i class="icon-zoom-in icon-large"></i></a>'
    )
};
$$.Cache = Backbone.Model.extend({
    initialize: function (options) {
        _.bindAll(this, 'refetch', 'prepPage');
        this.url = options.url;
        this.direction = options.direction;
        this.$el = options.$el;
        this.pageHeader = this.direction === 'next' ? 'X-NextPage' : 'X-PrevPage';
        if (this.url) {
            this.isFinished = false;
            this.fetch();
        // If a timezone is missing on first page load, we know we need to adjust
        } else {
            this.adjustTimezone = options.adjustTimezone;
        }
    },
    fetch: function () {
        // Load another page into the cache
        if (this.url) {
            this.isLoading = true;
            $.ajax({
                url: this.url,
                success: _.bind(function (data, textStatus, jqXHR) {
                    var serverTimezone = jqXHR.getResponseHeader('X-Timezone');
                    this.url = jqXHR.getResponseHeader(this.pageHeader);
                    if (this.url === "" || this.url === null) {
                        this.isLoading = false;
                        this.isFinished = true;
                    } else {
                        if ($$.clientTimezone !== serverTimezone) {
                            this.adjustTimezone = true;
                        }
                        this.prepPage(data);
                        this.isLoading = false;
                        this.trigger('loaded', this);
                    }
                }, this),
                statusCode: {
                    404: _.bind(function () {
                        this.isLoading = false;
                        this.isFinished = true;
                    }, this)
                },
                dataType: 'html'
            });
        } else {
            // Nothing to load, so we can still trigger loaded.
            this.trigger('loaded', this);
        }
    },
    isEmpty: function () {
        return this.$el.children('li').length === 0;
    },

    prepPage: function (html) {
        log('Cache:prepPage');
        var prevDate,
            self = this;
        if (html) {
            this.$el.html(html);
        }
        if (this.adjustTimezone) {
            this.$el.find('h3').remove();
            $.each(this.$el.children('li'), function (idx, el) {
                prevDate = $$.changeLineTimezone($(el), prevDate);
            });
        }
        if ($$.searchTerm) {
            this.$el.find('.message').highlight($$.searchTerm);
        }
        $$.imagePreviews(this.$el);

        // check timezone again on next fetch
        this.adjustTimezone = false;
    },
    refetch: function () {
        log('Cache:reFetch', this.url);
        this.$el.html('');
        this.fetch();
    }
});


$$.Views.LogViewer = Backbone.View.extend({
    $logEl: $('#Log'),

    events: {
        'click .toggle-preview': 'toggleImagePreview',
        'click .moment' : 'messageView'
    },

    initialize: function (options) {
        log('LogViewer:initialize');
        _.bindAll(this, "scrollLoad", "pageLoad",
                        "createDateHeaderWaypoints",
                        "setDateHeader", "checkPageSplit",
                        "insertCache", "highlight",
                        "messageView");
        $$.on('date:change', this.setDateHeader);

        $(window).bind('hashchange', this.highlight)

        this.current = options.current;
        this.eventSourceUrl = options.source;
        this.newestFirst = options.newestFirst;

        // initialize lines already in the DOM
        new $$.Cache({
            $el: this.$logEl,
            adjustTimezone: options.adjustTimezone
        }).prepPage();

        // Prep caches
        this.prevCache = new $$.Cache({
            url: options.prevPage,
            direction: 'prev',
            $el: $('#Log-Prep-Prev')
        });
        this.nextCache = new $$.Cache({
            url: options.nextPage,
            direction: 'next',
            $el: $('#Log-Prep-Next')
        });

        this.highlight()
        this.createDateHeaderWaypoints();
        // scroll to the bottom of the page if these are current logs
        if (this.current) {
            $$.trigger('at-bottom');
            this.setupEventSource();
            $('html, body').animate({
                scrollTop: $(document).height() - $(window).height()
            }, 0);
        }

        window.onscroll = this.scrollLoad;
        // make sure we add more items depending on initial scroll
        this.scrollLoad();
    },

    messageView: function(event) {
        // Check to see if we are still on the same path
        var href = $(event.target).parent().attr('href');
        if (window.location.href.indexOf(href) > 0) {
            this.highlight();
            return false;
        }
    },

    highlight: function(event) {
        this.$logEl.find('.highlight').removeClass('highlight');
        var highlighted = this.$logEl.find(window.location.hash);
        if (highlighted.length > 0) {
            highlighted.addClass('highlight')

            // move to middle of element
            $('html, body').animate({
                scrollTop: highlighted.offset().top + highlighted.height() - this.$el.offset().top - ($(window).height() - this.$el.offset().top) / 2
            }, 0);
        }
    },

    toggleImagePreview: function (event) {
        var href = event.currentTarget.href,
            $target = $(event.currentTarget),
            $message = $target.parents('.message'),
            $imgEl = $target.data('preview');

        event.preventDefault();
        if ($imgEl) {
            $imgEl.remove();
            $target.data('preview', null);
            $target.addClass('expand').removeClass('collapse');
            $target.find('.icon-zoom-out').removeClass('icon-zoom-out').addClass('icon-zoom-in');
        } else {
            $imgEl = $message.append($$.Templates.ImagePreview({link: href})).find('.preview-img');
            $target.data('preview', $imgEl);
            $target.addClass('collapse').removeClass('expand');
            $target.find('.icon-zoom-in').removeClass('icon-zoom-in').addClass('icon-zoom-out');
        }
    },

    setupEventSource: function () {
        log('LogViewer:setupEventSource');
        var self = this;
        $$.trigger('at-bottom');
        // only do this once
        if (this.source) {
            return;
        }
        this.source = new EventSource(this.eventSourceUrl);
        log('Creating event source'); 
        this.source.addEventListener('log', function (e) {
            log('received'); 
            log(e);
            log(this);
            var $el = $(e.data),
                $last = self.$logEl.find('li:last'),
                prevDate = moment($last.find('time').attr('datetime'));
            $el.each(function (idx, el) {
                prevDate = $$.changeLineTimezone($(el), prevDate);
            });
            log('mid');
            self.checkPageSplit($last, $el.first());
            $$.imagePreviews($el);
            self.$logEl.append($el);
            log('end');
            if ($$.isAtBottom()) {
                // if user is within 50px of the bottom, we'll auto-scroll on new messages
                $('html, body').animate({
                    scrollTop: $(document).height() - $(window).height()
                }, 50);
            }
        }, false);
        /*
        this.source.addEventListener('open', function (e) {
            // Connection was opened.
        }, false);

        this.source.addEventListener('error', function (e) {
            if (e.readyState === EventSource.CLOSED) {
                // Connection was closed.
            }
        }, false);
        */
    },

    checkPageSplit: function ($first, $second) {
        // de-dupe nick and check if date header is needed between pages
        var firstDate, secondDate,
            dupeNicks = $first.data('nick') === $second.data('nick'),
            dupeMsgType = $first.data('type') === $second.data('type') &&  $first.data('type') === 'message';
        if (dupeNicks && dupeMsgType) {
            $second.find('.actor').hide();
        }
        firstDate = moment($first.find('time').attr('datetime'));
        secondDate = moment($second.find('time').attr('datetime'));
        $$.checkForDateHeader($second, secondDate, firstDate);
    },

    createDateHeaderWaypoints: function () {
        log('LogViewer:createDateHeader');
        var $dateHeaders = this.$logEl.find('h3');
        if ($dateHeaders.length) {
            $dateHeaders.waypoint(function (event, direction) {
                // Trigger a date change based on the log immediately before
                // or after (depending on direction) we see a date header
                var date,
                    $log;
                if (direction === 'down') {
                    $log = $(event.currentTarget).next();
                } else {
                    $log = $(event.currentTarget).prev();
                }
                $$.trigger('date:change', moment($log.find('time').attr('datetime')));
            }, {
                offset: $('#Log-Container').offset().top + $('#Log h3').height()
            });
        } else {
            // if there aren't any headers, use the first log item
            $$.trigger('date:change', moment($('#Log time:first').attr('datetime')));
        }
    },

    setDateHeader: function (date) {
        log('LogViewer:setDateHeader');
        $('#Log-Header .date').text(date.format('MMMM Do YYYY'));
    },

    scrollLoad: function () {
        //log('LogViewer:scrollLoad', window.pageYOffset);
        var cache,
            scrollMaxY = document.documentElement.scrollHeight - document.documentElement.clientHeight;

        if (window.scrollY > 350 && window.scrollY < (scrollMaxY - 350)) {
            // do nothing (most common)
            return;
        } else if (window.scrollY < 50) {
            // scroll top
            cache = this.prevCache;
        } else if (window.scrollY > (scrollMaxY - 50)) {
            // scroll bottom
            cache = this.nextCache;
        }
        if (cache) {
            this.$el.addClass('loading-' + cache.direction);
            this.pageLoad(cache);
        }
    },

    pageLoad: function (cache) {
        log('LogViewer:pageLoad');
        // only wait for load once per AJAX call
        if (cache.isLoading) {
            if (!cache.hasListener) {
                cache.hasListener = true;
                cache.on('loaded', this.pageLoad);
            }
            return;
        }
        if (cache.isFinished) {
            this.$el.removeClass('loading-' + cache.direction);
            if (cache.direction === 'next') {
                this.setupEventSource();
            }
            return;
        }
        cache.hasListener = false;
        cache.off('loaded', this.pageLoad);
        this.insertCache(cache);
        $.waypoints('refresh');
        this.createDateHeaderWaypoints();
        this.$el.removeClass('loading-' + cache.direction);
    },

    insertCache: function (cache) {
        // Load element into DOM. Logic to handle prepend or append.
        // Catch anything that needs to happen across pages
        // Finally, refill the cache
        log('LogViewer:Insert', cache.direction);
        var height;
        if (cache.direction === 'prev') {
            // if there isn't already a date header at the top
            // see if we need to add one
            if (this.$logEl.children()[0].nodeName !== 'H3') {
                this.checkPageSplit(cache.$el.find('li:last'),
                                    this.$logEl.find('li:first'));
            }
            // dump prep into real log and scroll back to where we were
            cache.$el.width(this.$logEl.width());
            height = cache.$el.height();
            cache.$el.children().prependTo(this.$logEl);
            window.scrollBy(0, height);
        } else {
            this.checkPageSplit(this.$logEl.find('li:last'),
                                cache.$el.find('li:first'));
            cache.$el.children().appendTo(this.$logEl);
        }
        cache.refetch();
    }
});

$$.Views.TimezoneFormView = Backbone.View.extend({
    /* Submit guessed timezone if we haven't already */
    initialize: function (options) {
        var $tzField = this.$('#id_timezone');
        if (!$tzField.val()) {
            $tzField.val($$.clientTimezone);
            $.ajax({
                url: options.el.attr('action'),
                type: options.el.attr('method'),
                data: options.el.serialize()
            });
        }
    }
});

$$.Views.TimelineView = Backbone.View.extend({
    events: {
        'click li.year>a': 'toggleYearVisibility',
        'click a.jump-date': 'loadAndJumpToMonth',
        'click li.older>a': 'showAllYears'
    },

    initialize: function (options) {
        _.bindAll(this, 'setActive', 'showAllYears');
        this.isCurrent = options.isCurrent;
        $$.on('date:change', this.setActive);
        $$.on('at-bottom', this.setActive);
        this.hideOlderYears();
        // build up a list of all the links in navigation
        // we use this to determine which one is active
        this.links = _.map($('a.jump-date'), function (el, idx) {
            // while we're looping over the links, let's add the timezone data
            var $el = $(el);
            if ($$.clientTimezone && !$el.hasClass('current')) {
                $el.attr('href', $el.attr('href') + '?tz=' + $$.clientTimezone);
            }
            return {
                date: parseFloat($el.data('date')),
                $el: $el
            };
        });
        this.links = _.sortBy(this.links, function (obj) {
            return obj.date;
        });
    },

    hideOlderYears: function () {
        var years = this.$('li.year').length;
        this.$('li.year ul:last').show();
        if (years > 3) {
            this.$('li.year:lt(' + (years - 3) + ')').hide();
        }
    },

    showAllYears: function (event) {
        event.preventDefault();
        this.$('li.year').show();
        this.$('li.older').hide();
    },

    toggleYearVisibility: function (event) {
        event.preventDefault();
        this.$('ul.month-list:visible').slideUp('fast');
        $(event.currentTarget).siblings('ul.month-list').slideToggle('fast');
    },

    loadAndJumpToMonth: function (event) {
        var id = '#date-' + $(event.currentTarget).data('date');
        if ($(id).length) {
            return true;
        } else {
            log("Need to fetch " + id);
        }
    },

    setActive: function (date) {
        // given a moment.js date, determine which
        // link should be set to active
        var idxPast,
            $activateEl,
            flatDate;
        if (!date) {
            this.isCurrent = true;
        } else if (!$$.isAtBottom()) {
            this.isCurrent = false;
        }
        if (!this.isCurrent) {
            flatDate = parseInt(date.format("YYYYMMDD"), 10);
            // this will stop 1 item past the link that should be active
            _.find(this.links, function (link, idx) {
                idxPast = idx;
                return link.date > flatDate;
            });
            // set the new item as active and make it visible if it isn't
            $activateEl = this.links[idxPast - 1].$el.parent();
        } else {
            $activateEl = this.$('.current').parent();
        }
        this.$('li.active').removeClass('active');
        if (!$activateEl.is(':visible')) {
            $activateEl.parent().slideDown();
        }
        $activateEl.addClass('active');
    }
});

$$.isAtBottom = function () {
    return $(window).scrollTop() + $(window).height() > $(document).height() - 50;
};

$$.changeLineTimezone = function ($el, prevDate) {
    // adjust tz for an individual line
    var $time = $el.find('time'),
        thisDate = moment($time.attr('datetime'));
    $time.html(thisDate.format("h:mm a"));
    $$.checkForDateHeader($el, thisDate, prevDate);
    return thisDate;
};

$$.checkForDateHeader = function ($el, thisDate, prevDate) {
    // adds date headers if date changed
    if (prevDate && (prevDate.date() !== thisDate.date())) {
        log("Adding header for ", thisDate.format('YYYYMMDD'));
        $el.before($$.Templates.DateHeader({
            flatDate: thisDate.format('YYYYMMDD'),
            dateString: thisDate.format('MMMM Do, YYYY')
        }));
    }
};

$$.imagePreviews = function ($el) {
    // sets up toggler for images
    $el.find('a.image').each(function (idx, el) {
        $(el).after('&nbsp;' + $$.Templates.ImageToggle({link: el.href}));
    });
};

$(document).ready(function () {
    var serverSideTz = $('#Log').data('timezone'),
        $timeline = $('.timeline-navigation'),
        $tzForm = $('#Timezone'),
        isCurrent = $('#Log').data('current') === 'True';
    $$.clientTimezone = jstz.determine().name();
    $$.searchTerm = $('#Log').data('search-term');
    if ($tzForm.length) {
        new $$.Views.TimezoneFormView({
            el: $tzForm
        });
    }
    if ($timeline.length) {
        new $$.Views.TimelineView({
            el: $timeline,
            isCurrent: isCurrent
        });
    }
    $$.logs = (function () {
        return {
            view: new $$.Views.LogViewer({
                el: $("#Log-Container article"),
                source: $('#Log').data('source'),
                prevPage: $('#Log').data('previous'),
                nextPage: $('#Log').data('next'),
                current: isCurrent,
                newestFirst: $('#Log').data('order') === 'reversed',
                adjustTimezone: !serverSideTz
            })
        };
    }());

    $('.nav-toggle').click(function (event) {
        event.preventDefault();
        $('#Log-Nav').toggle();
    });
});
