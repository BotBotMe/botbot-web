import datetime
import json
import math
import random
import re

from django.conf import settings
from django.contrib.humanize.templatetags import humanize
from django.core.cache import cache
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.utils.functional import cached_property
from django.utils.translation import ugettext as _
from django.views.generic import ListView, TemplateView, View
from django.views.decorators.cache import patch_cache_control
import pytz

from botbot.apps.bots.utils import reverse_channel
from botbot.apps.bots.views import ChannelMixin
from . import forms
from botbot.apps.logs.models import Log
from botbot.apps.kudos.models import KudosTotal



class Help(ChannelMixin, TemplateView):

    """
    Help page for a channel.
    """
    template_name = 'logs/help.html'


class PaginatorPageLinksMixin(object):

    def paginate_queryset(self, queryset, page_size):
        paginator, page, object_list, has_other_pages = super(
            PaginatorPageLinksMixin, self).paginate_queryset(
                queryset, page_size)

        self.next_page = self.get_next_page_link(page)
        self.prev_page = self.get_previous_page_link(page)
        self.current_page = self.get_current_page_link(page)

        return paginator, page, object_list, has_other_pages

    def get_next_page_link(self, page):
        url = self.request.path
        params = self.request.GET.copy()

        if not page.has_next():
            return ""
        else:
            params['page'] = page.next_page_number()

        return '{0}?{1}'.format(url, params.urlencode())

    def get_previous_page_link(self, page):
        url = self.request.path
        params = self.request.GET.copy()

        if not page.has_previous():
            return ""
        else:
            params['page'] = page.previous_page_number()

        return '{0}?{1}'.format(url, params.urlencode())

    def get_current_page_link(self, page):
        url = self.request.path
        params = self.request.GET.copy()
        params['page'] = page.number
        return '{0}?{1}'.format(url, params.urlencode())


class LogDateMixin(object):

    def _get_base_queryset(self):
        return self.channel.filtered_logs()

    def channel_date_url(self, date=None):
        if not date:
            date = self.date
        viewname = self.format == 'text' and 'log_day_text' or 'log_day'
        return reverse_channel(
            self.channel, viewname, kwargs=self._kwargs_with_date(date))

    def _kwargs_with_date(self, date):
        kwargs = {
            'year': date.year,
            'month': "%02d" % date.month,
            'day': "%02d" % date.day
        }
        return kwargs

    def _local_date_at_midnight(self, timestamp):
        # cast timestamp into local timezone
        localized = timestamp.astimezone(self.request_timezone)
        # create a new date object starting at midnight in that timezone
        return datetime.datetime(localized.year,
                                 localized.month,
                                 localized.day,
                                 tzinfo=localized.tzinfo)

    def _get_previous_date(self):
        """
        Find the previous day, that has content.
        """
        date = None
        try:
            ts = (self._get_base_queryset()
                      .filter(timestamp__lt=self.date)[0].timestamp)
            date = self._local_date_at_midnight(ts)
        except IndexError:
            pass
        return date

    def _get_next_date(self):
        """
        Find the next day, that has content.
        """
        date = None
        try:
            ts = (self._get_base_queryset()
                .filter(timestamp__gte=datetime.timedelta(days=1) + self.date)
                .order_by('timestamp')[0].timestamp)
            date = self._local_date_at_midnight(ts)
        except IndexError:
            pass
        return date

    def _date_query_set(self, date):
        qs = self._get_base_queryset()
        return qs.filter(timestamp__gte=date,
                         timestamp__lt=date + datetime.timedelta(days=1))

class LogStream(ChannelMixin, View):
    def get(self, request, channel_slug, bot_slug):
        response = HttpResponse()
        response['X-Accel-Redirect'] = '/internal-channel-stream/{}'.format(
            self.channel.pk)
        if 'HTTP_LAST_EVENT_ID' in request.META:
            response['Last-Event-ID'] = request.META['HTTP_LAST_EVENT_ID']
        return response

def _utc_now():
    return datetime.datetime.now(tz=pytz.timezone('UTC'))

def _find_pk(pk, queryset):
    """Find a PK in a queryset in memory"""
    found = None
    try:
        pk = int(pk)
        found = next(obj for obj in queryset if obj.pk == pk)
    except (ValueError, StopIteration):
        pass
    return found

