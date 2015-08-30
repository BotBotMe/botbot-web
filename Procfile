web: manage.py runserver $WEB_PORT
plugins: celery -A botbot worker -l info
bot: botbot-bot -v=2 -logtostderr=true
