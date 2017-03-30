import logging
import os
import random
import re
from datetime import datetime

log = logging.getLogger('vk-bot')


def antidimon(bot, **fields):
    if fields['user_id'] == 36192710 or fields['user_id'] == 49656121:
        bot.api.messages.send(peer_id=fields['peer_id'], sticker_id=3473)
        return True

    return False


def status(bot, **fields):
    if fields['user_id'] in bot.admins:
        if 'PRODUCTION' in os.environ:
            server = 'production'
        else:
            server = 'test'

        now_time = datetime.now()
        formatted_text = '{bot_name} v{bot_version}\nUptime: {start_time}\nRunning on: {server}'.format(
            bot_name=bot.name, bot_version=bot.version, start_time=now_time - bot.start_time, server=server
        )
        bot.api.messages.send(peer_id=fields['peer_id'], message=formatted_text)
    else:
        bot.api.messages.send(peer_id=fields['peer_id'], message='\U0001F643')  # upside down face emoji

    return True


def help(bot, **fields):
    message = 'Помощь:\n'
    for event_handler in bot.event_handlers:
        if event_handler.help_name is not None:
            message += '{} — {}\n'.format(event_handler.help_name, event_handler.help_description)

    bot.api.messages.send(peer_id=fields['peer_id'], message=message)
    return True


def hello(bot, **fields):
    passed = False
    if fields['is_chat']:
        if re.match(r'при+ве+т(?:[\s,]+)(?:ма+рку+с|ma+rcu+s)', fields['text'], flags=re.IGNORECASE) \
                or re.match(r'(?:ма+рку+с|ma+rcu+s)(?:[\s,]+)при+ве+т', fields['text'], flags=re.IGNORECASE):
            passed = True
    else:
        if re.match(r'при+ве+т(?:\W+|$)', fields['text'], flags=re.IGNORECASE):
            passed = True

    if passed:
        emojies = ['\U0001F60E', '\U0001F60A', '\U0001F603', '\U0001F609']
        bot.api.messages.send(peer_id=fields['peer_id'],
                              message='Привет, {name}! {first_emoji}{second_emoji}'.format(
                                  name=fields['user']['first_name'], first_emoji=random.choice(emojies),
                                  second_emoji=random.choice(emojies))
                              )
        return True

    return False


def moon(bot, **fields):
    passed = False
    if fields['is_chat']:
        if re.match(r'(?:ма+рку+с|ma+rcu+s)(?:[\s,]+)🌚', fields['text'], flags=re.IGNORECASE):
            passed = True
    else:
        if fields['text'] == '':
            passed = True

    if passed:
        bot.api.messages.send(peer_id=fields['peer_id'], message='🌝')
        return True

    return False


def change_chat_title(bot, **fields):
    if fields['user_id'] in bot.admins:
        match = re.match("!title (.+)", fields['text'])
        if match:
            bot.set_chat_title(fields['chat_id'], match.group(1))
            bot.api.messages.editChat(chat_id=fields['chat_id'], title=bot.chat_titles[fields['chat_id']])
            return True

    return False


def chat_title_update(bot, **fields):
    if bot.chat_titles.get(fields['chat_id']):
        bot.api.messages.send(peer_id=fields['peer_id'],
                              message='Название беседы заблокировано')
        bot.api.messages.editChat(chat_id=fields['chat_id'],
                                  title=bot.chat_titles.get(fields['chat_id']))
        return True

    return False


def invite(bot, **fields):
    bot.api.messages.send(peer_id=fields['peer_id'],
                          message='Привет всем!')
    return True


def chat_kick(bot, **fields):
    user = bot.api.users.get(user_ids=fields['source_mid'])[0]
    bot.api.messages.send(peer_id=fields['peer_id'],
                          message='Мы будем скучать по тебе, {}...'.format(user['first_name']))
    return True


def chat_invite(bot, **fields):
    user = bot.api.users.get(user_ids=fields['source_mid'])[0]
    messages = [
        'Ну и зачем ты пришёл, {name}?'
    ]
    bot.api.messages.send(peer_id=fields['peer_id'],
                          message=random.choice(messages).format(name=user['first_name']))
    return True
