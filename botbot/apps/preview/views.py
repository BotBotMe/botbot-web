from launchpad.views import Signup

from botbot.apps.bots import models as bots_models


class LandingPage(Signup):
    def get_context_data(self, **kwargs):
        kwargs.update({
            'featured_channels': bots_models.Channel.objects \
                .filter(is_public=True, is_featured=True, is_active=True) \
                .select_related('chatbot'),
            'public_not_featured_channels': bots_models.Channel.objects \
                .filter(is_public=True, is_featured=False, is_active=True) \
                .select_related('chatbot')
        })
        return kwargs
