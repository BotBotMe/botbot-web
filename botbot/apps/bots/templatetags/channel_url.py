from django import template
from django.template.defaulttags import kwarg_re
from django.utils.encoding import smart_str

from .. import utils

register = template.Library()


class ChannelURLNode(template.Node):

    def __init__(self, channel, view_name, args, kwargs):
        self.channel = channel
        self.view_name = view_name
        self.args = args
        self.kwargs = kwargs

    def render(self, context):
        channel = self.channel.resolve(context)
        view_name = self.view_name.resolve(context)

        args = [arg.resolve(context) for arg in self.args]
        kwargs = dict([(smart_str(k, 'ascii'), v.resolve(context))
                       for k, v in self.kwargs.items()])

        return utils.reverse_channel(channel, view_name, args=args,
            kwargs=kwargs, current_app=context.current_app)


@register.tag
def channel_url(parser, token):
    bits = token.split_contents()

    if len(bits) < 3:
        raise template.TemplateSyntaxError("'%s' takes at least one argument"
            " (channel and view name)" % bits[0])

    channel = parser.compile_filter(bits[1])
    viewname = parser.compile_filter(bits[2])
    bits = bits[3:]

    args = []
    kwargs = {}

    if len(bits):
        for bit in bits:
            match = kwarg_re.match(bit)
            if not match:
                raise template.TemplateSyntaxError("Malformed arguments to "
                    "url tag")
            name, value = match.groups()
            if name:
                kwargs[name] = parser.compile_filter(value)
            else:
                args.append(parser.compile_filter(value))

    return ChannelURLNode(channel, viewname, args, kwargs)
