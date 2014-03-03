Developing with Botbot
========================

Go IRC Client (bot)
-------------------

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
------------

Working with LESS
~~~~~~~~~~~~~~~~~~

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


