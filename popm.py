#/usr/bin/env python
#popm.py
#The main file for running popm.
#Todo:
#MySQL logging system
#User interface public commands.
#User interface private commands.
#Reload/restart commands.
import os
import irclib
try:
	import config
except:
	pass
import time
import sqlite3 as lite
import sys
import socket
import traceback
import thread
import subprocess

debug = True
def poplog(str):
	file = open("./var/popm.log", 'a+')
	file.write(time.strftime('%m-%d->%H:%M:%S: ', time.gmtime()) + str + "\n")
	file.close()
	
def p_debug(str):
	if debug:
		print(time.strftime('%H:%M:%S->', time.gmtime()) + " DEBUG -> " + str)
	else:
		pass
def p_logchan(str):
	if config.logchan:
		server.privmsg(config.logchan, "LOG: -> " + str)
	else:
		pass
		
def p_logverbose(str):
	if bool(config.logverbose):
		p_logchan('(verbose) ' + str)
		p_debug('(verbose) ' + str)
	else:
		pass

#Cache Functions
def getcache(host):
	try:
		con = lite.connect('popm.db')
		cur = con.cursor()
		cur.execute("SELECT * FROM ipcache where ip='%s'" % (host))
		rows = cur.fetchall()
		con.close()
		return rows
	except lite.Error, e:
		return "SQLite Error: " + e.args[0]
	finally:
		if con:
			con.close()
		return

#End Cache Functions
def timestamp(secs):
	secs = int(secs)
	days = secs / 86400
	hours = (secs % 86400) / 3600
	minutes = ((secs % 86400) % 3600) / 60
	seconds = (((secs % 86400) % 3600) % 60)
	d = ("days","day")[days==1]
	h = ("hours", "hour")[hours==1]
	m = ("minutes","minute")[minutes==1]
	s = ("seconds", "second")[seconds==1]
	returnstring = "%s %s, %s %s, %s %s %s %s" % (str(days), d, str(hours), h, str(minutes), m, str(seconds), s)
	returnstring = returnstring.replace("0 days, ", "")
	returnstring = returnstring.replace("0 hours, ","")
	returnstring = returnstring.replace("0 minutes, ", "")
	#return "%s %s, %s %s, %s %s %s %s" % (str(days), d, str(hours), h, str(minutes), m, str(seconds), s)
	return returnstring
	
def reversebit(str):
	str = str.split(".")[::-1]
	out = ""
	c = 0
	for s in str:
		c += 1
		if (c < len(str)):
			out += s + "."
		else:
			out += s
	return out

def handleNoOper(con, event):
	if debug:
		print('Attempt to authorize as network Operator was unsuccessful.')
		print('POPM will continue running as it is in debug mode.')
		pass
	else:
		poplog('Couldn\'t identify as OPER with command given in config.py. Please check you have added an operline for POPM, and that it has the matching host/password.')
		sys.exit()
	
def scanban(host, blacklist):
	try:
		#lastResult = 0, innocent until proven guilty in this case.
		result = socket.gethostbyname(reversebit(host) + "." + blacklist['name'])
		if ("127.0.0." in result):
			last = result.split(".")[-1]
			try:
				reason = blacklist[last]
			except KeyError:
				reason = "Unknown"
			ban = blacklist['ban'].replace("%host%",host)
			ban = ban.replace("%reason%", reason)
			server.send_raw(ban)
			p_logchan("Hit->: %s positive reply from %s: %s." % (host, blacklist['name'], reason))
			p_debug("Hit->: %s positive reply from %s: %s." % (host, blacklist['name'], reason))
			try:
				con = lite.connect('popm.db')
				cur = con.cursor()
				cur.execute("UPDATE ipcache SET lastResult=1, time=%s where ip='%s'" % (int(time.time()), host))
				con.commit()
				con.close()
				p_debug('Updated cache for %s to positive result.' % (host))
			except lite.Error, e:
				p_debug('Error from SQLite: %s' % (e.args[0]))
				con.rollback()
				con.close()
			return
	except socket.error, e:
		if '[Errno -2]' in str(e):
			p_debug("Negative scan for %s on %s." % (host, blacklist['name']))
			return
		else:
			poplog(str(e))
			p_logverbose(str(e))
	except:
		poplog(traceback.format_exc())
		p_logverbose(sys.exc_info()[0])
		#A different type of error. 
		#Won't occur regularly.
		#Safe to print any error to logverbose.
		
