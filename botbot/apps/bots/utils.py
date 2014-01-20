from django.core.urlresolvers import reverse


def reverse_channel(channel, viewname, urlconf=None, args=None, kwargs=None,
        *reverse_args, **reverse_kwargs):
    """
    Shortcut to make reversing a channel view easier.
    """
    kwargs = kwargs or {}

    if channel.slug:
        kwargs['bot_slug'] = 'private'
        kwargs['channel_slug'] = channel.slug
    else:
        kwargs['bot_slug'] = channel.chatbot.slug
        kwargs['channel_slug'] = channel.name.lstrip('#').lower()

    return reverse(viewname, urlconf, args, kwargs, *reverse_args,
        **reverse_kwargs)
