# -*- coding: utf-8 -*-
###
# Copyright (c) 2021 Ormanya
# All rights reserved.
#
#
###

import supybot.plugins as plugins
from supybot.commands import *
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import requests
import json
import sys
import string, random

class WebParser():
	"""Contains functions for getting and parsing web data"""

	def getWebData(self, irc, url):
		headers = {'User-Agent' : 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17'}
		try:
			content = requests.get(url, headers=headers)
			return content.json()
		except:
			irc.reply("Error: Couldn't connect to "+url)
			sys.exit()

class Quotes(callbacks.Plugin):
	"""Contains commands for checking server status of various trackers."""
	threaded = True

	def Taytay(self, irc, msg, args, opts):
		"""[--image]

		Returns Taylor Swift quote from https://taylor.rest. Use --image to return an image too.
		"""

		# Get quote
		url = "https://api.taylor.rest/"
		key = "quote"
		content = WebParser().getWebData(irc,url)
		outstr = content[key]


		outstr += " -Taylor Swift "
		# Get image if available
		if opts == "--image":
			url = url + "image"
			key = "url"
			try:
				content = WebParser().getWebData(irc,url)
				outstr += " {}".format(content[key])
			except:
				pass

		irc.reply(outstr)

	tay = wrap(Taytay, [optional("something")])

	def GoodPlace(self, irc, msg, args, opts):
		"""[--char <name>]

		Returns quote from the TV show The Good Place. Use --char <name> to get quote from a specific character.
		"""
		base_url = "https://good-place-quotes.herokuapp.com/api/"
		flags = ["char"]

		if opts is not None:
			opts = opts.split()
			if opts[0] == "--char" and len(opts) > 1:
				try:
					url = base_url + "character/{}".format(opts[1])
					content = WebParser().getWebData(irc,url)
					content = random.choice(content)
					print(content)
				except:
					irc.reply("There are no quotes from {}.".format(opts[1]))
					return
			else:
				irc.reply("Unsupported parameters: {}".format(opts))
				return
		else:
			url = base_url + "random"
			content = WebParser().getWebData(irc,url)
		print(content)
	
		outstr = "{} -{}".format(content["quote"], content["character"])

		irc.reply(outstr)

	goodplace = wrap(GoodPlace, [optional("text")])

	def AestheticPerfection(self, irc, msg, args, opts):
		"""[--image]

		Returns quote from the band Aesthetic Perfection. Use --image to return an image too, when available.
		"""

		# Get quote
		url = "http://ap-q.glitch.me/api"
		key = "quote"
		content = WebParser().getWebData(irc,url)
		outstr = content[key]

		# Get image if available
		if opts == "--image":
			key = "image"
			try:
				outstr += " {}".format(content[key])
			except:
				pass

		outstr += " -Aesthetic Perfection"
		irc.reply(outstr)

	ap = wrap(AestheticPerfection, [optional("something")])

Class = Quotes




