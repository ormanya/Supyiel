###
# Copyright (c) 2012, Matthias Meusburger
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
###

from supybot.commands import *
import supybot.plugins as plugins
import supybot.callbacks as callbacks
import supybot.schedule as schedule
import supybot.ircdb as ircdb
import supybot.ircmsgs as ircmsgs
import supybot.log as log
import supybot.conf as conf


import threading, random, pickle, os, time, datetime


class dickHunt(callbacks.Plugin):
	"""
	A dickHunt game for supybot. Use the "start" command to start a game.
	The bot will randomly release dicks. Whenever a dick is released, the first
	person to use the "bendover" command wins a point. Using the "bendover" command
	when there is no dick released costs a point.
	"""

	threaded = True

	# Those parameters are per-channel parameters
	started = {}       # Has the hunt started?
	dick = {}          # Is there currently a dick to fuck?
	bends = {}         # Number of successfull penetrations in a hunt
	scores = {}        # Scores for the current hunt
	times = {}         # Elapsed time since the last dick was released
	channelscores = {} # Saved scores for the channel
	toptimes = {}      # Times for the current hunt
	channeltimes = {}  # Saved times for the channel
	worsttimes = {}    # Worst times for the current hunt
	channelworsttimes = {} # Saved worst times for the channel
	averagetime = {}   # Average shooting time for the current hunt
	orgyMode = {}      # Are we on orgy mode? (automatic)
	manualOrgy = {}    # Are we on orgy mode? (manual)
	missprobability = {} # Probability to miss a dick when shooting
	week = {}          # Scores for the week
	channelweek = {}   # Saved scores for the week
	leader = {}        # Who is the leader for the week?
	preparing = {}     # Who is currently preparing?
	preparetime = {}   # Time to prepare after shooting (in seconds)
	dickColor = {}     # Active dick
	lubed = {}	       # Who is lubed?
	needslube = {}     # Who needs lube?

	# Does a dick needs to be released?
	lastSpoke = {}
	minthrottle = {}
	maxthrottle = {}
	throttle = {}

	# Where to save scores?
	fileprefix = "dickHunt_"
	path = conf.supybot.directories.data

	# Enable the 'dbg' command, which release a dick, if true
	debug = 0

	# Other params
	debugLog = True  # Write errors to debug log
	debugFile = conf.supybot.directories.data.dirize("dickhunt/log.txt")

	perfectbonus = 5 # How many extra-points are given when someones does a perfect hunt?
	toplist = 8      # How many high{scores|times} are displayed by default?
	dow = int(time.strftime("%u")) # Day of week
	woy = int(time.strftime("%V")) # Week of year
	year = time.strftime("%Y") 
	dayname = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Caturday', 'Saturday', 'Sunday']

	def hl_protect(self, nick):
		"""
		Inserts non-printing character in nick to prevent highlights
		"""
		return nick[0] + '\u200B' + nick[1:]

	def irc_color(self, s):
		"""
		Returns a colorized version of the given text based on a random color.
		"""
		colors = ('03', '04', '05', '06', '07', '09', '10', '11',
				  '12', '13')
		num = random.randint(0,len(colors)-1)
		return "\x03%s%s\x03" % (colors[num], s)

	def _calc_scores(self, channel):
		"""
		Adds new scores and times to the already saved ones
		"""

		# scores
		# Adding current scores to the channel scores
		for player in list(self.scores[channel].keys()):
			if not player in self.channelscores[channel]:
				# It's a new player
				self.channelscores[channel][player] = self.scores[channel][player]
			else:
				# It's a player that already has a saved score
				self.channelscores[channel][player] += self.scores[channel][player]

		# times
		# Adding times scores to the channel scores
		for player in list(self.toptimes[channel].keys()):
			if not player in self.channeltimes[channel]:
				# It's a new player
				self.channeltimes[channel][player] = self.toptimes[channel][player]
			else:
				# It's a player that already has a saved score
				# And we save the time of the current hunt if it's better than it's previous time
				if(self.toptimes[channel][player] < self.channeltimes[channel][player]):
					self.channeltimes[channel][player] = self.toptimes[channel][player]

		# worst times
		# Adding worst times scores to the channel scores
		for player in list(self.worsttimes[channel].keys()):
			if not player in self.channelworsttimes[channel]:
				# It's a new player
				self.channelworsttimes[channel][player] = self.worsttimes[channel][player]
			else:
				# It's a player that already has a saved score
				# And we save the time of the current hunt if it's worst than it's previous time
				if(self.worsttimes[channel][player] > self.channelworsttimes[channel][player]):
					self.channelworsttimes[channel][player] = self.worsttimes[channel][player]

		# week scores
		for player in list(self.scores[channel].keys()):
			#FIXME: If the hunt starts a day and ends the day after, this will produce an error:
			if not player in self.channelweek[channel][self.woy][self.dow]:
				# It's a new player
				self.channelweek[channel][self.woy][self.dow][player] = self.scores[channel][player]
			else:
				# It's a player that already has a saved score
				self.channelweek[channel][self.woy][self.dow][player] += self.scores[channel][player]




	def _write_scores(self, channel):
		"""
		Write scores and times to the disk
		"""

		# scores
		outputfile = open(self.path.dirize("dickhunt/" + self.fileprefix + channel + ".scores"), "wb")
		pickle.dump(self.channelscores[channel], outputfile)
		outputfile.close()

		# times
		outputfile = open(self.path.dirize("dickhunt/" + self.fileprefix + channel + ".times"), "wb")
		pickle.dump(self.channeltimes[channel], outputfile)
		outputfile.close()

		# worst times
		outputfile = open(self.path.dirize("dickhunt/" + self.fileprefix + channel + ".worsttimes"), "wb")
		pickle.dump(self.channelworsttimes[channel], outputfile)
		outputfile.close()

		# week scores
		outputfile = open(self.path.dirize("dickhunt/" + self.fileprefix + channel + self.year + ".weekscores"), "wb")
		pickle.dump(self.channelweek[channel], outputfile)
		outputfile.close()







	def _read_scores(self, channel):
		"""
		Reads scores and times from disk
		"""
		filename = self.path.dirize("dickhunt/" + self.fileprefix + channel)
		# scores
		if not self.channelscores.get(channel):
			if os.path.isfile(filename + ".scores"):
				inputfile = open(filename + ".scores", "rb")
				self.channelscores[channel] = pickle.load(inputfile)
				inputfile.close()

		# times
		if not self.channeltimes.get(channel):
			if os.path.isfile(filename + ".times"):
				inputfile = open(filename + ".times", "rb")
				self.channeltimes[channel] = pickle.load(inputfile)
				inputfile.close()

		# worst times
		if not self.channelworsttimes.get(channel):
			if os.path.isfile(filename + ".worsttimes"):
				inputfile = open(filename + ".worsttimes", "rb")
				self.channelworsttimes[channel] = pickle.load(inputfile)
				inputfile.close()

		# week scores
		if not self.channelweek.get(channel):
			if os.path.isfile(filename + self.year + ".weekscores"):
				inputfile = open(filename + self.year + ".weekscores", "rb")
				self.channelweek[channel] = pickle.load(inputfile)
				inputfile.close()



	def _initdayweekyear(self, channel):
		self.dow = int(time.strftime("%u")) # Day of week
		self.woy = int(time.strftime("%V")) # Week of year
		year = time.strftime("%Y") 

		# Init week scores
		try:
			self.channelweek[channel]
		except:
			self.channelweek[channel] = {}
		try:
			self.channelweek[channel][self.woy]
		except:
			self.channelweek[channel][self.woy] = {}
		try:
			self.channelweek[channel][self.woy][self.dow]
		except:
			self.channelweek[channel][self.woy][self.dow] = {}


	
	def _initthrottle(self, irc, msg, args, channel):

		self._initdayweekyear(channel)
			
		if not self.leader.get(channel):
			self.leader[channel] = None

		# autoOrgy?
		if (not self.orgyMode.get(channel)):
			self.orgyMode[channel] = False

		if (not self.manualorgy.get(channel)):
			self.manualorgy[channel] = False


		if self.registryValue('autoOrgy', channel) == True:
			if int(time.strftime("%w")) == 5 and int(time.strftime("%H")) > 8 and int(time.strftime("%H")) < 17:
				self.orgyMode[channel] = True
			else:
				self.orgyMode[channel] = False

		# Miss probability
		if self.registryValue('missProbability', channel):
			self.missprobability[channel] = self.registryValue('missProbability', channel)
		else:
			self.missprobability[channel] = 0.2

		# prepare time
		if self.registryValue('prepareTime', channel):
			self.preparetime[channel] = self.registryValue('prepareTime', channel)
		else:
			self.preparetime[channel] = 5

		if self.orgyMode[channel] == False and self.manualOrgy[channel] == False:
			# Init min throttle[currentChannel] and max throttle[currentChannel]
			if self.registryValue('minthrottle', channel):
				self.minthrottle[channel] = self.registryValue('minthrottle', channel)
			else:
				self.minthrottle[channel] = 30

			if self.registryValue('maxthrottle', channel):
				self.maxthrottle[channel] = self.registryValue('maxthrottle', channel)
			else:
				self.maxthrottle[channel] = 300

		else:
			self.minthrottle[channel] = 3
			self.maxthrottle[channel] = 60

		self.throttle[channel] = random.randint(self.minthrottle[channel], self.maxthrottle[channel])


	def start(self, irc, msg, args, channel):
		"""
		[<channel>]

		Starts the hunt
		"""


		if irc.isChannel(channel):
			currentChannel = channel
		elif irc.isChannel(msg.args[0]):
			currentChannel = msg.args[0]
		else:
			irc.error('You have to be on a channel or specify a channel')
			return

		if irc.isChannel(currentChannel):
			if(self.started.get(currentChannel) == True):
				irc.reply("Fire up Grindr because the  hunt is already on!")
			else:
				# First of all, let's read the score if needed
				self._read_scores(currentChannel)

				self._initthrottle(irc, msg, args, currentChannel)

				# Init saved scores
				try:
					self.channelscores[currentChannel]
				except:
					self.channelscores[currentChannel] = {}

				# Init saved times
				try:
					self.channeltimes[currentChannel]
				except:
					self.channeltimes[currentChannel] = {}

				# Init saved times
				try:
					self.channelworsttimes[currentChannel]
				except:
					self.channelworsttimes[currentChannel] = {}

				# Init times
				self.toptimes[currentChannel] = {}
				self.worsttimes[currentChannel] = {}

				# Init benddelay
				self.times[currentChannel] = False

				# Init lastSpoke
				self.lastSpoke[currentChannel] = time.time()

				# Reinit current hunt scores
				if self.scores.get(currentChannel):
					self.scores[currentChannel] = {}

				# Reinit preparing
				self.preparing[currentChannel] = {}

				# Reinit lubed
				self.lubed[currentChannel] = {}

				# Reinit needslube
				self.needslube[currentChannel] = {}


				# Reinit dickColor
				self.dickColor[currentChannel] = ''

				# No dick released
				self.dick[currentChannel] = False

				# Hunt started
				self.started[currentChannel] = True

				# Init penetrations
				self.bends[currentChannel] = 0

				# Init averagetime
				self.averagetime[currentChannel] = 0;

				# Init schedule

				# First of all, stop the scheduler if it was still running
				try:
					schedule.removeEvent('dickHunt_' + currentChannel)
				except KeyError:
					pass

				# Then restart it
				def myEventCaller():
					self._releaseEvent(irc, msg, currentChannel)
				try:
					schedule.addPeriodicEvent(myEventCaller, 5, 'dickHunt_' + currentChannel, False)
				except AssertionError:
					pass

				irc.sendMsg(ircmsgs.privmsg(currentChannel, "The hunt starts now!"))

		else:
			irc.error('Has to be started in a channel or have a channel specified')


	start = wrap(start, [optional('channel')])


	def _releaseEvent(self, irc, msg, currentChannel):
		# currentChannel = msg.args[0]
		now = time.time()

		if irc.isChannel(currentChannel):
			if(self.started.get(currentChannel) == True):
				if (self.dick[currentChannel] == False):	
					if now > self.lastSpoke[currentChannel] + self.throttle[currentChannel]:
						self._release(irc, currentChannel, msg, '')




	def stop(self, irc, msg, args, channel):
		"""
		[<channel>]

		Stops the current hunt
		"""

		if irc.isChannel(channel):
			currentChannel = channel
		elif irc.isChannel(msg.args[0]):
			currentChannel = msg.args[0]
		else:
			irc.error('You have to be on a channel or specify a channel')
			return

		if True:
			if (self.started.get(currentChannel) == True):
				self._end(irc, msg, args, currentChannel)

			# If someone uses the stop command,
			# we stop the scheduler, even if autoRestart is enabled
			try:
				schedule.removeEvent('dickHunt_' + currentChannel)
			except KeyError:
				irc.reply('Error: the spammer wasn\'t running! This is a bug.')
			else:
				irc.reply('Nothing to stop: there\'s no hunt right now.')

	stop = wrap(stop, [optional('channel')])

	def orgymode(self, irc, msg, args, channel, status):
		"""
		[<status>] 
		Enable/disable orgy mode! (there are lots of dicks in an orgy :))
		"""
		if irc.isChannel(channel):

			if (status == 'status'):
				irc.reply('Manual orgy mode for ' + channel + ' is ' + str(self.manualOrgy.get(channel)));
				irc.reply('Auto orgy mode for ' + channel + ' is ' + str(self.orgyMode.get(channel)));
			else:
				if (self.manualOrgy.get(channel) == None or self.manualOrgy[channel] == False):
					self.manualOrgy[channel] = True
					irc.reply("Orgy mode is now enabled! Fuck alllllllllllll the dicks!")
				else:
					self.manualOrgy[channel] = False
					irc.reply("Orgy mode is now disabled.")

			self._initthrottle(irc, msg, args, channel)
		else:
			irc.error('You have to be on a channel')


	orgymode = wrap(orgymode, ['channel', 'admin', optional('anything')])

	def released(self, irc, msg, args):
		"""
		Is there a dick right now?
		"""

		currentChannel = msg.args[0]
		if irc.isChannel(currentChannel):
			if(self.started.get(currentChannel) == True):
				if(self.dick[currentChannel] == True):
					irc.reply("There is currently a dick! You can fuck it with the 'bendover' command")
				else:
					irc.reply("There is no dick right now! Wait for one to be released!")
			else:
				irc.reply("There is no hunt right now! You can start a hunt with the 'start' command")
		else:
			irc.error('You have to be on a channel')
	released = wrap(released)



	def score(self, irc, msg, args, nick):
		"""
		<nick>

		Shows the score for a given nick
		"""
		currentChannel = msg.args[0]
		if irc.isChannel(currentChannel):
			self._read_scores(currentChannel)
			try:
				self.channelscores[currentChannel]
			except:
				self.channelscores[currentChannel] = {}


			try:
				irc.reply(self.channelscores[currentChannel][nick])
			except:
				irc.reply("There is no score for %s on %s" % (self.hl_protect(nick), currentChannel))
		else:
			irc.error('You have to be on a channel')

	score = wrap(score, ['nick'])



	def mergescores(self, irc, msg, args, channel, nickto, nickfrom):
		"""
		[<channel>] <nickto> <nickfrom>
		
		nickto gets the points of nickfrom and nickfrom is removed from the scorelist
		"""
		if irc.isChannel(channel):
			self._read_scores(channel)

			# Total scores
			try:
				self.channelscores[channel][nickto] += self.channelscores[channel][nickfrom]
				del self.channelscores[channel][nickfrom]
				self._write_scores(channel)
				irc.reply("Total scores merged")

			except:
				irc.error("Can't merge total scores")

			# Day scores
			try:
				self._initdayweekyear(channel)
				day = self.dow
				week = self.woy

				try:
					self.channelweek[channel][week][day][nickto] += self.channelweek[channel][week][day][nickfrom]
				except:
					self.channelweek[channel][week][day][nickto] = self.channelweek[channel][week][day][nickfrom]

				del self.channelweek[channel][week][day][nickfrom]
				self._write_scores(channel)
				irc.reply("Day scores merged")

			except:
				irc.error("Can't merge day scores")



		else:
			irc.error('You have to be on a channel')


	mergescores = wrap(mergescores, ['channel', 'nick', 'nick', 'admin'])



	def mergetimes(self, irc, msg, args, channel, nickto, nickfrom):
		"""
		[<channel>] <nickto> <nickfrom>
		
		nickto gets the best time of nickfrom if nickfrom time is better than nickto time, and nickfrom is removed from the timelist. Also works with worst times. 
		"""
		if irc.isChannel(channel):
			try:
				self._read_scores(channel)

				# Merge best times
				if self.channeltimes[channel][nickfrom] < self.channeltimes[channel][nickto]:
					self.channeltimes[channel][nickto] = self.channeltimes[channel][nickfrom]
				del self.channeltimes[channel][nickfrom]

				# Merge worst times
				if self.channelworsttimes[channel][nickfrom] > self.channelworsttimes[channel][nickto]:
					self.channelworsttimes[channel][nickto] = self.channelworsttimes[channel][nickfrom]
				del self.channelworsttimes[channel][nickfrom]

				self._write_scores(channel)

				irc.replySuccess()

			except:
				irc.replyError()


		else:
			irc.error('You have to be on a channel')


	mergetimes = wrap(mergetimes, ['channel', 'nick', 'nick', 'admin'])



	def rmtime(self, irc, msg, args, channel, nick):
		"""
		[<channel>] <nick>
		
		Remove <nick>'s best time
		"""
		if irc.isChannel(channel):
			self._read_scores(channel)
			del self.channeltimes[channel][nick]
			self._write_scores(channel)
			irc.replySuccess()

		else:
			irc.error('Are you sure ' + str(channel) + ' is a channel?')

		rmtime = wrap(rmtime, ['channel', 'nick', 'admin'])



	def rmscore(self, irc, msg, args, channel, nick):
		"""
		[<channel>] <nick>
		
		Remove <nick>'s score
		"""
		if irc.isChannel(channel):
			try:
				self._read_scores(channel)
				del self.channelscores[channel][nick]
				self._write_scores(channel)
				irc.replySuccess()

			except:
				irc.replyError()

		else:
			irc.error('Are you sure this is a channel?')

		rmscore = wrap(rmscore, ['channel', 'nick', 'admin'])




	def dayscores(self, irc, msg, args, channel):
		"""
		[<channel>]
		
		Shows the score list of the day for <channel>. 
		"""

		if irc.isChannel(channel):

			self._read_scores(channel)
			self._initdayweekyear(channel)
			day = self.dow
			week = self.woy

			if self.channelweek.get(channel):
				if self.channelweek[channel].get(week):
					if self.channelweek[channel][week].get(day):
						# Getting all scores, to get the winner of the week
						msgstring = ''
						scores = sorted(iter(list(self.channelweek[channel][week][day].items())), key=lambda k_v2:(k_v2[1],k_v2[0]), reverse=True)
						for item in scores:
							msgstring += self.hl_protect(item[0]) + " "+ str(item[1]) + " | "

						if msgstring != "":
							irc.reply("Scores for today: " + msgstring)
						else:
							irc.reply("There aren't any day scores for today yet.")
					else:
						irc.reply("There aren't any day scores for today yet.")
				else:
					irc.reply("There aren't any day scores for today yet.")
			else:
				irc.reply("There aren't any day scores for this channel yet.")
		else:
			irc.reply("Are you sure this is a channel?")
	dayscores = wrap(dayscores, ['channel'])



	def weekscores(self, irc, msg, args, week, nick, channel):
		"""
		[<week>] [<nick>] [<channel>]
		
		Shows the score list of the week for <channel>. If <nick> is provided, it will only show <nick>'s scores.
		"""

		if irc.isChannel(channel):

			self._read_scores(channel)
			weekscores = {}

			if (not week):
				week = self.woy

			if self.channelweek.get(channel):
				if self.channelweek[channel].get(week):
					# Showing the winner for each day
					if not nick:
						msgstring = ''
						# for each day of week
						for i in range(1,7):
							if self.channelweek[channel][week].get(i):
								# Getting winner of the day
								winnernick, winnerscore = max(iter(list(self.channelweek[channel][week][i].items())), key=lambda k_v:(k_v[1],k_v[0]))
								msgstring += self.dayname[i - 1] + ": " + self.hl_protect(winnernick) + " (" + str(winnerscore) + ") | "

								# Getting all scores, to get the winner of the week
								for player in list(self.channelweek[channel][week][i].keys()):
									try:
										weekscores[player] += self.channelweek[channel][week][i][player]
									except:
										weekscores[player] = self.channelweek[channel][week][i][player]
							 
						if msgstring != '':
							irc.reply("Scores for week " + str(week) + ": " + msgstring)
							# Who's the winner at this point?
							winnernick, winnerscore = max(iter(list(weekscores.items())), key=lambda k_v1:(k_v1[1],k_v1[0]))
							irc.reply("Leader: %s with %i points." % (self.hl_protect(winnernick), winnerscore)) 

						else:
							irc.reply("There aren't any week scores for this week yet.")
					else:
						# Showing the scores of <nick>
						msgstring = ''
						total = 0
						for i in (1,2,3,4,5,6,7):
							if self.channelweek[channel][week].get(i):
								if self.channelweek[channel][week][i].get(nick):
									msgstring += self.dayname[i - 1] + ": "+ str(self.channelweek[channel][week][i].get(nick)) + " | "
									total += self.channelweek[channel][week][i].get(nick)

						if msgstring != "":
							irc.reply(self.hl_protect(nick) + " scores for week " + str(self.woy) + ": " + msgstring)
							irc.reply("Total: " + str(total) + " points.")
						else:
							irc.reply("There aren't any week scores for this nick.")
				else:
					irc.reply("There aren't any week scores for this week yet.")
			else:
				irc.reply("There aren't any week scores for this channel yet.")
		else:
			irc.reply("Are you sure this is a channel?")
	weekscores = wrap(weekscores, [optional('int'), optional('nick'), 'channel'])



	def listscores(self, irc, msg, args, size, channel):
		"""
		[<size>] [<channel>]
		
		Shows the <size>-sized score list for <channel> (or for the current channel if no channel is given)
		"""

		if irc.isChannel(channel):
			try:
				self.channelscores[channel]
			except:
				self.channelscores[channel] = {}

			self._read_scores(channel)

			# How many results do we display?
			if (not size):
				listsize = self.toplist
			else:
				listsize = size

			# Sort the scores (reversed: the higher the better)
			scores = sorted(iter(list(self.channelscores[channel].items())), key=lambda k_v9:(k_v9[1],k_v9[0]), reverse=True)
			del scores[listsize:] 

			msgstring = ""
			for item in scores:
				msgstring += self.hl_protect(item[0]) + " " + str(item[1]) + " | "
			if msgstring != "":
				irc.reply("8====D dickHunt top-" + str(listsize) + " scores for " + channel + " O====8")
				irc.reply(msgstring)
			else:
				irc.reply("There aren't any scores for this channel yet.")
		else:
			irc.reply("Are you sure this is a channel?")
	listscores = wrap(listscores, [optional('int'), 'channel'])


	def total(self, irc, msg, args, channel):
		"""
		Shows the total amount of dicks shot in <channel> (or in the current channel if no channel is given)
		"""

		if irc.isChannel(channel):
			self._read_scores(channel)
			if (self.channelscores.get(channel)):
				scores = self.channelscores[channel]
				total = 0
				for player in list(scores.keys()):
					total += scores[player]
				irc.reply(str(total) + " dicks have been fucked in " + channel + "!")
			else:
				irc.reply("There are no scores for this channel yet")

		else:
			irc.reply("Are you sure this is a channel?")
	total = wrap(total, ['channel'])


	def listtimes(self, irc, msg, args, size, channel):
		"""
		[<size>] [<channel>]
		
		Shows the <size>-sized time list for <channel> (or for the current channel if no channel is given)
		"""

		if irc.isChannel(channel):
			self._read_scores(channel)

			try:
				self.channeltimes[channel]
			except:
				self.channeltimes[channel] = {}

			try:
				self.channelworsttimes[channel]
			except:
				self.channelworsttimes[channel] = {}

			# How many results do we display?
			if (not size):
				listsize = self.toplist
			else:
				listsize = size

			# Sort the times (not reversed: the lower the better)
			times = sorted(iter(list(self.channeltimes[channel].items())), key=lambda k_v10:(k_v10[1],k_v10[0]), reverse=False)
			del times[listsize:] 

			msgstring = ""
			for item in times:
				msgstring += self.hl_protect(item[0]) + " "+ str(round(item[1],2)) + " | "
			if msgstring != "":
				irc.reply("8====D dickHunt Top " + str(listsize) + " times for " + channel + " O====8")
				irc.reply(msgstring)
			else:
				irc.reply("There aren't any best times for this channel yet.")


			times = sorted(iter(list(self.channelworsttimes[channel].items())), key=lambda k_v11:(k_v11[1],k_v11[0]), reverse=True)
			del times[listsize:] 

			msgstring = ""
			for item in times:
				#msgstring += "x" + item[0] + "x: "+ time.strftime('%H:%M:%S', time.gmtime(item[1])) + ", "
				roundseconds = round(item[1])
				delta = datetime.timedelta(seconds=roundseconds)
				msgstring += self.hl_protect(item[0]) + " " + str(delta) + " | "
			if msgstring != "":
				irc.reply("8====D dickHunt Top " + str(listsize) + " longest times for " + channel + " O====8")
				irc.reply(msgstring)
			else:
				irc.reply("There aren't any longest times for this channel yet.")



		else:
			irc.reply("Are you sure this is a channel?")
	listtimes = wrap(listtimes, [optional('int'), 'channel'])



	def dbg(self, irc, msg, args):
		""" 
		This is a debug command. If debug mode is not enabled, it won't do anything 
		"""
		currentChannel = msg.args[0]
		if (self.debug):
			if irc.isChannel(currentChannel):
				self._release(irc, currentChannel, msg, args)
	dbg = wrap(dbg)
		
	def lube(self, irc, msg, args, extra):
		"""
		Lubes you up so you are ready for dick!
		"""
		currentChannel = msg.args[0]

		if irc.isChannel(currentChannel):
			if(self.started.get(currentChannel) == True):
				if extra:
					if "liriel" in extra.lower():
						irc.sendMsg(ircmsgs.privmsg(currentChannel, "liriel shoves the lube down %s's throat and kicks them in the groin" % msg.nick))
						message = "Fuck off"
						irc.queueMsg(ircmsgs.kick(currentChannel, msg.nick, message))
					else:
						irc.reply("%s, you need to get %s into a private room for those shenanigans" % (msg.nick, extra))
				else: 
					if not self.lubed[currentChannel].get(msg.nick):
						self.lubed[currentChannel][msg.nick] = True
						self.needslube[currentChannel][msg.nick] = False
						irc.reply("%s, you are dripping wet and ready!" % (msg.nick))
					else:
						irc.sendMsg(ircmsgs.privmsg(currentChannel, "%s, you are too slippery and the lube tube slipped inside you!" % (msg.nick)))
						self.lubed[currentChannel][msg.nick] = False
						self.needslube[currentChannel][msg.nick] = False
						# If kickMode is enabled for this channel, and the bot have op capability, let's kick!
						if self.registryValue('kickMode', currentChannel) and irc.nick in irc.state.channels[currentChannel].ops:
							message = "Go to the doctor to get that tube removed"
							irc.queueMsg(ircmsgs.kick(currentChannel, msg.nick, message))
						else:
							irc.reply("%s, go to the doctor to get that tube removed" % (msg.nick))
			else:
				irc.reply("There is no hunt right now! You can start a hunt with the 'start' command")
		else:
			irc.error('You have to be on a channel')
	lube = wrap(lube, [optional('something')])

	def bendover(self, irc, msg, args):
		"""
		Fucks the dick!
		"""
		currentChannel = msg.args[0]

		if irc.isChannel(currentChannel):
			if(self.started.get(currentChannel) == True):

				# benddelay: how much time between the dick was released and is taken?
				if self.times[currentChannel]:
					benddelay = time.time() - self.times[currentChannel]
				else:
					benddelay = False


				# Is the player preparing?
				if not self.lubed[currentChannel].get(msg.nick):
					if (self.preparing[currentChannel].get(msg.nick) and time.time() - self.preparing[currentChannel][msg.nick] < self.preparetime[currentChannel]):
						irc.reply("%s, you are too dry... (\"natural lube\" takes %i seconds)" % (msg.nick, self.preparetime[currentChannel]))
						return 0
				

				# This player is now preparing
				self.preparing[currentChannel][msg.nick] = time.time()
				self.lubed[currentChannel][msg.nick] = False

				# There was a dick
				if (self.dick[currentChannel] == True):

					# Does the player need more lube?
					if msg.nick not in list(self.needslube[currentChannel].keys()):
						self.needslube[currentChannel][msg.nick] = False
					if (random.random() < self.missprobability[currentChannel]) or self.needslube[currentChannel][msg.nick]:
						irc.reply("%s, you need more lube!" % self.hl_protect(msg.nick))
						self.needslube[currentChannel][msg.nick] = True 
					else:

						# Adds one point for the nick that took the dick
						try:
							self.scores[currentChannel][msg.nick] += 1
						except:
							try:
								self.scores[currentChannel][msg.nick] = 1
							except:
								self.scores[currentChannel] = {} 
								self.scores[currentChannel][msg.nick] = 1

						#irc.reply("\x02%s~~~\x02 %s: %i (%.2f seconds)" % (self.dickColor[currentChannel], self.hl_protect(msg.nick),  self.scores[currentChannel][msg.nick], benddelay))
						irc.sendMsg(ircmsgs.privmsg(currentChannel, "\x02%s~~~\x02 %s: %i (%.2f seconds)" % (self.dickColor[currentChannel], self.hl_protect(msg.nick),  self.scores[currentChannel][msg.nick], benddelay)))

						self.averagetime[currentChannel] += benddelay

						# Now save the bend delay for the player (if it's quicker than it's previous benddelay)
						try:
							previoustime = self.toptimes[currentChannel][msg.nick]
							if(benddelay < previoustime):
								self.toptimes[currentChannel][msg.nick] = benddelay
						except:
							self.toptimes[currentChannel][msg.nick] = benddelay


						# Now save the bend delay for the player (if it's worst than it's previous benddelay)
						try:
							previoustime = self.worsttimes[currentChannel][msg.nick]
							if(benddelay > previoustime):
								self.worsttimes[currentChannel][msg.nick] = benddelay
						except:
							self.worsttimes[currentChannel][msg.nick] = benddelay


						self.dick[currentChannel] = False

						# Reset the basetime for the waiting time before the next dick
						self.lastSpoke[currentChannel] = time.time()

						if self.registryValue('dicks', currentChannel):
							maxBends = self.registryValue('dicks', currentChannel)
						else:
							maxBends = 10

						# End of Hunt
						if (self.bends[currentChannel]  == maxBends):
							self._end(irc, msg, args, currentChannel)

							# If autorestart is enabled, we restart a hunt automatically!
							if self.registryValue('autoRestart', currentChannel):
								# This code shouldn't be here
								self.started[currentChannel] = True
								self._initthrottle(irc, msg, args, currentChannel)
								if self.scores.get(currentChannel):
									self.scores[currentChannel] = {}
								if self.preparing.get(currentChannel):
									self.preparing[currentChannel] = {}
								if self.lubed.get(currentChannel):
									self.lubed[currentChannel] = {}
								if self.needslube.get(currentChannel):
										self.needslube[currentChannel] = {}
								self.averagetime[currentChannel] = 0


				# There was no dick or the dick has already been fucked
				else:

					# Removes one point for the nick that fucked
					try:
						self.scores[currentChannel][msg.nick] -= 1
					except:
						try:
							self.scores[currentChannel][msg.nick] = -1
						except:
							self.scores[currentChannel] = {} 
							self.scores[currentChannel][msg.nick] = -1

					# Base message
					message = 'There was no dick!'

					# Adding nick and score
					message += " %s: %i" % (msg.nick, self.scores[currentChannel][msg.nick])

					# If we were able to have a benddelay (ie: a dick was released before someone did bend)
					if (benddelay):
						# Adding time
						message += " (" + str(round(benddelay,2)) + " seconds)"

					# If kickMode is enabled for this channel, and the bot have op capability, let's kick!
					if self.registryValue('kickMode', currentChannel) and irc.nick in irc.state.channels[currentChannel].ops:
						irc.reply(message)
						irc.queueMsg(ircmsgs.kick(currentChannel, msg.nick, 'You just fucked yourself!'))
					else:
						# Else, just say it
						irc.reply(message)


			else:
				irc.reply("There is no hunt right now! You can start a hunt with the 'start' command")
		else:
			irc.error('You have to be on a channel')

	bendover = wrap(bendover)



	def _end(self, irc, msg, args, currentChannel):
		""" 
		End of the hunt (is called when the hunts stop "naturally" or when someone uses the !stop command)
		"""

		# currentChannel = msg.args[0]

		# End the hunt
		self.started[currentChannel] = False

		try:
			self.channelscores[currentChannel]
		except:
			self.channelscores[currentChannel] = {}


		if not self.registryValue('autoRestart', currentChannel):
			irc.sendMsg(ircmsgs.privmsg(currentChannel, "The hunt stops now!"))

		# Showing scores
		if (self.scores.get(currentChannel)):

			# Getting winner
			winnernick, winnerscore = max(iter(list(self.scores.get(currentChannel).items())), key=lambda k_v12:(k_v12[1],k_v12[0]))
			if self.registryValue('dicks', currentChannel):
				maxBends = self.registryValue('dicks', currentChannel)
			else:
				maxBends = 10

			# Is there a perfect?
			if (winnerscore == maxBends):
				irc.sendMsg(ircmsgs.privmsg(currentChannel, "\o/ %s: %i dicks out of %i: perfect!!! +%i \o/" % (self.hl_protect(winnernick), winnerscore, maxBends, self.perfectbonus)))
				self.scores[currentChannel][winnernick] += self.perfectbonus
			else:
				# Showing scores
                                out_dict = sorted(iter(list(self.scores.get(currentChannel).items())), key=lambda k_v4:(k_v4[1],k_v4[0]), reverse=True)
                                score_list = []
                                out_msg = "Scores:"
                                for (nick, score) in out_dict:
                                    out_msg = out_msg + " {} {},".format(self.hl_protect(nick), score)
                                    out_msg = out_msg[:-1]
                                    irc.sendMsg(ircmsgs.privmsg(currentChannel, out_msg))

			# Getting channel best time (to see if the best time of this hunt is better)
			channelbestnick = None
			channelbesttime = None
			if self.channeltimes.get(currentChannel):
				channelbestnick, channelbesttime = min(iter(list(self.channeltimes.get(currentChannel).items())), key=lambda k_v5:(k_v5[1],k_v5[0]))

			# Showing best time
			recordmsg = ''
			if (self.toptimes.get(currentChannel)):
				key,value = min(iter(list(self.toptimes.get(currentChannel).items())), key=lambda k_v6:(k_v6[1],k_v6[0]))
			if (channelbesttime and value < channelbesttime and self.toptimes.get(currentChannel)):
				recordmsg = '. This is the new record for this channel! (previous record was held by ' + self.hl_protect(channelbestnick) + ' with ' + str(round(channelbesttime,2)) +  ' seconds)'
			else:
				try:
					if(value < self.channeltimes[currentChannel][key]):
						recordmsg = ' (this is your new record in this channel! Your previous record was ' + str(round(self.channeltimes[currentChannel][key],2)) + ')'
				except:
					recordmsg = ''

			irc.sendMsg(ircmsgs.privmsg(currentChannel, "Best time: %s with %.2f seconds%s" % (self.hl_protect(key), value, recordmsg)))

			# Getting channel worst time (to see if the worst time of this hunt is worst)
			channelworstnick = None
			channelworsttime = None
			if self.channelworsttimes.get(currentChannel):
				channelworstnick, channelworsttime = max(iter(list(self.channelworsttimes.get(currentChannel).items())), key=lambda k_v7:(k_v7[1],k_v7[0]))


			# Showing worst time
			recordmsg = ''
			if (self.worsttimes.get(currentChannel)):
				key,value = max(iter(list(self.worsttimes.get(currentChannel).items())), key=lambda k_v8:(k_v8[1],k_v8[0]))
			if (channelworsttime and value > channelworsttime):
				recordmsg = '. This is the new longest time for this channel! (previous longest time was held by ' + self.hl_protect(channelworstnick) + ' with ' + str(round(channelworsttime,2)) +  ' seconds)'
			else:
				try:
					if(value > self.channelworsttimes[currentChannel][key]):
						recordmsg = ' (this is your new longest time in this channel! Your previous longest time was ' + str(round(self.channelworsttimes[currentChannel][key],2)) + ')'
				except:
					recordmsg = ''

			# Only display worst time if something new
			if (recordmsg != ''):
				irc.sendMsg(ircmsgs.privmsg(currentChannel, "Longest time: %s with %.2f seconds%s" % (self.hl_protect(key), value, recordmsg)))

			# Showing average shooting time:
			#if (self.bends[currentChannel] > 1):
			#irc.reply("Average shooting time: %.2f seconds" % ((self.averagetime[currentChannel] / self.bends[currentChannel])))

			# Write the scores and times to disk
			self._calc_scores(currentChannel)
			self._write_scores(currentChannel)

			# Did someone take the lead?
			weekscores = {}
			if self.channelweek.get(currentChannel):
				if self.channelweek[currentChannel].get(self.woy):
					msgstring = ''
					# for each day of week
					for i in range(1,7):
						if self.channelweek[currentChannel][self.woy].get(i):
							# Getting all scores, to get the winner of the week
							for player in list(self.channelweek[currentChannel][self.woy][i].keys()):
								try:
									weekscores[player] += self.channelweek[currentChannel][self.woy][i][player]
								except:
									weekscores[player] = self.channelweek[currentChannel][self.woy][i][player]
					winnernick, winnerscore = max(iter(list(weekscores.items())), key=lambda k_v3:(k_v3[1],k_v3[0]))
					if (winnernick != self.leader[currentChannel]):
						if self.leader[currentChannel] != None:
							irc.sendMsg(ircmsgs.privmsg(currentChannel, "%s took the lead for the week over %s with %i points." % (self.hl_protect(winnernick), self.leader[currentChannel], winnerscore)))
						else:
							irc.sendMsg(ircmsgs.privmsg(currentChannel, "%s has the lead for the week with %i points." % (self.hl_protect(winnernick), winnerscore)))
						self.leader[currentChannel] = winnernick



		else:
			irc.sendMsg(ircmsgs.privmsg(currentChannel, "Not a single dick was fucked during this hunt!"))

		# Reinit current hunt scores
		if self.scores.get(currentChannel):
			self.scores[currentChannel] = {}

		# Reinit current hunt times
		if self.toptimes.get(currentChannel):
			self.toptimes[currentChannel] = {}
		if self.worsttimes.get(currentChannel):
			self.worsttimes[currentChannel] = {}

		# No dick available
		self.dick[currentChannel] = False

		# Reinit number of bends
		self.bends[currentChannel] = 0



	def _release(self, irc, currentChannel, msg, args):
		"""
		release a dick
		"""

		# currentChannel = msg.args[0]
		if irc.isChannel(currentChannel):
			if(self.started[currentChannel] == True):
				if (self.dick[currentChannel] == False):

					# Store the time when the dick has been released
					self.times[currentChannel] = time.time()

					# Store the fact that there's a dick now
					self.dick[currentChannel] = True
					self.dickColor[currentChannel] = self.irc_color("8====D")
					# Send message directly (instead of queuing it with irc.reply)
					irc.sendMsg(ircmsgs.privmsg(currentChannel, '\x02%s\x02' % self.dickColor[currentChannel]))		        

					# Define a new throttle[currentChannel] for the next release
					self.throttle[currentChannel] = random.randint(self.minthrottle[currentChannel], self.maxthrottle[currentChannel])

					try:
						self.bends[currentChannel] += 1
					except:
						self.bends[currentChannel] = 1
				else:
					iirc.sendMsg(ircmsgs.privmsg(currentChannel, "Already a dick"))
			else:
				irc.sendMsg(ircmsgs.privmsg(currentChannel, "The hunt has not started yet!"))
		else:
			irc.error('You have to be on a channel you fool')


Class = dickHunt

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