def _timeline_context(timeline):
    """
    Context (template) vars needed for timeline display.
    """

    if not timeline:
        return {}

    today = _utc_now().date()
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

class LogViewer(ChannelMixin, object):
    context_object_name = "message_list"
    newest_first = False
    show_first_header = False   # Display date header above first line
    paginate_by = 150
    format = ''

    def __init__(self, *args, **kwargs):
        super(LogViewer, self).__init__(*args, **kwargs)
        self.next_page = ""
        self.prev_page = ""
        self.current_page = ""

    def dispatch(self, request, *args, **kwargs):
        self._setup_response_format()
        return super(LogViewer, self).dispatch(request, *args, **kwargs)

    def _setup_response_format(self):
        if self.format == 'text':
            self.include_timeline = False
            self.template_name = 'logs/logs.txt'
            self.content_type = 'text/plain; charset=utf-8'
        elif self.request.is_ajax():
            self.format = 'ajax'
            self.include_timeline = False
            self.template_name = 'logs/log_display.html'
        # Default to HTML view
        else:
            self.format = 'html'
            self.include_timeline = True
            self.template_name = "logs/logs.html"


    def get_ordered_queryset(self, queryset):
        order = 'timestamp'
        if self.newest_first:
            order = '-timestamp'

        return queryset.order_by(order)



    def get_context_data(self, **kwargs):
        context = super(LogViewer, self).get_context_data(**kwargs)

        if self.include_timeline:
            context.update(
                _timeline_context(self.channel.get_months_active()))

        if self.format == 'html':
            context.update({
                'is_current': getattr(self, 'is_current', False),
                'search_form': forms.SearchForm(),
                'show_first_header': self.show_first_header,
                'newest_first': self.newest_first,
                'show_kudos': self.channel.user_can_access_kudos(
                    self.request.user),
            })

        size = self.channel.current_size()
        context.update({
            'size': size,
            'big': (size >= settings.BIG_CHANNEL),
            'prev_page': self.prev_page,
            'next_page': self.next_page,
            'current_page': self.current_page,
        })

        return context



    def render_to_response(self, context, **response_kwargs):
        response = super(LogViewer, self).render_to_response(
            context, **response_kwargs)

        has_next_page = False
        if self.format == 'html':
            # Official SEO header
            links = []
            if self.next_page:
                links.append('{0}; rel="next"'.format(self.next_page))
                has_next_page = True

            if self.prev_page:
                links.append('{0}; rel="prev"'.format(self.prev_page))
            response['Link'] = ','.join(links)
        else:
            # No HTML, pass page info in easily parseable headers
            if self.next_page:
                response['X-NextPage'] = self.next_page
                has_next_page = True

            if self.prev_page:
                response['X-PrevPage'] = self.prev_page

        if has_next_page and self.request.user.is_anonymous():
            patch_cache_control(
                response, public=True,
                max_age=settings.CACHE_MIDDLEWARE_SECONDS)
        else:
            patch_cache_control(response, private=True)
        return response

    def _pages_for_queryset(self, queryset):
        return int(math.ceil(queryset.count() / float(self.paginate_by)))


