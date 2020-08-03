import requests
import json
import logging
import os.path
from datetime import datetime


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class EmoteStatTracker:

    def __init__(self, channel, ID):
        self.today = datetime.today()
        if os.path.isfile('./stats/' + self.today.strftime("%Y-%m-%d") +'.json'):
            with open('./stats/' + self.today.strftime("%Y-%m-%d") +'.json', 'r') as f:
                container = eval(f.read())
                self.ffz_stats = container['ffz']
                self.bttv_stats = container['bttv']
                self.sub_stats = container['sub']
                f.close()
        else:
            self.ffz_stats = dict()
            self.bttv_stats = dict()
            self.sub_stats = dict()
        self.stats = {'ffz': self.ffz_stats, 'bttv': self.bttv_stats, 'sub': self.sub_stats}
        self.emote_switch = dict()
        self.command_switch = dict()
        self.channel = channel
        self.id = ID
        self.word = ""
    

    def ffz(self):
        self.ffz_stats[self.word] += 1
        self.stats = {'ffz': self.ffz_stats, 'bttv': self.bttv_stats, 'sub': self.sub_stats}
        with open('./stats/' + self.today.strftime("%Y-%m-%d") +'.json', 'w') as f:
            f.write(json.dumps(self.stats))
            f.close
    

    def ffz_api(self):
        url = f'https://api.frankerfacez.com/v1/room/{self.channel}'
        with requests.get(url) as r:
            response = json.loads(r.content)
            emoteset = str(response['room']['set'])
            emotes = response['sets'][emoteset]['emoticons']
            r.close()
        emotelist = [item['name'] for item in emotes]
        return emotelist
    

    def ffz_update(self):
        emotes = self.ffz_api()
        for emote in emotes:
            if emote not in self.ffz_stats.keys():
                self.ffz_stats[emote] = 0
                self.emote_switch[emote] = self.ffz
        old_emotes = []
        for emote in self.ffz_stats.keys():
            if emote not in emotes:
                old_emotes.append(emote)
                del self.ffz_stats[emote]
                del self.emote_switch[emote]
        removed_emotes = ' '.join(old_emotes)
        logger.info("Removed ffz emotes " + removed_emotes)
    

    def bttv(self):
        self.bttv_stats[self.word] += 1
        self.stats = {'ffz': self.ffz_stats, 'bttv': self.bttv_stats, 'sub': self.sub_stats}
        with open('./stats/' + self.today.strftime("%Y-%m-%d") +'.json', 'w') as f:
            f.write(json.dumps(self.stats))
            f.close
    

    def bttv_api(self):
        url = f"https://api.betterttv.net/3/cached/users/twitch/{self.id}"
        with requests.get(url) as r:
            emotes = json.loads(r.content)["sharedEmotes"]
            r.close()
        emotelist = []
        for item in emotes:
            emotelist.append(item['code'])
        return emotelist
    

    def bttv_update(self):
        emotes = self.bttv_api()
        for emote in emotes:
            if emote not in self.bttv_stats.keys():
                self.bttv_stats[emote] = 0
                self.emote_switch[str(emote)] = self.bttv
        old_emotes = []
        for emote in self.bttv_stats.keys():
            if emote not in emotes:
                old_emotes.append(emote)
                del self.bttv_stats[emote]
                del self.emote_switch[emote]
        removed_emotes = ' '.join(old_emotes)
        logger.info('Removed bttv emotes ' + removed_emotes)
    
    
    def sub(self):
        self.sub_stats[self.word] += 1
        self.stats = {'ffz': self.ffz_stats, 'bttv': self.bttv_stats, 'sub': self.sub_stats}
        with open('./stats/' + self.today.strftime("%Y-%m-%d") +'.json', 'w') as f:
            f.write(json.dumps(self.stats))
            f.close
    

    def twitch_api(self):
        url = f'https://api.twitchemotes.com/api/v4/channels/{self.id}'
        with requests.get(url) as r:
            emotes = json.loads(r.content)['emotes']
            r.close()
        emotelist = []
        for item in emotes:
            emotelist.append(item['code'])
        return emotelist
    

    def sub_update(self):
        emotes = self.twitch_api()
        for emote in emotes:
            if emote not in self.sub_stats.keys():
                self.sub_stats[emote] = 0
                self.emote_switch[emote] = self.sub
        old_emotes = []
        for emote in self.sub_stats.keys():
            if emote not in emotes:
                old_emotes.append(emote)
                del self.sub_stats[emote]
                del self.emote_switch[emote]
    

    def start(self):
        self.sub_update()
        self.bttv_update()
        self.ffz_update()
        self.command_switch['!updateffz'] = self.ffz_update
        self.command_switch['!updatebttv'] = self.bttv_update
        self.command_switch['!updatesub'] = self.sub_update
    

    def new_day(self):
        for emote in self.ffz_stats.keys():
            self.ffz_stats[emote] = 0
        for emote in self.bttv_stats.keys():
            self.bttv_stats[emote] = 0
        for emote in self.sub_stats.keys():
            self.sub_stats[emote] = 0


    def process_message(self, message):
        try:
            if message['display-name'] == 'streamelements' or message['display-name'] == 'zambamai':
                return False
        except:
            logger.info('bad message')
            return
        today = datetime.today()
        if today != self.today:
            self.today = today
            self.new_day()
        word_list = message['actual message'].rstrip().split(" ")
        if message['display-name'] == 'zambam5':
            self.command_switch.get(word_list[0], lambda : False)()
        for word in word_list:
            
            self.word = word
            self.emote_switch.get(word, lambda : False)()
