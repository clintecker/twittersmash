# -*- coding: utf-8 -*-
from django.test import TestCase
from django.test.client import Client
from twittersmash.models import Feed, Message, TwitterAccount
import datetime
import twitter
import time

class SmashTest(TestCase):

    def setUp(self):
        self.feed1 = Feed.objects.create(
            url = 'http://twitter.com/statuses/user_timeline/45993.rss',
            name = 'Clint Ecker\'s Twitter',
            polling_rate = 5,
        )
        self.feed2 = Feed.objects.create(
            url = 'http://twitter.com/statuses/user_timeline/10169382.rss',
            name = 'Kurt Mackey\'s Twitter',
            polling_rate = 15,
        )
        self.ta1 = TwitterAccount.objects.create(
            username = 'arstest',
            password = 'ipitythefool',
            philter = '',
            active = True,
        )
        
        self.api = twitter.Api(username = self.ta1.username, password=self.ta1.password)

    def tearDown(self):
        print "Waiting for Twitter to catch up."
        time.sleep(10)
        statuses = self.api.GetUserTimeline(self.ta1.username)
        print "Destroying %s statuses" % (len(statuses))
        for status in statuses:
            self.api.DestroyStatus(status.id)

    def testBasicSmash(self):
        "Takes one feed and pipes it into one Twitter Account"
        from twittersmash.management.commands.smash_stuff import Command as SmashStuff
        ss = SmashStuff()
        
        # Add one feed to one TwitterAccount
        self.ta1.feeds.add(self.feed1)
        
        # Run the importer
        ss.handle()
        
        # There should be 20 entries in the test account
        statuses = self.api.GetUserTimeline(self.ta1.username)
        self.assertEquals(len(statuses), 20)
        