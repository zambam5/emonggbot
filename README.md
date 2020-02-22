The cfgai file contains all account information you need to run this.
For the PASS, I used https://twitchapps.com/tmi/ to generate the token

The giftcounts.txt file is to generate a dictionary with twitch user IDs as keys
so I don't feel comfortable giving it out

I have no idea what I'm doing here so if I missed anything let me know :)

Update:
Added spotify functionality using spotipy. To get a token use get_token.py and follow the link.
It will cache the token needed to run the main bot.

Here are what a typical message dictionary looks like:
{
	'@badge-info': 'subscriber/16', 
	'badges': 'broadcaster/1,subscriber/12,bits-charity/1', 
	'color': '#E83FF5', 
	'display-name': 'zambam5', 
	'emotes': '', 
	'flags': '', 
	'id': '6e0720ad-440c-4042-a7f9-a739880c6a0a', 
	'mod': '0', 
	'room-id': '145421973', 
	'subscriber': '1', 
	'tmi-sent-ts': '1581811634354', 
	'turbo': '0', 
	'user-id': '145421973', 
	'': '', 
	'message type': 'PRIVMSG', 
	'actual message': 'test\r\n'
}