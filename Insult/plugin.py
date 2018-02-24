###
# There are not limitations on the use of this code. Do whatever you want!
#
# Written by Ormanya
###

import supybot.utils as utils
from supybot.commands import *
import supybot.conf as conf
import supybot.log as log
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks

import json
import random
import os.path
from shutil import copyfile

class Insult(callbacks.Plugin):

    def __init__(self, irc):
        self.__parent = super(Insult, self)
        self.__parent.__init__(irc)

        # load the  database
        self.insult_list = {}
        #try:
        print os.path.exists(filename)
        print os.getcwd()

        if not os.path.exists(filename):
            dir_path = os.path.dirname(os.path.realpath(__file__))
            default_filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), "default_insults.json")
            copyfile(default_filename, filename)
            print "Copied"
        with open(filename) as json_data:
                self.insult_list = json.load(json_data)
            
       #except Exception as e:
       #    log.debug('Insults: Unable to load database: %s', e)
       #    print "bleh"

    @wrap([optional("something")]) 
    def insult(self, irc, msg, args, victim):
        """[<target>]

        Return an insult, with an optional target
        """
    
        response = random.choice(self.insult_list)
        if victim is not None:
            irc.reply("%s: %s" % (victim, response))
        else:    
            irc.reply("%s" % response)

#    insult = wrap(insult, [optional('text')])

filename = conf.supybot.directories.data.dirize("insults.json")

Class = Insult


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
