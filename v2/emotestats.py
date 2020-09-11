import requests
import json
import logging
import os.path
from datetime import datetime


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class EmoteStatTracker:
    folderpath = ''
    def __init__(self, channel, ID):
        self.channel = channel
        self.id = ID
        EmoteStatTracker.folderpath = f'./logs/{self.channel}/stats/'
        directory = os.path.dirname(EmoteStatTracker.folderpath)
        if not os.path.exists(directory):
            os.makedirs(directory)
    

    today = datetime.today()    
    if os.path.isfile(folderpath + today.strftime("%Y-%m-%d") +'.json'):
        with open(folderpath + today.strftime("%Y-%m-%d") +'.json', 'r') as f:
            container = eval(f.read())
            ffz_stats = container['ffz']
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

    def ffz(self):
        EmoteStatTracker.ffz_stats[EmoteStatTracker.word] += 1
        month = EmoteStatTracker.today.strftime("%B %Y")
        date = EmoteStatTracker.today.strftime("%Y-%m-%d")
        filename = f'{date}.json'
        folderpath = f'{EmoteStatTracker.folderpath}{month}/'
        directory = os.path.dirname(folderpath)
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(folderpath + filename, 'w') as f:
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
        current_emotes = []
        for emote in EmoteStatTracker.ffz_stats.keys():
            current_emotes.append(emote)
        for emote in current_emotes:
            if emote not in emotes:
                old_emotes.append(emote)
                del EmoteStatTracker.ffz_stats[emote]
                del EmoteStatTracker.emote_switch[emote]
        removed_emotes = ' '.join(old_emotes)
        logger.info("Removed ffz emotes " + removed_emotes)
        return removed_emotes
    

    def bttv(self):
        EmoteStatTracker.bttv_stats[EmoteStatTracker.word] += 1
        month = EmoteStatTracker.today.strftime("%B %Y")
        date = EmoteStatTracker.today.strftime("%Y-%m-%d")
        filename = f'{date}.json'
        folderpath = f'{EmoteStatTracker.folderpath}{month}/'
        directory = os.path.dirname(folderpath)
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(folderpath + filename, 'w') as f:
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
        current_emotes = []
        for emote in EmoteStatTracker.bttv_stats.keys():
            current_emotes.append(emote)
        for emote in current_emotes:
            if emote not in emotes:
                old_emotes.append(emote)
                try:
                    del EmoteStatTracker.bttv_stats[emote]
                except:
                    continue
                try:
                    del EmoteStatTracker.emote_switch[emote]
                except:
                    continue
        removed_emotes = ' '.join(old_emotes)
        logger.info('Removed bttv emotes ' + removed_emotes)
        return removed_emotes
    
    
    def sub(self):
        EmoteStatTracker.sub_stats[EmoteStatTracker.word] += 1
        month = EmoteStatTracker.today.strftime("%B %Y")
        date = EmoteStatTracker.today.strftime("%Y-%m-%d")
        filename = f'{date}.json'
        folderpath = f'{EmoteStatTracker.folderpath}{month}/'
        directory = os.path.dirname(folderpath)
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(folderpath + filename, 'w') as f:
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
        current_emotes = []
        for emote in EmoteStatTracker.sub_stats.keys():
            current_emotes.append(emote)
        for emote in current_emotes:
            if emote not in emotes:
                old_emotes.append(emote)
                try:
                    del EmoteStatTracker.sub_stats[emote]
                except:
                    continue
                try:
                    del EmoteStatTracker.emote_switch[emote]
                except:
                    continue
        removed_emotes = ' '.join(old_emotes)
        logger.info('Removed sub emotes ' + removed_emotes)
        return removed_emotes
    

    def start(self):
        self.sub_update()
        self.bttv_update()
        self.ffz_update()
        EmoteStatTracker.command_switch['!updateffz'] = self.ffz_update
        EmoteStatTracker.command_switch['!updatebttv'] = self.bttv_update
        EmoteStatTracker.command_switch['!updatesub'] = self.sub_update
    

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
            elif message['display-name'] == 'zambam5' and message['channel'] == 'zambam5':
                word_list = message['actual message'].rstrip().split(" ")
                removed_emotes = EmoteStatTracker.command_switch.get(word_list[0], lambda : False)()
                if removed_emotes == False:
                    return False
                elif removed_emotes == '':
                    return "Update completed, no emotes removed"
                else:
                    return "Update completed, removed " + removed_emotes
        except:
            logger.info('bad message')
            return False
        today = datetime.today()
        if EmoteStatTracker.today.day != today.day:
            EmoteStatTracker.today = datetime.today()
            self.new_day()
        word_list = message['actual message'].rstrip().split(" ")
        for word in word_list:
            EmoteStatTracker.word = word
            EmoteStatTracker.emote_switch.get(EmoteStatTracker.word, lambda : False)()
        return False
