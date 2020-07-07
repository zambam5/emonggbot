import cfgai as cfg
import time, logging, json, requests, socket, os
from datetime import datetime

dt = datetime.now().strftime("%Y-%m-%d")
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
filename = 'emotestats' + dt + '.log'
handler = logging.FileHandler(filename, mode='w')
formatter = logging.Formatter('''%(asctime)s -
                              %(name)s - %(levelname)s - %(message)s''')
handler.setFormatter(formatter)
logger.addHandler(handler)


def connect(HOST, PORT):
    global s
    s = None
    try:
        s.close()
    except:
        pass
    s = socket.socket()
    s.settimeout(300)
    try:
        s.connect((HOST, PORT))
    except ConnectionAbortedError:
        logger.info('Connection Failed')


def login(sock, PASS, NICK, CHAN):
    sock.send("PASS {}\r\n".format(PASS).encode("utf-8"))
    sock.send("NICK {}\r\n".format(NICK).encode("utf-8"))
    test = sock.recv(1024).decode("utf-8")
    logger.info(test)

    sock.send("JOIN {}\r\n".format(CHAN).encode("utf-8"))
    test = sock.recv(1024).decode("utf-8")
    logger.info(test)

    sock.send("CAP REQ :twitch.tv/tags\r\n".encode("utf-8"))
    test = sock.recv(1024).decode("utf-8")
    logger.info(test)
    sock.send("CAP REQ :twitch.tv/commands\r\n".encode("utf-8"))
    time.sleep(0.5)
    test = sock.recv(1024).decode("utf-8")
    logger.info(test)


def exponential_backoff():
    global s
    count = 1
    while True:
        try:
            connect(cfg.HOST, cfg.PORT)
            login(s, cfg.PASS, cfg.NICK, cfg.CHAN)
            return True
        except socket.error:
            time.sleep(count)
            count = count*2




def chat(sock, msg, CHAN):
    # this was not written by me
    """
    Send a chat message to the server.
    Keyword arguments:
    sock -- the socket over which to send the message
    msg  -- the message to be sent
    """
    sock.send("PRIVMSG {} :{}\r\n".format(CHAN, msg).encode("utf-8"))
    return True


def pong(sock):
    sock.send("PING :tmi.twitch.tv\r\n".encode("utf-8"))


def splitmessages(response):
    messages = response.splitlines()
    return messages


def message_dict_maker(message):
    messagedict = dict()
    if message.startswith('PING'):
        messagedict['message type'] = 'PING'
        messagedict['time'] = datetime.now()
        return messagedict
    elif 'user-type=' in message:
        messagelist1 = message.split('user-type=')
        messagelist = messagelist1[0].split(';')
        for item in messagelist:
            items = item.split('=')
            try:
                messagedict[items[0]] = items[1]
            except IndexError:
                messagedict[items[0]] = ''
        if "WHISPER" in messagelist1[1]:
            print("whisper")
            messagedict['message type'] = "WHISPER"
        elif "PRIVMSG" in messagelist1[1]:
            messagedict['message type'] = "PRIVMSG"
            firstsplit = messagelist1[1].split(" " + cfg.CHAN + " :")
            messagedict['actual message'] = firstsplit[1].strip(':')
        elif "USERNOTICE" in messagelist1[1]:
            messagedict['message type'] = "USERNOTICE"
        elif "USERSTATE" in messagelist1[1]:
            messagedict['message type'] = "USERSTATE"
        return messagedict
    if message.startswith('badge'):
        return False
    messagelist1 = message.split(' ')
    print(messagelist1)
    if messagelist1[1] == "HOSTTARGET":
        messagedict['message type'] = 'HOSTTARGET'
        messagedict['host target'] = messagelist1[3].strip(':')
    elif messagelist1[1] == "RECONNECT":
        messagedict['message type'] = 'RECONNECT'
    elif messagelist1[2] == "NOTICE":
        messagedict['message type'] = "NOTICE"
    elif messagelist1[2] == "CLEARCHAT":
        messagedict['message type'] = "CLEARCHAT"
    elif messagelist1[2] == "ROOMSTATE":
        messagedict['message type'] = "ROOMSTATE"
    elif messagelist1[2] == "CLEARMSG":
        print('here')
        messagedict['message type'] = "CLEARMSG"
    return messagedict

ffz_stats = {}
bttv_stats = {}
sub_stats = {}

def get_ffz():
    global ffz_stats
    url = 'https://api.frankerfacez.com/v1/room/emongg'
    with requests.get(url) as r:
        emotes = json.loads(r.content)["sets"]["319861"]["emoticons"]
        r.close()
    ffz_emotes = []
    for item in emotes:
        ffz_emotes.append(item["name"])
        if item["name"] not in ffz_stats.keys():
            ffz_stats[item["name"]] = 0
    return ffz_emotes

