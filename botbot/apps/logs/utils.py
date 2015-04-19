import json
import redis
import requests
from django.conf import settings

REDIS = redis.StrictRedis.from_url(settings.REDIS_SSE_URL)

def send_event_with_id(event_name, data, event_id, ip, channel):
    REDIS.publish(channel, json.dumps([event_name, data, event_id, ip]))
    requests.post(settings.PUSH_STREAM_URL.format(id=channel.split(':')[1]),
                  headers={'Event-Id': event_id, 'Event-Type': event_name},
                  data=data)

