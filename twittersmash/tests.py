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

    def tearDown(self):
        pass

    def testTwitterConnection(self):
        # Test twitter connection
        self.api = twitter.Api(username = self.ta1.username, password=self.ta1.password)
        
    def testBasicSmashNoFilterNoTwitter(self):
        "Test basic model functionality"
        self.ta1.philter = ''
        self.ta1.save()
        
        self.ta1.feeds.add(self.feed1)
        self.message1 = Message.objects.create(
            message = 'This is a test message',
            guid = 'http://twitter.com/clint/status/975241573',
            sent_to_twitter = True,
            tweeted = datetime.datetime.now(),
            twitter_account = self.ta1,
            feed = self.feed1,
        )

    def testBasicSmashFilterNoTwitter(self):
        "Smash two feeds into one account, with a filter, no actual twittering"
        self.ta1.philter = '#pdc'
        self.ta1.save()
        
        self.ta1.feeds.add(self.feed1)
        self.ta1.feeds.add(self.feed2)
        
        self.message1 = Message.objects.create(
            message = 'This is a test message',
            guid = 'http://twitter.com/clint/status/975241573',
            sent_to_twitter = True,
            tweeted = datetime.datetime.now(),
            twitter_account = self.ta1,
            feed = self.feed1,
        )
        self.message2 = Message.objects.create(
            message = 'I am Ken Fisher and I have approved this mesage',
            guid = 'http://twitter.com/kevinrose/status/975842840',
            sent_to_twitter = False,
            tweeted = datetime.datetime.now(),
            twitter_account = self.ta1,
            feed = self.feed2,
        )
        self.message3 = Message.objects.create(
            message = 'checked in and got a window seat for my red-eye flight to Newark tomorrow night.',
            guid = 'http://twitter.com/Joi/status/975833289',
            sent_to_twitter = True,
            tweeted = datetime.datetime.now(),
            twitter_account = self.ta1,
            feed = self.feed2,
        )
        self.message4 = Message.objects.create(
            message = 'I\'m at Schaumburg, IL (Schaumburg, IL, USA) in Schaumburg - http://bkite.com/021de',
            guid = 'http://twitter.com/Schwieb/status/975825768',
            sent_to_twitter = True,
            tweeted = datetime.datetime.now(),
            twitter_account = self.ta1,
            feed = self.feed1,
        )

    def testSmashStuffCommandNoFilter(self):
        "Sets up two feeds to get smashed into another and runs through the smash_stuff command with no filter"
        from twittersmash.management.commands.smash_stuff import Command as SmashStuff
        self.ta1.philter = ''
        self.ta1.save()
        
        self.ta1.feeds.add(self.feed1)
        self.ta1.feeds.add(self.feed2)
        c = SmashStuff()
        # Run the smash_stuff command
        results = c.handle(dryrun=True, quiet=True)
        self.assertEquals(results['accounts_ready'], 2)
        self.assertEquals(results['accounts_skipped'], 0)
        self.assertEquals(results['feeds_pulled'], 2)
        self.assertEquals(results['feeds_checked'], 2)
        self.assertEquals(results['messages_added'], 40)
        self.assertTrue(results['messages_added'] == results['entries_tweeted'] == results['entries_pulled'])
        
    def testSmashStuffCommandFilter(self):
        "Sets up two feeds to get smashed into another and runs through the smash_stuff command with filter"
        from twittersmash.management.commands.smash_stuff import Command as SmashStuff
        self.ta1.philter = 'tinyurl'
        self.ta1.save()
        
        self.ta1.feeds.add(self.feed1)
        self.ta1.feeds.add(self.feed2)
        c = SmashStuff()
        # Run the smash_stuff command
        
        results = c.handle(dryrun=True, quiet=True)
        self.assertEquals(results['accounts_ready'], 2)
        self.assertEquals(results['accounts_skipped'], 0)
        self.assertEquals(results['feeds_pulled'], 2)
        self.assertEquals(results['feeds_checked'], 2)
        self.assertEquals(results['messages_added'], 40)
        self.assertTrue(results['messages_added'] == results['entries_pulled'])
        self.assertTrue(results['messages_added'] > results['entries_tweeted'])

    def testSmashStuffCommandManyFilters(self):
        "Sets up two feeds to get smashed into another and runs through the smash_stuff command with multiple filters"
        from twittersmash.management.commands.smash_stuff import Command as SmashStuff
        self.ta1.philter = 'palin, bush, obama'
        self.ta1.save()
        
        self.ta1.feeds.add(self.feed1)
        self.ta1.feeds.add(self.feed2)
        c = SmashStuff()
        # Run the smash_stuff command
        results = c.handle(dryrun=True, quiet=True)
        self.assertEquals(results['accounts_ready'], 2)
        self.assertEquals(results['accounts_skipped'], 0)
        self.assertEquals(results['feeds_pulled'], 2)
        self.assertEquals(results['feeds_checked'], 2)
        self.assertEquals(results['messages_added'], 40)
        self.assertTrue(results['messages_added'] == results['entries_pulled'])
        self.assertTrue(results['messages_added'] > results['entries_tweeted'])

    def testSmashStuffCommandOneRateLimit(self):
        "Sets up two feeds to get smashed into another and runs through the smash_stuff command.  One account doesn't need to be checked."
        from twittersmash.management.commands.smash_stuff import Command as SmashStuff
        self.ta1.philter = ''
        self.ta1.save()
        
        self.feed1.polling_rate = 5
        self.feed1.last_checked = datetime.datetime.now()
        self.feed1.save()
        
        self.ta1.feeds.add(self.feed1)
        self.ta1.feeds.add(self.feed2)
        c = SmashStuff()
        # Run the smash_stuff command
        results = c.handle(dryrun=True, quiet=True)
        self.assertEquals(results['accounts_ready'], 1)
        self.assertEquals(results['accounts_skipped'], 1)
        self.assertEquals(results['feeds_checked'], 2)
        self.assertEquals(results['feeds_pulled'], 1)
        self.assertEquals(results['messages_added'], 20)
        self.assertTrue(results['messages_added'] == results['entries_pulled'] == results['entries_tweeted'])
    
    def testSmashStuffCommandTwoRateLimit(self):
        "Sets up two feeds to get smashed into another and runs through the smash_stuff command.  No accounts need to be checked."
        from twittersmash.management.commands.smash_stuff import Command as SmashStuff
        self.ta1.philter = ''
        self.ta1.save()

        self.feed1.polling_rate = 5
        self.feed1.last_checked = datetime.datetime.now()
        self.feed1.save()
        
        self.feed2.polling_rate = 5
        self.feed2.last_checked = datetime.datetime.now()
        self.feed2.save()

        self.ta1.feeds.add(self.feed1)
        self.ta1.feeds.add(self.feed2)
        c = SmashStuff()
        # Run the smash_stuff command
        results = c.handle(dryrun=True, quiet=True)
        self.assertEquals(results['accounts_ready'], 0)
        self.assertEquals(results['accounts_skipped'], 2)
        self.assertEquals(results['feeds_checked'], 2)
        self.assertEquals(results['feeds_pulled'], 0)
        self.assertEquals(results['messages_added'], 0)
        self.assertTrue(results['messages_added'] == results['entries_pulled'] == results['entries_tweeted'])
        
    def testSmashStuffCommandRateLimitKicksIn(self):
        "Sets up two feeds to get smashed into another and runs through the smash_stuff command.  Intitially neither account needs checked, but then one does."
        from twittersmash.management.commands.smash_stuff import Command as SmashStuff
        self.ta1.philter = ''
        self.ta1.save()

        self.feed1.polling_rate = 1
        self.feed1.last_checked = datetime.datetime.now() - datetime.timedelta(seconds=50)
        self.feed1.save()

        self.feed2.polling_rate = 1
        self.feed2.last_checked = datetime.datetime.now()
        self.feed2.save()

        self.ta1.feeds.add(self.feed1)
        self.ta1.feeds.add(self.feed2)
        c = SmashStuff()
        # Run the smash_stuff command
        results = c.handle(dryrun=True, quiet=True)
        self.assertEquals(results['accounts_ready'], 0)
        self.assertEquals(results['accounts_skipped'], 2)
        self.assertEquals(results['feeds_checked'], 2)
        self.assertEquals(results['feeds_pulled'], 0)
        self.assertEquals(results['messages_added'], 0)
        self.assertTrue(results['messages_added'] == results['entries_pulled'] == results['entries_tweeted'])
        
        time.sleep(10)
        
        c = SmashStuff()
        # Run the smash_stuff command
        results = c.handle(dryrun=True, quiet=True)
        self.assertEquals(results['accounts_ready'], 1)
        self.assertEquals(results['accounts_skipped'], 1)
        self.assertEquals(results['feeds_checked'], 2)
        self.assertEquals(results['feeds_pulled'], 1)
        self.assertEquals(results['messages_added'], 20)
        self.assertTrue(results['messages_added'] == results['entries_pulled'] == results['entries_tweeted'])
        
    