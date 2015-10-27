from django.conf import settings
from django.conf.urls import patterns, url, include

from botbot.apps.bots.views import SuggestUsers, ChannelList
from botbot.apps.preview.views import LandingPage

channel_patterns = patterns('',
    url(r'', include('botbot.apps.logs.urls')),
)

urlpatterns = patterns('django.shortcuts',
    url(r'^terms/$', 'render', {'template_name': 'terms.html'},
        name='terms'),
    url(r'^privacy/$', 'render', {'template_name': 'privacy.html'},
        name='privacy'),
    url(r'^how-to-setup-irc-channel/$', 'render', {
        'template_name': 'howto.html'},
        name='how-to'),
    url(r'^irc-guide/$', 'render', {
        'template_name': 'irc-guide.html'},
        name='irc-guide'),
)

if settings.INCLUDE_DJANGO_ADMIN:
    from .admin import urlpatterns as admin_urlpatterns
    # Prepend the admin urls.
    urlpatterns = admin_urlpatterns + urlpatterns

if settings.DEBUG:
    urlpatterns += patterns('django.shortcuts',
        url(r'^404/$', 'render', {'template_name': '404.html'}),
        url(r'^500/$', 'render', {'template_name': '500.html'}),
    )

urlpatterns += patterns('',
                        (r'^$', LandingPage.as_view()),
                        (r'', include('launchpad.urls')),
                        url(r'^sitemap\.xml$', include('botbot.apps.sitemap.urls')),

                        url(r'^_suggest_users/$', SuggestUsers.as_view(), name='suggest_users'),

                        url(r'^(?P<bot_slug>[\-\w\:\.]+(\@[\w]+)?)/(?P<channel_slug>[\-\w\.]+)/',
                            include(channel_patterns)),
                        url(r'^(?P<network_slug>[\-\w\.]+)/$', ChannelList.as_view())
                        )