def handleWhoReply(con, event):
	if bool(config.scanonconnect):
		##########################
		p_debug('host not already in clientlist')
		try:
			host = socket.gethostbyname(event.arguments()[2])
			if host in clientList:
				p_debug('Host exists in clientlist already.')
				return
			p_debug('I got the host from the who reply as ' + host)
			try:
				con = lite.connect('popm.db')
				cur = con.cursor()
				cur.execute("SELECT * FROM ipcache where ip='%s'" % (host))
				rows = cur.fetchall()
				p_debug(str(rows))
				if str(rows) == '[]':
					clientList.append(host)
					cur.execute("INSERT INTO ipcache values('%s', %s, 0)" % (host, int(time.time())))
					con.commit()
					p_debug('I appended a host to lookup.')
					con.close()
					return
				else:
					difference = int(time.time()) - rows[1]
					if rows[2] == 0 and difference < int(config.timecache):
						#Note: could also check time here.
						con.close()
						return
					elif rows[2] == 1:
						#We won't deal with banning it here and now, we'll just add it to the list.
						con.close()
						clientList.append(host)
						p_debug('I appended a host to lookup.')
						return
					else:
						#if something went wrong and we're not sure, get it checked anyway.
						clientList.append(host)
						return
					
			except lite.Error, e:
				server.privmsg(nick, 'Error from SQLite: %s' % (e.args[0]))
			finally:
				if con:
					con.close()
					return
		except:
			p_debug('Exception passed: ' + str(sys.exc_info()))
			pass
			
def scanWholeClientList():
	#Wait for the clientList to be populated.
	time.sleep(5)
	p_logverbose('Scan on connect is enabled, there are %s individual hosts which need to be scanned, I will begin scanning them now, it is expected to take around %s to complete.' % (len(clientList), timestamp(int((len(clientList) * 0.4)))))
	for client in clientList:
		for blacklist in config.blacklists:
			thread.start_new_thread(scanban, (client, blacklist))
		time.sleep(0.4)
		
