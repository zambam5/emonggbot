import socket
import logging
import time
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

        self.s.send(f"JOIN {CHAN}\r\n".encode("utf-8"))
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


    def chat(self, msg, CHAN):
        # this was not written by me
        '''
        Send a chat message to the server.
        Keyword arguments:
        sock -- the socket over which to send the message
        msg  -- the message to be sent
        '''
        self.s.send(f"PRIVMSG {CHAN} :{msg}\r\n".encode("utf-8"))
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
        '''
        take message from splitmessages, get dict
        this should be improved
        '''
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
                firstsplit = messagelist1[1].split(" " + self.CHAN + " :")
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
    

    def recv_message(self):
        try:
            response = self.s.recv(8192).decode("utf-8")
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


