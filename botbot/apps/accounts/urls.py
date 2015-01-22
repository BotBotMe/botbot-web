from django.conf.urls import patterns, url, include

from . import views

urlpatterns = patterns('',
    url(r'channels/$', views.Channels.as_view(), name='account_channels'),
    url(r'^$', views.Dashboard.as_view(), name='settings_dashboard'),

    url(r'account/$', views.ManageAccount.as_view(), name='settings_account'),
    url(r'_timezone/$', views.SetTimezone.as_view(), name="_set_timezone"),

    url(r'', include('allauth.urls')),
)
