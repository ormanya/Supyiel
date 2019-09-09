###
# Copyright (c) 2012-2014, spline
# All rights reserved.
#
#
###

from supybot.test import *

class AssortedTestCase(PluginTestCase):
    plugins = ('Assorted',)
        
    def testAssortedRegexp(self):
        self.assertRegexp('kernel', '[latest stable|Others]', re.I)
        # self.assertNotError('kernel')    

    def testDebt(self):
        try:
            self.assertRegexp('debt', 'As of')
        except:
            return

    def testbase64(self):
        self.assertResponse('b64decode aGVsbG8=', 'hello')
        self.assertResponse('b64encode hello', 'aGVsbG8=')

    #def testHex2ip(self):
    #    self.assertResponse('hex2ip 0200A8C0', 'HexIP: 0200A8C0 = ANantes-654-1-213-192.w2-0.abo.wanadoo.fr(2.0.168.192)')
    
    def testAdvice(self):
        self.assertNotError('advice')
        
    def testBash(self):
        self.assertNotError('bash')
    
    def testCatCommands(self):
        self.assertNotError('catfacts')
        self.assertNotError('catpix')
    
    def testBofh(self):
        self.assertNotError('bofh')

    def testCallook(self):
        self.assertNotError('callook W1JDD')

    def testChucknorris(self):
        self.assertNotError('chucknorris')
    
    def testDeveloperexcuses(self):
        self.assertNotError('developerexcuses')
        
    def testCoins(self):
        self.assertNotError('dogecoin')
        self.assertNotError('litecoin')
        self.assertNotError('bitcoin')
    
    def testFrink(self):
        self.assertResponse('frink 2+2', '2+2 :: 4')
    
    #def testFuckingDinner(self):
        #self.assertNotError('fuckingdinner')
    
    def testGeoIP(self):
        self.assertNotRegexp('geoip 209.94.100.100', 'ERROR')
    
    #def testMacVendor(self):
        #self.assertResponse('macvendor 0023AE000022', '0023AE000000-0023AEFFFFFF :: Dell Inc. UNITED STATES')
        #self.assertNotError('macvendor 0023AE000022')
    
    def testLotto(self):
        self.assertNotError('megamillions')
        self.assertNotError('powerball')
    
    def testMortgage(self):    
        self.assertNotError('mortgage')
        
    def testMyDrunkTexts(self):
        self.assertNotError('mydrunktexts')
    
    def testNerdman(self):   
        self.assertNotError('nerdman')
    
    def testPick(self):
        self.assertNotError('pick 1,2')
    
    def testPiglatin(self):
        self.assertResponse('piglatin hello to you', 'ellohay otay ouyay')
        #self.assertNotError('piglatin hello to you')
        
    def testRandomFacts(self):
        self.assertNotError('randomfacts')
    
    #def testSlur(self):
        #self.assertNotError('slur')
    
    def testWoot(self):
        self.assertNotError('woot')
    
    def testHackerNews(self):
        self.assertNotError('hackernews')
    

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