def handleConnect(con, event):
	#UnrealIRCd#
	if("*** Notice -- Client connecting" in event.arguments()[0] and config.ircd == "unrealircd"):
		p_debug('Connection notice: %s' % (event.arguments()[0]))
		interest = event.arguments()[0].split(":")[1]
		#host = interest.split("@")[1].replace(")","")
		host = event.arguments()[0].split("(")[1].split(")")[0].split("@")[1]
		if "[" in host:
			host = host.split("[")[0].replace(" ","")
		name = interest.split("@")[0].split("(")[0]
		#Check before resolve.
		if ":" in host:
			p_debug('An IPv6 client (%s) connected, but we ignored them.' % (name))
			#We're not interested in IPv6 clients.
			return
		try:
			host = socket.gethostbyname(host)
		except socket.error, e:
			p_logverbose(e.args[0])
		except:
			p_logverbose('Tried to resolve host (%s) but failed. Probably an IPv6 client.' % host)
			return
		p_debug('Resolved host to: %s' % (host))
		ident = interest.split("@")[0].split("(")[1]
		p_logverbose('Client connecting: %s!%s@%s' % (name[:-1], ident, host))
		#If the client was an IPv6 client that connected with a host that had 
		#both forward and reverse DNS they will have a hostname.
		#At this point, the IPv6 client's DNS lookup would have failed - host
		#will still be the FQHN, for example 'blah.smells.google.com'.
		#To avoid extra lookups, we should now check that all parts of the
		#host we're checking against the DNSBL is numeric.
		validIP = True
		for i in host.split('.'):
			if not i.isdigit():
				validIP = False
		if validIP == False:
			#This pathway should not be accessable. The IPv4 IP should be valid by this point.
			p_debug('%s was not a valid IPv4 address, so was not checked against DNSBL. This is nearly always the product of socket.gethostbyaddr of an IPv6 fully qualified hostname.' % (host))
			return
		p_debug('Checking against DNSBL.')
		#ADD CACHING CHECK HERE#
		try:
			doLookup = True
			#Set it to default True, so that if something goes wrong, we still check the host.
			con = lite.connect('popm.db')
			cur = con.cursor()
			cur.execute("SELECT * FROM ipcache where ip='%s'" % (host))
			rows = cur.fetchall()
			p_debug(str(rows))
			if str(rows) == '[]':
				cur.execute("INSERT INTO ipcache values('%s', %s, 0)" % (host, int(time.time())))
				con.commit()
				#lastResult = 0, innocent until proven guilty in this case.
			else:
				tableTime = rows[0][1]
				difference = int(time.time()) - tableTime
				if difference > int(config.timecache):
					doLookup = True
				else:
					p_debug('The time since last lookup of %s was less than 24 hours, so we didn\'t look it up again.' % (host))
					timeleft = int(config.timecache) - difference
					doLookup = False
					p_debug('rows[0][2]=' + str(rows[0][2]))
					p_debug(str(rows))
					if rows[0][2] == 1:
						p_debug('Banned a user using cache results only.')
						server.send_raw("GLINE +*@%s %ss :You appear in our DNS blacklist cache. This will expire in %s." % (host, timeleft + 600, timestamp(timeleft)))
						p_debug("Hit->: Banned %s from cache." % (host))
		except lite.Error, e:
			p_debug('Error from SQLite: %s' % (e.args[0]))
			con.rollback()
		finally:
			if con:
				con.close()
		if doLookup == True:
			for blacklist in config.blacklists:
				thread.start_new_thread(scanban, (host, blacklist))
		
			
	#<untested InspIRCd>, (VARIABLES ARE WRONG!)#
	#if ("*** CONNECT: Client connecting" in event.arguments()[0] and popmconf.ircd == "inspircd"):
	#	changestat('queries', len(popmconf.blacklists))
	#	changestat('connects', 1)
	#	host = event.arguments()[0].split("[")[1].replace("]","")
	#	if ":" in host:
	#		return
	#	info = event.arguments()[0].split("2")[7]
	#	if (popmconf.logchan and popmconf.logverbose):
	#		server.privmsg(popmconf.logchan, "Scanning client connecting from " + info)
	#	for blacklist in popmconf.blacklists:
	#		thread.start_new_thread(scanban, (host, blacklist))
	#</untested>#

def checkAdmin(host):
	return host in accessHosts
	
def handleDisconnect(con, event):
	time.sleep(20)
	try: 
		subprocess.Popen(["python", "popm.py"])
		sys.exit()
	except:
		poplog(traceback.format_exc().replace("\n"," "))
		sys.exit()

def handlePubMessage(con, event):
	messageSplit = event.arguments()[0].split(" ")
	if (server.get_nickname().lower() + ":" == messageSplit[0].lower()):
		host = event.source().split("@")[1]
		chan = event.target()
		command = messageSplit[1].lower()
		argsList = messageSplit[1:]
		if host == config.owners or checkAdmin(host):
			if command == "clientlist":
				for client in clientList:
					server.privmsg(chan, client)
		else:
			p_debug("%s attempted to use an admin command in %s but we ignored them." % (event.source(), chan))
			return
	else:
		return

