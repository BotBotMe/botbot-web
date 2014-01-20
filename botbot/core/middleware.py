from django.utils import timezone

class TimezoneMiddleware(object):
    def process_request(self, request):
        tz = request.session.get('django_timezone', "UTC") or "UTC"
        timezone.activate(tz)
