import json
import redis
from django.conf import settings

REDIS = redis.StrictRedis.from_url(settings.REDIS_SSE_URL)

def send_event_with_id(event_name, data, event_id, ip, channel):
    REDIS.publish(channel, json.dumps([event_name, data, event_id, ip]))
