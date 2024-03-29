# -*- coding: utf-8 -*-
###
# Copyright (c) 2016-2017 Ormanya
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
import re

import supybot.schedule as schedule
from datetime import datetime



status_commands = ['btnStatus', 'redStatus', 'ptpStatus', 'ggnStatus', 'arStatus', 'empStatus','mtvStatus']
status_trackers = ['btn', 'red', 'ptp', 'ggn', 'ar', 'emp','mtv']


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

	def prepareStatusString(self, site_name, status, status_headers, breakpoints, line_headers):
		# Specify look and feel
		status_states = ["Down","Up","Iffy","Stinky"]
		status_symbols = ["Ⓧ","✓","◯","💩"] #😳
		status_colours = [chr(3)+"04",chr(3)+"03",chr(3)+"07",chr(3)+"05"]

		# Prepare output status message
		outStr = [line_headers[0]]
		count = 0
		line = 0
		for element in status:
			count = count + 1
			i = int(element)

			outStr[line] = outStr[line]+status_colours[i]+status_symbols[i]+" "+status_headers[count - 1 ]+" "+status_states[i]

			# Split output at breakpoints
			if count in breakpoints:
				line = line + 1
				outStr.extend([line_headers[line]])
			# don't append "|" if end of line	
			elif count != len(status):
				outStr[line] = outStr[line]+chr(15)+" | "                  
		return outStr

