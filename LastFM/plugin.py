###
# Copyright (c) 2006, Ilya Kuznetsov
# Copyright (c) 2008,2012 Kevin Funk
# Copyright (c) 2014-2017 James Lu <james2overdrivenetworks.com>
# Copyright (c) 2016-2017 Ormanya
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

from __future__ import unicode_literals
import supybot.utils as utils
from supybot.commands import *
import supybot.conf as conf
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.world as world
import supybot.log as log
import supybot.ircdb as ircdb

import json
from datetime import datetime
from time import strftime
import time
import pickle
import urllib

class LastFMDB():
    """
    Holds the database LastFM IDs of all known LastFM IDs.

    This stores users by their bot account first, falling back to their
    ident@host if they are not logged in.
    """

    def __init__(self, *args, **kwargs):
        """
        Loads the existing database, creating a new one in memory if none
        exists.
        """
        self.db = {}
        try:
            with open(filename, 'rb') as f:
               self.db = pickle.load(f)
        except Exception as e:
            log.debug('LastFM: Unable to load database, creating '
                      'a new one: %s', e)

    def flush(self):
        """Exports the database to a file."""
        try:
            with open(filename, 'wb') as f:
                pickle.dump(self.db, f, 2)
        except Exception as e:
            log.warning('LastFM: Unable to write database: %s', e)

    def set(self, prefix, newId):
        """Sets a user ID given the user's prefix."""

        try:  # Try to first look up the caller as a supybot account.
            userobj = ircdb.users.getUser(prefix)
        except KeyError:  # If that fails, store them by nick (used to be nick@host)
            user = prefix.split('!', 1)[0]
        else:
            user = userobj.name

        self.db[user] = newId

    def get(self, prefix):
        """Sets a user ID given the user's prefix."""

        try:  # Try to first look up the caller as a supybot account.
            userobj = ircdb.users.getUser(prefix)
        except KeyError:  # If that fails, check by nick and hostmask (latter is for legacy support)
            try:
                user = prefix.split('!', 1)[0]  # nick
                user2 = prefix.split('!', 1)[1] # hostmask
            except:
                return None
        else:
            user = userobj.name
            user2 = prefix.split('!', 1)[1] # Added this for error in next if statement ...

        if self.db.get(user) == None:
            return self.db.get(user2)
        else:
            return self.db.get(user)


class LastFM(callbacks.Plugin):
    threaded = True

    def __init__(self, irc):
        self.__parent = super(LastFM, self)
        self.__parent.__init__(irc)
        self.db = LastFMDB(filename)
        world.flushers.append(self.db.flush)

        # 2.0 API (see http://www.lastfm.de/api/intro)
        self.APIURL = "http://ws.audioscrobbler.com/2.0/?"

    def die(self):
        world.flushers.remove(self.db.flush)
        self.db.flush()
        self.__parent.die()

    @wrap([optional("something")]) 
    def np(self, irc, msg, args, user):
        """[<user>]

        Announces the track currently being played by <user>. If <user>
        is not given, defaults to the LastFM user configured for your
        current nick.
        """
        apiKey = self.registryValue("apiKey")
        if not apiKey:
            irc.error("The API Key is not set. Please set it via "
                      "'config plugins.lastfm.apikey' and reload the plugin. "
                      "You can sign up for an API Key using "
                      "http://www.last.fm/api/account/create", Raise=True)

        if user != None:
            nick = user
            try:
                # To find last.fm id in plugin database
                hostmask = irc.state.nickToHostmask(user)
                user2 = self.db.get(hostmask)
                if user2 != None:
                    user = user2
            except:
                # To directly look up user on last.fm
                user = user
        else:
            nick = msg.nick
            if not self.db.get(msg.prefix):
                irc.reply("Please register with the bot using the command \".lastfm set <LastFM username>\"")
            user = (user or self.db.get(msg.prefix) or msg.nick)

        # see http://www.lastfm.de/api/show/user.getrecenttracks
        url = "%sapi_key=%s&method=user.getrecenttracks&user=%s&format=json" % (self.APIURL, apiKey, user)
        try:
            f = utils.web.getUrl(url).decode("utf-8")
        except utils.web.Error:
            irc.error("Unknown LastFM user %s." % user, Raise=True)
        self.log.debug("LastFM.nowPlaying: url %s", url)

        try:
            data = json.loads(f)["recenttracks"]
        except KeyError:
            irc.error("Unknown user %s." % user, Raise=True)

        user = data["@attr"]["user"]
        tracks = data["track"]

        # Work with only the first track.
        try:
            trackdata = tracks[0]
        except IndexError:
            irc.error("%s doesn't seem to have listened to anything." % user, Raise=True)

        artist = trackdata["artist"]["#text"].strip()  # Artist name
        track = trackdata["name"].strip()  # Track name
        # Album name (may or may not be present)
        album = trackdata["album"]["#text"].strip()
        if album:
            album = " [%s]" % album
        else:
            album = ""
        year = strftime("%Y")

        try:
