import ircclient
import emotestats
import cfgai as cfg

client = ircclient.Twitch(cfg.HOST, cfg.PORT, cfg.PASS, cfg.NICK, cfg.CHAN)
stattracker = emotestats.EmoteStatTracker(cfg.CHAN[1:], cfg.CHANID)
stattracker.start()

client.start()

while True:
    dictlist = client.recv_message()
    if dictlist == None:
        continue
    else:
        for message in dictlist:
            if message['message type'] == 'PRIVMSG':
                if message['actual message'] == None:
                    continue
                else:
                    stattracker.process_message(message)
