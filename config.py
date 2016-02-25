#This is an automatically created file. For more guidance on completing it, please use the file from ./doc/config.py which is a documented version of this file.

serverpass = 'None'
mysql_password = 'f00bars'
owners = 'localhost'
timecache = '86400'
realname = 'POPM, nomming your proxies.'
ircd = 'unrealircd'
away = 'Busy doing bot stuff.'
logverbose = 'False'
nickserv = 'PRIVMSG NickServ :id foobar'
mysql_user = 'popm'
mysql_host = 'localhost'
mysql_table = 'popmdata'
operline = 'OPER POPM F00barz'
yesnochoice = 'yes'
user = 'POPM'
mysql_db = 'popm'
logchan = '#services'
automodes = '+sBp +cF'
svr = 'localhost'
port = '6667'
invite = 'PRIVMSG ChanServ :invite #services'
scanonconnect = 'True'
blacklists = [
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
]