#            time = int(trackdata["date"]["uts"])  # Time of last listen
            # Format this using the preferred time format.
#            tformat = conf.supybot.reply.format.time()
#            time = datetime.fromtimestamp(time).strftime(tformat)

            # Calculate time since last played
            last_play = datetime.now() - datetime.fromtimestamp(int(trackdata["date"]["uts"]))
            # seconds
            if (last_play.days == 0) and (last_play.seconds < 60):
                time_passed = "%s seconds ago" % last_play.seconds
            # minutes
            elif last_play.days == 0 and last_play.seconds < 3600:
                time_passed = "%s minutes ago" % int(last_play.seconds / 60 )
            # hours
            elif last_play.days == 0:
                time_passed = "%s hours ago" % int(last_play.seconds / 3600 )
            else:
                time_passed = "%s days ago" % last_play.days

            #tformat = conf.supybot.reply.format.time()
            #time = "at %s" % datetime.fromtimestamp(time).strftime(tformat)
        except KeyError:  # Nothing given by the API?
            time_passed = "right now"

        public_url = ''
        # If the DDG plugin from this repository is loaded, we can integrate
        # that by finding a YouTube link for the track.
        if self.registryValue("fetchYouTubeLink"):
            ddg = irc.getCallback("DDG")
            if ddg:
                try:
                    results = ddg.search_core('site:youtube.com "%s - %s"' % (artist, track),
                                              channel_context=msg.args[0], max_results=1, show_snippet=False)


                    if results:
                        public_url = format('%u', results[0][2])
                    else:
                        time.sleep(2)
                        results = ddg.search_core('site:soundcloud.com "%s - %s"' % (artist, track),
                                              channel_context=msg.args[0], max_results=1, show_snippet=False)
                        if results:
                            public_url = format('%u', results[0][2])
                        else:
                            log.info("No Soundcloud link found for %s - %s", artist, track) 
                    
                except:
                    # If something breaks, log the error but don't cause the
                    # entire np request to fail.
                    error_txt = ('LastFM: failed to get public link for track %s - %s' % (artist, track))
                    log.exception(error_txt)        


        nick_bold = ircutils.bold(nick[0]) + u'\uFEFF' + ircutils.bold(nick[1:])
        try:
           trackdata["@attr"]["nowplaying"]
           irc.reply('%s is listening to %s by %s%s %s' %
                      (nick_bold, ircutils.bold(track), ircutils.bold(artist), album, public_url.strip('<>')))
        except:
            irc.reply('%s listened to %s by %s%s %s %s' %
                      (nick_bold, ircutils.bold(track), ircutils.bold(artist), album, time_passed, public_url.strip('<>')))
