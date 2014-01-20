Managing Bots
==============

Multiple Bots
-------------

Bots can be connected to multiple networks. For example you can have a bot that connects to Freenode, and another that connects to Mozilla's IRC network.

Multiple bots for the same network / server is not supported at this time.

Public, Private, and Featured Channels
---------------------------------------

These are primarily distinctions for the Django site and the display of logs.

Public
    Logs for public channels will be available on a public URL like *http://example.com/freenode/django*

Featured
    Featured channels are public channels. Used by `botbot.me <https://botbot.me>`_ for highlighting some public channels. May be deprecated in the future.

Private
    Logs for private channels are only availale to authenticated users of the site. They will have URLs that are not easy to guess.


Freenode
---------

Policy
~~~~~~

Before logging any public channels, take a couple simple steps to ensure no misunderstandings occur.

1. Have the consent of a channel operator.
2. Ask the operator to make it clear in the channel topic that it is being logged.

`Freenode's channel guidelines` <http://freenode.net/channel_guidelines.shtml>`_ don't seem to address non-operator users who want to run bots. (see final bullet point) Our preference is to favor honesty and transparency.

