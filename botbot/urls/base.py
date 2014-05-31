from django.conf.urls import patterns, url, include
from django.conf import settings

from botbot.apps.accounts.views import Dashboard
from botbot.apps.bots.views import AddChannel, SuggestUsers, RequestChannel
from botbot.apps.preview.views import LandingPage

channel_patterns = patterns('',
    url(r'', include('botbot.apps.logs.urls')),
    url(r'', include('botbot.apps.bots.urls')),
)

urlpatterns = patterns('',
    (r'^$', LandingPage.as_view()),
    (r'', include('launchpad.urls')),
    url(r'^dashboard/$', Dashboard.as_view(), name='dashboard'),
    url(r'^add/$', AddChannel.as_view(), name="add_channel"),
    url(r'^request/$', RequestChannel.as_view(), name='request_channel'),
    url(r'^request/success/$', 'django.shortcuts.render',
        {'template_name': 'bots/request_success.html'}, name='request_channel_success'),

    (r'^accounts/', include('botbot.apps.accounts.urls')),
    url(r'^_suggest_users/$', SuggestUsers.as_view(), name='suggest_users'),

    url(r'^(?P<bot_slug>[\-\w\:\.]+(\@[\w]+)?)/(?P<channel_slug>[\-\w\.]+)/',
        include(channel_patterns)),
)

urlpatterns += patterns('django.shortcuts',
    url(r'^terms/$', 'render', {'template_name': 'terms.html'}),
    url(r'^privacy/$', 'render', {'template_name': 'privacy.html'}),
)

if settings.INCLUDE_DJANGO_ADMIN:
    from .admin import urlpatterns as admin_urlpatterns
    # Prepend the admin urls.
    urlpatterns = admin_urlpatterns + urlpatterns

if settings.DEBUG:
    import os
    urlpatterns = patterns('django.views.static',
        url(r'^how-to-setup-irc-channel/$', 'serve', {
            'document_root': os.path.join(settings.PROJECT_DIR, 'static'),
            'path': 'howto.html'
        }),
    ) + urlpatterns
    urlpatterns += patterns('django.shortcuts',
        url(r'^404/$', 'render', {'template_name': '404.html'}),
        url(r'^500/$', 'render', {'template_name': '500.html'}),
    )
