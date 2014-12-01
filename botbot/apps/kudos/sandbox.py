import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'botbot.settings'

from botbot.apps.bots.models import Channel
from botbot.apps.kudos import utils


django_channel = Channel.objects.filter(name='#django')[0]
result = utils.parse_logs(django_channel.log_set.all(), stdout=sys.stderr)

print('People thanked')
for person in result['kudos']:
    print('{nick} ({count}, {first} - {recent})'.format(**person))
print(
    'Thank you messages: {kudos_given} ({appreciation:.2%} of all '
    'messages)'.format(
        appreciation=result['kudos_given']/float(result['message_count'] or 1),
        **result))
print('People thanked: {}'.format(len(result['kudos'])))
print('Unattributed: {unattributed}'.format(**result))
