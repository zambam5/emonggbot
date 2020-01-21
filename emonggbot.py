'''
I really don't wanna take the time to comment this all
a bunch of stuff is stored in text files
don't worry about that stuff :)
'''
import cfgai as cfg
import time,logging,random,json,requests,socket



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
handler = logging.FileHandler('emonggbot.log', mode='w')
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
    test = sock.recv(1024).decode("utf-8")
    logger.info(test)


def chat(sock, msg, CHAN):
    # this was not written by me
    """
    Send a chat message to the server.
    Keyword arguments:
    sock -- the socket over which to send the message
    msg  -- the message to be sent
    """
    sock.send("PRIVMSG {} :{}\r\n".format(CHAN, msg).encode("utf-8"))


def ping(sock, response):
    # check for ping from twitch and respond
    if response == "PING :tmi.twitch.tv\r\n":
        sock.send("PONG :tmi.twitch.tv\r\n".encode("utf-8"))
        return True


def pong(sock):
    sock.send("PING :tmi.twitch.tv\r\n".encode("utf-8"))


def splitmessages(response):
    linecount = response.count('@badge')
    messages = []
    if linecount == 1:
        messages.append(response)
    elif linecount > 1:
        messages1 = response.split('@badge')
        for i in messages1:
            if len(i) == 0:
                continue
            else:
                messages.append(i)
    return messages


def message_dict_maker(message):
    messagelist1 = message.split('user-type=')
    messagelist = messagelist1[0].split(';')
    messagedict = dict()
    for item in messagelist:
        items = item.split('=')
        try:
            messagedict[items[0]] = items[1]
        except IndexError:
            messagedict[items[0]] = ''
    if "PRIVMSG" in messagelist1[1]:
        messagedict['message type'] = "PRIVMSG"
        firstsplit = messagelist1[1].split(" " + cfg.CHAN + " :")
        messagedict['actual message'] = firstsplit[1].strip(':')
    elif "USERNOTICE" in messagelist1[1]:
        messagedict['message type'] = "USERNOTICE"
    return messagedict


def viewer_list(chan):
    # should only need the channel name here
    url = "https://tmi.twitch.tv/group/user/{}/chatters".format(chan)
    r = requests.get(url)
    chatters = json.loads(r.content)['chatters']
    moderators = chatters['moderators']
    viewers = chatters['viewers']
    return moderators, viewers



def sub(sock, subresponse, giftdict):
    '''
    sock to send message
    response is the received message
    giftdict is the dictionary of gifted sub counts
    respond to new subs and resubs
    log number gifted for gift subs
    USERNOTICE is the easiest way to pick the messages out
    pids = potential ids for subs
    '''
    pids = ["msg-id=sub","msg-id=resub","msg-id=subgift",'msg-id=submysterygift']
    if "USERNOTICE" == subresponse['message type']:
        message = subresponse
        msgid = message['msg-id']
        name = message['display-name']
        userid = message['user-id']
        if msgid == "sub":
            newresponses = ["Thanks for the sub {}, and welcome! emongC \r\n".format(name),
                            "Welcome {}! emongA \r\n".format(name),
                            "Welcome Detective {} emongL \r\n".format(name),
                            "Thanks for the sub {} emongGood".format(name),
                            "Welcome {}, and be sure to smile emongSmile".format(name),
                            "Welcome {} emongCool".format(name)
                            ]
            reply = random.choice(newresponses)
            chat(sock, reply,cfg.CHAN)
            logger.info("new sub")
        elif msgid == "resub":
            sublength = message['msg-param-cumulative-months']
            resubresponses = ["Welcome back {}! emongC\r\n".format(name),
                              "Thank you for your continued work Detective {} emongL \r\n".format(name),
                              "Here is your complimentary mustache from your local mustache salesman {} emongB \r\n".format(name),
                              "Thanks for the resub {} emongGood".format(name),
                              "Keep on smiling {} emongSmile".format(name),
                              "Welcome back {} emongCool".format(name)
                              ]
            if int(sublength) >= 24:
                resubresponses.append("Thanks for cancelling your sub {} emongPranked".format(name))
            elif int(sublength) >= 36:
                resubresponses.append("That's almost 2 years {} emongPotato").format(name)
            reply = random.choice(resubresponses)
            chat(sock, reply ,cfg.CHAN)
            logger.info("resub")
        elif name == "AnAnonymousGifter":
            return
        elif msgid == 'submysterygift':
            giftcount = int(message['msg-param-sender-count'])
            giftdict[userid] = giftcount
            with open("giftcounts.txt","w") as f:
                f.write(json.dumps(giftdict))
            logger.info("mystery gift")
        elif msgid == 'subgift':
            giftcount = int(message['msg-param-sender-count'])
            if giftcount == 0:
                #this is to avoid counting for a mass gift
                #could probably just add an "and" to the elif
                return
            else:
                giftdict[userid] = giftcount
                with open("giftcounts.txt","w") as f:
                    f.write(json.dumps(giftdict))
                logger.info("targeted gift")
        return
    return


