from django.conf.urls import patterns, url
from django.shortcuts import redirect

from . import views

urlpatterns = patterns('',
    url(r'(?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2})/$',
        views.DayLogViewer.as_view(), name="log_day"),
    url(r'^missed/(?P<nick>[\w\-\|]*)/$', views.MissedLogViewer.as_view(),
        name="log_missed"),
    url(r'^(?P<msg_pk>\d+)/$', views.MessagePermalinkView.as_view(),
        name="log_message_permalink"),
    url(r'^search/$', views.SearchLogViewer.as_view(), name='log_search'),
    url(r'^help/$', views.Help.as_view(), name='help_bot'),
    url(r'^$', views.CurrentLogViewer.as_view(),
        name="log_current"),
)