def handlePrivMessage(con, event):
	if config.owners:
		host = event.source().split("@")[1]
		nick = event.source().split("!")[0]
		if host == config.owners or checkAdmin(host):
			message = event.arguments()[0]
			messageSplit = message.split(" ")
			parametersGiven = len(messageSplit)
			command = messageSplit[0].lower()
			argsList = messageSplit[1:]
			args = ""
			for arg in args:
				args += arg + " "
			args = args[:-1]
			##########HELP##########
			if command == "help":
				if len(messageSplit) < 2:
					server.privmsg(nick, "Type 'help <command-here>'.")
					server.privmsg(nick, "Commands: help, addhost(owner), checkcache, resetcache(owner)")
				else:
					helpTopic = messageSplit[1].lower()
					if helpTopic == "addhost":
						server.privmsg(nick, "Command: addhost <hostname> (owner only command) - adds a hostname to the temporary access list to use POPM's commands.")
						server.privmsg(nick, "Example: addhost localhost")
					elif helpTopic == "help":
						server.privmsg(nick, "Command: help <command-name> - get information about a specific command.")
						server.privmsg(nick, "Example: help addhost")
					elif helpTopic == "checkcache":
						server.privmsg(nick, "Command: checkcache <ip> - get whether or not POPM has cached that IP.")
						server.privmsg(nick, "Example: checkcache 94.128.283.13")
						server.privmsg(nick, "Command: checkcache <all>")
						server.privmsg(nick, "With no parameters, it will check how many cache records there are, with the 'all' parameter, it will show you the table (spammy).")
					elif helpTopic == "resetcache":
						server.privmsg(nick, "Command: resetcache <ip> - remove the cached data about <ip>.")
						server.privmsg(nick, "Example: resetcache 94.128.283.13")
						server.privmsg(nick, "Command: resetcache -forcebadaction - remove ALL the cached data about IPs.")
					else:
						server.privmsg(nick, "I don't have any help topic for: %s" % (helpTopic))
						
						
			##########ADDHOST##########
			elif command == "addhost" and host == config.owners:
				if not parametersGiven == 2:
					server.privmsg(nick, "addhost command expects one argument, try 'help addhost' for more info.")
					return
				try:
					accessHosts.append(argsList[0])
					server.privmsg(nick, "Added %s to the owners list. Owners list is now: %s" % (argsList[0], str(accessHosts)))
				except:
					server.privmsg(nick, "addhost command failed:")
					server.privmsg(nick, str(sys.exc_info()))
			##########CHECKCACHE##########
			elif command == "checkcache":
				if not parametersGiven == 2:
					try:
						con = lite.connect('popm.db')
						cur = con.cursor()
						cur.execute("SELECT * FROM ipcache")
						rows = cur.fetchall()
						if str(rows) == '[]':
							server.privmsg(nick, "There are currently no records in the IPcache table!")
						else:
							numrecords = len(rows)
							server.privmsg(nick, "There %s %s record%s in the IPcache table, type 'checkcache all' to see them all." % (("are", "is")[numrecords == 1], str(numrecords), ("s", "")[numrecords == 1]))
					except lite.Error, e:
						server.privmsg(nick, 'Error from SQLite: %s' % (e.args[0]))
					finally:
						if con:
							con.close()
							return
				try:
					con = lite.connect('popm.db')
					cur = con.cursor()
					#~-~-ALL the records.
					if argsList[0].lower() == 'all':
						cur.execute("SELECT * FROM ipcache")
						rows = cur.fetchall()
						if str(rows) == '[]':
							server.privmsg(nick, "There are currently no records in the IPcache table!")
						else:
							for row in rows:
								server.privmsg(nick, "IP: %s     Last checked: %s ago     Last result: %s" % (str(row[0]), timestamp((int(time.time()) - row[1])), ("Positive", "Negative")[row[2] == 0]))
						con.close()
						return
					cur.execute("SELECT * FROM ipcache where ip='%s'" % (argsList[0]))
					rows = cur.fetchall()
					if str(rows) == '[]':
						server.privmsg(nick, "There is no cached data for %s" % (argsList[0]))
					else:
						tableTime = rows[0][1]
						difference = int(time.time()) - tableTime
						server.privmsg(nick, "The last lookup for %s was %s ago and was %s." % (argsList[0], timestamp(difference), ('negative', 'positive')[rows[0][2] == 1]))
				except lite.Error, e:
					server.privmsg(nick, 'Error from SQLite: %s' % (e.args[0]))
				finally:
					if con:
						con.close()
			##########RESETCACHE##########
			elif command == "resetcache" and host == config.owners:
				if not parametersGiven == 2:
					server.privmsg(nick, "resetcache expects only one argument, if you're clearing ALL cache, the second parameter should be -forcebadaction otherwise it should be the IP you want to clear the cache record for.")
					server.privmsg(nick, "See 'help resetcache' for more information.")
				else:
					try:
						con = lite.connect('popm.db')
						cur = con.cursor()
						cur.execute("SELECT * FROM ipcache where ip='%s'" % (argsList[0]))
						rows = cur.fetchall()
						if str(rows) == '[]' and not argsList[0].lower() == "-forcebadaction":
							server.privmsg(nick, "There is no cached data for %s" % (argsList[0]))
							return
						if argsList[0].lower() == "-forcebadaction":
							server.privmsg(nick, "Removing all cached data...")
							try:
								cur.execute("DELETE FROM ipcache")
								con.commit()
								server.privmsg(nick, "Data successfully removed, %s records were affected." % (str(cur.rowcount)))
							except:
								server.privmsg(nick, "Something went wrong and the action was not completed.")
								con.rollback()
						else:
							ip = argsList[0]
							try:
								cur.execute("DELETE FROM ipcache WHERE ip='%s'" % (ip))
								con.commit()
								server.privmsg(nick, "%s successfully removed, %s records were affected." % (ip, str(cur.rowcount)))
							except:
								server.privmsg(nick, "Something went wrong and the action was not completed.")
								con.rollback()
					except lite.Error, e:
						server.privmsg(nick, 'Error from SQLite: %s' % (e.args[0]))
					except:
						server.privmsg(nick, 'Unexpected error->')
						server.privmsg(nick, str(sys.exc_info()))
						con.rollback()
					finally:
						if con:
							con.close()
						
		else:
			server.privmsg(nick, "You do not have permission to talk to me.")
			return
	else: 
		return
	
	