#        s = '%s listened to %s by %s %s %s. %s' % (ircutils.bold(user), ircutils.bold(track),
#            ircutils.bold(artist), album, time, public_url)
#        irc.reply(utils.str.normalizeWhitespace(s))

    @wrap([optional("something")]) 
    def whatsplaying(self, irc, msg, args, extra):
        """
        Announces the track currrently being played by all users in the channel.
        """

        channel_state = irc.state.channels[msg.args[0]]
        nicks = list(channel_state.users)
        
        apiKey = self.registryValue("apiKey")
        if not apiKey:
            irc.error("The API Key is not set. Please set it via "
                      "'config plugins.lastfm.apikey' and reload the plugin. "
                      "You can sign up for an API Key using "
                      "http://www.last.fm/api/account/create", Raise=True)

        registered = 0
        listening = 0
        for nick in nicks:                      
            hostmask = irc.state.nickToHostmask(nick)
            user = self.db.get(hostmask)              

            if user != None:
                registered = registered + 1
                # see http://www.lastfm.de/api/show/user.getrecenttracks
                url = "%sapi_key=%s&method=user.getrecenttracks&user=%s&format=json" % (self.APIURL, apiKey, user)
                try:
                    f = utils.web.getUrl(url).decode("utf-8")
                except utils.web.Error:
                    irc.error("Unknown user %s." % user, Raise=True)
                self.log.debug("LastFM.nowPlaying: url %s", url)


                try:
                    data = json.loads(f)["recenttracks"]
                except:
                    pass

                user = data["@attr"]["user"]
                tracks = data["track"]

                # Work with only the first track.
                try:
                    trackdata = tracks[0]
                except:
                    pass

                artist = trackdata["artist"]["#text"].strip()  # Artist name
                track = trackdata["name"].strip()  # Track name
                # Album name (may or may not be present)
                album = trackdata["album"]["#text"].strip()
                if album:
                    album = " [%s]" % album
                else:
                    album = ""
                year = strftime("%Y")

                nick_bold = ircutils.bold(nick[0]) + u'\uFEFF' + ircutils.bold(nick[1:]) 
                try:
                   trackdata["@attr"]["nowplaying"]
                   irc.reply('%s is listening to %s by %s%s' % (nick_bold, ircutils.bold(track), ircutils.bold(artist), album))
                   listening = listening + 1
                except:
                    last_play = datetime.now() - datetime.fromtimestamp(int(trackdata["date"]["uts"]))
                    # if last played less than 10 minutes ago
                    if int(last_play.seconds) < 600:
                        irc.reply('%s is listening to %s by %s%s' % (nick_bold, ircutils.bold(track), ircutils.bold(artist), album))
                        listening = listening + 1
                    pass

        irc.reply("%d out of %d registered users are listening to music" % (listening, registered))

    @wrap([optional("something")])
    def set(self, irc, msg, args, newId):
        """<user>

        Sets the LastFM username for the caller and saves it in a database.
        """

        self.db.set(msg.prefix, newId)
        irc.replySuccess()

    @wrap(["text"])
    def sa(self, irc, msg, args, text):
        """<artist>

        Lists other similar artists.
        """

        artist = text
        apiKey = self.registryValue("apiKey")
        if not apiKey:
            irc.error("The API Key is not set. Please set it via "
                      "'config plugins.lastfm.apikey' and reload the plugin. "
                      "You can sign up for an API Key using "
                      "http://www.last.fm/api/account/create", Raise=True)

        # see http://www.last.fm/api/show/artist.getSimilar
        url = "%sapi_key=%s&method=artist.getsimilar&artist=%s&format=json" % (self.APIURL, apiKey, artist)
        try:
            f = utils.web.getUrl(url).decode("utf-8")
        except utils.web.Error:
            irc.error("Unknown artist %s." % artist, Raise=True)
        self.log.debug("LastFM.similarArtists: url %s", url)

        try:
            data = json.loads(f)["similarartists"]
        except KeyError:
            irc.error("Unknown artist %s." % artist, Raise=True)

        count = 0
        outstr = ""
        for artists in data["artist"]:
            if count == 0:
                artist_name = [artists["name"]]
                artist_pct = [float(artists["match"])]
                outstr = ("\x1DSimilar to {:s}\x1D: \x02{:s}\x02 {:02.0f}%".format(artist, artist_name[count], artist_pct[count]*100))
            elif count > 9:
                break
            else:
                artist_name += [artists["name"]]
                artist_pct += [float(artists["match"])]                
                outstr += (", \x02{:s}\x02 {:02.0f}%".format(artist_name[count], artist_pct[count]*100))
            count += 1

        irc.reply(outstr)


    @wrap([optional("something")])
    def profile(self, irc, msg, args, user):
        """[<user>]

        Prints the profile info for the specified LastFM user. If <user>
        is not given, defaults to the LastFM user configured for your
        current nick.
        """
        apiKey = self.registryValue("apiKey")
        if not apiKey:
            irc.error("The API Key is not set. Please set it via "
                      "'config plugins.lastfm.apikey' and reload the plugin. "
                      "You can sign up for an API Key using "
                      "http://www.last.fm/api/account/create", Raise=True)

        if user != None:
            nick = user
            try:
                # To find last.fm id in plugin database
                hostmask = irc.state.nickToHostmask(user)
                user2 = self.db.get(hostmask)
                if user2 != None:
                    user = user2
            except:
                # To directly look up user on last.fm
                user = user
        else:
            nick = msg.nick
            user = (user or self.db.get(msg.prefix) or msg.nick)

        # Get profile information
        url = "%sapi_key=%s&method=user.getInfo&user=%s&format=json" % (self.APIURL, apiKey, user)
        self.log.debug("LastFM.profile: url %s", url)
        try:
            f = utils.web.getUrl(url).decode("utf-8")
        except utils.web.Error:
            irc.error("Unknown LastFM user '%s'." % user, Raise=True)

        data = json.loads(f)
        keys = ("realname", "age", "gender", "country", "playcount","url")
        #profile = {"id": ircutils.bold(user)}
        profile = {"id": ircutils.bold(nick)}
        for tag in keys:
            try:
                s = data["user"][tag].strip() or "N/A"
            except KeyError: # empty field
                s = "N/A"
            finally:
                profile[tag] = ircutils.bold(s)

        # Get library information
        url = "%sapi_key=%s&method=Library.getArtists&limit=1&user=%s&format=json" % (self.APIURL, apiKey, user)
        self.log.debug("LastFM.library: url %s", url)
        try:
            f = utils.web.getUrl(url).decode("utf-8")
        except utils.web.Error:
            irc.error("Unknown LastFM user '%s'." % user, Raise=True) 
        libraryList = json.loads(f)
        profile["artistcount"] = ircutils.bold(libraryList["artists"]["@attr"]["total"])

        try:
            # LastFM sends the user registration time as a unix timestamp;
            # Format it using the preferred time format.
            timestamp = int(data["user"]["registered"]["unixtime"])
            tformat = conf.supybot.reply.format.time()
            s = datetime.fromtimestamp(timestamp).strftime(tformat)
        except:
            #s = "N/A"
            irc.error("Unknown LastFM user '%s'." % user, Raise=True)
        finally:
            profile["registered"] = ircutils.bold(s)

        #irc.reply("%(id)s (realname: %(realname)s) registered on %(registered)s; age: %(age)s / %(gender)s; "
        #          "Country: %(country)s; Tracks played: %(playcount)s" % profile)
        irc.reply("%(id)s registered on %(registered)s; "
                  "Country: %(country)s; Artists played: %(artistcount)s Tracks played: %(playcount)s URL: %(url)s" % profile)

    @wrap(["something", optional("something")])
    def compare(self, irc, msg, args, user1, user2):
        """<user> [<user2>]

        Reports the percent similarity between two users, based on their top 100 artists over the last 12 months.
        """
        #irc.error("This command is not ready yet. Stay tuned!", Raise=True)

        apiKey = self.registryValue("apiKey")
        if not apiKey:
            irc.error("The API Key is not set. Please set it via "
                      "'config plugins.lastfm.apikey' and reload the plugin. "
                      "You can sign up for an API Key using "
                      "http://www.last.fm/api/account/create", Raise=True)

        if user1 != None:
            nick1 = user1
            try:
                # To find last.fm id in plugin database
                hostmask = irc.state.nickToHostmask(user1)
                userx = self.db.get(hostmask)
                if userx != None:
                    user1 = userx
                else:
                    irc.reply("%s is not registered with the bot" % user1)
                    irc.error("Bot only supports compare for registered users", Raise=True)

            except:
                irc.reply("%s is not registered with the bot" % user2)
                irc.error("Bot only supports compare for registered users", Raise=True)
        else:
            irc.error("You need to provide at least one user for comparison", Raise=True)

        if user2 != None:
            nick2 = user2
            try:
                # To find last.fm id in plugin database
                hostmask = irc.state.nickToHostmask(user2)
                userx = self.db.get(hostmask)
                if userx != "None":
                    user2 = userx
            except:
                irc.reply("%s is not registered with the bot" % user2)
                irc.error("Bot only supports compare for registered users", Raise=True)
        else:
            user2 = user1
            nick2 = nick1
            nick1 = msg.nick
            user1 = self.db.get(msg.prefix)

        # Get library information for user
        #artists = [[],[]]
        artists = []
        artistsplays = []
        artistcount = [0,0]
        limit = 1000 # specify artists to return per page (api supports max of 1000)
        maxArtists = 100 # used to specify max total number of artists returned
        commonArtists = 0

        limit = min(limit, maxArtists)
        # Get list of artists for each library
        for idx, user in enumerate([user1,user2]):
            artists.append([])
            artistsplays.append([])
            page = 0
            pages = 1
            while (page < pages) and (artistcount[idx] < maxArtists):
                page += 1
                url = "%sapi_key=%s&method=library.getArtists&user=%s&limit=%d&page=%d&period=12month&format=json" % (self.APIURL, apiKey, user, limit, page)
                self.log.debug("LastFM.library: url %s", url)
                try:
                    f = utils.web.getUrl(url).decode("utf-8")
                except utils.web.Error:
                    irc.error("Unknown LastFM user '%s'." % user, Raise=True) 
                libraryList = json.loads(f)
                # Get size of data set
                if page == 1:
                    pages = int(libraryList["artists"]["@attr"]["totalPages"])
                    totartists = int(libraryList["artists"]["@attr"]["total"])
                artistcount[idx] += limit
                artistcount[idx] = min(artistcount[idx], totartists)

                for artist in libraryList["artists"]["artist"]:
                    # artists[idx].append({"name": artist["name"], "plays" : artist["playcount"]})
                    artists[idx].append(artist["name"])
                    artistsplays[idx].append(artist["playcount"])

        for artist in artists[0]:
            if artist in artists[1]:
                commonArtists += 1 

        totalArtists = artistcount[0] + artistcount[1] - commonArtists


        #irc.reply("%s and %s have %d artists in common, out of %s artists" % (nick1,nick2,commonArtists,totalArtists))
        irc.reply("%s and %s are %3.1f%% similar" % (nick1,nick2,100*float(commonArtists)/float(totalArtists)))
                
    @wrap([optional("something")])
    def topartists(self, irc, msg, args, user):
        """<user> [<user2>]

        Reports the top 10 artists for the user, over the last 12 months.
        """
        #irc.error("This command is not ready yet. Stay tuned!", Raise=True)

        apiKey = self.registryValue("apiKey")
        if not apiKey:
            irc.error("The API Key is not set. Please set it via "
                      "'config plugins.lastfm.apikey' and reload the plugin. "
                      "You can sign up for an API Key using "
                      "http://www.last.fm/api/account/create", Raise=True)

        if user != None:
            nick = user
            try:
                # To find last.fm id in plugin database
                hostmask = irc.state.nickToHostmask(user)
                userx = self.db.get(hostmask)
                if userx != None:
                    user = userx
                else:
                    irc.reply("%s is not registered with the bot" % user)
                    irc.error("Bot only supports top artists for registered users", Raise=True)

            except:
                irc.reply("%s is not registered with the bot" % user)
                irc.error("Bot only supports top artist for registered users", Raise=True)
        else:
            user = self.db.get(msg.prefix)
            nick = msg.nick


        # Get library information for user
        #artists = [[],[]]
        artists = []
        artistsplays = []
        artistcount = 0
        limit = 10 # specify artists to return per page (api supports max of 1000)
        outstr = "%s's top artists for the last 12 months are:" % nick

        # Get list of artists for each library

        url = "%sapi_key=%s&method=library.getArtists&user=%s&limit=%d&period=12month&format=json" % (self.APIURL, apiKey, user, limit)
        self.log.debug("LastFM.library: url %s", url)
        try:
            f = utils.web.getUrl(url).decode("utf-8")
        except utils.web.Error:
            irc.error("Unknown LastFM user '%s'." % user, Raise=True) 
        libraryList = json.loads(f)

        
        for artist in libraryList["artists"]["artist"]:
            #artists.append(artist["name"])
            #artistsplays.append(artist["playcount"])
            outstr = outstr + (" %s [%s]," % (ircutils.bold(artist["name"]), artist["playcount"]))
        outstr = outstr[:-1]

         
        #irc.reply("%s and %s have %d artists in common, out of %s artists" % (nick1,nick2,commonArtists,totalArtists))
        irc.reply(outstr)
                

        


filename = conf.supybot.directories.data.dirize("LastFM.db")

Class = LastFM


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
