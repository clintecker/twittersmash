# -*- coding: utf-8 -*-
from django.test import TestCase
from django.test.client import Client
from twittersmash.models import Feed, Message, TwitterAccount
import datetime
import twitter
import time

options = {
    'quiet': True,
}

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
        results = c.handle(dryrun=True, quiet=True, debug=True)
        self.assertEquals(results['accounts_ready'], 2)
        self.assertEquals(results['accounts_skipped'], 0)
        self.assertEquals(results['feeds_pulled'], 2)
        self.assertEquals(results['feeds_checked'], 2)
        self.assertEquals(results['messages_added'], 40)
        self.assertTrue(results['messages_added'] == results['entries_pulled'])
        self.assertEquals(results['entries_tweeted'], 0)
        
    def testSmashStuffCommandFilter(self):
        "Sets up two feeds to get smashed into another and runs through the smash_stuff command with filter"
        from twittersmash.management.commands.smash_stuff import Command as SmashStuff
        self.ta1.philter = 'tinyurl'
        self.ta1.save()
        
        self.ta1.feeds.add(self.feed1)
        self.ta1.feeds.add(self.feed2)
        c = SmashStuff()
        # Run the smash_stuff command
        
        results = c.handle(dryrun=True, quiet=True, debug=True)
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
        results = c.handle(dryrun=True, quiet=True, debug=True)
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
        results = c.handle(dryrun=True, quiet=True, debug=True)
        print results
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
        results = c.handle(dryrun=True, quiet=True, debug=True)
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
        results = c.handle(dryrun=True, quiet=True, debug=True)
        self.assertEquals(results['accounts_ready'], 0)
        self.assertEquals(results['accounts_skipped'], 2)
        self.assertEquals(results['feeds_checked'], 2)
        self.assertEquals(results['feeds_pulled'], 0)
        self.assertEquals(results['messages_added'], 0)
        self.assertTrue(results['messages_added'] == results['entries_pulled'] == results['entries_tweeted'])
        
        time.sleep(10)
        
        c = SmashStuff()
        # Run the smash_stuff command
        results = c.handle(dryrun=True, quiet=True, debug=True)
        self.assertEquals(results['accounts_ready'], 1)
        self.assertEquals(results['accounts_skipped'], 1)
        self.assertEquals(results['feeds_checked'], 2)
        self.assertEquals(results['feeds_pulled'], 1)
        self.assertEquals(results['messages_added'], 20)
        self.assertTrue(results['messages_added'] == results['entries_pulled'] == results['entries_tweeted'])

