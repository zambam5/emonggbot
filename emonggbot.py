'''
I really don't wanna take the time to comment this all
a bunch of stuff is stored in text files
don't worry about that stuff :)
'''
import cfgai as cfg
import time, logging, random, json, requests, socket, re
import spotipy
import spotipy.util as util
from datetime import datetime

dt = datetime.now().strftime("%Y-%m-%d")
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
filename = 'emonggbot' + dt + '.log'
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
    messagelist1 = message.split(' ')
    print(messagelist1)
    if messagelist1[1] == "HOSTTARGET":
        messagedict['message type'] = 'HOSTTARGET'
        messagedict['host target'] = messagelist1[3].strip(':')
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
    


def viewer_list(chan):
    # should only need the channel name here
    url = "https://tmi.twitch.tv/group/user/{}/chatters".format(chan)
    r = requests.get(url)
    chatters = json.loads(r.content)['chatters']
    moderators = chatters['moderators']
    viewers = chatters['viewers']
    return moderators, viewers


time_roulette = time.time()
def roulette(response, sock):
    global time_roulette
    if time.time() - time_roulette < 30:
        return False
    name = response['display-name']
    if response['mod'] == '1':
        if name == "Jasper_The_Winner":
            return chat(sock, "{} I'm on my way Clap2 emongPranked".format(name), cfg.CHAN)
        return chat(sock, "{} you're a mod, you can't die FeelsWeirdMan".format(name), cfg.CHAN)
    else:
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
        time_roulette = time.time()
        return True


def countcommand(s,message,leaderboard,giftdict):
    '''
    giftdict is a dictionary with user id strings as keys and int gift values
    leaderboard is an ordered list of tuples by highest gift value
    user id is used in case the user changes their username
    '''
    response = message['actual message']
    name = message['display-name']
    userid = message['user-id']
    if response.startswith("!giftcount"):
        if userid in giftdict.keys():
            giftcount = giftdict[userid]
            return chat(s,"{} you have gifted {} subs to emongg! If this number is wrong, whisper zambam5".format(name,giftcount),cfg.CHAN)
        else:
            return chat(s,"{} you have not gifted a sub since I started tracking, sorry!".format(name),cfg.CHAN)
    elif response.startswith("!giftrank"):
        if userid in giftdict.keys():
            giftcount = giftdict[userid]
            for i in range(0,len(leaderboard)):
                if userid in leaderboard[i]:
                    rank = i+1
                    break
            return chat(s,"{} you are unofficially {} out of {} with {} subs gifted".format(name,rank,len(leaderboard),giftcount),cfg.CHAN)
        else:
            return chat(s,"You are currently unranked",cfg.CHAN)


def word_filter(sock,message,banlist):
    '''
    ban people who say bad thing
    banlist contain bad thing
    '''
    m = message["actual message"]
    mlist = m.split(' ')
    for word in banlist:
        if word in mlist:
            name = message['display-name']
            time.sleep(1)
            return chat(sock, "/ban {}".format(name), cfg.CHAN)


def leaderboard(giftdict):
    '''
    takes the gift dict and orders it from highest to lowest
    '''
    leaderboard = []
    for name in sorted(giftdict, key=giftdict.get, reverse=True):
        leaderboard.append([name,giftdict[name]])
    return leaderboard


def remove_preview(message):
    if '.com' in message or '.be' in message:
        mlist = message.split(' ')
        for idx, item in enumerate(mlist):
            if '.com' in item or '.be' in item:
                if item.endswith("\r\n"):
                    print('found one')
                    item = item[:-2]
                item = '<' + item + '>'
                mlist[idx] = item
        message = ' '.join(mlist)
    return message


def extract_link(message):
    match = re.search(r"(?P<url>open.spotify.com[^\s]+)", message)
    if match is not None:
        return match.group("url")
    else:
        return None


def discord_message(name, content, url):
    data = {}
    #m = remove_preview(m)
    data["content"] = content
    data['username'] = name
    data['icon_url'] = "https://static-cdn.jtvnw.net/emoticons/v1/203782/3.0"

    requests.post(url, data=data, headers={'Content Type': 'application/json'})

