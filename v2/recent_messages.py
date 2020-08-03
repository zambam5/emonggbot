import requests, os
from datetime import datetime

class messageHistory:
    def __init__(self, channel):
        self.channel = channel
    
    def recent_messages(self, channel):
        url = f'https://recent-messages.robotty.de/api/v2/recent-messages/{channel}?clearchatToNotice=true'
        res = requests.get(url).json()
        if res['error'] == None:
            messages = res['messages']
        else:
            print(res)
            return None
        return messages

    def process_message(self, messages):
        #messages should be a list
        #output dict with display-name: message
        messagedict = {}
        for message in messages:
            if "PRIVMSG" in message:
                messageinfo = message.split('PRIVMSG')
                messageinfo_1 = messageinfo[0].split(';')
                for item in messageinfo_1:
                    if "display-name" in item:
                        name = item.split(':')[1]
                        break
                actual_message = messageinfo[1].split(" #" + self.channel + " :")
                messagedict[name] = actual_message
        return messagedict
    
    def nuke(self, name):
        #name is name of one account that spammed
        messagelist = self.recent_messages(self.channel)
        messagedict = self.process_message(messagelist)
        bans = []
        if name not in messagedict.keys():
            return False
        for user in messagedict.keys():
            if messagedict[user] == messagedict[name]:
                bans.append(name)
        dirname = "./nukelogs"
        if not os.path.exists(dirname):
            os.makedirs(dirname)
            print('Made directory: ' + dirname)
        dt = datetime.now().strftime("%Y-%m-%d")
        with open(dirname + '/' + dt + '.log', 'w+') as f:
            f.write(','.join(bans))
            f.close()
        return bans

