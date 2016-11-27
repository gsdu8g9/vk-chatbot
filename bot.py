import configparser
import datetime
import logging
import os
import re
import requests
import random
import vk_requests as vk
from vk_requests.exceptions import VkAPIError
from enum import IntEnum, unique

CHAT_OFFSET = 2000000000

log = logging.getLogger('vk-bot')
log.setLevel(logging.DEBUG)


def remove_urls(text):
    return re.sub(r'(\S+\.\S{2,20})+', '[url_removed]', text, 0, 0)


message_flags = {'unread': 1, 'outbox': 2, 'replied': 4, 'important': 8, 'chat': 16, 'friends': 32, 'spam': 64,
                'deleted': 128, 'fixed': 256, 'media': 512}


class Bot(object):
    def __init__(self):

        self.start_time = None
        self.api = None
        self.bot_user = None
        self.long_poll_server = None
        self.lang = 'ru'

        try:
            self.config = configparser.ConfigParser()
            self.config.read('config.ini')
            self.version = self.config['DEFAULT']['Version']
            self.vk_api_version = self.config['DEFAULT']['VkApiVersion']
            self.admin_id = self.config['DEFAULT']['AdminId']

            self.poll_config = {'mode': 170, 'wait': 25, 'version': 1}
        except configparser.Error:
            log.exception('Error while reading config')
        except KeyError:
            log.exception('One or more keys in config are missing')

        log.info('Initializing...')

    def start(self):
        if self.is_started():
            return False

        self.start_time = datetime.datetime.now()

        try:
            self.api = vk.create_api(app_id=os.environ['VK_APP_ID'], login=os.environ['VK_LOGIN'],
                                     password=os.environ['VK_PASSWORD'], phone_number=os.environ['VK_LOGIN'],
                                     scope=['friends', 'audio', 'status', 'offline', 'messages', 'groups'],
                                     api_version=self.vk_api_version, interactive=True, lang=self.lang)

            self.bot_user = self.api.users.get()[0]
            self.long_poll_server = self.api.messages.getLongPollServer(use_ssl=1)
        except VkAPIError as e:
            log.exception('Connection failure: {}'.format(e.message))
            return False

        log.info('Authorization success.')
        log.info('Name: {} {}, ID: {}, lang: {}'.format(
            self.bot_user['first_name'], self.bot_user['last_name'], self.bot_user['id'], self.lang)
        )

        log.info('Connected!')

        # start long polling
        try:
            request_url = self.get_long_poll_server_url(self.long_poll_server['ts'])

            while True:
                try:
                    response = requests.post(request_url).json()
                except ValueError:
                    response = None
                    pass

                log.debug('Response: {}'.format(response))

                if response:
                    request_url = self.get_long_poll_server_url(response['ts'])

                    for update in response['updates']:

                        if update[0] == 4:
                            try:
                                self._handle_message(update)
                            except VkAPIError as e:
                                log.error('%s\n%s', e.message, e.error_data)
                    pass

        except KeyboardInterrupt:
            log.info('Interrupt received, shutting down...')
            return True
        except VkAPIError as e:
            log.error('%s %s', e.message, e.error_data)
            return False

    def _handle_message(self, message):
        log.debug('Message: {}'.format(message))

        message_id = message[1]
        flags = message[2]
        peer_id = message[3]
        timestamp = message[4]
        text = message[6]

        chat_id = None

        user_id = None
        user = None

        if peer_id > CHAT_OFFSET:
            chat_id = peer_id - CHAT_OFFSET
            user_id = message[7].get("from", "?")
            user = self.api.users.get(user_ids=user_id)[0]
            chat_title = message[5]
            is_chat = True
        else:
            user_id = str(message[3])
            user = self.api.users.get(user_ids=user_id)[0]

        if flags & message_flags['outbox'] == 0:  # if inbox
            if text == "!s":
                if self._is_admin(user_id):
                    if 'PRODUCTION' in os.environ:
                        server = 'production'
                    else:
                        server = 'test'

                    now_time = datetime.datetime.now()
                    s_text = 'Bot v{}\nUptime: {}\nRunning on: {}'.format(
                        self.version, now_time - self.start_time, server
                    )
                    self.api.messages.send(peer_id=peer_id, message=s_text)
                else:
                    self.api.messages.send(peer_id=peer_id, message='\U0001F643')  # upside down face emoji
            elif re.match(r'при+ве+т(?:[\s,]+)(?:ма+рку+с|ma+rcu+s)', text, flags=re.IGNORECASE) if chat_id else \
                    re.match(r'при+ве+т(?:\W+|$)', text, flags=re.IGNORECASE):
                emojies = ['\U0001F60E', '\U0001F60A', '\U0001F603', '\U0001F609']
                self.api.messages.send(peer_id=peer_id,
                                       message='Привет, {}! {}{}'.format(
                                           user['first_name'], random.choice(emojies), random.choice(emojies))
                                       )

    def _is_admin(self, user_id):
        return user_id == self.admin_id


    def get_long_poll_server_url(self, ts_):
        return 'https://{server}?act=a_check&key={key}&ts={ts}&wait={wait}&mode={mode}\
                    &version={version}'.format(
            server=self.long_poll_server['server'], key=self.long_poll_server['key'], ts=ts_,
            wait=self.poll_config['wait'], mode=self.poll_config['mode'], version=self.poll_config['version'])

    def is_started(self):
        return self.start_time != None


if __name__ == '__main__':
    Bot().start()
