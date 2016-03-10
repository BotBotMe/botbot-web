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

* **Ubuntu**: ``apt-get install postgresql-contrib-9.3 postgresql-server-dev-9.3 python-dev virtualenvwrapper``

Go
~~

Version 1.2 or higher required

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
    # If your Postgres server requires a password, you'll need to override STORAGE_URL
    # The default database name is 'botbot'
    $EDITOR .env

    # Make the variables available to subprocesses
    export $(cat .env | grep -v ^# | xargs)

    createdb botbot
    echo "create extension hstore" | psql botbot
    manage.py migrate

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

If you plan make code changes, please read through the :doc:`developers` doc.

If you plan to run BotBot in a production environment please read the :doc:`production` doc.


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
