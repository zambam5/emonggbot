import socket
import logging
import time
import re
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

class Twitch:
    def __init__(self, HOST, PORT, PASS, NICK, CHAN):
        self.HOST = HOST
        self.PORT = PORT
        self.PASS = PASS
        self.NICK = NICK
        self.CHAN = CHAN
        self.s = None

        self.regex = {
            "data": re.compile(
                r"^(?:@(?P<tags>\S+)\s)?:(?P<data>\S+)(?:\s)"
                r"(?P<action>[A-Z]+)(?:\s#)(?P<channel>\S+)"
                r"(?:\s(?::)?(?P<content>.+))?"),
            "ping": re.compile(r"PING (?P<content>.+)"),
            "author": re.compile(
                r"(?P<author>[a-zA-Z0-9_]+)!(?P=author)"
                r"@(?P=author).tmi.twitch.tv"),
            "mode": re.compile(r"(?P<mode>[\+\-])o (?P<user>.+)"),
            "host": re.compile(
                r"(?P<channel>[a-zA-Z0-9_]+) "
                r"(?P<count>[0-9\-]+)")}
    

    def connect(self, HOST, PORT):
        self.s = None
        try:
            self.s.close()
        except:
            pass
        self.s = socket.socket()
        self.s.settimeout(310)
        try:
            self.s.connect((HOST, PORT))
        except ConnectionAbortedError:
            logger.info('Connection Failed')


    def login(self, PASS, NICK, CHAN):
        self.s.send(f"PASS {PASS}\r\n".encode("utf-8"))
        self.s.send(f"NICK {NICK}\r\n".encode("utf-8"))
        test = self.s.recv(1024).decode("utf-8")
        logger.info(test)

        for chan in CHAN:
            self.s.send(f"JOIN {chan}\r\n".encode("utf-8"))
            test = self.s.recv(1024).decode("utf-8")
            logger.info(test)

        self.s.send("CAP REQ :twitch.tv/tags\r\n".encode("utf-8"))
        test = self.s.recv(1024).decode("utf-8")
        logger.info(test)
        self.s.send("CAP REQ :twitch.tv/commands\r\n".encode("utf-8"))
        time.sleep(0.5)
        test = self.s.recv(1024).decode("utf-8")
        logger.info(test)


    def ping(self):
        self.s.send("PONG :tmi.twitch.tv\r\n".encode("utf-8"))
        logger.info("PING")
        return True
    

    def start(self):
        self.connect(self.HOST, self.PORT)
        self.login(self.PASS, self.NICK, self.CHAN)


    def exponential_backoff(self):
        count = 1
        while True:
            try:
                self.connect(self.HOST, self.PORT)
                self.login(self.PASS, self.NICK, self.CHAN)
                return True
            except socket.error:
                time.sleep(count)
                count = count*2


    def reconnect(self):
        self.connect(self.HOST, self.PORT)
        self.login(self.PASS, self.NICK, self.CHAN)


    def chat(self, msg, CHAN):
        # this was not written by me
        '''
        Send a chat message to the server.
        Keyword arguments:
        sock -- the socket over which to send the message
        msg  -- the message to be sent
        '''
        self.s.send(f"PRIVMSG #{CHAN} :{msg}\r\n".encode("utf-8"))
        return True


    def splitmessages(self, response):
        '''
        Sometimes twitch sends multiple messages at a time
        so this deals with that
        used to be way longer, so wrote a function
        now I just keep it cause why not
        '''
        messages = response.splitlines()
        return messages


    def process_message(self, message):
        messagedict = {}
        if message.startswith('PING'):
            messagedict['message type'] = 'PING'
            messagedict['time'] = datetime.now()
            return messagedict
        else:
            m = self.regex['data'].match(message)
            try:
                tags = m.group("tags")
                for tag in tags.split(';'):
                    t = tag.split('=')
                    messagedict[t[0]] = t[1]
            except:
                tags = None
            
            try:
                action = m.group('action')
                messagedict['message type'] = action
                if action == 'HOSTTARGET':
                    try:
                        hostm = self.regex['host'].match(message)
                        hchannel = hostm.group("channel")
                        viewers = hostm.group('count')
                        messagedict['host target'] = hchannel
                        messagedict['host views'] = viewers
                    except:
                        messagedict['host target'] = '-'
            except:
                action = None
            
            try:
                data = m.group('data')
                messagedict['data'] = data
            except:
                data = None
            
            try:
                content = m.group('content')
                messagedict['actual message'] = content
            except:
                content = None
            
            try:
                channel = m.group('channel')
                messagedict['channel'] = channel
            except:
                channel = None
        return messagedict

    def recv_message(self):
        try:
            response = self.s.recv(2048).decode("utf-8")
        except socket.timeout:
            print("timed out, attempting reconnect")
            self.exponential_backoff()
            return None
        if response == "":
            return None
        messagelist = self.splitmessages(response)
        dictlist = []
        for message in messagelist:
            try:
                messagedict = self.process_message(message)
            except:
                logger.exception(response)
                continue
            try:
                if not messagedict:
                    logger.info('bad message')
                    logger.info(message)
                    continue
                elif messagedict['message type'] == 'PING':
                    self.ping()
                else:
                    dictlist.append(messagedict)
            except:
                logger.info('bad dict')
                print(messagedict)
        if dictlist == []:
            return None
        else:
            return dictlist


