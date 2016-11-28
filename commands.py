import os
import random
import re
import logging
from datetime import datetime

log = logging.getLogger('vk-bot')


def status(bot, **fields):
    if fields['user_id'] == bot.admin_id:
        if 'PRODUCTION' in os.environ:
            server = 'production'
        else:
            server = 'test'

        now_time = datetime.now()
        formatted_text = 'Bot v{}\nUptime: {}\nRunning on: {}'.format(
            bot.version, now_time - bot.start_time, server
        )
        bot.api.messages.send(peer_id=fields['peer_id'], message=formatted_text)
    else:
        bot.api.messages.send(peer_id=fields['peer_id'], message='\U0001F643')  # upside down face emoji

    return True


def help(bot, **fields):
    bot.api.messages.send(peer_id=fields['peer_id'],
                          message='Помощь скоро будет! Жди...')
    return True


def hello(bot, **fields):
    if re.match(r'при+ве+т(?:[\s,]+)(?:ма+рку+с|ma+rcu+s)', fields['text'], flags=re.IGNORECASE) \
            if fields['is_chat'] else re.match(r'при+ве+т(?:\W+|$)', fields['text'], flags=re.IGNORECASE):
        emojies = ['\U0001F60E', '\U0001F60A', '\U0001F603', '\U0001F609']
        bot.api.messages.send(peer_id=fields['peer_id'],
                              message='Привет, {}! {}{}'.format(
                                  fields['user']['first_name'], random.choice(emojies), random.choice(emojies))
                              )
        return True

    return False


def invite(bot, **fields):
    bot.api.messages.send(peer_id=fields['peer_id'],
                          message='Привет всем!')
    return True
