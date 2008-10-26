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
        
        #self.api = twitter.Api(username = self.ta1.username, password=self.ta1.password)

    def tearDown(self):
        pass

    def testBasicSmash(self):
        "Takes one feed and pipes it into one Twitter Account"
        from twittersmash.management.commands.smash_stuff import Command as SmashStuff
        # Add one feed to one TwitterAccount
        self.ta1.feeds.add(self.feed1)
        self.message1 = Message.objects.create(
            message = 'This is a test message',
            guid = 'http://twitter.com/clint/status/975241573',
            sent_to_twitter = True,
            tweeted = datetime.datetime.now(),
            twitter_account = self.ta1,
            feed = self.feed1,
        )
        