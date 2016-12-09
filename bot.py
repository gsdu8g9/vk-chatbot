import configparser
import logging
import os
import re
import requests
import commands
from datetime import datetime
import vk_requests as vk
from vk_requests.exceptions import VkAPIError

CHAT_OFFSET = 2000000000

log = logging.getLogger('vk-bot')
log.setLevel(logging.DEBUG)


def remove_urls(text):
    return re.sub(r'(\S+\.\S{2,20})+', '[url_removed]', text, 0, 0)


events = {'set_flags': 1, 'update_flags': 2, 'reset_flags': 3, 'add_message': 4, 'read_inbox': 6, 'read_outbox': 7,
          'online': 8, 'offline': 9, 'update_chat_params': 51, 'start_typing': 61, 'start_typing_char': 62,
          'update_unread_count': 80, 'update_notification_params': 114}

message_flags = {'unread': 1, 'outbox': 2, 'replied': 4, 'important': 8, 'chat': 16, 'friends': 32, 'spam': 64,
                 'deleted': 128, 'fixed': 256, 'media': 512}


class Bot(object):
    def __init__(self):
        self.start_time = None
        self.api = None
        self.bot_user = None
        self.long_poll_server = None
        self.chat_titles = {}
        self.lang = 'ru'

        try:
            self.config = configparser.ConfigParser()
            self.config.read('config.ini')
            self.name = self.config['DEFAULT']['Name']
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

        self.start_time = datetime.now()

        try:
            self.api = vk.create_api(app_id=os.environ['VK_APP_ID'], login=os.environ['VK_LOGIN'],
                                     password=os.environ['VK_PASSWORD'], phone_number=os.environ['VK_LOGIN'],
                                     scope=['friends', 'audio', 'status', 'offline', 'messages', 'groups'],
                                     api_version=self.vk_api_version, interactive=True, lang=self.lang)

            self.bot_user = self.api.users.get()[0]
            self.long_poll_server = self.api.messages.getLongPollServer(use_ssl=1)

            self._add_event_handlers()
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
            self._start_long_polling()

        except KeyboardInterrupt:
            log.info('Interrupt received, shutting down...')
            return True
        except VkAPIError as e:
            log.error('%s %s', e.message, e.error_data)
            return False

    def _start_long_polling(self):
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
                    try:
                        self._handle_event(update)
                    except VkAPIError as e:
                        log.error('%s\n%s', e.message, e.error_data)
                pass

    def _handle_event(self, event):
        log.debug('Event: {}'.format(event))

        if event[0] == events['add_message']:
            self._handle_message(message_id=event[1], flags=event[2], peer_id=event[3], timestamp=event[4],
                                 chat_title=event[5], text=event[6], attachments=event[7], random_id=event[8])

    def _handle_message(self, **fields):

        if fields['peer_id'] > CHAT_OFFSET:
            fields['is_chat'] = True
            fields['chat_id'] = fields['peer_id'] - CHAT_OFFSET
            fields['user_id'] = fields['attachments'].get('from')
            fields['source_act'] = fields['attachments'].get('source_act')
            fields['source_mid'] = fields['attachments'].get('source_mid')
            fields['source_old_text'] = fields['attachments'].get('source_old_text')
            fields['source_text'] = fields['attachments'].get('source_text')
        else:
            fields['is_chat'] = False
            fields['user_id'] = str(fields['peer_id'])
            fields['source_act'] = None
            fields['source_mid'] = None

        fields['user'] = self.api.users.get(user_ids=fields['user_id'])[0]

        for command in self.event_handlers:
            if command.event == events['add_message']:
                text = command.fields.get('text')
                flags = command.fields.get('flags')
                lack_flags = command.fields.get('lack_flags')
                source_act = command.fields.get('source_act')
                source_mid = command.fields.get('source_mid')

                text_check = False
                if isinstance(text, (list, tuple)):
                    for t in text:
                        if t == fields['text']:
                            text_check = True
                            break
                else:
                    text_check = (text is None or text == fields['text'])

                if text_check and (flags is None or fields['flags'] & flags == flags) \
                        and (lack_flags is None or fields['flags'] & lack_flags == fields['flags']) \
                        and (source_act is None or source_act == fields['source_act']) \
                        and (source_mid is None or str(source_mid) == str(fields['source_mid'])):
                    if command.function(self, **fields):
                        return True
                    else:
                        pass

        return False

    def get_long_poll_server_url(self, ts_):
        return 'https://{server}?act=a_check&key={key}&ts={ts}&wait={wait}&mode={mode}\
                    &version={version}'.format(
            server=self.long_poll_server['server'], key=self.long_poll_server['key'], ts=ts_,
            wait=self.poll_config['wait'], mode=self.poll_config['mode'], version=self.poll_config['version'])

    def is_started(self):
        return self.start_time is not None

    def _add_event_handlers(self):
        self.event_handlers = [
            EventHandler(events['add_message'], commands.status, text=['!s', '!status'],
                         lack_flags=(~message_flags['outbox'])),
            EventHandler(events['add_message'], commands.hello, lack_flags=(~message_flags['outbox'])),
            EventHandler(events['add_message'], commands.invite, source_act='chat_invite_user',
                         source_mid=self.bot_user['id'], lack_flags=(~message_flags['outbox'])),
            EventHandler(events['add_message'], commands.change_chat_title, lack_flags=(~message_flags['outbox'])),
            EventHandler(events['add_message'], commands.chat_title_update, source_act='chat_title_update',
                         lack_flags=(~message_flags['outbox'])),
            EventHandler(events['add_message'], commands.help, text=['!h', '!help'])
        ]


class EventHandler(object):
    def __init__(self, event, function, **fields):
        self.event = event
        self.function = function
        self.fields = fields
        self.help_name = fields.get('help_name')
        self.help_description = fields.get('help_description')


# start bot
if __name__ == '__main__':
    Bot().start()
