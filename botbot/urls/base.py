from django.conf import settings
from django.conf.urls import patterns, url, include

from botbot.apps.bots.views import ChannelList
from botbot.apps.preview.views import LandingPage

channel_patterns = patterns('',
    url(r'', include('botbot.apps.logs.urls')),
)

urlpatterns = patterns('',
                        (r'^$', LandingPage.as_view()),
                        url(r'^sitemap\.xml$', include('botbot.apps.sitemap.urls')),

                        url(r'^(?P<bot_slug>[\-\w\:\.]+(\@[\w]+)?)/(?P<channel_slug>[\-\w\.]+)/',
                            include(channel_patterns)),
                        url(r'^(?P<network_slug>[\-\w\.]+)/$', ChannelList.as_view())
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
