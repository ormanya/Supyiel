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
		"""[--id]

		Returns Taylor Swift quote from https://taylor.rest. Use --id flag to specify a particular quote from the API.
		"""
		if opts == "--image":
			url = "https://api.taylor.rest/image"
			key = "url"
		else:
                        url = "https://api.taylor.rest/"
			key = "quote"
		content = WebParser().getWebData(irc,url)

		outstr = content[key]
		irc.reply(outstr)

	tay = wrap(Taytay, [optional("something")])

Class = Quotes




