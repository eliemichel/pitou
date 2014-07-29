#!/usr/bin/env python
#-*- coding: utf-8 -*-

import ircbot
import sys
import time
import re
import thread

debug = True

words = {
	'#courssysteme': {},
	'#b6': {}
}

class IRCCat(ircbot.SimpleIRCClient):
	def __init__(self, targets):
		ircbot.SimpleIRCClient.__init__(self)
		self.targets = targets
		self.server = None
	
	def sayto(self, target, msg):
		if self.server == None:
			print("Target not joined yet : unable to say \"%s\"" % (msg,))
		else:
			self.server.privmsg(target, "%c14%s" % (3, msg))

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
		self.say('hello')
	
	def on_pubmsg(self, server, ev):
		chan = ev.target()
		msg_ = ev.arguments()[0]
		msg = msg_.lower()
		nick = ev.source().split('!')[0]

		score = {c: 0 for c in words.keys()}
		for w in msg.split(' '):
			if not w in words[chan]:
				words[chan][w] = 0
			words[chan][w] += 1

			for c in score.keys():
				if w in words[c]:
					score[c] += words[c][w]
		maxchan = max(score, key=score.get)
		ratio = score[maxchan] / score[chan] if score[chan] > 0 else 0
		if (ratio > 0.75 and maxchan != chan):
			self.sayto(chan, '==> %s' % (maxchan,))

		print(msg)
		for s in score.items():
			print('%s: %s' % s)
		print('')


def main():
	server = "ulminfo.fr"
	port = 6667
	nickname = "nsfbot"
	targets = words.keys()

	c = IRCCat(targets)
	try:
		c.connect(server, port, nickname)
	except ircbot.ServerConnectionError as x:
		print(x)
		sys.exit(1)
	c.start()

if __name__ == "__main__":
	main()



