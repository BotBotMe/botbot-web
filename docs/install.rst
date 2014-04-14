==================
Installation
==================

Pre-requisites
---------------

Some of the suggested commands that follow may require root privileges on your system.

Python
~~~~~~~

* Python 2.7

Postgresql with hStore extension
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **OS X**:

  * Homebrew: installed by default
  * Postgres.app: installed by default

* **Ubuntu**: ``apt-get install postgresql-contrib-9.1``

Go
~~

* **OS X**: ``brew install go``
* **Ubuntu**: ``apt-get install golang-go``

Redis
~~~~~

* **OS X**: ``brew install redis``
* **Ubuntu**: ``apt-get install redis-server``

Install
--------

Run in a terminal:

.. code-block:: bash

    virtualenv botbot && source botbot/bin/activate
    pip install -e git+https://github.com/BotBotMe/botbot-web.git#egg=botbot
    cd $VIRTUAL_ENV/src/botbot

    # This builds the project environment and will run for at least several minutes
    make dependencies

    # Adjust ``.env`` file if necessary. Defaults are chosen for local debug environments.
    # If your Postgres server requires a password, you'll need to override DATABASE_URL
    # The default database name is 'botbot'
    $EDITOR .env

    createdb botbot
    echo "create extension hstore" | psql botbot
    manage.py syncdb --migrate

    # You'll need a staff account for creating a bot and registering channels
    manage.py createsuperuser

Redis needs to be running prior to starting the BotBot services. For example:

.. code-block:: bash

    redis-server

Then, to run all the services defined in ``Procfile``:

.. code-block:: bash

    honcho start

.. note:: `foreman <http://ddollar.github.com/foreman/>`_ will also work if you have the gem or Heroku toolbelt installed.

You should now be able to access the site at ``http://localhost:8000``. Log in with the username you created.

See :doc:`getting_started` for instructions on configuring a bot.

Environment Variables to override
---------------------------------::

    # Django (required)
    WEB_SECRET_KEY=supersecretkeyhere

    # DB Storage where channel/bot information is stored
    STORAGE_URL=postgres://user:pass@localhost:5432/botbot

    # Pipes
    REDIS_PLUGIN_STORAGE_URL=redis://localhost:6379/1
    REDIS_PLUGIN_QUEUE_URL=redis://localhost:6379/2
    REDIS_SSEQUEUE_URL=redis://localhost:6379/3

    # The host and port eventsource is delivering and the browser is listening
    # for live changes.
    SSE_ENDPOINT_URL=http://localhost:3000/

    # Specific Django settings to override
    # MEMCACHE_URL=127.0.0.1:11211
    # STATIC_ROOT=/var/www/botbot/static
    # MEDIA_ROOT=/var/www/botbot/uploads
    # DEBUG=True
    # SMTP_URL=smtp://user:pass@host:port
    # SMTP_TLS=True
    # ALLOWED_HOSTS=host1,host2
    # INCLUDE_DJANGO_ADMIN=False
    # EXCLUDE_NICKS=nick1,nick2

Serving In Production
---------------------

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
    env DATABASE_URL=postgres://yourdburl
    env REDIS_PLUGIN_QUEUE_URL=redis://localhost:6379/0

    exec /srv/botbot/bin/botbot-bot
    setuid www-data

Running In A Subdirectory
-------------------------

If you intend to run botbot in a subdirectory of your website, for example at ``http://example.com/botbot`` you'll need to add two options to your ``settings.py``:

.. code-block:: python

    FORCE_SCRIPT_NAME = '/botbot'
    USE_X_FORWARDED_HOST = True


Running Tests
--------------

The tests can currently be run with the following command:

.. code-block:: bash

    manage.py test accounts bots logs plugins


Building Documentation
----------------------

Documentation is available in ``docs`` and can be built into a number of
formats using `Sphinx <http://pypi.python.org/pypi/Sphinx>`_:

.. code-block:: bash

    pip install Sphinx
    cd docs
    make html

This creates the documentation in HTML format at ``docs/_build/html``.
