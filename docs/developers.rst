**********************
Developing with BotBot
**********************

Architecture
============

Several loosely coupled pieces make up the whole of BotBot:

1. **botbot-bot:** An IRC client capable of connecting to multiple IRC networks, and connecting multiple channels and nicks per network. (Go)
2. **botbot-plugins:** A plugin framework - plugins receive messages from IRC channels and can respond within the channel. (Python)
3. **botbot-web:** A web site for managing bots/channels as well as a beautiful public interface for channel logs. (Python/Django)
4. **botbot-eventsource:** A basic SSE provider that the web site can connect to for real-time logs. (Go)

Configuration / Environment Variables
-------------------------------------

At Lincoln Loop we've found the 12-factor style to be helpful and use those guidelines. As recommended, we rely on environment variables whenever possible for determining site-specific configuration values.

The .env file
^^^^^^^^^^^^^

We've adopted a convention used by Heroku and others of creating a ``.env`` file in the project root that can be used as a base for managing environment variables. Tools like Honcho and Foreman will use the ``.env`` file to bootstrap the environment for each process it starts up. If you prefer to use these tools, all you have to worry about is editing the ``.env`` file as needed. The ``.env`` file can also be used as a template for other methods of populating environment variables.

We don't want make assumptions about how developers prefer to configure their environments. There are some handy open source libs out there that we could use to easily make each service utilize the ``.env`` file, but this won't work well for everyone or every environment. If you need to run a service individually, you'll need to make sure the proper environment variables are configured. The next section describes some easy ways to handle this.


Running Services
----------------

Run All Services
^^^^^^^^^^^^^^^^

Honcho is great for getting everything started quickly. Running this command will load all services defined in the ``Procfile``::

    honcho start

Run Services Individually
^^^^^^^^^^^^^^^^^^^^^^^^^

When working on code changes or debugging, it is often desirable to manage one or more of the services (bot, plugin runner, runserver, eventsource) independently.

If you'd like to make use of the ``.env`` file, you can still start services individually using Honcho::

    honcho start web  # Starts Django site
    honcho start bot  # Starts IRC client
    honcho start plugins  # Starts plugin runner
    honcho start realtime # Starts event source (SSE)

If you would prefer not to use Honcho, you'll need to manage the environment variables. Many developers use the virtualenv ``postactivate`` feature to set required environment variables whenever a virtualenv is activated. An alternative approach could be to attempt to set variables directly from the ``.env`` file. As an example, you could put the following into a ``set_env.sh`` file::

    export $(cat .env | grep -v ^# | xargs)

Then you could invoke commands and individual services like::

    source set_env.sh && manage.py runserver
    source set_env.sh && botbot-bot
    source set_env.sh && botbot-eventsource
    source set_env.sh && manage.py run_plugins

If you've explicitly set the environment through your own methods, services can be invoked like usual::

    manage.py runserver
    botbot-bot
    botbot-eventsource
    manage.py run_plugins


Go IRC Client (bot)
~~~~~~~~~~~~~~~~~~~

Execution starts in main.go, in function "main". That starts the chatbots (via NetworkManager), the goroutine which listens for commands from Redis, and the mainLoop goroutine, then waits for a Ctrl-C or kill to quit.

The core of the bot is in mainLoop (main.go). That listens to two Go channels, fromServer and fromBus. fromServer receives everything coming in from IRC. fromBus receives commands from the plugins, sent via a Redis list.

A typical incoming request to a plugin would take this path:


    IRC -> TCP socket -> ChatBot.listen (irc.go) -> fromServer channel -> mainLoop (main.go) -> Dispatcher (dispatch.go) -> redis PUBLISH -> plugin


A reply from the plugin takes this path:


    plugin -> redis LPUSH -> listenCmd (main.go) -> fromBus channel -> mainLoop (main.go) -> NetworkManager.Send (network.go) -> ChatBot.Send (irc.go) -> TCP socket -> IRC


And now, in ASCII art::

    plugins <--> REDIS -BLPOP-> listenCmd (main.go) --> fromBus --> mainLoop (main.go) <-- fromServer <-- n ChatBots (irc.go) <--> IRC
                   ^                                                  | |                                      ^
                   | PUBLISH                                          | |                                      |
                    ------------ Dispatcher (dispatch.go) <----------   ----> NetworkManager (network.go) ----


Django Site
~~~~~~~~~~~~

You can run commands within the Honcho environment using the ``run`` command::

    honcho run manage.py dbshell
    honcho run manage.py syncdb

If you're using the ``set_env`` method::

    source set_env.sh && manage.py dbshell
    source set_env.sh && manage.py syncdb

If you've explicitly set the environment variables, run commands like usual::

    manage.py dbshell
    manage.py syncdb



Working with LESS
~~~~~~~~~~~~~~~~~

LESS requires Node.js. There are shortcuts in the Makefile for installing everything necessary:

.. code-block:: bash

   make less-install

From this point forward, if you need to compile LESS run:

.. code-block:: bash

    make less-compile

To automatically compile whenever you save a change:

.. code-block:: bash

    make less-watch


Plugins
--------

You can optionally run the plugins under gevent (``pip install gevent``) which will parallelize them when running the plugins under load:

.. code-block:: bash

    manage.py run_plugins --with-gevent


