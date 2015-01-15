"""
Site map URLs
"""
from django.conf.urls import patterns, url
from django.contrib import sitemaps
from django.contrib.sitemaps.views import sitemap
from django.core.urlresolvers import reverse
from django.views.decorators.cache import cache_page

from botbot.apps.bots.sitemaps import ChannelSitemap


class StaticSitemap(sitemaps.Sitemap):
    priority = 0.5
    changefreq = 'monthly'

    def items(self):
        return ['terms', 'privacy', 'how-to', 'request_channel']

    def location(self, item):
        return reverse(item)



sitemaps = {
    'channels': ChannelSitemap,
    'static': StaticSitemap,
}

urlpatterns = patterns('',
    url(r'^$', cache_page(86400)(sitemap), {'sitemaps': sitemaps},
        name='sitemap'),
)