class Trackers(callbacks.Plugin):
	"""Contains commands for checking server status of various trackers."""
	threaded = True

	# def __init__(self, irc):
	# 	print "Setting it up"

	# 	self.__parent = super(Trackers, self)
	# 	self.__parent.__init__(irc)
	# 	# Set  scheduler variables

	# 	# Schedule announce check
	# 	# Check if event already exists
	# 	try:
	# 		schedule.removeEvent('statusAnnounce')
	# 	except KeyError:
	# 		pass

	# 	def myEventCaller():
	# 		print "Scheduling announce"
	# 		self.autoAnnounce(irc)


	# 	schedule.addPeriodicEvent(myEventCaller, 30, 'statusAnnounce')
	# 	self.irc = irc

	# 	print "All done"

	def formatTimeSince(self, interval):
		# seconds
		if (interval.days == 0) and (interval.seconds < 60):
			time_passed = "%s seconds ago" % interval.seconds
		# minutes
		elif interval.days == 0 and interval.seconds < 3600:
			if interval.seconds < 120:
				time_passed = "1 minute ago"
			else:
				time_passed = "%s minutes ago" % int(interval.seconds / 60 )
		# hours
		elif interval.days == 0:
			if interval.seconds < 7200:
				time_passed = "1 hour ago" 
			else:
				time_passed = "%s hours ago" % int(interval.seconds / 3600 )
		# days
		elif interval.days < 7:
			if interval.days == 1:
				time_passed = "1 day ago" 
			else:
				time_passed = "%s days ago" % interval.days
		# weeks
		else:
			if interval.days < 14:
				time_passed = "1 week ago"
			else:
				time_passed = "%s weeks ago" % int(interval.days/7)

		return time_passed

	def btnStatus(self, irc, msg, args, opts):
		"""[--message]

		Check the status of BTN site, tracker, and irc. Use --message flag to force return of message, even if older than 24 hours.
		"""
		url = "https://btn.trackerstatus.info/api/status/"
		site_name = "BTN"

		content = WebParser().getWebData(irc,url)

		status = [content["Website"], content["TrackerHTTP"], content["TrackerHTTPS"], content["IRC"], content["CableGuy"], content["Barney"], 3]
		status_headers = ["Site","Tracker","Tracker SSL","IRC","IRC Id","IRC Announce","kenyz"]
		breakpoints = [0]
		line_headers = [""]

		outStr = WebParser().prepareStatusString(site_name, status, status_headers, breakpoints,line_headers)

		for i in range(0, len(outStr)):
			irc.reply(outStr[i])

		# Output message if --message flag specified or newer than 1 day
		interval = datetime.now() - datetime.fromtimestamp(float(content["tweet"]["unix"]))
		if opts == "--message" or interval.days < 1:
			message_string = content["tweet"]["message"]
			time_string = self.formatTimeSince(interval)

			outstr = "%s message: %s (%s)" % (site_name, message_string, time_string)
			irc.reply(outstr)

	btn = wrap(btnStatus, [optional("something")])

	def redStatus(self, irc, msg, args, opts):
		"""[--message]

		Check the status of Redacted site, tracker, and irc. Use --message flag to force return of message, even if older than 24 hours.
		"""
		url = "http://red.trackerstatus.info/api/status/"
		site_name = "RED"

		content = WebParser().getWebData(irc,url)

		status = [content["Website"], content["TrackerHTTP"], content["TrackerHTTPS"], content["IRC"], content["IRCTorrentAnnouncer"], content["IRCUserIdentifier"]]
		status_headers = [site_name+" Site","Tracker","Tracker SSL","IRC","IRC Announce","IRC ID"]
		breakpoints = [0]
		line_headers = [""]
 
		outStr = WebParser().prepareStatusString(site_name, status, status_headers, breakpoints,line_headers)

		for i in range(0, len(outStr)):
			irc.reply(outStr[i])
			
		# Output message if --message flag specified or newer than 1 day
		interval = datetime.now() - datetime.fromtimestamp(float(content["tweet"]["unix"]))
		if opts == "--message" or interval.days < 1:
			message_string = content["tweet"]["message"]
			time_string = self.formatTimeSince(interval)

			outstr = "%s message: %s (%s)" % (site_name, message_string, time_string)
			irc.reply(outstr)

	red = wrap(redStatus, [optional("something")])

	def mtvStatus(self, irc, msg, args, opts):
		"""[--message]

		Check the status of MoreThanTV site, tracker, and irc.
		"""
		url = "http://is.morethantv.online/status.json"
		site_name = "MTV"

		content = WebParser().getWebData(irc,url)

		status = [content["moreme"], content["tracker"], content["trackerssl"], content["irc"]]
		status_headers = [site_name+" Site","Tracker","Tracker SSL","IRC"]
		breakpoints = [0]
		line_headers = [""]
 
		outStr = WebParser().prepareStatusString(site_name, status, status_headers, breakpoints,line_headers)

		for i in range(0, len(outStr)):
			irc.reply(outStr[i])
			
	mtv = wrap(mtvStatus, [optional("something")])

	def opsStatus(self, irc, msg, args, opts):
		"""[--message]

		Check the status of Orpheus site, tracker, and irc. Use --message flag to force return of message, even if older than 24 hours.
		"""
		url = "http://ops.trackerstatus.info/api/status/"
		site_name = "OPS"

		content = WebParser().getWebData(irc,url)

		status = [content["Website"], content["TrackerHTTP"], content["TrackerHTTPS"], content["IRC"], content["IRCTorrentAnnouncer"], content["IRCUserIdentifier"]]
		status_headers = [site_name+" Site","Tracker","Tracker SSL","IRC","IRC Announce","IRC ID"]
		breakpoints = [0]
		line_headers = [""]
 
		outStr = WebParser().prepareStatusString(site_name, status, status_headers, breakpoints,line_headers)

		for i in range(0, len(outStr)):
			irc.reply(outStr[i])
			
		# Output message if --message flag specified or newer than 1 day
		interval = datetime.now() - datetime.fromtimestamp(float(content["tweet"]["unix"]))
		if opts == "--message" or interval.days < 1:
			message_string = content["tweet"]["message"]
			time_string = self.formatTimeSince(interval)

			outstr = "%s message: %s (%s)" % (site_name, message_string, time_string)
			irc.reply(outstr)

	ops = wrap(opsStatus, [optional("something")])

	
	def ptpStatus(self, irc, msg, args, opts):
		"""
		Check the status of PTP site, tracker, and irc. Use --message flag to force return of message, even if older than 24 hours.
		"""
		url = "https://ptp.trackerstatus.info/api/status/"
		site_name = "PTP"

		content = WebParser().getWebData(irc,url)
	
		status = ([content["Website"], content["IRC"], content["IRCTorrentAnnouncer"], content["IRCUserIdentifier"],
			     content["TrackerHTTPAddresses"]["185.107.83.53"],
			     content["TrackerHTTPSAddresses"]["185.107.83.53"]])
		status_headers = ([site_name+" Site","IRC","IRC Announce","IRC ID",
						 "Tracker","Tracker SSL"])
		breakpoints = [4]
		line_headers = ["Services: ", "Trackers: "]

		outStr = WebParser().prepareStatusString(site_name, status, status_headers,breakpoints,line_headers)

		for i in range(0, len(outStr)):
			irc.reply(outStr[i])

		# Output message if --message flag specified or newer than 1 day
		interval = datetime.now() - datetime.fromtimestamp(float(content["tweet"]["unix"]))
		if opts == "--message" or interval.days < 1:
			message_string = content["tweet"]["message"]
			time_string = self.formatTimeSince(interval)

			outstr = "%s message: %s (%s)" % (site_name, message_string, time_string)
			irc.reply(outstr)

	ptp = wrap(ptpStatus, [optional("something")])

	def ggnStatus(self, irc, msg, args, opts):
		"""
		Check the status of GGN site, tracker, and irc. Use --message flag to force return of message, even if older than 24 hours.
		"""
		url = "https://ggn.trackerstatus.info/api/status/"
		site_name = "GGn"
		status_keys = ["Website","TrackerHTTP","TrackerHTTPS"] #,"IRC","IRCTorrentAnnouncer","IRCUserIdentifier"]
		status_headers = [site_name+" Site","Tracker","TrackerSSL"] #,"IRC","IRC Announce","IRC ID"]

		content = WebParser().getWebData(irc,url)

		status = []
		for i,item in enumerate(status_keys):
			try:
				status += content[item]
			except:
				status_headers.pop(i)
		breakpoints = [0]	
		line_headers = [""]	

		outStr = WebParser().prepareStatusString(site_name, status, status_headers,breakpoints,line_headers)

		for i in range(0, len(outStr)):
			irc.reply(outStr[i])

		# Output message if --message flag specified or newer than 1 day
		interval = datetime.now() - datetime.fromtimestamp(float(content["tweet"]["unix"]))
		if opts == "--message" or interval.days < 1:
			message_string = content["tweet"]["message"]
			time_string = self.formatTimeSince(interval)

			outstr = "%s message: %s (%s)" % (site_name, message_string, time_string)
			irc.reply(outstr)

	ggn = wrap(ggnStatus, [optional("something")])

	def arStatus(self, irc, msg, args, opts):
		"""
		Check the status of AR site, tracker, and irc. Use --message flag to force return of message, even if older than 24 hours.
		"""
		url = "http://ar.trackerstatus.info/api/status/"
		site_name = "AR"

		content = WebParser().getWebData(irc,url)

		status = [content["Website"], content["TrackerHTTP"], content["TrackerHTTPS"], content["IRC"], content["IRCTorrentAnnouncer"], content["IRCUserIdentifier"]]
		status_headers = [site_name+" Site","Tracker","Tracker SSL","IRC","IRC Announce","IRC ID"]
		breakpoints = [0]
		line_headers = [""]

		outStr = WebParser().prepareStatusString(site_name, status, status_headers, breakpoints,line_headers)

		for i in range(0, len(outStr)):
		        irc.reply(outStr[i])

		# Output message if --message flag specified or newer than 1 day
		interval = datetime.now() - datetime.fromtimestamp(float(content["tweet"]["unix"]))
		if opts == "--message" or interval.days < 1:
			message_string = content["tweet"]["message"]
			time_string = self.formatTimeSince(interval)

			outstr = "%s message: %s (%s)" % (site_name, message_string, time_string)
			irc.reply(outstr)

	ar = wrap(arStatus, [optional("something")])

	def abStatus(self, irc, msg, args, all):
		"""
		Check the status of AB site, tracker, and irc.
		"""
		url = "http://status.animebytes.tv/api/status"
		site_name = "AB"

		content = WebParser().getWebData(irc,url)
		content = content["status"]

		status = [content["site"]["status"], content["tracker"]["status"], content["irc"]["status"], content["mei"]["status"]]
		status_headers = [site_name+" Site","Tracker","IRC","Image Host"]
		breakpoints = [0]
		line_headers = [""]

		outStr = WebParser().prepareStatusString(site_name, status, status_headers, breakpoints,line_headers)

		for i in range(0, len(outStr)):
		        irc.reply(outStr[i])

	ab = wrap(abStatus, [optional("something")])

	def empStatus(self, irc, msg, args, all):
		"""
		Check the status of EMP site, tracker, and irc.
		"""

		# This function is different than the others because it scrapes HTML rather than use an api site
		url = "http://about.empornium.ph/"
		site_name = "EMP"

        # Get web page content
		headers = {'User-Agent' : 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17'}
		try:
			content = requests.get(url, headers=headers)
		except:
			irc.reply("Error: Couldn't connect to "+url)
			sys.exit()

		# Extract statuses
		status_txt = re.search(r'.*pull-right">(.*)<\/span>[\S\s.]+?pull-right">(.*)<\/span>[\S\s.]+?pull-right">(.*)<\/span>[\S\s.]+?pull-right">(.*)<\/span>', content.text)
		status = []
		for i in range(0,5):
			if status_txt.group(i) == "Online":
				status.append(1)
			else:
				status.append(0)

		status = [status[1],status[2],status[4],status[3]]
		status_headers = [site_name+" Site.me","Site.sx","Tracker","IRC"]
		breakpoints = [0]
		line_headers = [""]

		outStr = WebParser().prepareStatusString(site_name, status, status_headers, breakpoints,line_headers)

		for i in range(0, len(outStr)):
			irc.reply(outStr[i])

	emp = wrap(empStatus, [optional("something")])

	# def autoAnnounce(self, irc):
	# 	"""Schedule periodic announces for enabled trackers and channels"""
	# 	print "Start"
	# 	i = 0
	# 	for cmd in status_commands:
	# 		print cmd
	# 		for channel in irc.state.channels:
	# 			print "announce.relay"+status_trackers[i]
	# 			if self.registryValue("announce.relay"+status_trackers[i], channel):
	# 				print "announce.relay"+status_trackers[i]
	# 				try:
	# 					locals()["self."+cmd]()
	# 				except:
	# 					print "Failed to query status"
	# 				print channel
	# 		i = +1

Class = Trackers




