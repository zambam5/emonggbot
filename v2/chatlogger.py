import datetime
import csv
import os.path

class ChatLogger:
    def __init__(self, channel):
        self.channel = channel
        self.log_folder = f'logs/{channel}'
        directory = os.path.dirname(self.log_folder)
        if not os.path.exists(directory):
            os.makedirs(directory)
    

    def privmsg_log(self, message):
        today = datetime.datetime.now()
        month = today.strftime("%B %Y")
        date = today.strftime("%Y-%m-%d")
        filename = f'{self.log_folder}/chat/{month}/{date}.csv'
        folderpath = f'{self.log_folder}/chat/{month}/'
        directory = os.path.dirname(folderpath)
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(filename, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([message['display-name'], message['user-id'], today.strftime('%H:%M:%S:%f'), message['actual message']])
    

    def usernotice_log(self, message):
        #TODO: Add file for gift subs
        today = datetime.datetime.now()
        month = today.strftime("%B %Y")
        date = today.strftime("%Y-%m-%d")
        filename = f'/subs/{self.log_folder}/{month}/{date}.csv'
        with open(filename, 'a', newline='') as f:
            writer = csv.writer(f)
            if message['msg-id'] == 'sub':
                row = [message['display-name'], message['msg-id'], '1', today.strftime('%H:%M:%S:%f %Z')]
                writer.writerow(row)
            elif message['msg-id'] == 'resub':
                row = [message['display-name'], message['msg-id'], message['msg-param-cumulative-months'], today.strftime('%H:%M:%S:%f %Z')]
                writer.writerow(row)