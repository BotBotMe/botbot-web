```
    ____        __  ____        __
   / __ )____  / /_/ __ )____  / /_
  / __  / __ \/ __/ __  / __ \/ __/
 / /_/ / /_/ / /_/ /_/ / /_/ / /__
/_____/\____/\__/_____/\____/\___/

```

[![Build Status](https://api.travis-ci.org/BotBotMe/botbot-web.png)](https://travis-ci.org/BotBotMe/botbot-web)

Botbot is collection of tools for running IRC bots. It has primarily been
used with Freenode channels but works with other IRC networks or servers.

[Documentation](http://botbot.readthedocs.org/en/latest/)


Quickstart Guide:
=================

```
mkvirtualenv botbotenv
cdvirtualenv

# Set necessary environment variables
vi bin/postactivate

```
export GOPATH=$VIRTUAL_ENV
export STORAGE_URL=postgres://user:pass@localhost:5432/botbot
export REDIS_PLUGIN_STORAGE_URL=redis://localhost:6379/0
export REDIS_PLUGIN_QUEUE_URL=redis://localhost:6379/1
export REDIS_SSEQUEUE_URL=redis://localhost:6379/2
export SSE_ENDPOINT_URL=http://localhost:3000/
```

source bin/postactivate

# Clone and install the Django part
mkdir src
git clone git@github.com:BotBotMe/botbot-web.git
pip install -e botbot-web
pip install -r botbot-web/requirements.txt

# Install the Go related part
cd ..
go get github.com/BotBotMe/botbot-bot
go get github.com/BotBotMe/botbot-eventsource

# Setup the database
manage.py syncdb
manage.py migrate
manage.py collectstatic

# Run all of the services at once with Foreman
ln -s src/botbot-web/Procfile
foreman start

# Or each one manually
botbot-bot
botbot-eventsource
manage.py runserver
manage.py run_plugins
```

Go to http://127.0.0.1:8000/admin/ and setup a bot and a channel.
Finally ppen http://127.0.0.1:8000/.
