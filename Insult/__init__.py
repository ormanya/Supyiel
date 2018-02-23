###
# There are not limitations on the use of this code. Do whatever you want!
#
# Written by Ormanya
###

import supybot
import supybot.world as world

# Use this for the version of this plugin.  You may wish to put a CVS keyword
# in here if you're keeping the plugin in CVS or some similar system.
__version__ = "%%VERSION%%"

__author__ = supybot.Author("liriel")

# This is a dictionary mapping supybot.Author instances to lists of
# contributions.
__contributors__ = {
    supybot.Author('Ormanya', 'Ormanya', 'ormanyab@gmail.com')
}

# This is a url where the most recent plugin package can be downloaded.
__url__ = '' # 'http://supybot.com/Members/yourname/Insult/download'

import config
import plugin
reload(plugin) # In case we're being reloaded.
# Add more reloads here if you add third-party modules and want them to be
# reloaded when this plugin is reloaded.  Don't forget to import them as well!

if world.testing:
    import test

Class = plugin.Class
configure = config.configure


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
