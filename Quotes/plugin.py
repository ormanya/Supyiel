# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Ormanya
# All rights reserved.
#
#

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
		url = requests.utils.requote_uri(url)
		try:
			content = requests.get(url, headers=headers)
			return content.json(), content.status_code
		except:
			#irc.reply("Error: Couldn't connect to "+url)
			return None,200

class Quotes(callbacks.Plugin):
	"""Contains commands for checking server status of various trackers."""
	threaded = True

	def Taytay(self, irc, msg, args, opts=None):
		"""[--album | --song]

		Returns Taylor Swift quote from https://taylorswiftapi.herokuapp.com/. 
		Use --album or --song to restrict search to specific tracks.
		"""

		valid_flags = ['--song','--album']
		# Get quote
		url = "https://taylorswiftapi.herokuapp.com/get"
		if opts is not None:
			category = opts.split(" ", 1)[0].replace("--","")
			if "--{}".format(category) in valid_flags:
				title = opts.split(" ", 1)[1]
				url = "{}?{}={}".format(url, category, title)
			else:
				irc.reply("Error: Invalid parameter '{}'. Valid parameters are {} ".format(opts, valid_flags))
				return
		key = "quote"

		content, status_code = WebParser().getWebData(irc,url)
		print("This is it{}it".format(content))
		if status_code != 200 or content is None:
			irc.reply("Error: The {} '{}' does not exist in the database.".format(category, title))
		else:
			outstr = "{} -Taylor Swift".format(content[key])
			irc.reply(outstr)

	tay = wrap(Taytay, [optional("text")])

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




