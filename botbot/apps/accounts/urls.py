from django.conf.urls.defaults import patterns, url, include

from . import views

urlpatterns = patterns('django.contrib.auth.views',
    url('login/$', 'login', {'template_name': 'accounts/login.html'}, 'login'),
    url('logout/$', 'logout', {'next_page': '/'},
        'logout'),
    url('password/reset/$', 'password_reset',
        name='password_reset'),
    url('password/sent/$', 'password_reset_done',
        name='password_reset_done'),
    (r'', include('django.contrib.auth.urls')),
    (r'', include('social_auth.urls')),

    url('manage/$', views.ManageAccount.as_view(), name='account_manage'),
    url('_timezone/$', views.SetTimezone.as_view(), name="_set_timezone"),
)
