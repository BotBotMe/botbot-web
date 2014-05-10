import datetime
import math

import re
from django.db.models import Q
from django.http import Http404
from django.shortcuts import redirect
from django.utils.timezone import get_current_timezone_name
from django.views.generic import ListView, TemplateView, RedirectView
from django.utils.translation import ugettext as _
from django.conf import settings
import pytz

from botbot.apps.accounts import forms as accounts_forms
from botbot.apps.bots.utils import reverse_channel
from botbot.apps.bots.views import ChannelMixin
from . import forms


class Help(ChannelMixin, TemplateView):

    """
    Help page for a channel.
    """
    template_name = 'logs/help.html'


class PaginatorPageLinksMixin(object):

    def paginate_queryset(self, queryset, page_size):
        paginator, page, object_list, has_other_pages = super(
            PaginatorPageLinksMixin, self).paginate_queryset(queryset, page_size)

        self.next_page = self.get_next_page_link(page)
        self.prev_page = self.get_previous_page_link(page)

        return paginator, page, object_list, has_other_pages

    def get_next_page_link(self, page):
        url = self.page_base_url
        params = self.request.GET.copy()

        if not page.has_next():
            return ""
        else:
            params['page'] = page.next_page_number()

        return '{0}?{1}'.format(url, params.urlencode())

    def get_previous_page_link(self, page):
        url = self.page_base_url
        params = self.request.GET.copy()

        if not page.has_previous():
            return ""
        else:
            params['page'] = page.previous_page_number()

        return '{0}?{1}'.format(url, params.urlencode())


class LogDateMixin(object):

    def _get_base_queryset(self):
        return self.channel.filtered_logs()

    def _kwargs_with_date(self, date):
        kwargs = {
            'year': date.year,
            'month': "%02d" % date.month ,
            'day': "%02d" % date.day
        }
        return kwargs

    def _get_previous_date(self):
        """
        Find the previous day, that has content.
        """
        qs = self._get_base_queryset().filter(timestamp__lt=self.date)
        if qs.exists():
            return qs[0].timestamp.date()

    def _get_next_date(self):
        """
        Find the previous day, that has content.
        """
        qs = self._get_base_queryset().filter(
            timestamp__gte=datetime.timedelta(days=1) + self.date).order_by('timestamp')
        if qs.exists():
            return qs[0].timestamp.date()

    def _date_query_set(self, date):
        qs = self._get_base_queryset()
        return qs.filter(timestamp__gte=date,
                         timestamp__lt=date + datetime.timedelta(days=1))