#spotify stuff with a z at the end is for my account
userz = cfg.SPOTIFY_USERz
playlist = cfg.SPOTIFY_PLAYLIST
history = cfg.SPOTIFY_PLAYLIST2
CACHEz = '.zambamoauthcache'
oauthz = spotipy.oauth2.SpotifyOAuth(cfg.SPOTIFY_ID, cfg.SPOTIFY_SECRET,
                                    cfg.SPOTIFY_REDIRECT,
                                    scope='playlist-modify-public playlist-modify-private',
                                    cache_path=CACHEz)

tokenz = oauthz.get_cached_token()
if tokenz:
    spz = spotipy.Spotify(auth=tokenz['access_token'])
else:
    print("Can't get token for ", user_config['username'])

#this is for emongg's account
user = cfg.SPOTIFY_USER
CACHE = '.emonggoauthcache'
oauth = spotipy.oauth2.SpotifyOAuth(cfg.SPOTIFY_ID, cfg.SPOTIFY_SECRET,
                                    cfg.SPOTIFY_REDIRECT,
                                    scope='playlist-modify-public playlist-modify-private',
                                    cache_path=CACHE)
token = oauth.get_cached_token()
if token:
    sp = spotipy.Spotify(auth=token['access_token'])
else:
    print ("Can't get token for ", user_config['username'])


screwup = dict()
def song_requests(sock, message, url):
    global userz, playlist, spz, tokenz, oauthz, history, screwup
    try:
        expired = spotipy.oauth2.is_token_expired(tokenz)
    except spotipy.client.SpotifyException:
        logger.info("error")
    if expired:
        try:
            tokenz = oauthz.refresh_access_token(tokenz['refresh_token'])
        except spotipy.client.SpotifyException:
            logger.info("error")
        spz = spotipy.Spotify(auth=tokenz['access_token'])
        logger.info('token refreshed?')
    name = message['display-name']
    m = message['actual message']
    song = extract_link(m)
    if song == None:
        chat(sock, "{}, be sure your link is for open.spotify.com. You can try a differnt link in the next 5 minutes using the !requeue command".format(name), cfg.CHAN)
        content = 'Request did not include a spotify link: \"' + m +'\"'
        discord_message(name, content, cfg.URL)
        screwup[name] = (True, time.time())
    elif "track" not in song:
        chat(sock, "{}, be sure the Spotify link includes \"track\". You can try a different link in the next 5 minutes using the !requeue command".format(name), cfg.CHAN)
        content = 'Request was not a song link: \"' + m +'\"'
        discord_message(name, content, cfg.URL)
        screwup[name] = (True, time.time())
    else:
        songl = [song]
        try:
            track1 = spz.track(song)
        except spotipy.client.SpotifyException:
            chat(sock, "{}, that link is dead or returned an error. You can try a different link in the next 5 minutes using the !requeue command. If the error happens again notify a mod.".format(name), cfg.CHAN)
            content = 'Song link is dead or returned an error \"' + m + '\"'
            discord_message(name, content, cfg.URL)
            screwup[name] = (True, time.time())
        track = track1['id']
        #features = sp.audio_features(songl)[0]
        #length = features['duration_ms']
        length = track1['duration_ms']
        tracks = spz.playlist_tracks(playlist)['items']
        '''if 'US' not in track1['available_markets']:
            chat(sock, "{}, sorry that song is not available in the US".format(name), cfg.CHAN)'''
        if length > 300000:
            chat(sock, "{}, we have a 5 minute limit on songs. You can try a different song in the next 5 minutes using the !requeue command.".format(name), cfg.CHAN)
            content = 'Request is too long: \"' + m +'\"'
            discord_message(name, content, cfg.URL)
            screwup[name] = (True, time.time())
        elif len(tracks) < 1:
            spz.user_playlist_add_tracks(userz, playlist, songl, position=None)
            spz.user_playlist_add_tracks(userz, history, songl, position=None)
            chat(sock, "{}, song added to playlist".format(name), cfg.CHAN)
            content = 'Request added to playlist: \"' + m +'\"'
            discord_message(name, content, cfg.URL)
            screwup[name] = (False, time.time())
        else:
            for item in tracks[-11:]:
                check = item['track']['id']
                if track == check:
                    duplicate = True
                else:
                    duplicate = False
            if duplicate:
                chat(sock, "{}, sorry that song is already in queue! You can try a different song in the next 5 minutes using the !requeue command.".format(name), cfg.CHAN)
                content = 'Request is a duplicate: \"' + m +'\"'
                discord_message(name, content, cfg.URL)
                screwup[name] = (True, time.time())
            else:
                spz.user_playlist_add_tracks(userz, playlist, songl, position=None)
                spz.user_playlist_add_tracks(userz, history, songl, position=None)
                chat(sock, "{} song added to playlist".format(name), cfg.CHAN)
                content = 'Request added to playlist: \"' + m +'\"'
                discord_message(name, content, cfg.URL)
                screwup[name] = (False, time.time())
    return True


