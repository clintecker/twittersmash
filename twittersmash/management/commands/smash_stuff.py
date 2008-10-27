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
tag_pat = r'\#([A-Za-z0-9]+)'
tag_re = re.compile(tag_pat)

class Command(BaseCommand):
    help = "Loops through feeds and determines if messages need to be sent to any twitter accounts"
    option_list = BaseCommand.option_list + (
        make_option('--dryrun', '-D', action='store_true', dest='dryrun', default=False,
            help='Go through the motions but commit nothing to Twitter'),
        make_option('--quiet', '-q', action='store_true', dest='quiet', default=False,
            help='Don\t print anything to console'),
        make_option('--debug', '-d', action='store_true', dest='debug', default=False,
            help='Return debugging information'),
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
            reply_re = re.compile(r'\@%s' % account.username)
            # Prepare keywords
            keywords = account.philter.lower().strip().split(',')
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
                        
                        if twit_re.search(entry.title) and not account.prepend_names:
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
                        tweeted_dt = datetime.datetime(
                            tweeted_dt_utc.utctimetuple()[0],
                            tweeted_dt_utc.utctimetuple()[1],
                            tweeted_dt_utc.utctimetuple()[2],
                            tweeted_dt_utc.utctimetuple()[3],
                            tweeted_dt_utc.utctimetuple()[4],
                            tweeted_dt_utc.utctimetuple()[5],
                        )
                        
                        msg, created = Message.objects.get_or_create(
                            guid=guid, 
                            twitter_account=account, 
                            defaults={
                                'feed': f, 
                                'tweeted': tweeted_dt,
                                'message': message,
                                'twitter_account': account,
                        })
                        
                        send_to_twitter = False
                        
                        if created:
                            messages_added += 1
                            
                            # Wasn't already in the db                        
                            if min_dt and tweeted_dt_utc <= min_dt:
                                if not quiet:
                                    print "   * Skipped because of time restrictions"
                            else:
                                # Check to see if this message contains any of the keywords
                                if keywords:
                                    for keyword in keywords:
                                        if keyword in message.lower():
                                            send_to_twitter = True
                                            break
                                else:
                                    send_to_twitter = True
                            
                                # Check to see if the message was directed at this account
                                if account.philter_replies:
                                    if reply_re.search(message):
                                        send_to_twitter = True
                                        message = reply_re.sub('', message).strip()
                                
                        if send_to_twitter:
                            
                            if account.strip_tags:
                                print "Removing tags"
                                message = tag_re.sub('', message)

                            if account.append_tags:
                                m = re.findall(tag_pat, message)
                                if m:
                                    # remove each hashtag
                                    for match in m:
                                        message = tag_re.sub('', message)
                                    # remove double spaces left from replacements
                                    message = message.replace('  ', ' ')
                                    # clean up whitespace
                                    message = message.strip()
                                    # append each tag to message
                                    for match in m:
                                        message += " #%s" % (match,)
                                        
                            # Clean up whitespace
                            message = message.strip()

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
            