def main():
	#Initialize IRC Objects
	#Global for access by other classes.
	global irc
	global server
	global con
	global accessHosts
	global clientList
	accessHosts = list()
	accessHosts.append(config.owners)
	clientList = list()
	irc = irclib.IRC()
	server = irc.server()
	#Reload the config file to implement changes.
	reload(config)
	#Set up sqlite tables and databases
	try:
		con = lite.connect('popm.db')
		cur = con.cursor()
		cur.execute("CREATE TABLE IF NOT EXISTS ipcache(ip TEXT, time INT, lastResult INT)")
		cur.execute("CREATE TABLE IF NOT EXISTS stats(lookups INT, banned INT, bannedsinceconnect INT, connecttime INT)")
		con.commit()
		con.close()
	except lite.Error, e:
		p_debug('Error from SQLite: %s' % (e.args[0]))
		con.rollback()
		con.close()
		
	#We don't know if we are the first thread, 
	#give the potential old thread a few secs
	#to die.
	time.sleep(3) 
	#Connect!
	server.connect(config.svr, int(config.port), config.user, config.serverpass, config.realname)
	p_debug('Connected.')
	#Backup: realname doesn't seem to be registered properly in connect.
	server.send_raw("SETNAME :"+ config.realname)
	if config.operline:
		server.send_raw(config.operline)
	server.send_raw("WHO +R")
	if config.away:
		server.send_raw("AWAY :" + config.away)
	if config.nickserv:
		server.send_raw(config.nickserv)
	if config.automodes:
		server.send_raw("MODE " + server.get_nickname() + " " + config.automodes) 
	if config.logchan:
		if config.invite:
			server.send_raw(config.invite)
		time.sleep(2)
		server.send_raw("JOIN " + config.logchan)
	p_debug('Sent details to server.')
	if config.scanonconnect:
		thread.start_new_thread(scanWholeClientList, ())
	#Register commands, see IRCLIB if adding functionality to events.	
	irc.add_global_handler ( 'privnotice', handleConnect )
	irc.add_global_handler ( 'disconnect', handleDisconnect )
	irc.add_global_handler ( 'pubmsg', handlePubMessage )
	irc.add_global_handler ( 'privmsg', handlePrivMessage )
	irc.add_global_handler ( 'nooperhost', handleNoOper )
	irc.add_global_handler ( 'passwdmismatch', handleNoOper )
	irc.add_global_handler ( 'whoreply', handleWhoReply )
	p_debug('Entering main loop (process_forever()).')
	irc.process_forever()
	#When we say forever, we don't literally mean forever. 
	#Because you know. 
	#Forever is only a concept I guess.
	
	
if not os.path.isfile("config.py"):
	p_debug('There is no config file present, you must not have made one yet, OR you made one but makeconf.py did not have sufficient privileges to write the file.')
	import makeconf
else:
	try:
		main()
	except:
		if debug:
			print traceback.format_exc()
		poplog(traceback.format_exc())





	