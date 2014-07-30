#!/usr/bin/env python
#-*- coding: utf-8 -*-

import ircbot
import sys
import time
import re
import thread
import sqlite3

debug = True

chans = ['#courssysteme', '#b6']
count = {}

class IRCCat(ircbot.SimpleIRCClient):
	def __init__(self, targets, db):
		ircbot.SimpleIRCClient.__init__(self)
		self.targets = targets
		self.server = None
		self.db = db
		self.cur = db.cursor()
	
	def sayto(self, target, msg):
		if self.server == None:
			print("Target not joined yet : unable to say \"%s\"" % (msg,))
		else:
			self.server.privmsg(target, "%c34%s" % (3, msg))

	def on_welcome(self, server, ev):
		print("Welcomed")
		for t in self.targets:
			if ircbot.is_channel(t):
				server.join(t)

	def on_join(self, server, ev):
		print("Joined")
		self.server = server

	def on_disconnect(self, server, ev):
		sys.exit(0)
	
	def on_pubmsg(self, server, ev):
		chan = ev.target()
		msg_ = ev.arguments()[0]
		msg = msg_.lower()
		nick = ev.source().split('!')[0]

		words = re.split('\W+', msg)
		count[chan] += 1
		entries = []
		for w in words:
			entries.extend([{'word': w, 'chan': c, 'incr': 1 if c == chan else 0} for c in chans])
		q = "INSERT OR REPLACE INTO Word (word, chan, count) VALUES (:word, :chan, COALESCE((SELECT count + :incr FROM Word WHERE word = :word AND chan = :chan), 0))"
		self.cur.executemany(q, entries)
		self.db.commit()

		q = "SELECT chan, SUM(count) FROM Word WHERE word IN (%s) GROUP BY chan" % (', '.join(['?'] * len(words)),)
		self.cur.execute(q, words)
		score = {s[0]: float(s[1]) / count[s[0]] for s in self.cur.fetchall()}

		maxchan = max(score, key=score.get)
		ratio = score[maxchan] / score[chan] if score[chan] > 0 else 0
		if (ratio > 2.0 and maxchan != chan):
			self.sayto(chan, '%s: ==> %s' % (nick, maxchan))

		print(msg)
		for s in score.items():
			print('%s: %s' % s)
		print('')



def check_install(db):
	"""Check whether table have been correctly set up."""
	c = db.cursor()
	c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Word'")
	return c.fetchone() != None


def install(db):
	"""Initialize database"""
	print('Installation...')
	c = db.cursor()
	c.execute('CREATE TABLE Word(word TEXT NOT NULL, chan TEXT COLLATE NOCASE NOT NULL, count INT NOT NULL DEFAULT 0, UNIQUE (word, chan))')
	db.commit()


def main():
	server = "ulminfo.fr"
	port = 6667
	nickname = "pitou"

	db = sqlite3.connect('nsfbot.db')

	if not check_install(db):
		install(db)

	cur = db.cursor()
	cur.execute("SELECT chan, SUM(count) FROM Word GROUP BY chan")
	for c in cur.fetchall():
		count[c[0]] = c[1]


	c = IRCCat(chans, db)
	try:
		print('Connection...')
		c.connect(server, port, nickname)
	except ircbot.ServerConnectionError as x:
		print(x)
		sys.exit(1)
	c.start()

if __name__ == "__main__":
	main()



