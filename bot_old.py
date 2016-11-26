import vk, os, time, datetime, random, codecs, sys, re, requests, json, wolframalpha, wikipedia
from configparser import ConfigParser

VERSION = '0.1'

def removeUrls(text):
    return re.sub(r'(\S+\.\S{2,20})+', '[url_removed]', text, 0, 0)

print('Initializing...')
config = ConfigParser()
config.read('settings.ini')
wolfram = wolframalpha.Client("")
token = os.environ['VK_API_TOKEN']
session = vk.AuthSession(access_token=token)
api = vk.API(session, v='5.60')
bot = api.users.get()
adminid = 207020628
wikipedia.set_lang('ru')
print(' Авторизация успешна.\n  Имя: {} {}, ID: {}.'.format(bot[0]['first_name'], bot[0]['last_name'], bot[0]['id']))
print(' Загрузка и обработка сообщений...')
m_id = 0
start_now_time = datetime.datetime.now()
starttime = start_now_time.strftime('%H:%M:%S %d.%m.%y')
while True:
    now_time = datetime.datetime.now()
    current_time = now_time.strftime('%H:%M:%S')
    # try:
    lastmsg = api.messages.getDialogs(unread=1, count=1)
    if (lastmsg['count'] != 0):
        message = lastmsg['items'][0]['message']
        if (message['out'] == 1):
            continue
        if (message['id'] != m_id):
            s_send = False
            m_from_chat = False
            m_text = removeUrls(message['body'])
            if ('chat_id' in message):
                m_from_peer = 2000000000 + int(message['chat_id'])
                m_from_id = message['user_id']
                m_from_chat_id = message['chat_id']
                m_from_chat_name = removeUrls(message['title'])
                m_from_chat = True
            else:
                m_from_id = message['user_id']
                m_from_peer = m_from_id

            is_admin = False
            shutdown = False
            if (len(m_text) > 0):
                api.messages.send(peer_id=m_from_peer, message=(m_text[::-1]))
            if (m_from_id == adminid):
                is_admin = True
            print('[RX]From: {}, User: {}, Admin: {}'.format(m_from_peer, m_from_id, is_admin))
            if (m_text == '!status'):
                print(' [{}][Info]Requested bot status. ID: {}, Admin: {}'.format(current_time, m_from_id, is_admin))
                if ('PRODUCTION' in os.environ):
                    server = 'production'
                else:
                    server = 'test'

                s_text = 'Bot v{}\nUptime: {}\nRunning on: {}'.format(VERSION, now_time - start_now_time, server)
                s_send = True
                print('[TX]To: {}, Text: {}'.format(m_from_peer, s_text.replace('\n', ' ')))
            if (m_text == '!whoami'):
                print(
                    ' [{}][Info]Requested user information. ID: {}, Admin: {}'.format(current_time, m_from_id, is_admin))
                s_text = 'vkID: {}, Admin: {}'.format(m_from_id, is_admin)
                s_send = True
            if (m_text == '/shutdown'):
                print(' [{}][Info]Requested bot shutdown. ID: {}, Admin: {}'.format(current_time, m_from_id, is_admin))
                if (is_admin):
                    s_text = 'Bot is going down for halt NOW!'
                    shutdown = True
                    s_send = True
                else:
                    s_text = 'You have no permissions to execute this command.'
                    s_send = True
            if (m_text == '/music'):
                try:
                    print(' [{}][Info]Requested a song. Prepearing...'.format(current_time))
                    print('  [Info]Getting music database...')
                    musicdbselection = random.randint(80, 83)
                    if (musicdbselection == 80):
                        musicdb = api.audio.get(owner_id=-39531827)
                        print('  [Info]Selected Monstercat DB')
                        music_source = 'Monstercat'
                    if (musicdbselection == 81):
                        musicdb = api.audio.get(owner_id=-54507092)
                        print('  [Info]Selected FDM DB')
                        music_source = 'FDM'
                    music_count = int(musicdb['count'])
                    r_musicid = random.randint(0, music_count)
                    print('  [Info]Database get. Count {}. Generating random...'.format(music_count))
                    print('  [Info]Random generated: {}. Sending response...'.format(r_musicid))
                    if (int(musicdb['items'][r_musicid]['duration']) > 720):
                        print('[ERROR]This audio seems to be too long for music')
                        raise Exception('Oh, yeah, this audio is too long...')
                    music_owner = musicdb['items'][r_musicid]['owner_id']
                    music_id = musicdb['items'][r_musicid]['id']
                    music_upload_unix = musicdb['items'][r_musicid]['date']
                    music_upload = time.ctime(int(music_upload_unix))
                    api.messages.send(peer_id=m_from_peer,
                                      message='Слушай на здоровье ;)\nДата загрузки: {}\nИсточник: {}'.format(
                                          music_upload, music_source),
                                      attachment='audio{}_{}'.format(music_owner, music_id))
                except Exception:
                    print('[ERROR]Troubles in Music module!')
                    continue
            if (m_text == '/peerinfo'):
                print(
                    ' [{}][Info]Requested peer information. ID: {}, Admin: {}'.format(current_time, m_from_id, is_admin))
                if (m_from_chat):
                    peer_info = api.messages.getChat(chat_id=m_from_chat_id)
                    peer_admin = peer_info['admin_id']
                    peer_uamount = len(peer_info['users'])
                    peer_title = m_from_chat_name
                    s_text = 'Название: {}\nID беседы: {}\nАдминистратор: {}\nКоличество пользователей: {}'.format(
                        peer_title, m_from_chat_id, peer_admin, peer_uamount)
                else:
                    s_text = 'Данная комманда может быть выполнена только внутри чата.'
                s_send = True
                print('[TX]To: {}'.format(m_from_peer))
            if (re.match('/createchat*', m_text)):
                print(' [{}][Info]Chat creation started...'.format(current_time))
                ids = m_text.replace('/createchat ', "")
                ids = ids.split(',')
                ids_count = len(ids)
                i = 0
                allfriends = True
                friendscheck = api.friends.areFriends(user_ids=ids)
                while (i < ids_count):
                    nowfriends = friendscheck[i]['friend_status']
                    if (nowfriends != 3):
                        allfriends = False
                        api.messages.send(peer_id=m_from_peer,
                                          message='Невозможно создать чат: пользователь {} не является другом. areFriends response: {}'.format(
                                              ids[i], nowfriends))
                    i += 1
                if (allfriends):
                    print(' [Info]Users that will be added to chat: {}'.format(ids))
                    time.sleep(1)
                    api.messages.createChat(user_ids=ids, title='Temporary Chatname')
            if (m_text == '/deletechat'):
                if (m_from_chat):
                    if (m_from_id == adminid):
                        print(' [Info]Requested chat cleanup. Chat id: {}'.format(m_from_chat_id))
                        peer_info = api.messages.getChat(chat_id=m_from_chat_id)
                        time.sleep(1)
                        if (peer_info['admin_id'] == bot[0]['id']):
                            print(' [Info]Bot is admin of current chat.')
                            users_amount = len(peer_info['users'])
                            i = 0
                            while (i < users_amount):
                                if (peer_info['users'][i] != bot[0]['id']):
                                    api.messages.removeChatUser(chat_id=m_from_chat_id, user_id=peer_info['users'][i])
                                    print(' [Info]User {} has been removed from {} chat.'.format(peer_info['users'][i],
                                                                                                 m_from_chat_id))
                                i += 1
                            time.sleep(1)
                            api.messages.removeChatUser(chat_id=m_from_chat_id, user_id=bot[0]['id'])
                            print(' [Info]Bot has left {} chat. Cleanup complete.'.format(m_from_chat_id))
                        else:
                            s_text = 'Бот не является администратором текущего чата.'
                            s_send = True
                    else:
                        s_text = 'You have no permissions to execute this command'
                        s_send = True
                else:
                    s_text = 'Данная комманда может быть выполнена только внутри чата'
                    s_send = True
            if (re.match('!rename*', m_text)):
                print(' [{}][Info]Requested chat rename. Chat id: {}'.format(current_time, m_from_chat_id))
                if (m_from_chat):
                    new_name = m_text.replace('!rename ', "")
                    if ('.ru' in new_name):
                        s_text = 'Невозможно переименовать чат, т.к. в новом имени содержится ссылка *.ru'
                        s_send = True
                    else:
                        api.messages.editChat(chat_id=m_from_chat_id, title=new_name)
                else:
                    s_text = 'Данная комманда может быть выполнена только внутри чата'
                    s_send = True

            if (re.match('/adduser*', m_text)):
                ids = m_text.replace('/adduser ', "")
                ids = ids.split(',')
                print(' [{}][Info]Requested user add to current chat. ChatID: {}, UsersID: {}'.format(current_time,
                                                                                                      m_from_chat_id,
                                                                                                      ids))
                ids_count = len(ids)
                i = 0
                friendscheck = api.friends.areFriends(user_ids=ids)
                while (i < ids_count):
                    nowfriends = friendscheck[i]['friend_status']
                    if (nowfriends != 3):
                        api.messages.send(peer_id=m_from_peer,
                                          message='Невозможно добавить в чат: пользователь {} не является другом. areFriends response: {}'.format(
                                              ids[i], nowfriends))
                    else:
                        api.messages.addChatUser(chat_id=m_from_chat_id, user_id=ids[i])
                    i += 1
                    time.sleep(1)
            if (re.match('/kick*', m_text)):
                if (is_admin):
                    ids = m_text.replace('/kick ', "")
                    ids = ids.split(',')
                    print(' [{}][Info]Requested user kick. ChatID: {}, UserID: {}'.format(current_time, m_from_chat_id,
                                                                                          ids))
                    ids_count = len(ids)
                    peer_info = api.messages.getChat(chat_id=m_from_chat_id)
                    chat_users = peer_info['users']
                    i = 0
                    while (i < ids_count):
                        if (int(ids[i]) in chat_users):
                            api.messages.removeChatUser(chat_id=m_from_chat_id, user_id=ids[i])
                            print('  [Info]User {} has been kicked from {} chat'.format(ids[i], m_from_chat_id))
                        else:
                            api.messages.send(peer_id=m_from_peer,
                                              message='Невозможно кикнуть пользователя {}. Пользователь не в чате.'.format(
                                                  ids[i]))
                        i += 1
                        time.sleep(1)
                else:
                    s_text = 'You have no permussions to execute this command'
                    s_send = True
            # if (m_text == '/lockname'):
            #     if (m_from_id == adminid):
            #         peer_title = m_from_chat_name
            #         if (m_from_chat_id not in rename_not_allowed):
            #             rename_not_allowed.append(m_from_chat_id)
            #             config.set('Settings', 'rna', str(rename_not_allowed))
            #             with open('settings.ini', 'w') as configfile:
            #                 config.write(configfile)
            #                 configfile.close()
            #             s_text = 'Успешно. В беседе '{}' запрещено использование /rename'.format(peer_title)
            #             s_send = True
            #         else:
            #             rename_not_allowed.remove(m_from_chat_id)
            #             config.set('Settings', 'rna', str(rename_not_allowed))
            #             with open('settings.ini', 'w') as configfile:
            #                 config.write(configfile)
            #                 configfile.close()
            #             s_text = 'Успешно. В беседе '{}' снят запрет на использование /rename'.format(peer_title)
            #             s_send = True
            #     else:
            #         s_text = 'Данный параметр доступен только для администратора'
            #         s_send = True
            if (re.match('/comeback*', m_text)):
                comeback_chat_id = m_text.replace('/comeback ', "")
                print(' [{}][Info]Requested comeback to {} chat. Trying...'.format(current_time, m_from_chat_id))
                try:
                    api.messages.send(chat_id=comeback_chat_id, message='I\'m back!')
                except Exception:
                    print(' [{}][Info]Cannot comeback to {} chat.'.format(m_from_chat_id))
                    api.messages.send(peer_id=m_from_peer, message='Невозможно вернутся в беседу.')
                    pass
            if (m_text == '/picture'):
                print(' [{}][Info]Requested randome picture. Prepearing...'.format(current_time))
                picture_id = str(random.randint(1, 450000))
                extention = 'jpg'
                if (os.path.exists('temp.{}'.format(extention))):
                    print('  [Info]temp.jpg alredy exists. Removing...')
                    os.remove('temp.{}'.format(extention))
                print('  [Info]Random generated: {}. Getting picture.'.format(picture_id))
                picture = requests.get(
                    'https://wallpapers.wallhaven.cc/wallpapers/full/wallhaven-{}.{}'.format(picture_id, extention))
                if (picture.status_code == 404):
                    print('  [Info]Picture with id {}. Not found... Trying to change to png...'.format(picture_id))
                    extention = 'png'
                    picture = requests.get(
                        'https://wallpapers.wallhaven.cc/wallpapers/full/wallhaven-{}.{}'.format(picture_id, extention))
                if (picture.status_code == 404):
                    print('  [ERROR]Error while downloading picture. 404 Not found.')
                    api.messages.send(peer_id=m_from_peer, message='Невозможно загрузить картинку. Попробуйте еще раз.')
                    raise Exception('Picture Download error')
                else:
                    out = open('temp.{}'.format(extention), 'wb')
                    out.write(picture.content)
                    out.close()
                print('  [Info]Picture downloaded. Requesting server to upload...')
                data = api.photos.getMessagesUploadServer()
                data_user_id = data['user_id']
                data_album_id = data['album_id']
                data_upload_url = data['upload_url']
                print('  [Info]All needed data geted. Uploading photo...')
                r = requests.post(data_upload_url, files={'photo': open('temp.jpg', 'rb')})
                r.status_code == requests.codes.ok
                print('  [Info]Photo uploaded. Saving...')
                params = {'server': r.json()['server'], 'photo': r.json()['photo'], 'hash': r.json()['hash']}
                msgphoto = api.photos.saveMessagesPhoto(**params)
                photoID = msgphoto[0]['id']
                os.remove('temp.{}'.format(extention))
                print(' [Info]Sending response...')
                api.messages.send(peer_id=m_from_peer,
                                  message='Любуйся на здоровье ;)\nИсточник: https://alpha.wallhaven.cc/wallpaper/{}'.format(
                                      picture_id), attachment='photo{}_{}'.format(data_user_id, photoID))
            if (re.match('/wolfram*', m_text)):
                print(' [{}][Info]Requested wolfram calculations...')
                m_text = m_text.replace('/wolfram ', "")
                try:
                    wolfram_response = wolfram.query(m_text)
                    s_text = next(wolfram_response.results).text
                    s_send = True
                except Exception:
                    s_text = 'Что-то пошло не так, попробуй другой запрос'
                    s_send = True
            if (re.match('/wiki*', m_text)):
                print(' [{}][Info]Wikipedia request'.format(current_time))
                m_text = m_text.replace('/wiki ', "")
                try:
                    wiki_response = wikipedia.summary(m_text, sentences=4)
                    s_text = wiki_response
                    s_send = True
                except wikipedia.exceptions.DisambiguationError as e:
                    s_text = 'Возможно, вы имели в виду:\n{}'.format('\n'.join(e.options))
                    s_send = True
                except wikipedia.exceptions.PageError:
                    s_text = 'Такой страницы не существует, попробуй изменить запрос'
                    s_send = True
            # talktobotblock
            if (re.match('Рут,*', m_text)):
                m_text = m_text.replace('Рут, ', "")
                if (m_text == 'привет'):
                    s_text = 'Привет :3'
                if (m_text == 'ты няша ^_^'):
                    s_text = 'ты тоже ^_^'
                if (m_text == 'иди нахуй'):
                    s_text = 'Единственный тут, кто сейчас пойдет нахуй - ты.'
                if (m_text == 'мать ебал'):
                    s_text = 'Мать трогают только конченные петухи, видимо ты один из них.'
                if (m_text == 'я тебя люблю'):
                    if (is_admin):
                        s_text = 'А я тебя ;)'
                    else:
                        s_text = 'А я люблю только Санёчка, так что пошёл нахуй.'
                if (m_text == 'я тебя не люблю'):
                    s_text = 'Ну и пошёл нахуй'
                s_send = True
            # mathblock
            if (re.match('/math*', m_text)):
                m_text = m_text.replace('/math ', "")
                print(' [{}][Info]Requested math function.'.format(current_time))
                if (re.match('random*', m_text)):
                    m_text = m_text.replace('random ', "")
                    randompoints = m_text.split(', ')
                    try:
                        randomnumber = random.randint(int(randompoints[0]), int(randompoints[1]))
                        print(' [Info]Requested random form to: {}'.format(randompoints))
                        s_text = 'Твоё случайное число в диапазоне от {} до {}: {}'.format(randompoints[0],
                                                                                           randompoints[1],
                                                                                           randomnumber)
                        s_send = True
                    except ValueError:
                        s_text = 'Ошибка, оба числа должны быть целыми.'
                        s_send = True
                        pass
                if (m_text == 'about'):
                    s_text = 'Math core v0.1'
            # lastblock
            m_id = lastmsg['items'][0]['message']['id']
            api.messages.markAsRead(peer_id=m_from_peer, message_ids=m_id)
            if (s_send):
                api.messages.send(peer_id=m_from_peer, message=s_text)
            if (shutdown):
                exit()
                # except Exception:
                #	print('GLOBAL EXCEPTION HANDLED!')
                #	continue
    time.sleep(1)
