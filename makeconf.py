#config-editor.py
#To edit your config.py file.
import os
import sys
from ctypes import *
try:
	windll.Kernel32.GetStdHandle.restype = c_ulong
	h = windll.Kernel32.GetStdHandle(c_ulong(0xfffffff5))
	windll.Kernel32.SetConsoleTextAttribute(h, 7)
except: 
	pass
def changecolor(color):
	try:
		windll.Kernel32.SetConsoleTextAttribute(h, color)
	except:
		pass
settings = dict()
def askquestion(question, suggestion, key):
	changecolor(7)
	print(question)
	print('Press enter to use suggested value.')
	changecolor(8)
	print('Suggested: "%s"' % (suggestion))
	changecolor(10)
	settings[key] = raw_input('%s: --> ' % (key)) 
	if settings[key] == "":
		settings[key] = suggestion
	print('"' + key + '" set to ' + settings[key])
	print('')
	
print('Welcome to makeconf.py.')
print('This is designed to make setting up your new popm simple and easy.')
print('You must answer a few questions, and then the config file will be automatically created for you.')
print('')
raw_input('Press enter to begin.')
print('')
changecolor(2)
print('#########################################')
print('#            IRC options.               #')
print('#########################################')
askquestion('Please enter the server hostname you would like popm to connect to.', 'localhost', 'svr')
askquestion('Please enter what port you would like to connect to on that server.', '6667', 'port')
askquestion('Please enter the server\'s password, if there isn\'t one, simply enter \'None\'', 'None', 'serverpass')
askquestion('What nickname should POPM use?', 'POPM', 'user')
askquestion('What realname would you like POPM to use?', 'POPM, nomming your proxies.', 'realname')
askquestion('What away message should POPM have set?', 'Busy doing bot stuff.', 'away')
askquestion('What modes should popm set automatically on connection?', '+sBp +cF', 'automodes')
askquestion('How should POPM identify with NickServ?', 'PRIVMSG NickServ :id foobar', 'nickserv')
askquestion('What should POPM send to the server to get oper privelleges?', 'OPER POPM F00barz', 'operline')
changecolor(2)
print('#                                       #')
print('#           End IRC options.            #')
print('#########################################')
print('')
print('#########################################')
print('#          General Settings             #')
print('#########################################')
askquestion('What IRCd should POPM expect?', 'unrealircd', 'ircd')
askquestion('How long (in seconds) should POPM cache DNS lookups for? The suggested value is 24h (86400 seconds). To learn more about why POPM caches, read README.html', '86400', 'timecache')
askquestion('What hostnames (cloaked) should POPM allow access to commands? More can be added once the bot is running.', 'localhost', 'owners')
askquestion('Should POPM log important information to any channels? (As well as the default ./log.txt', '#services', 'logchan')
askquestion('Should POPM invite itself to a restricted channel?', 'PRIVMSG ChanServ :invite #services', 'invite')
askquestion('Should POPM log verbosely, i.e, in great detail? Useful for debbuging.', 'False', 'logverbose')
askquestion('Should POPM scan every user on connect? (Warning: resource intensive, DO NOT RUN ON LARGE (1500+) NETWORKS)', 'True', 'scanonconnect')

print('#                                       #')
print('#         End General Settings          #')
print('#########################################')
print('')
print('#########################################')
print('#         Statistical settings          #')
print('#########################################')
askquestion('Would you like POPM to collect statistical data and input it into a MySQL database?', 'yes', 'yesnochoice')
settings['yesnochoice'] = settings['yesnochoice'].lower()
if settings['yesnochoice'] == 'yes':
	try:
		import MySQLdb
		askquestion('What is the host of the MySQL server?', 'localhost', 'mysql_host')
		askquestion('What username should POPM identify by?', 'popm', 'mysql_user')
		askquestion('What password should POPM use?', 'f00bars', 'mysql_password')
		askquestion('What is the name of the database POPM should use?', 'popm', 'mysql_db')
		askquestion('What should the table POPM stores info\' in be called?', 'popmdata', 'mysql_table')

	except:
		changecolor(12)
		print('Error: Python module MySQLdb was not found. Please install it on your system in order to set up MySQL logging.')
		askquestion('Would you still like to setup mysql data? (It won\'t work until after you\'ve installed MySQLdb).', 'yes', 'yesnochoice')
		if settings['yesnochoice'].lower() == 'yes':
			askquestion('What is the host of the MySQL server?', 'localhost', 'mysql_host')
			askquestion('What username should POPM identify by?', 'popm', 'mysql_user')
			askquestion('What password should POPM use?', 'f00bars', 'mysql_password')
			askquestion('What is the name of the database POPM should use?', 'popm', 'mysql_db')
			askquestion('What should the table POPM stores info\' in be called?', 'popmdata', 'mysql_table')
			
changecolor(14)
print('')
print('#Config editing complete. Blacklists are set by default, \nbut if you want to edit blacklists to use manually,\nor you want to edit any of these without rerunning this program, \nsimply open up config.py in your favourite text editor.')
changecolor(15)
print('You can now run POPM (by running command \'python popm.py\' or using the daemonizing script \'popm\' by running \'python popm\'')
changecolor(15)
blacklists = '''blacklists = [
#Begin blacklist.
	#Each seperate dnsbl can be set out like below.
	#The blacklists are queried in this order (roughly).
	
	#Begin blacklist block.
	{"name":'dnsbl.dronebl.org',
	"type":"A record reply",
	"2":"Sample",
	"3":"IRC Drone",
	"5":"Bottler",
	"6":"Unknown spambot or drone",
	"7":"DDoS Drone",
	"8":"SOCKS Proxy",
	"9":"HTTP Proxy",
	"10":"ProxyChain",
	"13":"Brute force attackers",
	"255":"Unknown",
	"ban":"gline +*@%host% 24h :Your host was found in the DroneBL: '%reason%'. Please secure any legitimate proxy software you are running, or scan your computer for malware."
	}
	#End blacklist block.
	,
	
	#Begin blacklist block.
	{"name":"rbl.efnetrbl.org",
	"type":"A record reply",
	"1":"Open Proxy",
	"2":"spamtrap666",
	"3":"spamtrap50",
	"4":"TOR",
	"5":"Drones / Flooding",
	"ban":"gline +*@%host% 24h :Your host was found in the EFNet RBL: '%reason%'. For more information, see " }
	#End blacklist block.
	
	,
	
	#Begin blacklist block.
	{"name":"6667.38.121.64.208.ip-port.exitlist.torproject.org",
	"type":"A record reply",
	"2":"TOR exit node",
	"ban":"gline +*@%host% 24h :TOR exit nodes are not allowed on this network." }
	#End blacklist block.
#End blacklist.	
]'''
try:
	f = open('./config.py', 'w')
	f.write('#This is an automatically created file. For more guidance on completing it, please use the file from ./doc/config.py which is a documented version of this file.\n\n')
	for element in settings:
		f.write(element + " = " + ("", "'")[type(settings[element]) is str] + settings[element] + ("", "'")[type(settings[element]) is str] + "\n")
	for line in blacklists.split("\n"):
		f.write(line + "\n")
except:
	print('Fatal error: failed to write file.')

print('')
raw_input('Press the Enter key to QUIT.')