from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns('',
    url(r'^manage/$', views.ManageChannel.as_view(), name='manage_channel'),
    url(r'^delete/$', views.DeleteChannel.as_view(), name='delete_channel'),
)
