'''
I really don't wanna take the time to comment this all
a bunch of stuff is stored in text files
don't worry about that stuff :)
'''
import cfgai as cfg
import time, logging, random, json, requests, socket, re
import spotipy
import spotipy.util as util
import nowplaying


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
    """
    Send a chat message to the server.
    Keyword arguments:
    sock -- the socket over which to send the message
    msg  -- the message to be sent
    """
    sock.send("PRIVMSG {} :{}\r\n".format(CHAN, msg).encode("utf-8"))
    return True


def ping(sock, response):
    # check for ping from twitch and respond
    if "PING :tmi.twitch.tv" in response:
        sock.send("PONG :tmi.twitch.tv\r\n".encode("utf-8"))
        logger.info("ping")
        return True


def pong(sock):
    # a function to ping twitch I guess?
    sock.send("PING :tmi.twitch.tv\r\n".encode("utf-8"))


def splitmessages(response):
    '''
    when chat is moving very fast twitch sometimes mashes messages together
    this aims to split messages that are mashed together
    '''
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
    '''
    break messages into dictionaries
    there isn't a strict structure to message tags, so we try to force some
    PRIVMSG are normal chat messages, but also include highlight messages
    USERNOTICE includes subs, resubs and gift subs
    '''
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
    elif "WHISPER" in messagelist1[1]:
        logger.info('whisper')
        messagedict['message type'] = "WHISPER"
    return messagedict


def viewer_list(chan):
    '''
    return viewer list for given channel
    moderators and viewers are seperate lists
    '''
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


def whisper_response(response, sock):
    name = response['display-name']
    message = '/w {} This is a bot account, whisper another mod'.format(name)
    return chat(sock, message, cfg.CHAN)


def roulette(response, sock):
    '''
    russian roulette for timeout
    return True will put the roulette on a cooldown
    return False will not
    mods do not trigger cooldown as they cannot be timed out
    jasper wanted to feel special
    '''
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
            oneliners = ["RIP in pieces, {}".format(name),
                        "{} BOP".format(name)]
            line = random.choice(oneliners)
            chat(sock, "/timeout {} 120 roulette".format(name), cfg.CHAN)
            chat(sock, "RIP in pieces, {}".format(name), cfg.CHAN)
        return True
    else:
        return False


def countcommand(s,message,leaderboard,giftdict):
    '''
    giftdict is a dictionary with user id strings as keys and int gift values
    leaderboard is an ordered list of tuples by highest gift value
    user id is used in case the user changes their username
    '''
    response = message['actual message']
    if "!giftcount" in response or "!giftrank" in response:
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


def remove_text(message):
    if '.com' in message or '.be' in message:
        mlist = message.split(' ')
        for idx, item in enumerate(mlist):
            if '.com' in message or '.be' in message:
                if item.endswith("\r\n"):
                    print('found one')
                    item = item[:-4]
                    item.strip('\\r\\n')
                item = '<' + item + '>'
                mlist[idx] = item
        message = ' '.join(mlist)
    return message


def extract_link(message):
    match = re.search("(?P<url>open.spotify.com[^\s]+)", message)
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

    result = requests.post(url, data=data, headers={'Content Type': 'application/json'})


def song_requests(sock, message, url):
    global userz, playlist, spz, tokenz, oauthz, history
    try:
        expired = spotipy.oauth2.is_token_expired(tokenz)
    except spotipy.client.SpotifyException:
        logger.info("error")
    if expired:
        try:
            tokenz = oauthz.refresh_access_token(token['refresh_token'])
        except spotipy.client.SpotifyException:
            logger.info("error")
        spz = spotipy.Spotify(auth=token['access_token'])
        logger.info('token refreshed?')
    name = message['display-name']
    m = message['actual message']
    song = extract_link(m)
    if song == None:
        chat(sock, "{}, be sure your link is for open.spotify.com".format(name), cfg.CHAN)
        content = 'Request did not include a spotify link: \"' + m +'\"'
        discord_message(name, content, cfg.URL)
    elif "track" not in song:
        chat(sock, "{}, you have to link to a Spotify song for song requests".format(name), cfg.CHAN)
        content = 'Request was not a song link: \"' + m +'\"'
        discord_message(name, content, cfg.URL)
    else:
        songl = [song]
        try:
            track1 = spz.track(song)
        except spotipy.client.SpotifyException:
            chat(sock, "{}, that link is dead".format(name), cfg.CHAN)
            content = 'Song link is dead \"' + m + '\"'
            discord_message(name, content, cfg.URL)
        track = track1['id']
        #features = sp.audio_features(songl)[0]
        #length = features['duration_ms']
        length = track1['duration_ms']
        tracks = spz.playlist_tracks(playlist)['items']
        '''if 'US' not in track1['available_markets']:
            chat(sock, "{}, sorry that song is not available in the US".format(name), cfg.CHAN)'''
        if length > 360000:
            chat(sock, "{}, we have a 6 minute limit on songs".format(name), cfg.CHAN)
            content = 'Request is too long: \"' + m +'\"'
            discord_message(name, content, cfg.URL)
        elif len(tracks) < 1:
            spz.user_playlist_add_tracks(userz, playlist, songl, position=None)
            spz.user_playlist_add_tracks(userz, history, songl, position=None)
            chat(sock, "{}, song added to playlist".format(name), cfg.CHAN)
            content = 'Request added to playlist: \"' + m +'\"'
            discord_message(name, content, cfg.URL)
        else:
            for item in tracks[-11:]:
                check = item['track']['id']
                if track == check:
                    duplicate = True
                else:
                    duplicate = False
            if duplicate:
                chat(sock, "{}, sorry that song is already in queue!".format(name), cfg.CHAN)
                content = 'Request is a duplicate: \"' + m +'\"'
                discord_message(name, content, cfg.URL)
            else:
                spz.user_playlist_add_tracks(userz, playlist, songl, position=None)
                spz.user_playlist_add_tracks(userz, history, songl, position=None)
                chat(sock, "{} song added to playlist".format(name), cfg.CHAN)
                content = 'Request added to playlist: \"' + m +'\"'
                discord_message(name, content, cfg.URL)


