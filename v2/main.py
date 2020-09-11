import ircclient
import emotestats
import chatlogger
import time
import cfgai as cfg

client = ircclient.Twitch(cfg.HOST, cfg.PORT, cfg.PASS, cfg.NICK, cfg.CHAN)
stattracker = emotestats.EmoteStatTracker(cfg.CHAN[0][1:], cfg.CHANID)
chatlog = chatlogger.ChatLogger(cfg.CHAN[0][1:])
chatlogz = chatlogger.ChatLogger(cfg.CHAN[1][1:])
stattracker.start()

client.start()

#message type WHISPER
def whisper_response(response):
    name = response['display-name']
    message = f'/w {name} This is a bot account, whisper another mod'
    return client.chat(message, cfg.CHAN)

#message type USERNOTICE
def sub(subresponse):
    '''
    sock to send message
    response is the received message
    giftdict is the dictionary of gifted sub counts
    respond to new subs and resubs
    log number gifted for gift subs
    user id logged in case of name change
    
    message = subresponse
    msgid = message['msg-id']
    name = message['display-name']
    userid = message['user-id']
    if msgid == "sub":
        newresponses = [f"Thanks for the sub {name}, and welcome! emongC",
                        f"Welcome {name}! emongAYAYA",
                        f"Welcome Detective {name} emongL",
                        f"Thanks for the sub {name} emongGood",
                        f"Welcome {name}, and remember to smile emongSmile",
                        f"Welcome {name} emongCool",
                        f"Welcome {name} emongH"
                        ]
        discord_m = "Be sure to join the discord at https://discord.gg/emongg emongH"
        reply = random.choice(newresponses) + ' ' + discord_m
        logger.info("new sub")
        return chat(sock, reply,cfg.CHAN)
    elif msgid == "resub":
        sublength = message['msg-param-cumulative-months']
        resubresponses = [f"Welcome back {name}! emongC\r\n",
                          f"Thank you for your continued work Detective {name} emongL \r\n",
                          f"Keep on vibin' {name} emongVibe \r\n",
                          f"Thanks for the resub {name} emongGood",
                          f"Keep on smiling {name} emongSmile",
                          f"Welcome back {name} emongCool"
                          ]
        if int(sublength) >= 24 and int(sublength) < 36:
            resubresponses.append(f"Thanks for cancelling your sub {name} emongSmug")
        elif int(sublength) >= 36 and int(sublength) < 48:
            resubresponses.append(f"That's almost 2 years {name} emongPotato")
        elif int(sublength) >= 48:
            resubresponses.append(f'It\'s not like I wanted you around this long or anything {name} emongBaka')
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
            f.close()
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
                f.close()
            logger.info("targeted gift")
    '''
    return False

#message type RECONNECT
def reconnect():
    client.reconnect()

#message type HOSTTARGET
def host(message):
    target = message['host target']
    if target == '-':
        return False
    else:
        return client.chat(f"If the host broke on your end, here is the link: https://twitch.tv/{target}", message['channel'])

#message type PRIVMSG
def PRIVMSG(mtesting):
    if messagedict['actual message'] == None:
        return False
    else:
        message = stattracker.process_message(messagedict)
        if messagedict['channel'] == "emongg":
            try:
                chatlog.privmsg_log(messagedict)
            except:
                print('bad message: ' + str(messagedict))
        elif messagedict['channel'] == "zambam5":
            try:
                chatlogz.privmsg_log(messagedict)
            except:
                print('bad message: ' + str(messagedict))
        if not message:
            return False
        else: 
            mtesting = client.chat(message, messagedict['channel'])
    '''if 'custom-reward-id' in messagedict.keys():
        reward_switch = {
            'e3c335a6-5465-4c02-9c7a-2f30937a1daa': lambda : timeout_request(s, messagedict),
            '77b13a93-d4fb-481f-bb28-e590999641f8': lambda : whitelist_request(s, messagedict),
            'f38c9ea7-4540-4379-a7a4-8ef42d64f6e9': lambda : other_requests(s, messagedict),
            '6e0bba83-8b95-4b02-9d29-4d6c53b06682': lambda : other_requests(s, messagedict)
        }
        mtesting = reward_switch.get(messagedict['custom-reward-id'], lambda : False)()
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
                '!requeue': lambda : requeue(s, messagedict),
                '!nuke': lambda : nuke(s, messagedict, nukeloader)
            }
        mtesting = command_switch.get(command, lambda : False)()'''
    return mtesting

#message type: userstate, clearchat, clearmsg, notice, roomstate
def the_rest(): return False


message_switch = {
            "WHISPER": lambda : whisper_response(messagedict),
            "PRIVMSG": lambda : PRIVMSG(mtesting),
            "USERNOTICE": lambda : sub(messagedict),
            "USERSTATE": lambda : the_rest(),
            "CLEARCHAT": lambda : the_rest(),
            "CLEARMSG": lambda : the_rest(),
            "HOSTTARGET": lambda : host(messagedict),
            "NOTICE": lambda : the_rest(),
            "ROOMSTATE": lambda : the_rest(),
            "RECONNECT": lambda : reconnect()
        }

while True:
    dictlist = client.recv_message()
    if dictlist == None:
        continue
    else:
        for messagedict in dictlist:
            t = time.time()
            mtesting = False
            mtesting = message_switch.get(messagedict['message type'], lambda : False)()
            if mtesting:
                time.sleep(1/cfg.RATE)
            print(time.time()-t)
