******************************************
Serving BotBot In a Production Environment
******************************************

When you deploy botbot to production, we recommend that you do not use the Procfile. Instead, serve three pieces individually:

* **botbot-web**: should be served as a wsgi application, from the ``wsgi.py`` file located at ``src/botbot/botbot/wsgi.py`` from `uwsgi <https://uwsgi-docs.readthedocs.org/en/latest/>`_, `gunicorn <http://gunicorn.org/>`_, `mod_wsgi <https://code.google.com/p/modwsgi/>`_, or any other wsgi server.
* **botbot-plugins**: should be run as an application from botbot's manage.py file. Use `upstart <http://upstart.ubuntu.com/>`_, `systemd <http://freedesktop.org/wiki/Software/systemd/>`_, `init <http://www.sensi.org/~alec/unix/redhat/sysvinit.html>`_, or whatever your system uses for managing long-running tasks. An example upstart script is provided below.
* **botbot-bot**: should also be run as an application from your system's task management system. An example upstart script is provided below.

Example upstart scripts
-----------------------

``botbot-plugins.conf``:

.. code-block:: bash

    # BotBot Plugins
    # logs to /var/log/upstart/botbot_plugins.log

    description "BotBot Plugins"
    start on startup
    stop on shutdown

    respawn
    env LANG=en_US.UTF-8
    exec /srv/botbot/bin/manage.py run_plugins
    setuid www-data

``botbot-bot.conf``:

.. code-block:: bash

    # BotBot-bot
    # logs to /var/log/upstart/botbot.log

    description "BotBot"
    start on startup
    stop on shutdown

    respawn
    env LANG=en_US.UTF-8
    env STORAGE_URL=postgres://yourdburl
    env REDIS_PLUGIN_QUEUE_URL=redis://localhost:6379/0

    exec /srv/botbot/bin/botbot-bot
    setuid www-data

Running In A Subdirectory
-------------------------

If you intend to run botbot in a subdirectory of your website, for example at ``http://example.com/botbot`` you'll need to add two options to your ``settings.py``:

.. code-block:: python

    FORCE_SCRIPT_NAME = '/botbot'
    USE_X_FORWARDED_HOST = True

