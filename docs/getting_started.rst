Getting Started
================


Create a Bot and Connect to a Freenode Channel
-----------------------------------------------

Add a new Bot
~~~~~~~~~~~~~

A bot acts as an IRC client. It connects to one or more IRC servers and joins one or more channels per server.

1. Go to ``http://localhost:8000/admin/bots/chatbot/add/``

2. Log in with your username. If you didn’t create a superuser during installation, you can create one via:

.. code-block:: bash

    manage.py createsuperuser

3. Select **'Is active'**
4. **Server:** ``chat.freenode.net:6667``
5. **Nick:** You'll need to create a unique nick for your bot.

.. note::

    `Freenode registration guidelines <http://freenode.net/faq.shtml#userregistration>`_ suggest creating a separate nick if you plan to run a bot.

    It isn't necessary to register your bot's nick right away if you're just trying things out. However, you'll want to choose a nick that isn't already in use. Also, be aware that many channels will require registered nick to join (the +r flag). See IRC Resources for information about valid Freenode nicks. If you're planning on running a bot for real-world or regular use, definitely register your nick. You can check if a nick is registered in your IRC client via::

        /msg NickServ info <desired_nick>

6. **Real Name:** This should be a readable identifier related to your bot: a URL, project name, etc. The spec leaves a lot of room for interpretation about what this value should be. It could probably be any random value but other members of the Freenode community would likely appreciate if you use a sensible name. See **4.1.3 User message** in the `IRC protocol spec <http://www.ietf.org/rfc/rfc1459.txt>`_ for more info.

7. **Save** the Bot. Check the output in the console you started ``honcho`` in. You should see a number of messages indicating the bot has connected to Freenode and identified itself.


Add a Channel
~~~~~~~~~~~~~

Now that your bot is connected to a network or server, you can start having it join channels:

1. Go to ``http://localhost:8000/admin/bots/channel/add/``
2. Select your bot from the dropdown
3. **Channel**: ``#botbot-warmup``. This is a channel commonly used for testing IRC bots.
4. If you'd like the channel to be listed on the site home page, Select **'Is public'**
5. Several useful plugins will already be configured. At a minimum, ``ping`` and ``logger`` will be helpful for testing the bot.
6. Save. In the ``honcho`` console output you should see messages similar to::
7. On the Channel list view, select your channel. From the ``Actions`` dropdown select "Reload botbot-bot configuration" and press "Go". You should see something similar in the ``honcho`` console output (edited for brevity)::

    14:15:07 bot.1      | I0711 14:15:07.557470 61493 botbot.go:67] Command:  REFRESH
    14:15:07 bot.1      | I0711 14:15:07.557546 61493 botbot.go:124] HandleCommand: REFRESH
    14:15:07 bot.1      | I0711 14:15:07.557557 61493 botbot.go:153] Reloading configuration from database
    14:15:07 bot.1      | I0711 14:15:07.557564 61493 network.go:49] Entering in NetworkManager.RefreshChatbots
    14:15:07 bot.1      | I0711 14:15:07.558013 61493 storage.go:121] config.Id: 1
    14:15:07 bot.1      | I0711 14:15:07.558753 61493 storage.go:145] config.Channel: [#botbot-warmup]
    ...
    14:15:07 bot.1      | I0711 14:15:07.559072 61493 irc.go:460] [Info] The channels the bot is connected to need to be updated
    14:15:07 bot.1      | I0711 14:15:07.559083 61493 irc.go:473] [Info] Joining new channel:  #botbot-warmup
    14:15:07 bot.1      | I0711 14:15:07.559096 61493 network.go:98] Exiting NetworkManager.RefreshChatbots
    14:15:07 bot.1      | I0711 14:15:07.559111 61493 irc.go:228] [RAW thahslkd334558 on chat.freenode.net:6667 (0xc208028750) ] --> JOIN #botbot-warmup


8. In your IRC client, join `#botbot-warmup <irc://irc.freenode.net:6667/botbot-warmup>`_. Try issuing a `ping` command (using your bot's nick in place of "mybot"). The bot should respond with a friendly message.
9. Go back to the home page ``http://localhost:8000``, you should see the channel listed as a public channel.
10. **Add another Active Plugin** and this time select **Logger**.
11. **Save**.  Your ``honcho`` console should once again show a refresh
12. In your IRC client, go to `#botbot-warmup <irc:irc.freenode.net:6667/botbot-warmup>`_ and post a message. You should now have a log available at ``http://localhost:8000/freenode/botbot-warmup``. Each message you post in the channel shows up in the ``honcho`` console.


.. warning:
    Currently a UI bug will scroll the message out of view after page load. Scroll up or post several messages in the channel.

You're ready to configure your own channels and utilize other plugins.