def now_playing(sock):
    global playlist, sp, token, oauth
    expired = spotipy.oauth2.is_token_expired(token)
    if expired:
        token = oauth.refresh_access_token(token['refresh_token'])
        sp = spotipy.Spotify(auth=token['access_token'])
        logger.info('token refreshed?')
    data = sp.current_user_playing_track()
    if data == None:
        message = 'The song is unknown, just like our futures pepeJAM'
        chat(sock, message, cfg.CHAN)
        return
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
    chat(sock, message, cfg.CHAN)


def clear_playlist(sock, message):
    global spz, tokenz, oauthz, userz, playlist
    expired = spotipy.oauth2.is_token_expired(tokenz)
    if expired:
        tokenz = oauth.refresh_access_token(tokenz['refresh_token'])
        spz = spotipy.Spotify(auth=tokenz['access_token'])
        logger.info('token refreshed?')
    if message['mod'] == '1' or 'broadcaster' in message['badges']:
        tracks = spz.playlist_tracks(playlist)['items']
        track_list = []
        for item in tracks:
            track_list.append(item['track']['id'])
        spz.user_playlist_remove_all_occurrences_of_tracks(userz, playlist,
                                                          track_list)
        logger.info('playlist cleared')
        chat(sock, "Playlist cleared", cfg.CHAN)


def queue_length(sock, message):
    global spz, tokenz, oauthz, userz, playlist
    expired = spotipy.oauth2.is_token_expired(tokenz)
    if expired:
        tokenz = oauth.refresh_access_token(tokenz['refresh_token'])
        sp = spotipy.Spotify(auth=tokenz['access_token'])
        logger.info('token refreshed?')
    tracks = len(spz.playlist_tracks(playlist)['items'])
    chat(sock, "There are {} songs in queue".format(tracks), cfg.CHAN)


if __name__ == "__main__":
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
    user = cfg.SPOTIFY_USER
    CACHE = '.spotipyoauthcache'
    oauth = spotipy.oauth2.SpotifyOAuth(cfg.SPOTIFY_ID, cfg.SPOTIFY_SECRET,
                                        cfg.SPOTIFY_REDIRECT,
                                        scope='playlist-modify-public playlist-modify-private',
                                        cache_path=CACHE)
    token = oauth.get_cached_token()
    if token:
        sp = spotipy.Spotify(auth=token['access_token'])
    else:
        print ("Can't get token for ", user_config['username'])
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
    timer, timeq, times = time.time(), time.time(), time.time()
    timecheck = False
    cd = 15
    while True:
        mtesting = False
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
                if "USERNOTICE" == messagedict['message type']:
                    mtesting = sub(s, messagedict, giftdict)
                elif "PRIVMSG" == messagedict['message type']:
                    mtesting = word_filter(s, messagedict, banlist)
                    if 'custom-reward-id' in messagedict.keys():
                        if messagedict['custom-reward-id'] == 'dc52dc53-f7a1-4229-afda-a404a2e37c5f':
                            song_requests(s, messagedict, cfg.URL)
                            mtesting = True
                    elif messagedict['actual message'].startswith('!'):
                        word_list = messagedict['actual message'][:-2].split(" ")
                        command = word_list[0]
                        if command == '!roulette' and time.time() - timer > 30:
                            timecheck = roulette(messagedict, s)
                            mtesting = True
                            if timecheck:
                                timer = time.time()
                        elif command == '!clearplaylist':
                            clear_playlist(s, messagedict)
                            mtesting = True
                        elif command == '!srqueue' and time.time() - timeq > 20:
                            queue_length(s, messagedict)
                            timeq = time.time()
                            mtesting = True
                        elif command == '!giftrank' or command == '!giftcount':
                            countcommand(s, messagedict, leaderb, giftdict)
                            mtesting = True
                        '''elif command == '!song' and time.time() - times > 22:
                            now_playing(s)
                            times = time.time()
                            mtesting = True'''
                elif "WHISPER" == messagedict['message type']:
                    mtesting = whisper_response(messagedict, s)
        except Exception as e:
            logger.exception("error")
            logger.debug(response)
        if mtesting:
            time.sleep(1/cfg.RATE)
