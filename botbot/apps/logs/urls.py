from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns('',
    url(r'(?P<year>\d{4})-(?P<month>0[1-9]|1[0-2])-(?P<day>0[1-9]|[1-2][0-9]|3[0-1])/$',
        views.DayLogViewer.as_view(), name="log_day"),
    url(r'(?P<year>\d{4})-(?P<month>0[1-9]|1[0-2])-(?P<day>0[1-9]|[1-2][0-9]|3[0-1]).log$',
        views.DayLogViewer.as_view(format='text'), name="log_day_text"),
    url(r'^missed/(?P<nick>[\w\-\|]*)/$', views.MissedLogViewer.as_view(),
        name="log_missed"),
    url(r'^msg/(?P<msg_pk>\d+)/$', views.SingleLogViewer.as_view(),
        name="log_message_permalink"),
    url(r'^search/$', views.SearchLogViewer.as_view(), name='log_search'),
    url(r'^kudos.json$', views.Kudos.as_view(), name='kudos_json'),
    url(r'^kudos/$', views.ChannelKudos.as_view(), name='kudos'),
    url(r'^help/$', views.Help.as_view(), name='help_bot'),
    url(r'^stream/$', views.LogStream.as_view(), name='log_stream'),
    url(r'^$', views.DayLogViewer.as_view(),
        name="log_current"),
)
