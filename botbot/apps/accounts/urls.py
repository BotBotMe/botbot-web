from django.conf.urls import patterns, url, include

from . import views

urlpatterns = patterns('',
    url(r'manage/$', views.ManageAccount.as_view(), name='account_manage'),
    url(r'_timezone/$', views.SetTimezone.as_view(), name="_set_timezone"),
    url(r'', include('allauth.urls')),
)