# noinspection PyShadowingNames,PyShadowingNames
def roulette(response, sock):
    if "PRIVMSG" == response['message type']:
        message = response
        name = message['display-name']
        actualmessage = message['actual message']
        if actualmessage.startswith("!roulette"):
            if message['mod'] == '1':
                if name == "Jasper_The_Winner":
                    chat(sock, "{} I'm on my way Clap2 emongPranked".format(name), cfg.CHAN)
                    return False
                chat(sock, "{} you're a mod, you can't die FeelsWeirdMan".format(name), cfg.CHAN)
                return False
            logger.info("roulette")
            shotlist = [True, True, True, True, True, False]
            oneliners = ["{}'s skull is too thick to be pierced by the bullet".format(name),
                         "{} somehow missed the shot".format(name),
                         "The shot has been fired and  hit, but {} doesn't seem to have noticed?".format(name),
                         "{} chickened out and threw the gun down".format(name),
                         "The trigger is pulled and... *click* {} has survived".format(name)]
            x = random.choice(shotlist)
            if x:
                line = random.choice(oneliners)
                chat(sock, line, cfg.CHAN)
            else:
                chat(sock, "/timeout {} 120 roulette".format(name), cfg.CHAN)
                chat(sock, "RIP in pieces, {}".format(name), cfg.CHAN)
            return True
        else:
            return False


# noinspection PyShadowingNames,PyShadowingNames,PyShadowingNames
def countcommand(s,message,leaderboard,giftdict):
    if message["message type"] == "PRIVMSG":
        response = message['actual message']
        if "!giftcount" in response or "!giftrank" in response:
            name = message['display-name']
            userid = message['user-id']
            if response.startswith("!giftcount"):
                if userid in giftdict.keys():
                    giftcount = giftdict[userid]
                    chat(s,"{} you have gifted {} subs to emongg! If this number is wrong, whisper zambam5".format(name,giftcount),cfg.CHAN)
                else:
                    chat(s,"{} you have not gifted a sub since I started tracking, sorry!".format(name),cfg.CHAN)
            elif response.startswith("!giftrank"):
                if name == "evergreentrail":
                    chat(s,"You have ascended beyond my rankings, and have become the tree under which gifts are placed.",cfg.CHAN)
                elif userid in giftdict.keys():
                    giftcount = giftdict[userid]
                    for i in range(0,len(leaderboard)):
                        if userid in leaderboard[i]:
                            rank = i
                    chat(s,"{} you are unofficially {} out of {} with {} subs gifted".format(name,rank,len(leaderboard)-1,giftcount),cfg.CHAN)
                else:
                    chat(s,"You are currently unranked",cfg.CHAN)


def word_filter(sock,message,banlist):
    if "PRIVMSG" == message['message type']:
        m = message["actual message"]
        mlist = m.split(' ')
        for word in banlist:
            if word in mlist:
                name = message['display-name']
                time.sleep(1)
                chat(sock, "/ban {}".format(name), cfg.CHAN)


def leaderboard(giftdict):
    leaderboard = []
    for name in sorted(giftdict, key=giftdict.get, reverse=True):
        leaderboard.append([name,giftdict[name]])
    return leaderboard


def discord_message(message, webhook):
    data = {}
    name = message['display-name']
    data["content"] = message['actual message']
    data['username'] = name
    data['icon_url'] = "https://static-cdn.jtvnw.net/emoticons/v1/203782/3.0"

    result = requests.post(url, data=data, headers={'Content Type': 'application/json'})


if __name__ == "__main__":
    with open("giftcounts.txt") as f:
        giftdict = eval(f.read())

    with open("bannedwords.txt") as f:
        banlist = [line.split(',') for line in f][0]

    for i in giftdict.keys():
        giftdict[i] = int(giftdict[i])
    with open("giftcounts.txt", "w") as f:
        f.write(json.dumps(giftdict))

    connect(cfg.HOST, cfg.PORT)
    login(s, cfg.PASS, cfg.NICK, cfg.CHAN)
    chan = cfg.CHAN[1:]
    t = time.time()
    timer = time.time()
    timecheck = False
    cd = 15
    while True:
        try:
            response = s.recv(4096).decode("utf-8")
        except UnicodeDecodeError:
            continue
        if response == "":
            continue
        try:
            messagelist = splitmessages(response)
            ping_test = ping(s, response)
            for message in messagelist:
                if "USERSTATE" in message:
                    continue
                try:
                    messagedict = message_dict_maker(message)
                except:
                    logging.exception(response)
                    continue
                leaderb = leaderboard(giftdict)
                sub(s, messagedict, giftdict)
                countcommand(s,messagedict,leaderb,giftdict)
                word_filter(s, messagedict, banlist)
                if 'custom-reward-id' in messagedict.keys():
                    print(messagedict) #just until emongg does a thing
                    if messagedict['custom-reward-id'] == 'tbd':
                        discord_message(messagedict, cfg.URL)
                if time.time() - timer > 30:
                    timecheck = roulette(messagedict, s)
                    if timecheck:
                        timer = time.time()
        except Exception as e:
            logger.exception("error")
            logger.debug(response)
        time.sleep(1/cfg.RATE)
