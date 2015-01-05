# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import collections
import re

from django.core.management.base import OutputWrapper

RE_KUDOS = re.compile(
    r'\b(?:'
    r'thanks|thank ?you|thx|thnx|thanx|ty|tysm|tyvm|cheers'
    r'|danke(:?sch.n)?'
    r'|gracias'
    r'|merci'
    r')\b')

RE_DIRECTED = re.compile(
    ' *(?:({irc_nick_chars}+)[:,]|@({irc_nick_chars}+))'.format(
        irc_nick_chars=r'[-a-zA-Z0-9_\\\[\]{}^`|]'))


def directed_message(message):
    match = RE_DIRECTED.match(message)
    if match:
        for g in match.groups():
            if g:
                return g


def _iterate_log(qs, block_size=100000):
    """
    Split iteration of the queryset into blocks of 100,000 for increased
    performance.
    """
    qs = qs.order_by('pk')
    last_pk = 0
    while last_pk is not None:
        block_qs = qs.filter(pk__gt=last_pk)[:block_size]
        last_pk = None
        for obj in block_qs.iterator():
            yield obj
            last_pk = obj[0]


def parse_logs(qs, stdout=None):
    """
    Parse logs for kudos.
    """
    names = collections.deque(maxlen=200)
    unattributed = 0
    count = 0
    kudos = {}
    kudos_count = 0
    kudos_first = {}
    kudos_recent = {}

    if stdout and not isinstance(stdout, OutputWrapper):
        stdout = OutputWrapper(stdout)

    def set_thanked(nick):
        timestamp = log[3]
        kudos[nick] = kudos.get(nick, 0) + 1
        kudos_first.setdefault(nick, timestamp)
        kudos_recent[nick] = timestamp

    qs = qs.order_by('pk').filter(command='PRIVMSG')
    qs = qs.values_list('pk', 'nick', 'text', 'timestamp')
    for log in _iterate_log(qs):
        log_nick = log[1].lower()
        log_text = log[2]
        count += 1
        directed = directed_message(log_text)
        if directed:
            directed = directed.lower()
            if directed == log_nick:
                # Can't thank yourself :P
                directed = None
        if RE_KUDOS.search(log_text):
            kudos_count += 1
            attributed = False
            if directed:
                for nick, _ in names:
                    if nick == directed:
                        set_thanked(nick)
                        attributed = True
                        break
            if not attributed:
                lower_text = log_text.lower()
                for recent in (
                        bits[0] for bits in names if bits[0] != log_nick):
                    re_text = '(?:^| )@?{}(?:$|\W)'.format(re.escape(recent))
                    if re.search(re_text, lower_text):
                        set_thanked(recent)
                        attributed = True
            if not attributed:
                for nick, directed in names:
                    if directed == log_nick:
                        set_thanked(nick)
                        attributed = True
                        break
            if not attributed:
                unattributed += 1
        names.append((log_nick, directed))
        if stdout and not count % 10000:
            stdout.write('.', ending='')
            stdout.flush()
    if stdout:
        stdout.write('')

    kudos_list = []
    for c, nick in sorted((c, nick) for nick, c in kudos.items()):
        kudos_list.append({
            'nick': nick,
            'count': c,
            'first': kudos_first[nick],
            'recent': kudos_recent[nick]
        })
    return {
        'kudos': kudos_list,
        'message_count': count,
        'kudos_given': kudos_count,
        'unattributed': unattributed,
    }
