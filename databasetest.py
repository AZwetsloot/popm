import sqlite3 as lite
import time
try:
	con = lite.connect('popm.db')
	cur = con.cursor()
	cur.execute("CREATE TABLE IF NOT EXISTS ipcache(ip TEXT, time INTEGER)")
	cur.execute("INSERT OR REPLACE INTO ipcache (ip, time) VALUES('127.0.0.1',%s)" % (int(time.time())))
	con.commit()
	cur.execute("SELECT time FROM ipcache where ip='127.0.0.1'")
	rows = cur.fetchall()
	print rows[0][0]
	if str(rows) == "[]":
		print 'Apparently that doesn\'t exist.'
	else:
		print str(rows)
		
except lite.Error, e:
	print('Error from SQLite: %s' % (e.args[0]))
finally:
	if con:
		con.close()

print('Done!')
raw_input()