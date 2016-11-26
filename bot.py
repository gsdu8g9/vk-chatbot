import configparser
import datetime
import logging
import os
import re
import requests
import random
import vk_requests as vk
from vk_requests.exceptions import VkAPIError

CHAT_OFFSET = 2000000000

log = logging.getLogger('vk-bot')
log.setLevel(logging.DEBUG)


def remove_urls(text):
    return re.sub(r'(\S+\.\S{2,20})+', '[url_removed]', text, 0, 0)


class Bot(object):
    def __init__(self):

        self.start_time = None
        self.api = None
        self.bot_user = None
        self.lang = 'ru'

        try:
            self.config = configparser.ConfigParser()
            self.config.read('config.ini')
            self.version = self.config['DEFAULT']['Version']
            self.vk_api_version = self.config['DEFAULT']['VkApiVersion']
            self.admin_id = self.config['DEFAULT']['AdminId']
        except configparser.Error:
            log.exception('Error while reading config')
        except KeyError:
            log.exception('One or more keys in config are missing')

        log.info('Initializing...')

    def start(self):
        self.start_time = datetime.datetime.now()

        try:
            self.api = vk.create_api(app_id=os.environ['VK_APP_ID'], login=os.environ['VK_LOGIN'],
                                     password=os.environ['VK_PASSWORD'], phone_number=os.environ['VK_LOGIN'],
                                     scope=['friends', 'audio', 'status', 'offline', 'messages', 'groups'],
                                     api_version=self.vk_api_version, interactive=True, lang=self.lang)

            self.bot_user = self.api.users.get()[0]
        except VkAPIError as e:
            log.exception('Connection failure: {}'.format(e.message))
            return False

        log.info('Authorization success.\n  Name: {} {}, ID: {}.'.format(
            self.bot_user['first_name'], self.bot_user['last_name'], self.bot_user['id'])
        )

        log.info('Connected!')

        # start long polling
        poll_config = {'mode': 170, 'wait': 25, 'version': 1}

        try:
            long_poll = self.api.messages.getLongPollServer(use_ssl=1)
            poll_server = 'https://{server}?act=a_check&key={key}&ts={ts}&wait={wait}&mode={mode}\
            &version={version}'.format(
                server=long_poll['server'], key=long_poll['key'], ts=long_poll['ts'],
                wait=poll_config['wait'], mode=poll_config['mode'], version=poll_config['version'])

            while True:

                try:
                    response = requests.post(poll_server).json()
                except ValueError:
                    response = None
                    pass

                log.debug('Response: {}'.format(response))

                if response:
                    poll_server = 'https://{server}?act=a_check&key={key}&ts={ts}&wait={wait}&mode={mode}\
                    &version={version}'.format(
                        server=long_poll['server'], key=long_poll['key'], ts=response['ts'],
                        wait=poll_config['wait'], mode=poll_config['mode'], version=poll_config['version'])

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

    def _handle_message(self, message):
        log.debug('Message: {}'.format(message))

        message_id = message[1]
        flags = message[2]
        peer_id = message[3]
        timestamp = message[4]
        text = message[6]

        user_id = None
        user = None

        is_chat = False

        if peer_id > CHAT_OFFSET:
            user_id = message[7].get("from", "?")
            user = self.api.users.get(user_ids=user_id)[0]
            title = message[5]
            is_chat = True
        else:
            user_id = str(message[3])
            user = self.api.users.get(user_ids=user_id)[0]

        if flags & 2 == 0: # if inbox
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
            elif re.match(r'при+ве+т(?:[\s,]+)(?:ма+рку+с|ma+rcu+s)', text, flags=re.IGNORECASE) if is_chat else \
                    re.match(r'при+ве+т(?:\W+|$)', text, flags=re.IGNORECASE):
                emojies = ['\U0001F60E', '\U0001F60A', '\U0001F603', '\U0001F609']
                self.api.messages.send(peer_id=peer_id,
                                       message='Привет, {}! {}{}'.format(
                                           user['first_name'], random.choice(emojies), random.choice(emojies))
                                       )

    def _is_admin(self, user_id):
        return user_id == self.admin_id


if __name__ == '__main__':
    Bot().start()