class DayLogViewer(PaginatorPageLinksMixin, LogDateMixin, LogViewer, ListView):
    show_first_header = False
    allow_empty = True

    def get(self, request, *args, **kwargs):
        self.date = self.set_view_date()
        self.object_list = self.get_queryset()

        # Redirect to nearby logs if this queryset is empty to avoid a 404
        if not self.get_allow_empty() and not self.object_list.exists():
            url = self._nearby_log_url()
            if url:
                return redirect(url)
            raise Http404(_("Empty list and '%(class_name)s.allow_empty' is False.")
                          % {'class_name': self.__class__.__name__})

        context = self.get_context_data()
        return self.render_to_response(context)

    def _nearby_log_url(self):
        """Find a date-based log URL that will not be empty"""
        # First check if there is anything in the past
        closet_qs = self.channel.filtered_logs().order_by(
            "-timestamp").filter(timestamp__lte=self.date)

        # If not go to the future
        if not closet_qs.exists():
            closet_qs = self.channel.filtered_logs().order_by(
                "timestamp").filter(
                timestamp__gte=self.date)

        # Return the URL where the first log line found will be
        try:
            return self.channel_date_url(closet_qs[0].timestamp)
        except IndexError:
            pass
        return None


    def get_context_data(self):
        context = super(DayLogViewer, self).get_context_data()
        try:
            context.update({
                'highlight': int(self.request.GET.get('msg')),
            })
        except (TypeError, ValueError):
            pass
        return context


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
        url = self.channel_date_url()
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

            url = self.channel_date_url(date)
        else:
            params['page'] = page.previous_page_number()

        return '{0}?{1}'.format(url, params.urlencode())

    def get_next_page_link(self, page):
        """
        Generate a link to the next page, from the current one.
        """
        url = self.channel_date_url()

        # copy, to maintain any params that came in to original request.
        params = self.request.GET.copy()

        if not page.has_next():
            date = self._get_next_date()
            if date:
                url = self.channel_date_url(date)
                params['page'] = 1  # If new date, always start at page 1.
            else:
                return ""
        else:
            params['page'] = page.next_page_number()

        return '{0}?{1}'.format(url, params.urlencode())

    def get_current_page_link(self, page):
        # copy, to maintain any params that came in to original request.
        params = self.request.GET.copy()
        date = _utc_now()
        url = self.channel_date_url(date)
        params['page'] = page.number
        return '{0}?{1}'.format(url, params.urlencode())

    @cached_property
    def request_timezone(self):
        """
        Read timezone in from GET param otherwise use UTC
        """
        try:
            tz = pytz.timezone(self.request.GET.get('tz', ''))
        except pytz.UnknownTimeZoneError:
            tz = pytz.timezone('UTC')
        return tz

    def set_view_date(self):
        """Determine start date for queryset"""
        if all([field in self.kwargs for field in ['year', 'month', 'day']]):
            # localize date so logs start at local time
            try:
                return datetime.datetime(year=int(self.kwargs['year']),
                                         month=int(self.kwargs['month']),
                                         day=int(self.kwargs['day']),
                                         tzinfo=self.request_timezone)
            except ValueError:
                raise Http404("Invalid date.")

        # Use the last page.
        self.kwargs['page'] = 'last'
        return _utc_now().date()


