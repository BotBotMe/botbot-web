import json
import datetime
from urllib import urlencode

from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import Http404
from django.utils.decorators import method_decorator
from django.utils.timezone import get_current_timezone_name
from django.views.generic import View, ListView, TemplateView, RedirectView
from django.views.decorators.csrf import csrf_exempt
from django_sse import redisqueue
from django.conf import settings
import pytz

from botbot.apps.accounts import forms as accounts_forms
from botbot.apps.bots.utils import reverse_channel
from botbot.apps.bots.views import ChannelMixin
from botbot.apps.logs.utils import datetime_to_date
from . import forms, models

PAGINATE_BY = 150

class Help(ChannelMixin, TemplateView):
    """
    Help page for a channel.
    """
    template_name = 'logs/help.html'

class LogDateMixin(object):

    def _kwargs_with_date(self, date):
        kwargs = self.kwargs.copy()
        kwargs.update({
            'year' : date.year,
            'month' : date.month,
            'day' : date.day
        })
        return kwargs

    def _get_previous_date(self):
        """
        Find the previous day, that has content.
        """
        qs = super(LogDateMixin, self).get_queryset().filter(timestamp__lt=self.date)
        if qs.count() > 1:
            return datetime_to_date(qs[0].timestamp)

    def _get_next_date(self):
        """
        Find the previous day, that has content.
        """
        qs = super(LogDateMixin, self).get_queryset().filter(timestamp__gte=datetime.timedelta(days=1) + self.date).order_by('timestamp')
        if qs.count() > 1:
            return datetime_to_date(qs[0].timestamp)

    def _date_query_set(self, date):
        qs = super(LogDateMixin, self).get_queryset()
        return qs.filter(timestamp__gte=date,
            timestamp__lt=date + datetime.timedelta(days=1))


class LogViewer(ChannelMixin, View):
    context_object_name = "message_list"
    newest_first = False
    show_timeline = True
    show_first_header = False   # Display date header above first line

    def dispatch(self, request, *args, **kwargs):
        self.form = forms.SearchForm(request.GET)
        self.page_base_url = request.path
        self.timezone = get_current_timezone_name()
        if request.is_ajax():
            self.show_timeline = False
            self.template_name = 'logs/log_display.html'
        return super(LogViewer, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.channel.filtered_logs()

    def get_context_data(self, **kwargs):
        # message to highlight
        kwargs.update({'highlight_pk': getattr(self, 'highlight', -1)})
        if self.show_timeline:
            kwargs.update(self._timeline_context())

        kwargs["size"] = self.channel.current_size()
        kwargs["big"] = (kwargs["size"] >= settings.BIG_CHANNEL)

        if not self.request.is_ajax():
            kwargs.update({
                'is_current': getattr(self, 'is_current', False),
                'search_form': self.form,
                'tz_form': accounts_forms.TimezoneForm(self.request),
                'show_first_header': self.show_first_header,
                'newest_first': self.newest_first,
            })
        context = super(LogViewer, self).get_context_data(**kwargs)
        context.update({
            'prev_page': self.prev_page,
            'next_page': self.next_page,
        })

        return context

    def _timeline_context(self):
        """Context (template) vars needed for timeline display.
        """

        timeline = self.channel.get_months_active()
        if not timeline:
            return {}

        today = datetime.date.today()
        last_monday = today - datetime.timedelta(days=today.weekday())
        last_week = last_monday - datetime.timedelta(days=7)

        # the last month in the timeline needs special treatment so it
        # doesn't get ordered ahead of the last/current weeks
        last_month = timeline[timeline.keyOrder[-1]].pop()
        if last_month >= last_week:
            last_month_adjusted = (last_week -
                                    datetime.timedelta(days=1))
        elif last_month >= last_monday:
            last_month_adjusted = (last_monday -
                                    datetime.timedelta(days=1))
        else:
            last_month_adjusted = last_month

        result = {
            'timeline': timeline,
            'this_week': last_monday,
            'last_week': last_week,
            'last_month': {'real': last_month,
                           'adjusted': last_month_adjusted},
        }
        return result

    def render_to_response(self, context, **response_kwargs):
        response = super(LogViewer, self).render_to_response(context,
                                                             **response_kwargs)
        if self.request.is_ajax():
            # easily parsed with Javascript
            if self.next_page:
                response['X-NextPage'] = self.next_page

            if self.prev_page:
                response['X-PrevPage'] = self.prev_page
        else:
            # Official SEO header
            links = []
            if self.next_page:
                links.append('{0}; rel="prev"'.format(self.next_page))

            if self.prev_page:
                links.append('{0}; rel="prev"'.format(self.prev_page))
            response['Link'] = ','.join(links)
        response['X-Timezone'] = self.timezone
        return response


class CurrentLogViewer(LogDateMixin, LogViewer, RedirectView):

    def get_redirect_url(self, **kwargs):
        params = self.request.GET.copy()
        try:
            date = datetime_to_date(self.get_queryset()[0].timestamp)
            count = self._date_query_set(date).count()
            pages = count / PAGINATE_BY
            if count % PAGINATE_BY:
                pages += 1

            params['page'] = pages
        except IndexError:
            raise Http404("No logs yet.")
        url = reverse_channel(self.channel, 'log_day',
            kwargs=self._kwargs_with_date(date))
        return '{0}?{1}'.format(url, params.urlencode())



class DayLogViewer(LogDateMixin, LogViewer, ListView):
    show_first_header = True
    template_name = "logs/logs.html"
    paginate_by = PAGINATE_BY

    def dispatch(self, *args, **kwargs):
        try:
            self.tz = pytz.timezone(self.request.GET.get('tz', 'UTC'))
        except (KeyError, pytz.UnknownTimeZoneError):
            self.tz = pytz.utc
        try:
            year = int(self.kwargs['year'])
            month = int(self.kwargs['month'])
            day = int(self.kwargs['day'])

            self.date = self.tz.localize(datetime.datetime(year=year, month=month, day=day))
        except ValueError:
            raise Http404

        return super(DayLogViewer, self).dispatch(*args, **kwargs)

    def get_queryset(self):

        order = 'timestamp'
        if self.newest_first:
            order = '-timestamp'

        qs = super(DayLogViewer, self).get_queryset().order_by(order)
        start = self.date
        end = start + datetime.timedelta(days=1)
        return qs.filter(timestamp__gte=start, timestamp__lt=end)

    def _date_paginator(self, date):
        qs = self._date_query_set(date)
        return self.get_paginator(qs, self.get_paginate_by(qs))

    def paginate_queryset(self, queryset, page_size):
        paginator, page, object_list, has_other_pages = super(DayLogViewer, self).paginate_queryset(queryset, page_size)
        # if len(object_list) == 0:
        #     raise Http404('No matching logs for {0}'.format(self.channel))
        self.prev_page = self.get_previous_page_link(page)
        self.next_page = self.get_next_page_link(page)

        return paginator, page, object_list, has_other_pages

    def get_previous_page_link(self, page):
        """
        Generate a link to the next page, from the current one.
        """
        url = self.page_base_url

        # copy, to maintain any params that came in to original request.
        params = self.request.GET.copy()

        if not page.has_previous():
            date = self._get_previous_date()

            if not date:
                # We have no more logs!
                return None

            # Use new paginator to get dates max page number.
            paginator = self._date_paginator(date)
            params['page'] = paginator.num_pages

            url = reverse_channel(self.channel, 'log_day', kwargs=self._kwargs_with_date(date))
        else:
            params['page'] = page.previous_page_number()

        return '{0}?{1}'.format(url, params.urlencode())

    def get_next_page_link(self, page):
        """
        Generate a link to the next page, from the current one.
        """
        url = self.page_base_url

        # copy, to maintain any params that came in to original request.
        params = self.request.GET.copy()

        if not page.has_next():
            date = self._get_next_date()
            if date:
                url = reverse_channel(self.channel, 'log_day', kwargs=self._kwargs_with_date(date))
                params['page'] = 1 # If new date, always start at page 1.
            else:
                # If we have no more pages, we should be listening to the live feed.
                url = reverse('log_update', kwargs={'channel_pk' : self.channel.pk})
        else:
            params['page']  = page.next_page_number()

        return '{0}?{1}'.format(url, params.urlencode())

class MessageLogViewer(LogViewer):
    def dispatch(self, request, *args, **kwargs):
        try:
            self.highlight = int(kwargs['message_id'])
        except ValueError:
            raise Http404
        return super(MessageLogViewer, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        self.page_base_url = reverse_channel(self.channel, 'log_all')
        msg_id = self.kwargs['message_id']
        half_page_count = self.paginate_by / 2
        queryset = super(MessageLogViewer, self).get_queryset()
        try:
            message = queryset.get(pk=msg_id)
            timestamp = message.timestamp
        except models.Log.DoesNotExist:
            raise Http404
        # This is pretty inefficient, but it gets us the queryset we want
        messages_before = (queryset.filter(timestamp__lt=timestamp)
                                   .order_by('-timestamp'))
        messages_after = (queryset.filter(timestamp__gt=timestamp)
                                  .order_by('timestamp'))

        try:
            first = list(messages_before[:half_page_count])[-1]
        except IndexError:
            first = message
        try:
            last = list(messages_after[:half_page_count - 1])[-1]
        except IndexError:
            last = message
        return queryset.filter(timestamp__range=(first.timestamp,
                                                 last.timestamp))


class SearchLogViewer(LogViewer):
    show_first_header = True
    newest_first = True
    allow_empty = True
    show_timeline = False

    def get_context_data(self, **kwargs):
        """
        Add the search term to the context data.
        """
        data = super(SearchLogViewer, self).get_context_data(**kwargs)
        data['q'] = self.search_term
        return data

    def get_queryset(self):
        """
        Use search results rather than the standard queryset.
        """
        if self.form.is_valid():
            self.search_term = self.form.cleaned_data.get("q", "")
        else:
            self.search_term = ""
        return self.channel.log_set.search(self.search_term)\
            .filter(self.channel.visible_commands_filter)

    def paginate_queryset(self, queryset, page_size):
        (paginator, page, object_list, has_other_pages) = (
            self._paginate_queryset(queryset, page_size))
        if len(object_list) == 0:
            self.prev_page = ""
            self.next_page = ""
        else:
            self.prev_page, self.next_page = self.get_page_links(object_list)
        return paginator, page, object_list, has_other_pages

class MissedLogViewer(LogViewer):
    show_first_header = True

    def get_queryset(self):
        queryset = super(MissedLogViewer, self).get_queryset()
        nick = self.kwargs['nick']
        try:
            # cover nicks in the form: nick OR nick_ OR nick|<something>
            last_exit = queryset.filter(
                Q(nick__iexact=nick) |
                Q(nick__istartswith="{0}|".format(nick)) |
                Q(nick__iexact="{0}_".format(nick)),
                Q(command='QUIT') | Q(command='PART')).order_by('-timestamp')[0]
        except IndexError:
            raise Http404("User hasn't left room")
        try:
            last_join = queryset.filter(
                Q(nick__iexact=nick) |
                Q(nick__istartswith="{0}|".format(nick)) |
                Q(nick__iexact="{0}_".format(nick)), Q(command='JOIN'),
                Q(timestamp__gt=last_exit.timestamp)).order_by('timestamp')[0]
            date_filter = {'timestamp__range': (last_exit.timestamp,
                                                last_join.timestamp)}
        except IndexError:
            date_filter = {'timestamp__gte': last_exit.timestamp}
        # Only fetch results from when the user logged out.
        self.fetch_after = (last_exit.timestamp -
            datetime.timedelta(milliseconds=1))
        return queryset.filter(**date_filter)


class LogUpdate(ChannelMixin, redisqueue.RedisQueueView):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(LogUpdate, self).dispatch(request, *args, **kwargs)

    def iterator(self):
        connection = redisqueue._connect()
        pubsub = connection.pubsub()
        pubsub.subscribe(self.get_redis_channel())
        last_id = self.get_last_id()
        # catch up with missed messages
        if last_id:
            missed = self.channel.filtered_logs().filter(timestamp__gt=last_id)
            missed = list(missed)
            try:
                self.sse.set_event_id(missed[-1].timestamp.isoformat())
                for line in missed:
                    self.sse.add_message('log', line.as_html())
                yield
            except IndexError:
                pass

        # listen to new messages
        for message in pubsub.listen():
            if message['type'] == 'message':
                try:
                    event, data, event_id = json.loads(message['data'])
                except ValueError:
                    event_id = None
                    event, data = json.loads(message['data'])
                if event_id:
                    self.sse.set_event_id(event_id)
                self.sse.add_message(event, data)
                yield

    def get_redis_channel(self):
        return 'channel_update:{0}'.format(self.channel.pk)
