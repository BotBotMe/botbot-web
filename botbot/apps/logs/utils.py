import json
import logging

from django.conf import settings
from django.core.cache import cache
import requests
import geoip2.database, geoip2.errors

LOG = logging.getLogger(__name__)

try:
    GEOIP = geoip2.database.Reader(settings.GEOIP_CITY_DB_PATH)
except:
    LOG.warn('Could not open GEOIP database. Map stream is disabled. '
             'Try `make geoip-db` to download a copy.')
    GEOIP = None


def ip_lookup(ip):
    cache_key = 'location:{}'.format(ip)
    coords = cache.get(cache_key)
    if not coords:
        try:
            location = GEOIP.city(ip).location
            coords = (location.latitude, location.longitude)
        except (geoip2.errors.AddressNotFoundError, ValueError):
            coords = (0, 0)
        cache.set(cache_key, coords)
    return coords


def _send_event_with_id(event_name, data, event_id, ip, channel):
    """HTTP POST to Nginx which manages the Server-Sent Events"""
    requests.post(settings.PUSH_STREAM_URL.format(id=channel),
                  headers={'Event-Id': event_id, 'Event-Type': event_name},
                  data=data.encode('utf-8'))
    if GEOIP:
        requests.post(settings.PUSH_STREAM_URL.format(id='glob'),
                      headers={'Event-Id': event_id, 'Event-Type': 'loc'},
                      data=json.dumps(ip_lookup(ip)))

if settings.PUSH_STREAM_URL:
    send_event_with_id = _send_event_with_id
else:
    LOG.info('PUSH_STREAM_URL setting not defined. Realtime updates disabled.')
    send_event_with_id = lambda *a,**kw: None

