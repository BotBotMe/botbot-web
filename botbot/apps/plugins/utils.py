from django.template import Template, Context
from django.template.defaultfilters import urlize
import markdown

def plugin_docs_as_html(plugin, channel):
    tmpl = Template(plugin.user_docs)
    ctxt = Context({
        'nick': channel.chatbot.nick,
        'channel': channel,
        'SITE': 'https://botbot.me',
    })
    return markdown.markdown(urlize(tmpl.render(ctxt)))