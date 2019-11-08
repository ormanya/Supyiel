# -*- coding: utf-8 -*-
###
# Copyright (c) 2012-2014, spline
# All rights reserved.
#
#
###
# py3 compat
from __future__ import print_function, unicode_literals
from __future__ import absolute_import, division

# my libs
from lxml import etree
from bs4 import BeautifulSoup
import sys
if sys.version_info[0] > 2:
    import urllib.request, urllib.error, urllib.parse
else:  # python2.
    import urllib2
from random import choice
import json
import re
import xml.dom.minidom
import feedparser
import base64
#import socket
import random
try:
    import xml.etree.cElementTree as ElementTree
except ImportError:
    import xml.etree.ElementTree as ElementTree
# supybot libs
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks

import requests


class Assorted(callbacks.Plugin):
    """Add the help for "@plugin help Assorted" here
    This should describe *how* to use this plugin."""
    threaded = True

    ##############
    # FORMATTING #
    ##############

    def _rainbow(self, text):
        text = ''.join([ircutils.mircColor(x, choice(list(ircutils.mircColors.keys()))) for x in text])
        return text

    def _red(self, string):
        return ircutils.mircColor(string, 'red')

    def _yellow(self, string):
        """Returns a yellow string."""
        return ircutils.mircColor(string, 'yellow')

    def _green(self, string):
        """Returns a green string."""
        return ircutils.mircColor(string, 'green')

    def _blue(self, string):
        """Returns a blue string."""
        return ircutils.mircColor(string, 'blue')

    def _lightblue(self, string):
        """Returns a light blue string."""
        return ircutils.mircColor(string, 'light blue')

    def _orange(self, string):
        """Returns an orange string."""
        return ircutils.mircColor(string, 'orange')

    def _bold(self, string):
        """Returns a bold string."""
        return ircutils.bold(string)

    def _ul(self, string):
        """Returns an underline string."""
        return ircutils.underline(string)

    def _bu(self, string):
        """Returns a bold/underline string."""
        return ircutils.bold(ircutils.underline(string))

    ######################
    # INTERNAL FUNCTIONS #
    ######################

    def _size_fmt(self, num):
        for x in ['','k','M','B','T']:
            if num < 1000.0:
              return "%3.1f%s" % (num, x)
            num /= 1000.0

    def _myfloat(self, float_string):
        """It takes a float string ("1,23" or "1,234.567.890") and
        converts it to floating point number (1.23 or 1.234567890).
        """

        float_string = str(float_string)
        errormsg = "ValueError: Input must be decimal or integer string"
        try:
            if float_string.count(".") == 1 and float_string.count(",") == 0:
                return float(float_string)
            else:
                midle_string = list(float_string)
                while midle_string.count(".") != 0:
                    midle_string.remove(".")
                out_string = str.replace("".join(midle_string), ",", ".")
            return float(out_string)
        except ValueError as error:
            print("%s\n%s" %(errormsg, error))
            return None

    def _splitinput(self, txt, seps):
        default_sep = seps[0]
        for sep in seps[1:]:
            txt = txt.replace(sep, default_sep)
        return [i.strip() for i in txt.split(default_sep)]

    def _httpget(self, url, h=None, d=None, l=True):
        """General HTTP resource fetcher. Pass headers via h, data via d, and to log via l."""

        if self.registryValue('logURLs') and l:
            self.log.info(url)

        try:
            if h and d:
                page = utils.web.getUrl(url, headers=h, data=d)
            else:
                page = utils.web.getUrl(url)
            return page
        except Exception as e:
            self.log.error("ERROR opening {0} message: {1}".format(url, e))
            return None

    ####################
    # PUBLIC FUNCTIONS #
    ####################

    def gasprices(self, irc, msg, args, optzip):
        """<zipcode>

        Display lowest reported gas price in zipcode.
        """

        url = 'http://gasprices.mapquest.com/station/us/nh/nashua/%s' % optzip
        html = self._httpget(url)
        if not html:  # http fetch breaks.
            irc.reply("ERROR: Trying to open: {0}".format(url))
            return
        # process html
        try:
            html = html.decode('utf-8')
            soup = BeautifulSoup(html)
            div = soup.find('div', attrs={'id': 'results-wrapper'})
            price = div.find('div', attrs={'class': 'price'})
            price = price.getText().encode('utf-8').replace('\n', '')
            # output
            irc.reply("{0} :: Lowest reported gas price for unleaded(87) is: {1}".format(optzip, price))
        except Exception as e:
            self.log.info("gasprices :: ERROR looking up {0} :: {1}".format(optzip, e))
            irc.reply("ERROR: Trying to fetch gas prices for: {0}".format(optzip))

    gasprices = wrap(gasprices, (['somethingWithoutSpaces']))

    def catfact(self, irc, msg, args):
        """
        Display random factfact.
        """
        
        url = 'https://catfact.ninja/fact'
        html = self._httpget(url)
        if not html:  # http fetch breaks.
            irc.reply("ERROR: Trying to open: {0}".format(url))
            return
        # process html
        html = html.decode('utf-8')
        jsondata = json.loads(html)
        fact = jsondata.get('fact')
        if fact:
            irc.reply(fact)
    
    catfact = wrap(catfact)

    def catpix(self, irc, msg, args):
        """
        Display random catpic from /r/cats
        """

        urls = ['http://imgur.com/r/cats','http://imgur.com/r/funnycats','http://imgur.com/r/supermodelcats', \
                'http://imgur.com/r/CatGifs']
        url = random.choice(urls)
        html = self._httpget(url)
        if not html:  # http fetch breaks.
            irc.reply("ERROR: Trying to open: {0}".format(url))
            return
        # process html
        soup = BeautifulSoup(html) #, convertEntities=BeautifulSoup.HTML_ENTITIES, fromEncoding='utf-8')
        px = soup.findAll('div', attrs={'class':'post'})
        zz = []
        for p in px:
            l = 'http://imgur.com' + p.find('a')['href']
            print(l)
            if sys.version_info[0] == 3:
                t = p.find('p').getText()
            else:
                t = p.find('p').getText().encode('utf-8')
            zz.append({'l':l, 't':t})
        o = random.choice(zz)
        #output
        img_tag = o['l'].split('/')[-1]
        title = o['t']
        base_url = 'https://i.imgur.com/{}'.format(img_tag)
        if requests.get(base_url+'.mp4').status_code == 200:
            url = base_url+'.mp4'
            irc.reply('{0} :: {1}'.format(title, url))          
        elif requests.get(base_url+'.jpg').status_code == 200:
            url = base_url+'.jpg'
            irc.reply('{0} :: {1}'.format(title, url)) 
        else:
            irc.reply('The kitties are playing hide and seek! Try to find them again!')  


    catpix = wrap(catpix)

    def kpix(self, irc, msg, args, text):
        """
        Display random pic from /r/kpics
        """

        url = 'http://imgur.com/r/kpics'
        html = self._httpget(url)
        if not html:  # http fetch breaks.
            irc.reply("ERROR: Trying to open: {0}".format(url))
            return
        # process html
        soup = BeautifulSoup(html) #, convertEntities=BeautifulSoup.HTML_ENTITIES, fromEncoding='utf-8')
        px = soup.findAll('div', attrs={'class':'post'})
        zz = []
        plen = 0
        for p in px:
            plen += 1
            l = 'http://imgur.com' + p.find('a')['href']
            if sys.version_info[0] == 3:
                t = p.find('p').getText()
            else:
                t = p.find('p').getText().encode('utf-8')
            if text is None:
                zz.append({'l':l, 't':t})
            elif text in t:
                zz.append({'l':l, 't':t})
 
        # output
        if len(zz) == 0:
            irc.reply("No matches for %s" % text.decode('utf-8'))
        else:
            o = random.choice(zz)
            irc.reply("{0} :: {1}".format(o['t'], o['l']))

    kpix = wrap(kpix, [optional('somethingWithoutSpaces')])

    def slur(self, irc, msg, args):
        """
        Display a random racial slur from the racial slur database (rsdb.org)
        """

        # build and fetch url.
        url = 'http://www.rsdb.org/full'
        html = self._httpget(url)
        if not html:  # http fetch breaks.
            irc.reply("ERROR: Trying to open: {0}".format(url))
            return
        # process html
        soup = BeautifulSoup(html)
        div = soup.find('div', attrs={'id':'slurs'})
        rows = div.findAll('tr', attrs={'id':re.compile('slur_.*')})

        slurs = []

        for row in rows:
            tds = [item.getText().strip() for item in row.findAll('td')]
            if sys.version_info[0] == 3:
                slur = tds[0]
                group = tds[1]
                reasoning = tds[2]
            else:
                slur = tds[0].encode('utf-8')
                group = tds[1].encode('utf-8')
                reasoning = tds[2].encode('utf-8')
            slurs.append("{0}({1}) :: {2}".format(slur, group, reasoning))

        randomslur = choice(slurs)
        irc.reply(randomslur)

    slur = wrap(slur)

    #def hex2ip(self, irc, msg, args, optinput):
    #    """<hexip>
    #    Try and turn hexIP back into IP address.
    #    Ex: 0200A8C0
    #    """
    #
    #    ip = self._numToDottedQuad(optinput)
    #    #ip = '.'.join(str(int(i, 16)) for i in reversed([optinput[i:i+2] for i in range(0, len(optinput), 2)]))
    #
    #    if ip and len(optinput) == 8:
    #        try:
    #            record = socket.gethostbyaddr(ip)  # do dns here.
    #        except Exception:  # no DNS found.
    #            record = None
    #        # here.
    #        if record:
    #            reply = "HexIP: {0} = {1}({2})".format(optinput, record[0].encode('utf-8'), ip)
    #        else:
    #            reply = "HexIP: {0} = {1}".format(optinput, ip)
    #    else:
    #        reply = "ERROR: {0} is an invalid HexIP".format(optinput)
    #    # output.
    #    irc.reply(reply)

    #hex2ip = wrap(hex2ip, (['somethingWithoutSpaces']))

    def kernel(self, irc, msg, args):
        """
        Display the latest linux kernels from kernel.org.
        """

        url = 'https://www.kernel.org/releases.json'
        html = self._httpget(url)
        if not html:  # http fetch breaks.
            irc.reply("ERROR: Trying to open: {0}".format(url))
            return
        # parse json
        if sys.version_info[0] == 3:
            releases = json.loads(html.decode('utf-8'))
        else:
            releases = json.loads(html)
        # parse json.
        lateststable = releases['latest_stable']['version']
        releases = releases['releases']
        output = []
        for release in releases:
            moniker = release['moniker']
            version = release['version']
            released = release['released']['isodate']
            if release['iseol']:
                output.append("{0} {1} (EOL) {2}".format(moniker, version, released))
            else:
                output.append("{0} {1} (EOL) {2}".format(moniker, version, released))
        # output
        irc.reply("The latest stable kernel is: {0}".format(lateststable))
        irc.reply("Others: {0}".format(" | ".join(output)))

    kernel = wrap(kernel)

    def b64decode(self, irc, msg, args, optstring):
        """Returns base64 decoded string."""

        try:
            if sys.version_info[0] == 3:
                s = base64.b64decode(optstring.encode('utf-8'))
                irc.reply(s.decode('utf-8'))
            else:
                irc.reply(base64.b64decode(optstring))
        except Exception as e:
            irc.reply("ERROR: decoding '{0}' :: {1}".format(optstring, e))

    b64decode = wrap(b64decode, [('somethingWithoutSpaces')])

    def b64encode(self, irc, msg, args, optstring):
        """Returns bas64 encoded string."""

        try:
            if sys.version_info[0] == 3:
                s = base64.b64encode(bytes(optstring, "utf-8"))
                irc.reply(s.decode('utf-8'))
            else:
                irc.reply(base64.b64encode(optstring))
        except Exception as e:
            irc.reply("ERROR: encoding '{0}' :: {1}".format(optstring, e))

    b64encode = wrap(b64encode, [('somethingWithoutSpaces')])

    def _pigword(self, word):
        shouldCAP = (word[:1] == word[:1].upper())
        word = word.lower()

        letters = "qwertyuiopasdfghjklzxcvbnm"
        i = len(word) - 1
        while i >= 0 and letters.find(word[i]) == -1:
            i = i - 1
        if i == -1:
            return word
        punctuation = word[i+1:]
        word = word[:i+1]

        vowels = "aeiou"
        if vowels.find(word[0]) >= 0:
            word = word + "yay" + punctuation
        else:
            word = word[1:] + word[0] + "ay" + punctuation

        if shouldCAP:
            return word[:1].upper() + word[1:]
        else:
            return word

    def piglatin(self, irc, msg, args, optinput):
        """<text>
        Convert text from English to Pig Latin.
        """

        l = optinput.split(" ")
        for i in range(len(l)):
            l[i] = self._pigword(l[i])

        irc.reply(" ".join(l))

    piglatin = wrap(piglatin, [('text')])

    def _frinkcleanup(self, text):
        text = text.replace(' in ', ' -> ')
        text = text.replace(' to ', ' -> ')
        text = text.replace(' as ', ' -> ')
        text = text.replace(' over ', ' / ')
        return text

    def frink(self, irc, msg, args, optinput):
        """<expression>
        Use the Frink online calculator. Ex: 2+2
        """

        optinput = self._frinkcleanup(optinput)
        url = 'http://futureboy.us/fsp/frink.fsp?hideHelp=Hide+%27help%27+information+below&fromVal=' + utils.web.urlquote(optinput)
        html = self._httpget(url)
        if not html:  # http fetch breaks.
            irc.reply("ERROR: Trying to open: {0}".format(url))
            return

        if sys.version_info[0] == 3:
            result = html.decode('utf-8')
        else:
            result = html
        r_result = re.compile(r'(?i)<A NAME=results>(.*?)</A>')
        r_tag = re.compile(r'<\S+.*?>')
        match = r_result.search(result)

        if not match:
            irc.reply("Calculation error looking up: {0}.".format(optinput))
            return

        result = match.group(1)
        result = r_tag.sub("", result) # strip span.warning tags
        result = result.replace("&gt;", ">")
        result = result.replace("(undefined symbol)", "(?) ")
        result = result.strip()

        irc.reply("{0} :: {1}".format(optinput, result))

    frink = wrap(frink, [('text')])

    def geoip(self, irc, msg, args, optip):
        """<ip.address>
        Use a GeoIP API to lookup the location of an IP.
        """

        url = 'http://freegeoip.net/json/%s' % (optip)
        html = self._httpget(url)
        if not html:  # http fetch breaks.
            irc.reply("ERROR: Trying to open: {0}".format(url))
            return
        
        if sys.version_info[0] == 3:
            jsondata = json.loads(html.decode('utf-8'))
        else:
            jsondata = json.loads(html)

        city = jsondata.get('city')
        region_code = jsondata.get('region_code')
        #region_name = jsondata.get('region_name', None)
        #zipcode = jsondata.get('zipcode', None)
        longitude = jsondata.get('longitude')
        latitude = jsondata.get('latitude')
        ip = jsondata.get('ip')

        if ip and city and region_code and longitude and latitude:
            output = "{0} {1} {2} ({3}, {4})".format(self._bu(ip), city, region_code, longitude, latitude)
            irc.reply(output)
        else:
            irc.reply("ERROR :: looking up '{0}' at {1}".format(optip, url))

    geoip = wrap(geoip, [('somethingWithoutSpaces')])

    def mydrunktexts(self, irc, msg, args):
        """
        Display random text from mydrunktexts.com
        """

        url = 'http://mydrunktexts.com/random'
        html = self._httpget(url)
        if not html:  # http fetch breaks.
            irc.reply("ERROR: Trying to open: {0}".format(url))
            return
        soup = BeautifulSoup(html) #, convertEntities=BeautifulSoup.HTML_ENTITIES)
        txt = soup.find('div', attrs={'class':'bubblecontent'}).getText() # <div class="bubblecontent">
        irc.reply(txt)

    mydrunktexts = wrap(mydrunktexts)

    def bash(self, irc, msg, args):
        """
        Display a random bash.org quote.
        """

        url = 'http://www.bash.org/?random1'
        html = self._httpget(url)
        if not html:  # http fetch breaks.
            irc.reply("ERROR: Trying to open: {0}".format(url))
            return
        soup = BeautifulSoup(html)
        quotes = soup.findAll('p', attrs={'class':'qt'})
        quote = choice(quotes)
        num = quote.findPrevious('b').getText()
        quote = quote.getText().replace("\n", " ").replace("\r", " ")
        quote = utils.str.normalizeWhitespace(quote)
        irc.reply("[{0}] {1}".format(num, quote))

    bash = wrap(bash)

    def fml(self, irc, msg, args, getopts):
        """
        Display a random fmylife.com entry.
        """

        url = 'http://api.betacie.com/view/random?key=4be9c43fc03fe&language=en'
        html = self._httpget(url)
        if not html:  # http fetch breaks.
            irc.reply("ERROR: Trying to open: {0}".format(url))
            return

        tree = ElementTree.fromstring(html)
        if tree.find('code').text != "1":
            irc.reply("Something went wrong doing FML. Try again later.")
            return

        #gender = tree.find('items/item/author').get('gender') # can be none
        #country = tree.find('items/item/author').get('country')
        #region = tree.find('items/item/author').get('region')
        if sys.version_info[0] == 3:
            category = tree.find('items/item/category').text
            message = tree.find('items/item/text').text
        else:
            category = tree.find('items/item/category').text.encode('utf-8')
            message = tree.find('items/item/text').text.encode('utf-8')
        #link = tree.find('items/item/short_url').text

        irc.reply("FML: [{0}] {1}".format(category, message))

    fml = wrap(fml, [getopts({})])

    def powerball(self, irc, msg, args):
        """
        Show powerball numbers.
        """

        url = 'http://www.usamega.com'
        html = self._httpget(url)
        if not html:  # http fetch breaks.
            irc.reply("ERROR: Trying to open: {0}".format(url))
            return
        # process html.
        html = html.decode('iso-8859-1')
        soup = BeautifulSoup(html) #.replace('&nbsp;',''))
 
        nextpbdate = soup.findAll('div', attrs={'class':'BluebarSmText'})[2]
        prevpbdate = soup.findAll('div', attrs={'class':'BluebarSmText'})[3]
        curjackpot = soup.findAll('td', attrs={'class':'JackpotText'})[1]
        prevpb = soup.findAll('td', attrs={'class':'ResultsText'})[1]
        # str
        if sys.version_info[0] == 3:
            curjackpot = curjackpot.getText()
            nextpbdate = nextpbdate.getText()
            prevpb = prevpb.getText()
            prevpbdate = prevpbdate.getText()
        else:
            curjackpot = curjackpot.getText().encode('utf-8')
            nextpbdate = nextpbdate.getText().encode('utf-8')
            prevpb = prevpb.getText().encode('utf-8')
            prevpbdate = prevpbdate.getText().encode('utf-8')
            
        output = "Current jackpot: {0} for {1} :: Previous numbers: {2} from: {3}".format(\
            self._bold(curjackpot), nextpbdate, self._bold(prevpb), prevpbdate)
        irc.reply(output)

    powerball = wrap(powerball)

    def megamillions(self, irc, msg, args):
        """
        Show megamillions numbers.
        """

        url = 'http://www.megamillions.com'
        html = self._httpget(url)
        if not html:  # http fetch breaks.
            irc.reply("ERROR: Trying to open: {0}".format(url))
            return

        soup = BeautifulSoup(html)
        one = soup.find('div', attrs={'class':'home-next-drawing-estimated-jackpot'}).getText()
        one = utils.str.normalizeWhitespace(one.replace('\r', '').replace('\n', ''))
        three = soup.find('table', attrs={'class':'home-mini-winning-numbers-widget'}).getText(separator=' ')
        three = utils.str.normalizeWhitespace(three.replace('\r', '').replace('\n', ''))
        
        irc.reply("{0}: {1} || {2}".format(self._bold("MEGAMILLIONS"), one, three))

    megamillions = wrap(megamillions)

    def mortgage(self, irc, msg, args, state):
        """[state code]

        Returns latest mortgage rates summary from Zillow --
        http://www.zillow.com/howto/api/APIOverview.htm
        Optional: call with the two-letter state code to display specific rates.
        """



        url = 'http://www.zillow.com/webservice/GetRateSummary.htm?zws-id=X1-ZWz1crn3j8npjf_1sm5d&output=json'
        if state:
            url += "&state=%s" % state

        html = self._httpget(url)
        if not html:  # http fetch breaks.
            irc.reply("ERROR: Trying to open: {0}".format(url))
            return

        if sys.version_info[0] == 3:
            response = json.loads(html.decode('utf-8'))
        else:
            response = json.loads(html)
        
        # check for error.
        if response['message']['code'] != "0":
            irc.reply("ERROR :: {0}".format(response['message']['text']))
            return
        else:
            rates = response.get('response')
            o = "The average rate on a 30 year mortgage is %s. Last week it was %s. " + \
            "If you want a 15 year mortgage the average rate is %s. Last week it was %s. " + \
            "If you're crazy enough to want a 5-1 ARM the average rate is %s. Last week it was %s. "

            resp = o % (
                self._red(rates['today']['thirtyYearFixed']), self._red(rates['lastWeek']['thirtyYearFixed']),
                self._red(rates['today']['fifteenYearFixed']), self._red(rates['lastWeek']['fifteenYearFixed']),
                self._red(rates['today']['fiveOneARM']), self._red(rates['lastWeek']['fiveOneARM']))

            irc.reply(resp)

    mortgage = wrap(mortgage, [optional('somethingWithoutSpaces')])

    def callook(self, irc, msg, args, optsign):
        """<callsign>
        
        Lookup specific callsign in radio DB.
        Ex: W1JDD
        """

        url = 'http://callook.info/%s/json' % optsign
        html = self._httpget(url)
        if not html:  # http fetch breaks.
            irc.reply("ERROR: Trying to open: {0}".format(url))
            return

        if sys.version_info[0] == 3:
            html = html.decode('utf-8')

        jsondata = json.loads(html)
        status = jsondata.get('status')

        if status == "INVALID":
            irc.reply("%s is INVALID" % optsign)
            return
        elif status == "VALID":
            lictype = jsondata.get('type')
            name = jsondata.get('name')
            grantDate = jsondata['otherInfo'].get('grantDate')
            operclass = jsondata['current'].get('operClass')
            output = "{0} :: {1} {2} {3} {4}".format(optsign, lictype, name, grantDate, operclass)
            irc.reply(output)

    callook = wrap(callook, [('somethingWithoutSpaces')])

    def randomfacts(self, irc, msg, args):
        """
        Fetch a random fact from www.randomfunfacts.com
        """

        url = 'http://www.randomfunfacts.com'
        html = self._httpget(url)
        if not html:  # http fetch breaks.
            irc.reply("ERROR: Trying to open: {0}".format(url))
            return
        
        if sys.version_info[0] == 3:
            html = html.decode('windows-1252')

        fact = re.search(r'<strong><i>(.*?)</i></strong>', html, re.I|re.S)
        irc.reply(fact.group(1))

    randomfacts = wrap(randomfacts)

    def chucknorris(self, irc, msg, args, opts):
        """
        Grab a random ChuckNorris from icndb.com.
        Use --rainbow to display in a colorful way.
        """

        opts = dict(opts)

        url = 'http://api.icndb.com/jokes/random'
        html = self._httpget(url)
        if not html:  # http fetch breaks.
            irc.reply("ERROR: Trying to open: {0}".format(url))
            return

        if sys.version_info[0] == 3:
            html = html.decode('utf-8')

        data = json.loads(html)

        if (data['value']['joke']):
            joke = data['value']['joke']
        else:
            irc.reply("Missing output value.")
            return
        # options for rainbow. Thanks to ProgVal for the syntax here.
        if 'rainbow' in opts:
            irc.reply("{0}".format(self._rainbow(joke)))
        else:
            irc.reply(joke)

    chucknorris = wrap(chucknorris, [getopts({'rainbow': ''})])

    def litecoin(self, irc, msg, args):
        """
        Return pretty-printed litecoin ticker in USD.
        """

        url = 'https://btc-e.com/api/2/ltc_usd/ticker'
        html = self._httpget(url)
        if not html:  # http fetch breaks.
            irc.reply("ERROR: Trying to open: {0}".format(url))
            return

        if sys.version_info[0] == 3:
            ticker = json.loads(html.decode('utf-8'))
        else:
            ticker = json.loads(html)

        if 'ticker' not in ticker:
            irc.reply("Error parsing btc-e.com API at {0}".format(url))
            return
        else:
            bitcoin = ticker['ticker']
            last = self._green(bitcoin['last'])
            vol = self._orange(bitcoin['vol'])
            low = self._blue(bitcoin['low'])
            high = self._red(bitcoin['high'])
            average = self._lightblue(bitcoin['avg'])
            irc.reply("Last Litecoin(btc-e.com) trade: {0}  24hr Vol: {1}  low: {2}  high: {3}  avg: {4} (USD)".format(last, vol, low, high, average))

    litecoin = wrap(litecoin)

    def dogecoin(self, irc, msg, args):
        """
        Return current Dogecoin ticker in USD.
        """
        
        url = 'http://data.bter.com/api/1/ticker/doge_cny'
        html = self._httpget(url)
        if not html:  # http fetch breaks.
            irc.reply("ERROR: Trying to open: {0}".format(url))
            return
        
        if sys.version_info[0] == 3:
            ticker = json.loads(html.decode('utf-8'))
        else:
            ticker = json.loads(html)

        if 'result' not in ticker:
            irc.reply("Error parsing bter API at {0}".format(url))
            return
        else:
            bitcoin = ticker
            last = self._green(bitcoin['last'])
            vol = self._orange(bitcoin['vol_doge'])
            low = self._blue(bitcoin['low'])
            high = self._red(bitcoin['high'])
            average = self._lightblue(bitcoin['avg'])
            irc.reply("Last Dogecoin(bter.com) trade: {0}  24hr Vol: {1}  low: {2}  high: {3}  avg: {4} (USD)".format(last, vol, low, high, average))
            
    dogecoin = wrap(dogecoin)

    def bitcoin(self, irc, msg, args):
        """
        Return pretty-printed bitcoin ticker in USD.
        """

        url = 'https://btc-e.com/api/2/btc_usd/ticker'
        html = self._httpget(url)
        if not html:  # http fetch breaks.
            irc.reply("ERROR: Trying to open: {0}".format(url))
            return

        if sys.version_info[0] == 3:
            ticker = json.loads(html.decode('utf-8'))
        else:
            ticker = json.loads(html)

        if 'ticker' not in ticker:
            irc.reply("Error parsing btc-e.com API at {0}".format(url))
            return
        else:
            bitcoin = ticker['ticker']
            last = self._green(bitcoin['last'])
            vol = self._orange(bitcoin['vol'])
            low = self._blue(bitcoin['low'])
            high = self._red(bitcoin['high'])
            average = self._lightblue(bitcoin['avg'])
            irc.reply("Last Bitcoin(btc-e.com) trade: {0}  24hr Vol: {1}  low: {2}  high: {3}  avg: {4} (USD)".format(last, vol, low, high, average))

    bitcoin = wrap(bitcoin)

    def hackernews(self, irc, msg, args):
        """
        Display top hackernews.com headlines.
        """

        # construct and fetch url.
        url = 'https://news.ycombinator.com/rss'
        html = self._httpget(url)
        if not html:  # http fetch breaks.
            irc.reply("ERROR: Trying to open: {0}".format(url))
            return

        # parse RSS.
        rss = html #.decode('utf-8')
        rss = feedparser.parse(rss)
        items = rss['entries']
        # process each item and output.
        for item in items[0:5]:
            if sys.version_info[0] == 3:
                title = item.title
            else:
                title = item.title.encode('utf-8')
            title = utils.str.ellipsisify(title, 150)
            url = item.link
            comments = item.comments            
            irc.reply("{0} - {1} :: Comments {2}".format(title, url, comments))

    hackernews = wrap(hackernews)

    def developerexcuses(self, irc, msg, args):
        """
        Returns an excuse from http://developerexcuses.com
        """

        url = 'http://developerexcuses.com'
        html = self._httpget(url)
        if not html:  # http fetch breaks.
            irc.reply("ERROR: Trying to open: {0}".format(url))
            return

        soup = BeautifulSoup(html)
        text = soup.find('center').getText()
        irc.reply("{0}".format(text))

    developerexcuses = wrap(developerexcuses)

    def bofh(self, irc, msg, args):
        """
        Returns an excuse from http://pages.cs.wisc.edu/~ballard/bofh/
        """

        url = 'http://pages.cs.wisc.edu/~ballard/bofh/excuses'
        # url = 'http://pgl.yoyo.org/bofh/excuses.txt'
        html = self._httpget(url)
        if not html:  # http fetch breaks.
            irc.reply("ERROR: Trying to open: {0}".format(url))
            return

        lines = html.splitlines()
        if sys.version_info[0] == 3:
            randomline = choice(lines).decode()
        else:
            randomline = choice(lines)
        
        irc.reply("Random BOFH excuse :: {0}".format(randomline))

    bofh = wrap(bofh)

    #def macvendor(self, irc, msg, args, optinput):
    #    """<MA:C:ADDRESS>
    #
    #    The MAC Address Vendor/Manufacturer Lookup API allows you to query and obtain information about any MAC or OUI.
    #    Ex: 0023AE000022
    #    """
    #
    #    url = 'http://www.macvendorlookup.com/api/AKzKyAB/' + optinput # 0023AE7B5899
    #    html = self._httpget(url)
    #    if not html:  # http fetch breaks.
    #        irc.reply("ERROR: Trying to open: {0}".format(url))
    #        return
    #    # process json
    #    if 'none' in html:
    #        irc.reply("ERROR: {0} is an invalid MAC Address.".format(optinput))
    #        return
    #    elif 'Error:' in html:
    #        irc.reply("ERROR: {0}".format(html))
    #    else:
    #        jsd = json.loads(html)[0]
    #        out = "{0}-{1} :: {2} {3}".format(jsd['startHex'], jsd['endHex'], jsd['company'], jsd['country'])
    #        irc.reply(out)
    #
    #macvendor = wrap(macvendor, [('somethingWithoutSpaces')])

    def nerdman(self, irc, args, msg, opts):
        """
        Display one of nerdman's wonderful quotes.
        """

        opts = dict(opts)

        url = 'http://www.hockeydrunk.com/nerdman/random.php'
        html = self._httpget(url)
        if not html:  # http fetch breaks.
            irc.reply("ERROR: Trying to open: {0}".format(url))
            return
        
        # decode for py3.
        if sys.version_info[0] == 3:
            html = html.decode('utf-8')

        if 'rainbow' in opts:
            irc.reply("<nerdman> {0}".format(self._rainbow(html)))
        else:
            irc.reply("<nerdman> {0}".format(html))

    nerdman = wrap(nerdman, [getopts({'rainbow': ''})])

    def woot(self, irc, msg, args, optlist):
        """[--wine]

        Display daily woot.com deal.
        Use --wine to display the daily wine woot deal.
        """

        url = "http://www.woot.com/salerss.aspx"

        opts = dict(optlist)
        if 'wine' in opts:  # option for vegetarian
            url = 'http://wine.woot.com/salerss.aspx'

        if sys.version_info[0] == 3:
            dom = xml.dom.minidom.parse(urllib.request.urlopen(url))
        else:
            dom = xml.dom.minidom.parse(urllib2.urlopen(url))

        product = dom.getElementsByTagName("woot:product")[0].childNodes[0].data
        price = dom.getElementsByTagName("woot:price")[0].childNodes[0].data
        purchaseurl = dom.getElementsByTagName("woot:purchaseurl")[0].childNodes[0].data
        soldout = dom.getElementsByTagName("woot:soldout")[0].childNodes[0].data # false
        shipping = dom.getElementsByTagName("woot:shipping")[0].childNodes[0].data

        if soldout == 'false':
            output = self._green("IN STOCK ")
        else:
            output = self._red("SOLDOUT ")

        output += self._bu("ITEM:") + " " + product + " "
        output += self._bu("PRICE:") + " " + price + " (Shipping:" + shipping + ") "
        output += self._bu("URL:") + " " + purchaseurl + " "
        #output += self._bu("URL:") + " " + self._shortenUrl(purchaseurl) + " "

        irc.reply(output)

    woot = wrap(woot, [getopts({'wine':''})])

    def pick(self, irc, msg, args, choices):
        """[choices]
        Picks a random item from choices. Separate the list by a comma.
        """

        choicelist = self._splitinput(choices, [','])
        output = "From the {0} choice(s) you entered, I have selected: {1}".format(self._red(len(choicelist)), self._bu(choice(choicelist)))
        irc.reply(output)

    pick = wrap(pick, ['text'])

    def advice(self, irc, msg, args):
        """
        Grab some advice from http://www.leonatkinson.com/random/
        """

        url = "http://www.leonatkinson.com/random/index.php/rest.html?method=advice"
        doc = etree.parse(url)
        quote = doc.find("quote").text
        author = doc.find("author").text
        date = doc.find("date").text

        output = "'{0}' {1} ({2})".format(quote, self._bu(author), date)
        irc.reply(output)

    advice = wrap(advice)

    def debt(self, irc, msg, args):
        """Display the debt."""

        url = "http://www.treasurydirect.gov/NP/BPDLogin?application=np"
        html = self._httpget(url)
        if not html:  # http fetch breaks.
            irc.reply("ERROR: Trying to open: {0}".format(url))
            return

        soup = BeautifulSoup(html)
        debt = soup.find('table', attrs={'class':'data1'}).findAll('td')[3].contents
        asof = soup.find('table', attrs={'class':'data1'}).findAll('td')[0].contents

        url = 'http://quickfacts.census.gov/qfd/states/00000.html'
        html = self._httpget(url)
        if not html:  # http fetch breaks.
            irc.reply("ERROR: Trying to open: {0}".format(url))
            return

        soup = BeautifulSoup(html)
        population = soup.find('td', attrs={'headers':'usa', 'align':'right', 'valign':'bottom'}).getText()
        # turn population and debt into float so we can divide into per_person
        strpopulation = str(population.replace(",",""))
        strdebt = str(debt[0]).replace(",", "")
        per_person = float(strdebt)/float(strpopulation)

        # format the output and clean it up
        asof = self._ul(asof[0])
        # format debt
        debt = self._myfloat(strdebt)
        debt = self._bold("$" + self._size_fmt(debt))
        # per_person + population just need millify + bold
        per_person = self._bold("$" + self._size_fmt(float(per_person)))
        population = self._bold("$" + self._size_fmt(float(strpopulation)))

        irc.reply("As of {0} the US Debt is {1}. {2} per person with a population of {3}".format(asof, debt, per_person, population))

    debt = wrap(debt)

Class = Assorted


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=250:
