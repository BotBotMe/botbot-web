import json
import datetime
import re
from urllib import urlencode

from django.db.models import Q
from django.http import Http404
from django.utils.decorators import method_decorator
from django.utils.timezone import get_current_timezone_name
from django.views.generic import ListView, TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import pytz

from botbot.apps.accounts import forms as accounts_forms
from botbot.apps.bots.utils import reverse_channel
from botbot.apps.bots.views import ChannelMixin
from botbot.core.paginator import InfinitePaginator
from . import forms, models


class Help(ChannelMixin, TemplateView):
    """
    Help page for a channel.
    """
    template_name = 'logs/help.html'


class LogViewer(ChannelMixin, ListView):
    template_name = "logs/logs.html"
    context_object_name = "message_list"
    paginate_by = 150
    paginator_class = InfinitePaginator
    newest_first = False
    show_timeline = True
    show_first_header = False   # Display date header above first line
    fetch_before = None
    fetch_after = None

    def dispatch(self, request, *args, **kwargs):
        self.form = forms.SearchForm(request.GET)
        self.page_base_url = request.path
        self.timezone = get_current_timezone_name()
        if request.is_ajax():
            self.show_timeline = False
            self.template_name = 'logs/log_display.html'
        return super(LogViewer, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        order = 'timestamp'
        if self.newest_first:
            order = '-timestamp'
        return self.channel.filtered_logs().order_by(order)

    def _paginate_queryset(self, queryset, page_size):
        # This logic made my head hurt.
        # Best to draw a diagram with all the possibilities
        # Intentionally verbose to make it easier to understand
        fetch_before = self.request.GET.get('before', self.fetch_before)
        fetch_after = self.request.GET.get('after', self.fetch_after)
        if fetch_before:
            queryset = queryset.filter(timestamp__lt=fetch_before)
            if not self.newest_first:
                queryset = queryset.reverse()
        elif fetch_after:
            queryset = queryset.filter(timestamp__gt=fetch_after)
            if self.newest_first:
                queryset = queryset.reverse()
        elif not self.newest_first:
            queryset = queryset.reverse()
        (paginator, page, object_list, has_other_pages) = (
            super(LogViewer, self).paginate_queryset(queryset, page_size))
        # fix ordering after pagination if it was reversed
        if not queryset.query.standard_ordering:
            object_list = list(reversed(object_list))
        return (paginator, page, object_list, has_other_pages)


    def paginate_queryset(self, queryset, page_size):
        (paginator, page, object_list, has_other_pages) = (
            self._paginate_queryset(queryset, page_size))
        if len(object_list) == 0:
            raise Http404('No matching logs for {0}'.format(self.channel))
        self.prev_page, self.next_page = self.get_page_links(object_list)
        return paginator, page, object_list, has_other_pages

    def get_page_links(self, message_list):
        """Gets links to previous and next pages for current page"""
        # coerce to list
        if not isinstance(message_list, list):
            message_list = list(message_list)
        first = message_list[0].timestamp.isoformat()
        last = message_list[-1].timestamp.isoformat()
        prev_vars = self.request.GET.copy()
        next_vars = self.request.GET.copy()
        if self.newest_first:
            prev_vars.update({'after': first})
            next_vars.update({'before': last})
        else:
            next_vars.update({'after': last})
            prev_vars.update({'before': first})
        next_page_link = '{0}?{1}'.format(self.page_base_url,
                                          next_vars.urlencode())
        prev_page_link = '{0}?{1}'.format(self.page_base_url,
                                          prev_vars.urlencode())
        return prev_page_link, next_page_link

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
            response['X-NextPage'] = self.next_page
            response['X-PrevPage'] = self.prev_page
        else:
            # Official SEO header
            response['Link'] = ','.join([
                '{0}; rel="prev"'.format(self.prev_page),
                '{0}; rel="next"'.format(self.next_page),
            ])
        response['X-Timezone'] = self.timezone
        return response


class CurrentLogViewer(LogViewer):
    is_current = True


class DayLogViewer(LogViewer):
    show_first_header = True

    def get_queryset(self):
        # individual page URLs will already be passed a date
        # they don't need to use the date in the URL
        self.page_base_url = reverse_channel(self.channel, 'log_all')
        try:
            year = int(self.kwargs['year'])
            month = int(self.kwargs['month'])
            day = int(self.kwargs['day'])
        except ValueError:
            raise Http404
        try:
            tz = pytz.timezone(self.request.GET.get('tz', 'UTC'))
        except (KeyError, pytz.UnknownTimeZoneError):
            tz = pytz.utc
        self.fetch_after = tz.localize(datetime.datetime(year, month,
                                                         day, 0, 0, 0))
        return super(DayLogViewer, self).get_queryset()


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
        self.search_term = self.search_term.replace('%', '%%')

        filter_args = self.channel.visible_commands_filter

        # If a user is mentioned, filter those users first
        matches = re.search(r'(\bnick:([\w\-]+)\b)', self.search_term)
        if matches:
            self.search_term = self.search_term.replace(matches.groups()[0], '')
            filter_args = filter_args & Q(nick__icontains=matches.groups()[1])

        return self.channel.log_set.search(self.search_term).filter(filter_args)

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
