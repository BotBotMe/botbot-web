import json
import datetime
from django_sse import redisqueue

def send_event_with_id(event_name, data, event_id, channel):
    connection = redisqueue._connect()
    connection.publish(channel, json.dumps([event_name, data, event_id]))

def datetime_to_date(dt):
    return datetime.date(*dt.timetuple()[:3])