time_song = time.time()
def now_playing(sock):
    global playlist, sp, token, oauth, time_song
    expired = spotipy.oauth2.is_token_expired(token)
    if expired:
        token = oauth.refresh_access_token(token['refresh_token'])
        sp = spotipy.Spotify(auth=token['access_token'])
        logger.info('token refreshed?')
    if time.time() - time_song < 20:
        return False
    data = sp.current_user_playing_track()
    if data == None:
        message = '/me The song is unknown, just like our futures pepeJAM'
        return chat(sock, message, cfg.CHAN)
    name = data['item']['name']
    artists = data['item']['artists']
    message = name + " by "
    if len(artists) == 1:
        message += artists[0]['name']
    else:
        combined = ""
        for artist in artists:
            combined += artist['name'] + " & "
        message += combined[:-3]
    time_song = time.time()
    return chat(sock,"/me " + message, cfg.CHAN)


def clear_playlist(sock, message):
    global spz, tokenz, oauthz, userz, playlist
    expired = spotipy.oauth2.is_token_expired(tokenz)
    if expired:
        tokenz = oauthz.refresh_access_token(tokenz['refresh_token'])
        spz = spotipy.Spotify(auth=tokenz['access_token'])
        logger.info('token refreshed?')
    if message['mod'] == '1' or 'broadcaster' in message['badges']:
        tracks = spz.playlist_tracks(playlist)['items']
        track_list = []
        for item in tracks:
            track_list.append(item['external_urls']['external_urls']['linked_from']['uri'])
        spz.user_playlist_remove_all_occurrences_of_tracks(user, playlist,
                                                          track_list)
        logger.info('playlist cleared')
        return chat(sock, "Playlist cleared", cfg.CHAN)
    else:
        return False

time_queue = time.time()
def queue_length(sock, message):
    global spz, tokenz, oauthz, userz, playlist, time_queue
    expired = spotipy.oauth2.is_token_expired(tokenz)
    try:
        expired = spotipy.oauth2.is_token_expired(tokenz)
    except spotipy.client.SpotifyException:
        logger.exception("error", exc_info=True)
    if expired:
        try:
            tokenz = oauthz.refresh_access_token(tokenz['refresh_token'])
        except spotipy.client.SpotifyException:
            logger.exception("error", exc_info=True)
            return
        spz = spotipy.Spotify(auth=tokenz['access_token'])
        logger.info('token refreshed?')
    if time.time() - time_queue < 20:
        return False
    tracks = len(spz.playlist_tracks(playlist)['items'])
    time_queue = time.time()
    return chat(sock, "There are {} songs in queue".format(tracks), cfg.CHAN)


def requeue(sock, message):
    name = message['display-name']
    if name in screwup.keys():
        if screwup[name][0] and time.time() - screwup[name][1] < 301:
            return song_requests(sock, message, cfg.URL)
        elif time.time() - screwup[name][1] >= 301:
            del screwup[name]
            return chat(sock, f"{name}, sorry it's been more than 5 minutes.", cfg.CHAN)
    else:
        return False

