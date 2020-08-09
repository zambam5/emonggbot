import requests
import json
import logging
import os.path
from datetime import datetime


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class EmoteStatTracker:
    today = datetime.today()
    if os.path.isfile('./stats/' + today.strftime("%Y-%m-%d") +'.json'):
        with open('./stats/' + today.strftime("%Y-%m-%d") +'.json', 'r') as f:
            container = eval(f.read())
            ffz_stats = container['ffz']
            print(ffz_stats)
            bttv_stats = container['bttv']
            sub_stats = container['sub']
            f.close()
    else:
        ffz_stats = dict()
        bttv_stats = dict()
        sub_stats = dict()
    stats = {'ffz': ffz_stats, 'bttv': bttv_stats, 'sub': sub_stats}
    emote_switch = dict()
    command_switch = dict()
    word = ""

    def __init__(self, channel, ID):
        self.channel = channel
        self.id = ID


    def ffz(self):
        EmoteStatTracker.ffz_stats[EmoteStatTracker.word] += 1
        with open('./stats/' + EmoteStatTracker.today.strftime("%Y-%m-%d") +'.json', 'w') as f:
            f.write(json.dumps(EmoteStatTracker.stats))
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
            if emote not in EmoteStatTracker.ffz_stats.keys():
                EmoteStatTracker.ffz_stats[emote] = 0
                EmoteStatTracker.emote_switch[emote] = self.ffz
            elif emote not in EmoteStatTracker.emote_switch.keys():
                EmoteStatTracker.emote_switch[emote] = self.ffz
        old_emotes = []
        for emote in EmoteStatTracker.ffz_stats.keys():
            if emote not in emotes:
                old_emotes.append(emote)
                del EmoteStatTracker.ffz_stats[emote]
                del EmoteStatTracker.emote_switch[emote]
        removed_emotes = ' '.join(old_emotes)
        logger.info("Removed ffz emotes " + removed_emotes)
    

    def bttv(self):
        EmoteStatTracker.bttv_stats[EmoteStatTracker.word] += 1
        with open('./stats/' + EmoteStatTracker.today.strftime("%Y-%m-%d") +'.json', 'w') as f:
            f.write(json.dumps(EmoteStatTracker.stats))
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
            if emote not in EmoteStatTracker.bttv_stats.keys():
                EmoteStatTracker.bttv_stats[emote] = 0
                EmoteStatTracker.emote_switch[str(emote)] = self.bttv
            elif emote not in EmoteStatTracker.emote_switch.keys():
                EmoteStatTracker.emote_switch[emote] = self.bttv
        old_emotes = []
        for emote in EmoteStatTracker.bttv_stats.keys():
            if emote not in emotes:
                old_emotes.append(emote)
                del EmoteStatTracker.bttv_stats[emote]
                del EmoteStatTracker.emote_switch[emote]
        removed_emotes = ' '.join(old_emotes)
        logger.info('Removed bttv emotes ' + removed_emotes)
    
    
    def sub(self):
        EmoteStatTracker.sub_stats[EmoteStatTracker.word] += 1
        with open('./stats/' + EmoteStatTracker.today.strftime("%Y-%m-%d") +'.json', 'w') as f:
            f.write(json.dumps(EmoteStatTracker.stats))
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
            if emote not in EmoteStatTracker.sub_stats.keys():
                EmoteStatTracker.sub_stats[emote] = 0
                EmoteStatTracker.emote_switch[emote] = self.sub
            elif emote not in EmoteStatTracker.emote_switch.keys():
                EmoteStatTracker.emote_switch[emote] = self.sub
        old_emotes = []
        for emote in EmoteStatTracker.sub_stats.keys():
            if emote not in emotes:
                old_emotes.append(emote)
                del EmoteStatTracker.sub_stats[emote]
                del EmoteStatTracker.emote_switch[emote]
    

    def start(self):
        self.sub_update()
        self.bttv_update()
        self.ffz_update()
        EmoteStatTracker.command_switch['!updateffz'] = self.ffz_update
        EmoteStatTracker.command_switch['!updatebttv'] = self.bttv_update
        EmoteStatTracker.command_switch['!updatesub'] = self.sub_update
        print(EmoteStatTracker.emote_switch)
    

    def new_day(self):
        logger.info('New day, clearing stats')
        print(EmoteStatTracker.today.strftime("%Y-%m-%d"))
        for emote in EmoteStatTracker.ffz_stats.keys():
            EmoteStatTracker.ffz_stats[emote] = 0
        for emote in EmoteStatTracker.bttv_stats.keys():
            EmoteStatTracker.bttv_stats[emote] = 0
        for emote in EmoteStatTracker.sub_stats.keys():
            EmoteStatTracker.sub_stats[emote] = 0


    def process_message(self, message):
        try:
            if message['display-name'] == 'streamelements' or message['display-name'] == 'zambamai':
                return False
        except:
            logger.info('bad message')
            return
        today = datetime.today()
        if EmoteStatTracker.today.day != today.day:
            EmoteStatTracker.today = datetime.today()
            self.new_day()
        word_list = message['actual message'].rstrip().split(" ")
        if message['display-name'] == 'zambam5':
            EmoteStatTracker.command_switch.get(word_list[0], lambda : False)()
        for word in word_list:
            EmoteStatTracker.word = word
            EmoteStatTracker.emote_switch.get(EmoteStatTracker.word, lambda : False)()
