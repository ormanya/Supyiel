###
# Copyright (c) 2012-2014, spline
# All rights reserved.
###

"""
Add a description of the plugin (to be presented to the user inside the wizard)
here.  This should describe *what* the plugin does.
"""

import supybot
import supybot.world as world

# Use this for the version of this plugin.  You may wish to put a CVS keyword
# in here if you're keeping the plugin in CVS or some similar system.
__version__ = "2017.01.16+git"

# XXX Replace this with an appropriate author or supybot.Author instance.
__author__ = supybot.Author('James Lu', 'GLolol', 'GLolol@overdrivenetworks.com')

# This is a dictionary mapping supybot.Author instances to lists of
# contributions.
__contributors__ = {}

# This is a url where the most recent plugin package can be downloaded.
__url__ = 'https://github.com/GLolol/SupyPlugins/'

from . import config
from . import plugin
from imp import reload
# In case we're being reloaded.
reload(config)
reload(plugin)

# Add more reloads here if you add third-party modules and want them to be
# reloaded when this plugin is reloaded.  Don't forget to import them as well!

if world.testing:
    from . import test

Class = plugin.Class
configure = config.configure


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