class TweetProcessing(TestCase):
    def setUp(self):
        
        self.ta2 = TwitterAccount.objects.create(
            username = 'arstest',
            password = 'ipitythefool',
            philter = '', # Default
            active = True, # Default
            philter_replies = True, # Default
            minimum_datetime = None, # Default
            strip_tags = False, # Default
            prepend_names = True, # Default
            append_tags = True, # Default
        )
        
        self.test_tweet1 = 'mrkurt: #pdc2008 tomorrow isn\'t just about infrastructure; it\'s about the user experience, etc..'
        self.test_tweet2 = 'drpizza: #pdc2008 er, the pricing should be competitive...'
        self.test_tweet3 = 'arspdc: #pdc2008 muglia is saying that this is the same scale as the 1992 introduction of NT'
        self.test_tweet4 = 'clint: @shadowbottle By doing stuff like letting the screen get dim and shipping better drivers'
        self.test_tweet5 = 'kenfisher: There\'s a giant bouncy Channel 9 mascot #pdc2008 #pdc08'
        self.test_tweet6 = 'Lorem ipsum dolor sit #pdc amet, #blah consectetur adipisicing elit'
        self.test_tweet7 = 'scobleizer: @arstest Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod'
        self.test_tweet8 = 'Lorem ipsum dolor sit amet, @arstest consectetur adipisicing elit, sed do eiusmod'
        self.test_tweet9 = 'blah: Lorem ipsum dolor sit amet, @arstest consectetur adipisicing elit, sed do eiusmod'
        self.test_tweet10 = 'ejacqui: Lorem #pdc08 dolor sit amet, consectetur adipisicing elit, sed do eiusmod'

        from twittersmash.management.commands.smash_stuff import Command as SmashStuff
        self.process = SmashStuff().process_messages

    def tearDown(self):
        pass

    def testDefaults(self):
        "Test defaults"     
        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet1,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, False)
        self.assertEquals(message, 'mrkurt: tomorrow isn\'t just about infrastructure; it\'s about the user experience, etc.. #pdc2008')
        
        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet2,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, False)
        self.assertEquals(message, 'drpizza: er, the pricing should be competitive... #pdc2008')
        
        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet3,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, False)
        self.assertEquals(message, 'arspdc: muglia is saying that this is the same scale as the 1992 introduction of NT #pdc2008')
        
        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet4,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, False)
        self.assertEquals(message, self.test_tweet4)
        
        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet5,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, False)
        self.assertEquals(message, self.test_tweet5)
        
        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet6,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, False)
        self.assertEquals(message, 'Lorem ipsum dolor sit amet, consectetur adipisicing elit #pdc #blah')
        
        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet7,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, True)
        self.assertEquals(message, 'scobleizer: Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod')
        
        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet8,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, True)
        self.assertEquals(message, 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod')
        
        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet9,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, True)
        self.assertEquals(message, 'blah: Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod')

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet10,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, False)
        self.assertEquals(message, 'ejacqui: Lorem dolor sit amet, consectetur adipisicing elit, sed do eiusmod #pdc08')

    def testTagStripping(self):
        "Test tag stripping"
        self.ta2.strip_tags = True
        self.ta2.save()
    
        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet1,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, False)
        self.assertEquals(message, 'mrkurt: tomorrow isn\'t just about infrastructure; it\'s about the user experience, etc..')

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet2,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, False)
        self.assertEquals(message, 'drpizza: er, the pricing should be competitive...')

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet3,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, False)
        self.assertEquals(message, 'arspdc: muglia is saying that this is the same scale as the 1992 introduction of NT')

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet4,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, False)
        self.assertEquals(message, self.test_tweet4)

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet5,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, False)
        self.assertEquals(message, 'kenfisher: There\'s a giant bouncy Channel 9 mascot')

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet6,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, False)
        self.assertEquals(message, 'Lorem ipsum dolor sit amet, consectetur adipisicing elit')

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet7,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, True)
        self.assertEquals(message, 'scobleizer: Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod')

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet8,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, True)
        self.assertEquals(message, 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod')

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet9,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, True)
        self.assertEquals(message, 'blah: Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod')

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet10,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, False)
        self.assertEquals(message, 'ejacqui: Lorem dolor sit amet, consectetur adipisicing elit, sed do eiusmod')
        
    def testReplyFiltering(self):
        "Test reply filtering"
        self.ta2.philter_replies = False
        self.ta2.save()
        
        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet1,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, False)
        self.assertEquals(message, 'mrkurt: tomorrow isn\'t just about infrastructure; it\'s about the user experience, etc.. #pdc2008')
        
        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet2,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, False)
        self.assertEquals(message, 'drpizza: er, the pricing should be competitive... #pdc2008')
        
        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet3,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, False)
        self.assertEquals(message, 'arspdc: muglia is saying that this is the same scale as the 1992 introduction of NT #pdc2008')
        
        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet4,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, False)
        self.assertEquals(message, self.test_tweet4)
        
        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet5,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, False)
        self.assertEquals(message, self.test_tweet5)
        
        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet6,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, False)
        self.assertEquals(message, 'Lorem ipsum dolor sit amet, consectetur adipisicing elit #pdc #blah')
        
        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet7,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, False)
        self.assertEquals(message, 'scobleizer: @arstest Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod')
        
        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet8,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, False)
        self.assertEquals(message, 'Lorem ipsum dolor sit amet, @arstest consectetur adipisicing elit, sed do eiusmod')
        
        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet9,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, False)
        self.assertEquals(message, 'blah: Lorem ipsum dolor sit amet, @arstest consectetur adipisicing elit, sed do eiusmod')

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet10,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, False)
        self.assertEquals(message, 'ejacqui: Lorem dolor sit amet, consectetur adipisicing elit, sed do eiusmod #pdc08')

    def testNamePrepending(self):
        "Test Name Prepending"     
        self.ta2.prepend_names = False
        self.ta2.save()
        
        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet1,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, False)
        self.assertEquals(message, 'tomorrow isn\'t just about infrastructure; it\'s about the user experience, etc.. #pdc2008')

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet2,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, False)
        self.assertEquals(message, 'er, the pricing should be competitive... #pdc2008')

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet3,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, False)
        self.assertEquals(message, 'muglia is saying that this is the same scale as the 1992 introduction of NT #pdc2008')

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet4,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, False)
        self.assertEquals(message, '@shadowbottle By doing stuff like letting the screen get dim and shipping better drivers')

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet5,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, False)
        self.assertEquals(message, 'There\'s a giant bouncy Channel 9 mascot #pdc2008 #pdc08')

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet6,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, False)
        self.assertEquals(message, 'Lorem ipsum dolor sit amet, consectetur adipisicing elit #pdc #blah')

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet7,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, True)
        self.assertEquals(message, 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod')

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet8,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, True)
        self.assertEquals(message, 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod')

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet9,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, True)
        self.assertEquals(message, 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod')

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet10,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, False)
        self.assertEquals(message, 'Lorem dolor sit amet, consectetur adipisicing elit, sed do eiusmod #pdc08')

    def testTagAppending(self):
        "Test tag appending"     
        self.ta2.append_tags = False
        self.ta2.save()

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet1,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, False)
        self.assertEquals(message, 'mrkurt: #pdc2008 tomorrow isn\'t just about infrastructure; it\'s about the user experience, etc..')

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet2,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, False)
        self.assertEquals(message, 'drpizza: #pdc2008 er, the pricing should be competitive...')

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet3,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, False)
        self.assertEquals(message, 'arspdc: #pdc2008 muglia is saying that this is the same scale as the 1992 introduction of NT')

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet4,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, False)
        self.assertEquals(message, self.test_tweet4)

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet5,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, False)
        self.assertEquals(message, self.test_tweet5)

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet6,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, False)
        self.assertEquals(message, 'Lorem ipsum dolor sit #pdc amet, #blah consectetur adipisicing elit')

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet7,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, True)
        self.assertEquals(message, 'scobleizer: Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod')

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet8,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, True)
        self.assertEquals(message, 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod')

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet9,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, True)
        self.assertEquals(message, 'blah: Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod')

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet10,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, False)
        self.assertEquals(message, 'ejacqui: Lorem #pdc08 dolor sit amet, consectetur adipisicing elit, sed do eiusmod')

    def testTagFilteringOneTag(self):
        "Test tag filters"  
        self.ta2.philter = '#pdc2008'
        self.ta2.save()
        
        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet1,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, True)
        self.assertEquals(message, 'mrkurt: tomorrow isn\'t just about infrastructure; it\'s about the user experience, etc.. #pdc2008')

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet2,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, True)
        self.assertEquals(message, 'drpizza: er, the pricing should be competitive... #pdc2008')

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet3,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, True)
        self.assertEquals(message, 'arspdc: muglia is saying that this is the same scale as the 1992 introduction of NT #pdc2008')

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet4,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, False)
        self.assertEquals(message, self.test_tweet4)

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet5,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, True)
        self.assertEquals(message, self.test_tweet5)

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet6,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, False)
        self.assertEquals(message, 'Lorem ipsum dolor sit amet, consectetur adipisicing elit #pdc #blah')

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet7,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, True)
        self.assertEquals(message, 'scobleizer: Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod')

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet8,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, True)
        self.assertEquals(message, 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod')

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet9,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, True)
        self.assertEquals(message, 'blah: Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod')

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet10,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, False)
        self.assertEquals(message, 'ejacqui: Lorem dolor sit amet, consectetur adipisicing elit, sed do eiusmod #pdc08')

    def testTagFilteringMultipleTags(self):
        "Test tag filters"  
        self.ta2.philter = '#pdc2008, #pdc08'
        self.ta2.save()

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet1,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, True)
        self.assertEquals(message, 'mrkurt: tomorrow isn\'t just about infrastructure; it\'s about the user experience, etc.. #pdc2008')

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet2,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, True)
        self.assertEquals(message, 'drpizza: er, the pricing should be competitive... #pdc2008')

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet3,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, True)
        self.assertEquals(message, 'arspdc: muglia is saying that this is the same scale as the 1992 introduction of NT #pdc2008')

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet4,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, False)
        self.assertEquals(message, self.test_tweet4)

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet5,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, True)
        self.assertEquals(message, self.test_tweet5)

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet6,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, False)
        self.assertEquals(message, 'Lorem ipsum dolor sit amet, consectetur adipisicing elit #pdc #blah')

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet7,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, True)
        self.assertEquals(message, 'scobleizer: Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod')

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet8,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, True)
        self.assertEquals(message, 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod')

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet9,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, True)
        self.assertEquals(message, 'blah: Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod')

        send_to_twitter, message = self.process(
            account = self.ta2,
            message = self.test_tweet10,
            created = datetime.datetime.now(),
            options = options,
        )
        self.assertEquals(send_to_twitter, True)
        self.assertEquals(message, 'ejacqui: Lorem dolor sit amet, consectetur adipisicing elit, sed do eiusmod #pdc08')