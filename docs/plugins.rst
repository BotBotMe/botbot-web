Plugin API Documentation
=========================

You can write your own Botbot plugin by extending the core plugin class and providing one or more message handlers. A
message handler is a method on the plugin class that receives an object representing a user message that has been
posted to the IRC channel the plugin is associated with. The existing plugins in ``botbotme_plugins/plugins`` serve as good examples to follow. **ping** and **brain** are good ones to start with due to their simplicity.

Plugin Capabilities
--------------------

Plugins provide three basic capabilities:

1. Parse messages and optionally respond with an output message.
2. Associate configuration variables. Useful if your plugin needs to connect to external services.
3. Store and retrieve key/value pairs.

All plugins extend the BasePlugin class, providing them with the ability to utilize these capabilities.

Parsing and responding to messages
-----------------------------------

In the simplest case, a plugin will receive a message from an IRC channel and parse it based on a rule. When the parsed input
matches a rule, the plugin may return a response.

Additional methods should be defined on your ``Plugin`` class that will listen and optionally respond to incoming messages. They are registered with the app using one of the following decorators from ``botbotme_plugins.decorators``:

* ``listens_to_mentions(regex)``: A method that should be called only when the bot's nick prefixes the message and that message matches the regex pattern. For example, ``[o__o]: What time is it in Napier, New Zealand?``. The nick will be stripped prior to regex matching.
* ``listens_to_all(regex)``: A method that should be called on any line that matches the regex pattern.

The method should accept a ``line`` object as its first argument and any named matches from the regex as keyword args. Any text returned by the method will be echoed back to the channel.

The ``line`` object has the following attributes:

* ``user``: The nick of the user who wrote the message
* ``text``: The text of the message (stripped of nick if addressed to the bot)
* ``full_text``: The text of the message

Configuration Metadata
-----------------------

Metadata can be associated with your plugin that can be referenced as needed in the message handlers. A common use case for
this is storing authentication credentials and/or API endpoint locations for external services. The ``github`` plugin is an example that uses configuration for the ability to query a Github repository.

To add configuration to your plugin, define a config class that inherits from ``config.BaseConfig``. Configuration values are
declared by adding instances of ``config.Field`` as attributes of the class.

Once your config class is defined, you associate it with the plugin via the ``config_class`` attribute::

    class MyConfig(BaseConfig):
        unwarranted_comments = Field(
            required=False,
            help_text="Responds to every message with sarcastic comment",
            default=True)

    class Plugin(BasePlugin):
        config_class = MyConfig

        @listens_to_all
        def peanut_gallery(self, line):
            if self.config.unwarranted_comments:
                return "Good one!"


Storage / Persisting Data
--------------------------

BasePlugin provides a wrapper around the Redis API that Plugins should use for storage. Since multiple channels can be using the same plugin, keys need to unique per plugin instance. BasePlugin takes care of this for you.


Testing Your Plugins
---------------------

In order to simulate the plugin running in its normal environment, an app instance must be instantiated. See the current
tests for examples. This may change with subsequent releases.