def get_bttv():
    global bttv_stats
    url = "https://api.betterttv.net/3/cached/users/twitch/23220337"
    with requests.get(url) as r:
        emotes = json.loads(r.content)["sharedEmotes"]
        r.close()
    bttv_emotes = []
    for item in emotes:
        bttv_emotes.append(item['code'])
        if item['code'] not in bttv_stats.keys():
            bttv_stats[item['code']] = 0
    return bttv_emotes

def get_sub():
    global sub_stats
    #url = "https://api.twitch.tv/kraken/chat/emoticon_images?emotesets=300675880"
    #ID = cfg.ID
    #token = cfg.TOKEN
    '''headers = {
            'Client-ID': ID
        }'''
    url = 'https://api.twitchemotes.com/api/v4/channels/23220337'
    with requests.get(url) as r:
        emotes = json.loads(r.content)['emotes']
        r.close()
    sub_emotes = []
    for item in emotes:
        sub_emotes.append(item['code'])
        if item['code'] not in sub_stats.keys():
            sub_stats[item['code']] = 0
    return sub_emotes

ffz_emotes = get_ffz()
print(len(ffz_emotes))
bttv_emotes = get_bttv()
print(len(bttv_emotes))
sub_emotes = get_sub()
print(len(sub_emotes))

word = ''
def ffz():
    global ffz_stats, word
    ffz_stats[word] += 1
    print(ffz_stats[word])

def bttv():
    global bttv_stats, word
    bttv_stats[word] += 1
    print(bttv_stats[word])

def sub():
    global sub_stats, word
    sub_stats[word] += 1
    print(sub_stats[word])


emote_type_switch = {}
for emote in ffz_emotes:
    emote_type_switch[emote] = lambda : ffz()

for emote in bttv_emotes:
    emote_type_switch[emote] = lambda : bttv()

for emote in sub_emotes:
    emote_type_switch[emote] = lambda : sub()

def PRIVMSG(message):
    global word
    if message['display-name'] == 'streamelements' or message['display-name'] == 'zambamai':
        return False
    word_list = message['actual message'].rstrip().split(" ")
    for word in word_list:
        emote_type_switch.get(word, lambda : False)()


def HOSTTARGET(message):
    global ffz_stats, bttv_stats, sub_stats
    target = message['host target']
    if target == '-':
        return False
    else:
        today_stats = {'ffz':ffz_stats, 'bttv':bttv_stats, 'sub':sub_stats}
        today = datetime.today()
        month = today.strftime('%B %Y')
        dirname = './emotelogs/' + month
        if not os.path.exists(dirname):
            os.makedirs(dirname)
            print('Made directory: ' + dirname)
        with open('./emotelogs/' + month + '/' + today.strftime("%Y-%m-%d") +'.json', 'w') as f:
            f.write(json.dumps(today_stats))
            f.close
        for emote in ffz_stats.keys():
            ffz_stats[emote] = 0
        for emote in bttv_stats.keys():
            bttv_stats[emote] = 0
        for emote in sub_stats.keys():
            sub_stats[emote] = 0

def reconnect(HOST, PORT, PASS, NICK, CHAN):
    global s
    connect(HOST, PORT)
    login(s, PASS, NICK, CHAN)

def ping(sock):
    sock.send("PONG :tmi.twitch.tv\r\n".encode("utf-8"))
    logger.info("PING")
    return True

def the_rest():
    return False

message_switch = {
            "WHISPER": lambda : the_rest(),
            "PRIVMSG": lambda : PRIVMSG(messagedict),
            "USERNOTICE": lambda : the_rest(),
            "USERSTATE": lambda : the_rest(),
            "CLEARCHAT": lambda : the_rest(),
            "CLEARMSG": lambda : the_rest(),
            "HOSTTARGET": lambda : HOSTTARGET(messagedict),
            "NOTICE": lambda : the_rest(),
            "ROOMSTATE": lambda : the_rest(),
            "PING": lambda : ping(s),
            "RECONNECT": lambda : reconnect(cfg.HOST, cfg.PORT, cfg.PASS, cfg.NICK, cfg.CHAN)
        }

if __name__ == "__main__":
    connect(cfg.HOST, cfg.PORT)
    login(s, cfg.PASS, cfg.NICK, cfg.CHAN)
    chan = cfg.CHAN[1:]
    while True:
        try:
            response = s.recv(4096).decode("utf-8")
        except socket.timeout:
            print("timed out, attempting reconnect")
            exponential_backoff()
            continue
        if response == "":
            continue
        messagelist = splitmessages(response)
        for message in messagelist:
            try:
                timet = time.time()
                try:
                    messagedict = message_dict_maker(message)
                except:
                    logging.exception(response)
                    continue
                if not messagedict:
                    print('bad message')
                    continue
                else:
                    message_switch.get(messagedict['message type'], lambda : False)()
                print(time.time()-timet)
            except:
                print(message)
                logger.exception("Error processing message")
