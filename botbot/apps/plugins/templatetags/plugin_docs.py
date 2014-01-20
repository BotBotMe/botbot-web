from django import template

from .. import utils

register = template.Library()


class PluginDocsNode(template.Node):

    def __init__(self, plugin, channel):
        self.plugin = plugin
        self.channel = channel

    def render(self, context):
        plugin = self.plugin.resolve(context)
        channel = self.channel.resolve(context)
        return utils.plugin_docs_as_html(plugin, channel)


@register.tag
def plugin_docs(parser, token):
    bits = token.split_contents()

    if len(bits) < 3:
        raise template.TemplateSyntaxError("'%s' takes two arguments"
            " (plugin and channel)" % bits[0])

    plugin = parser.compile_filter(bits[1])
    channel = parser.compile_filter(bits[2])

    return PluginDocsNode(plugin, channel)