import twitter
import datetime
import feedparser
import re
import string
from django.core.management.base import BaseCommand
from optparse import make_option
from twittersmash.models import Feed, TwitterAccount, Message

import pytz
from pytz import timezone

central = timezone('US/Central')
utc = pytz.utc

twit_re = re.compile(r'^(?P<username>\S+): (?P<message>.*)$')
tag_re = re.compile(r'\#([A-Za-z0-9]+)')

class Command(BaseCommand):
    help = "Loops through feeds and determines if messages need to be sent to any twitter accounts"
    option_list = BaseCommand.option_list + (
        make_option('--dryrun', '-d', action='store_true', dest='dryrun', default=False,
            help='Go through the motions but commit nothing to Twitter'),
        make_option('--quiet', '-q', action='store_true', dest='quiet', default=False,
            help='Don\t print anything to console'),
    )

    def handle(self, *args, **options):
        # Get list of TwitterAccounts
        quiet = options.get('quiet')
        entries_pulled = 0
        accounts_skipped = 0
        accounts_ready = 0
        entries_tweeted = 0
        feeds_pulled = 0
        messages_added = 0
        feeds_checked = 0
        accounts = TwitterAccount.objects.all().filter(active=True)
        for account in accounts:
            # Prepare keywords
            keywords = account.philter.lower().split(',')
            keywords = map(string.strip, keywords)
            # Prep minimum DT
            if account.minimum_datetime:
                # Stored value here is UTC
                min_dt = utc.localize(account.minimum_datetime)
            else:
                min_dt = None
            api = twitter.Api(username=account.username, password=account.password)
            if not quiet:
                print "Checking %s" % (account,)
            feed_list = account.feeds.all()
            for f in feed_list:
                feeds_checked += 1
                if not quiet:
                    print " - %s" % (f,)
                # Get list of feeds who'se last_update + polling_rate is less than now
                if f.last_checked == None or f.last_checked + \
                datetime.timedelta(minutes=f.polling_rate) < datetime.datetime.now():
                    accounts_ready += 1
                    # Update timestamp
                    f.last_checked = datetime.datetime.now()
                    f.save()
                    if not quiet:
                        print "   * Pulling feed"
                    # Pull each feed
                    d = feedparser.parse(f.url)
                    feeds_pulled += 1
                    # Loop through feed
                    d.entries.reverse()
                    for entry in d['entries']:
                        entries_pulled += 1
                        guid = entry.id
                        tweeted = entry.updated_parsed
                        if twit_re.search(entry.title):
                            message = twit_re.search(entry.title).groups()[1]
                        else:
                            message = entry.title
                        #print guid, tweeted, message
                        tweeted_dt = datetime.datetime(
                            tweeted[0], 
                            tweeted[1], 
                            tweeted[2], 
                            tweeted[3], 
                            tweeted[4], 
                            tweeted[5], 
                            tzinfo=None
                        )
                        tweeted_dt_cst = central.localize(tweeted_dt)
                        tweeted_dt_utc = tweeted_dt_cst.astimezone(utc)
                        
                        
                        msg, created = Message.objects.get_or_create(
                            guid=guid, 
                            twitter_account=account, 
                            defaults={
                                'feed': f, 
                                'tweeted': tweeted_dt_utc,
                                'message': message,
                                'twitter_account': account,
                        })
                        
                        if created:
                            messages_added += 1
                            # Wasn't already in the db                        
                            if min_dt and tweeted_dt_utc <= min_dt:
                                if not quiet:
                                    print "   * Skipped because of time restrictions"
                                continue
                            for keyword in keywords:
                                if keyword in message.lower():
                                    if account.strip_tags:
                                        print "Removing tags"
                                        # Remove any hashtags
                                        message = tag_re.sub('', message)
                                    # We need to send it to the twitter account
                                    try:
                                        if not options.get('dryrun'):
                                            status = api.PostUpdate(message)
                                            if not quiet:
                                                print "   * Sent to Twitter: '%s' (%s)" % (message, keyword,)
                                        else:
                                            if not quiet:
                                                print "   * Dry run: '%s' (%s)" % (message, keyword,)
                                        entries_tweeted += 1
                                        msg.sent_to_twitter = True
                                        msg.save()
                                    except e:
                                        if not quiet:
                                            print "   - Failed to send to twitter (%s)" % (e,)
                else:
                    if not quiet:
                        print "   * Checked within the last %s minutes" % (f.polling_rate)
                    accounts_skipped += 1
        return {
            'entries_pulled': entries_pulled,
            'accounts_skipped': accounts_skipped,
            'accounts_ready': accounts_ready,
            'entries_tweeted': entries_tweeted,
            'feeds_pulled': feeds_pulled,
            'messages_added': messages_added,
            'feeds_checked': feeds_checked,
        }
            
