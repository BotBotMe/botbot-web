from botbot.celery import app
from .runner import PluginRunner


runner = PluginRunner()
runner.register_all_plugins()

@app.task(bind=True)
def route_line(self, line_json):
    try:
        runner.process_line(line_json)
    # For any error we retry after 10 seconds.
    except Exception as exc:
        raise self.retry(exc, countdown=10)