class SearchLogViewer(PaginatorPageLinksMixin, LogViewer, ListView):
    show_first_header = True
    newest_first = True
    allow_empty = True
    include_timeline = False

    def get(self, request, *args, **kwargs):
        self.form = forms.SearchForm(request.GET)
        return super(SearchLogViewer, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """
        Add the search term to the context data.
        """
        context = super(SearchLogViewer, self).get_context_data(**kwargs)
        context.update({
            'q': self.search_term,
            'search_form': self.form,
        })
        return context

    def get_queryset(self):
        """
        Use search results rather than the standard queryset.
        """
        self.form = forms.SearchForm(self.request.GET)
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


class SingleLogViewer(DayLogViewer):
    """
    Find a single log line and redirect to a permalink to it.

    This inherits from DayLogViewer because it needs to use same queryset
    and pagination methods to ensure the page is found in the same place.
    """

    def get(self, request, *args, **kwargs):
        try:
            log = get_object_or_404(Log.objects, pk=self.kwargs['msg_pk'])
        except ValueError:
            raise Http404
        # set date to midnight so get_queryset starts pages correctly
        self.date = log.timestamp.date()
        self.object_list = self.get_queryset()
        # Find the page in the queryset the message is located on.
        page_url = self._permalink_to_log(log)
        return redirect(page_url, permanent=True)

    def _permalink_to_log(self, log):
        """Scan pages for a single log. Return to permalink to page"""
        cache_key = "line:{}:permalink".format(log.pk)
        url, params = cache.get(cache_key, [None, {}])
        if not url:
            paginator = self.get_paginator(
                self.object_list, self.get_paginate_by(self.object_list))
            for n in paginator.page_range:
                page = paginator.page(n)
                if log in page.object_list:
                    params = {"msg": log.pk, "page": n}
                    url = self.channel_date_url()
                    cache.set(cache_key, [url, params], None)
                    break  # Found the page.
            # page wasn't found
            if not url:
                raise Http404
        oparams = self.request.GET.copy()
        oparams.update(params)
        return '{0}?{1}'.format(url, oparams.urlencode())

class MissedLogViewer(PaginatorPageLinksMixin, LogViewer, ListView):
    include_timeline = False
    show_first_header = True
    newest_first = False

    def get_context_data(self, **kwargs):
        data = super(MissedLogViewer, self).get_context_data(**kwargs)
        data['use_absolute_url'] = True
        return data

    def get_queryset(self):
        queryset = self.get_ordered_queryset(self.channel.log_set.all())
        nick = self.kwargs['nick']
        try:
            # cover nicks in the form: nick OR nick_ OR nick|<something>
            last_exit = (queryset
                .filter(
                    Q(nick__iexact=nick) |
                    Q(nick__istartswith="{0}|".format(nick)) |
                    Q(nick__iexact="{0}_".format(nick)),
                    Q(command='QUIT') | Q(command='PART'))
                .order_by('-timestamp')[0])
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
        self.fetch_after = (
            last_exit.timestamp - datetime.timedelta(milliseconds=1))
        return queryset.filter(**date_filter)


class KudosMixin(object):
    """
    View mixin to check that kudos access is allowed.

    If the channel's ``public_kudos`` is False then only accessible to channel
    admins.

    Must go after ChannelMixin.
    """

    def dispatch(self, *args, **kwargs):
        """
        Check kudos authorization.
        """
        if not self.channel.user_can_access_kudos(self.request.user):
            raise Http404("Only accessible to channel admins")
        return super(KudosMixin, self).dispatch(*args, **kwargs)


class Kudos(ChannelMixin, KudosMixin, View):
    """
    View that returns a ranked JSON list of users with the most kudos.

    Not accessible to anonymous users.
    """

    def dispatch(self, *args, **kwargs):
        if not self.request.user.is_authenticated():
            raise Http404('Only accessible to authenticated users')
        return super(Kudos, self).dispatch(*args, **kwargs)

    def get(self, *args, **kwargs):
        return HttpResponse(
            json.dumps(
                self.channel.kudos_set.ranks(debug=settings.DEBUG),
                indent=2 if settings.DEBUG else None),
            content_type='text/json')


class ChannelKudos(ChannelMixin, KudosMixin, TemplateView):
    """
    Display a shuffled subset of the people with the most kudos.
    """
    template_name = 'logs/kudos.html'

    def rounded_percentage(self, score, total):
        percentage = score / float(total) * 100
        for i in (1, 10, 25, 50):
            if i >= percentage:
                return i

    def get_context_data(self, **kwargs):
        nick = self.request.GET.get('nick')

        ranks = self.channel.kudos_set.ranks(debug=nick)
        top_tier = ranks[:100]
        if len(top_tier) > 20:
            scoreboard = [r[0] for r in random.sample(top_tier, 20)]
        elif len(top_tier) > 4:
            scoreboard = random.shuffle([r[0] for r in ranks])
        else:
            scoreboard = None
        kwargs.update({
            'random_scoreboard': scoreboard,
        })

        try:
            channel_kudos = self.channel.kudostotal
        except KudosTotal.DoesNotExist:
            channel_kudos = None
        if channel_kudos and channel_kudos.message_count:
            if channel_kudos.message_count > 1000000:
                kwargs['channel_messages'] = humanize.intword(
                    channel_kudos.message_count)
            else:
                kwargs['channel_messages'] = humanize.intcomma(
                    channel_kudos.message_count)
            kwargs['channel_kudos_perc'] = '{:.2%}'.format(
                channel_kudos.appreciation)

        if nick:
            nick_lower = nick.lower()
            details = None
            for rank_nick, alltime, info in ranks:
                if rank_nick == nick_lower:
                    details = {
                        'alltime': alltime,
                        'alltime_perc': self.rounded_percentage(
                            alltime, len(ranks)),
                        'current': info['current_rank'],
                        'current_perc': self.rounded_percentage(
                            info['current_rank'], len(ranks)),
                    }
                    break
            kwargs['search'] = {'nick': nick, 'details': details}

        return super(ChannelKudos, self).get_context_data(**kwargs)