#Handle each message type found by message_dict_maker

#message type PING
def ping(sock):
    sock.send("PONG :tmi.twitch.tv\r\n".encode("utf-8"))
    logger.info("PING")
    return True

#message type WHISPER
def whisper_response(response, sock):
    name = response['display-name']
    message = '/w {} This is a bot account, whisper another mod'.format(name)
    return chat(sock, message, cfg.CHAN)

#message type USERNOTICE
def sub(sock, subresponse, giftdict):
    '''
    sock to send message
    response is the received message
    giftdict is the dictionary of gifted sub counts
    respond to new subs and resubs
    log number gifted for gift subs
    user id logged in case of name change
    '''
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
        logger.info("new sub")
        return chat(sock, reply,cfg.CHAN)
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
        logger.info("resub")
        return chat(sock, reply ,cfg.CHAN)
    elif name == "AnAnonymousGifter":
        return False
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
            return False
        else:
            giftdict[userid] = giftcount
            with open("giftcounts.txt","w") as f:
                f.write(json.dumps(giftdict))
            logger.info("targeted gift")
    return False

#message type RECONNECT
def reconnect(HOST, PORT, PASS, NICK, CHAN):
    global s
    connect(HOST, PORT)
    login(s, PASS, NICK, CHAN)

#message type HOSTTARGET
def host(sock, message):
    target = message['host target']
    if target == '-':
        return False
    else:
        return chat(s, "If the host broke on your end, here is the link: https://twitch.tv/{}".format(target), cfg.CHAN)

#message type PRIVMSG
def PRIVMSG(mtesting):
    if 'custom-reward-id' in messagedict.keys():
        if messagedict['custom-reward-id'] == 'dc52dc53-f7a1-4229-afda-a404a2e37c5f':
            mtesting = song_requests(s, messagedict, cfg.URL)
    elif messagedict['actual message'].startswith('!'):
        word_list = messagedict['actual message'].split(" ")
        command = word_list[0]
        leaderb = leaderboard(giftdict)
        command_switch = {
                '!roulette': lambda : roulette(messagedict, s),
                '!clearplaylist': lambda : clear_playlist(s, messagedict),
                '!srqueue': lambda : queue_length(s, messagedict),
                '!giftrank': lambda : countcommand(s, messagedict, leaderb, giftdict),
                '!giftcount': lambda : countcommand(s, messagedict, leaderb, giftdict),
                '!song': lambda : now_playing(s),
                '!requeue': lambda : requeue(s, messagedict)
            }
        mtesting = command_switch.get(command, lambda : False)()
    return mtesting

#message type: userstate, clearchat, clearmsg, notice, roomstate
def the_rest(): return False


message_switch = {
            "WHISPER": lambda : whisper_response(messagedict, s),
            "PRIVMSG": lambda : PRIVMSG(mtesting),
            "USERNOTICE": lambda : sub(s, messagedict, giftdict),
            "USERSTATE": lambda : the_rest(),
            "CLEARCHAT": lambda : the_rest(),
            "CLEARMSG": lambda : the_rest(),
            "HOSTTARGET": lambda : host(s, messagedict),
            "NOTICE": lambda : the_rest(),
            "ROOMSTATE": lambda : the_rest(),
            "PING": lambda : ping(s)
        }

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
    while True:
        try:
            response = s.recv(4096).decode("utf-8")
        except:
            #exponential_backoff()
            logging.exception("error", exc_info=True)
            continue
        if response == "":
            continue
        messagelist = splitmessages(response)
        for message in messagelist:
            mtesting = False
            timet = time.time()
            try:
                messagedict = message_dict_maker(message)
            except:
                logging.exception(response)
                continue
            mtesting = message_switch.get(messagedict['message type'], lambda : False)()
            if mtesting:
                time.sleep(1/cfg.RATE)