class LogViewer(ChannelMixin, object):
    context_object_name = "message_list"
    template_name = "logs/logs.html"
    newest_first = False
    show_timeline = True
    show_first_header = False   # Display date header above first line
    paginate_by = 150

    def __init__(self, *args, **kwargs):
        super(LogViewer, self).__init__(*args, **kwargs)
        self.next_page = ""
        self.prev_page = ""

    def dispatch(self, request, *args, **kwargs):
        self.page_base_url = request.path
        self.form = forms.SearchForm(request.GET)
        self.timezone = get_current_timezone_name()

        if request.is_ajax():
            self.show_timeline = False
            self.template_name = 'logs/log_display.html'

        return super(LogViewer, self).dispatch(request, *args, **kwargs)

    def get_ordered_queryset(self, queryset):
        order = 'timestamp'
        if self.newest_first:
            order = '-timestamp'

        return queryset.order_by(order)

    def get_context_data(self, **kwargs):
        context = super(LogViewer, self).get_context_data(**kwargs)

        if self.show_timeline:
            context.update(self._timeline_context())

        context["size"] = self.channel.current_size()
        context["big"] = (context["size"] >= settings.BIG_CHANNEL)

        if not self.request.is_ajax():
            highlight_pk = None if not self.request.GET.get('msg') else int(
                self.request.GET.get('msg'))
            highlight = None
            if highlight_pk:
                for l in context['message_list']:
                    if l.pk == highlight_pk:
                        highlight = l
                        break

            context.update({
                'highlight': highlight,
                'is_current': getattr(self, 'is_current', False),
                'search_form': self.form,
                'tz_form': accounts_forms.TimezoneForm(self.request),
                'show_first_header': self.show_first_header,
                'newest_first': self.newest_first,
            })
        context.update({
            'prev_page': self.prev_page,
            'next_page': self.next_page,
        })

        return context

    def _timeline_context(self):
        """
        Context (template) vars needed for timeline display.
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

    def _pages_for_queryset(self, queryset):
        return int(math.ceil(queryset.count() / float(self.paginate_by)))


class MessagePermalinkView(LogDateMixin, LogViewer, RedirectView):

    """
    Reverse a message id to a pagination result.
    """
    permanent = True

    def get_redirect_url(self, **kwargs):
        params = self.request.GET.copy()
        line = self.channel.log_set.get(pk=self.kwargs['msg_pk'])
        try:
            date = line.timestamp.date()
            params['page'] = self._pages_for_queryset(
                self._date_query_set(date))
        except IndexError:
            raise Http404("No logs yet.")
        params['msg'] = line.pk
        url = reverse_channel(self.channel, 'log_day',
                              kwargs=self._kwargs_with_date(date))
        return '{0}?{1}'.format(url, params.urlencode())


class CurrentLogViewer(LogDateMixin, LogViewer, RedirectView):

    permanent = False
    newest_first = True  # Make sure we find the newest record.

    def get_redirect_url(self, **kwargs):
        params = self.request.GET.copy()
        queryset = self.get_ordered_queryset(self.channel.filtered_logs())
        try:
            date = queryset[0].timestamp.date()
            params['page'] = self._pages_for_queryset(
                self._date_query_set(date))
        except IndexError:
            raise Http404("No logs yet.")
        url = reverse_channel(self.channel, 'log_day',
                              kwargs=self._kwargs_with_date(date))
        return '{0}?{1}'.format(url, params.urlencode())


class DayLogViewer(PaginatorPageLinksMixin, LogDateMixin, LogViewer, ListView):
    show_first_header = False
    allow_empty = False

    def dispatch(self, request, *args, **kwargs):
        try:
            self.tz = pytz.timezone(self.request.GET.get('tz', 'UTC'))
        except (KeyError, pytz.UnknownTimeZoneError):
            self.tz = pytz.utc
        try:
            year = int(self.kwargs['year'])
            month = int(self.kwargs['month'])
            day = int(self.kwargs['day'])

            self.date = self.tz.localize(
                datetime.datetime(year=year, month=month, day=day))
        except ValueError:
            raise Http404

        return super(DayLogViewer, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        allow_empty = self.get_allow_empty()
        if not allow_empty:
            is_empty = not self.object_list.exists()
            if is_empty:
                try:
                    closet_date = self.get_ordered_queryset(
                        self.channel.filtered_logs().filter(
                            timestamp__gte=self.date)
                    )[0].timestamp

                    url = reverse_channel(self.channel, 'log_day',
                                          kwargs=self._kwargs_with_date(closet_date))
                    return redirect(url)

                except IndexError:
                    raise Http404(_("Empty list and '%(class_name)s.allow_empty' is False.")
                                  % {'class_name': self.__class__.__name__})
        context = self.get_context_data()
        return self.render_to_response(context)

    def get_queryset(self):
        qs = self.channel.filtered_logs()
        qs = self.get_ordered_queryset(qs)
        start = self.date
        end = start + datetime.timedelta(days=1)
        return qs.filter(timestamp__gte=start, timestamp__lt=end)

    def _date_paginator(self, date):
        qs = self._date_query_set(date)
        return self.get_paginator(qs, self.get_paginate_by(qs))

    def paginate_queryset(self, queryset, page_size):
        paginator, page, object_list, has_other_pages = super(
            DayLogViewer, self).paginate_queryset(queryset, page_size)

        if not self.next_page:
            self.is_current = True

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

            url = reverse_channel(
                self.channel, 'log_day', kwargs=self._kwargs_with_date(date))
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
                url = reverse_channel(
                    self.channel, 'log_day', kwargs=self._kwargs_with_date(date))
                params['page'] = 1  # If new date, always start at page 1.
            else:
                return ""
        else:
            params['page'] = page.next_page_number()

        return '{0}?{1}'.format(url, params.urlencode())


class SearchLogViewer(PaginatorPageLinksMixin, LogViewer, ListView):
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
        data['use_absolute_url'] = True
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


class MissedLogViewer(PaginatorPageLinksMixin, LogViewer, ListView):

    show_first_header = True
    newest_first = False

    def get_context_data(self, **kwargs):
        data = super(MissedLogViewer, self).get_context_data(**kwargs)
        data['use_absolute_url'] = True
        return data

    def get_queryset(self):
        queryset = self.channel.log_set.all()
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