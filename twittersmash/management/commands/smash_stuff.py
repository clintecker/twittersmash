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

# Parses the "Tweet Format" in Twitter RSS feeds
twit_re = re.compile(r'^(?P<username>\S+): (?P<message>.*)$')
# Parses out hashtags
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
        messages_sent = []
        accounts = TwitterAccount.objects.all().filter(active=True)
        feeds_to_mark_as_checked = []
        for account in accounts:
            api = twitter.Api(username=account.username, password=account.password)
            if not quiet:
                print "Checking %s" % (account,)
            feed_list = account.feeds.all()
            for f in feed_list:
                feeds_checked += 1
                if not quiet:
                    print " - %s" % (f,)
                # Get list of feeds whose last_update + polling_rate is less than now
                if f.last_checked == None or f.last_checked + \
                datetime.timedelta(minutes=f.polling_rate) < datetime.datetime.now() or \
                options.get('dryrun'):
                    accounts_ready += 1
                    feeds_to_mark_as_checked.append(f.id)
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
                        message = entry.title
                        # TODO: Should probably consider moving
                        #  to dateutil here
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
                            send_to_twitter, message = self.process_messages(
                                account=account,
                                source_feed = f,
                                message=message,
                                created=tweeted_dt_utc,
                                options=options
                            )
                        if send_to_twitter:
                            try:
                                if not options.get('dryrun'):
                                    status = api.PostUpdate(message[:139])
                                    if not quiet:
                                        print "   * Sent to Twitter: '%s' (%s)" % (message, account.philter.lower().strip(),)
                                else:
                                    if not quiet:
                                        print "   * Dry run: '%s' (%s)" % (message, account.philter.lower().strip(),)
                                entries_tweeted += 1
                                msg.sent_to_twitter = True
                                msg.save()
                            except Exception, e:
                                print "   - Failed to send to twitter (%s)" % (e,)
                else:
                    if not quiet:
                        print "   * Checked within the last %s minutes" % (f.polling_rate)
                    accounts_skipped += 1
        
        feeds_to_mark = Feed.objects.filter(id__in=feeds_to_mark_as_checked)
        
        if feeds_to_mark.count():
          feeds_to_mark.update(last_checked=datetime.datetime.now())

        if options.get('debug'):
            return {
                'entries_pulled': entries_pulled,
                'accounts_skipped': accounts_skipped,
                'accounts_ready': accounts_ready,
                'entries_tweeted': entries_tweeted,
                'feeds_pulled': feeds_pulled,
                'messages_added': messages_added,
                'feeds_checked': feeds_checked,
            }
           
    def process_messages(self, account, source_feed, message, created, options):
        """
        This method determines whether or not a message should be sent
        to Twitter.  If needed, filters and munging are applied as well.
        
        `account` - A Twitter account instance
        `message` - The text of a single tweet
        `created` - The date/time at which a Tweet was Tweeted
        `options` - A dict of options, the only values used here are 'quiet' 
                    to suppress output.
        """
        send_to_twitter = False
        quiet = options.get('quiet')
        reply_re = re.compile(r'\@%s' % account.username)
        
        # Prepare keywords
        keywords = account.philter.lower().strip().split(',')
        keywords = map(string.strip, keywords)
        if keywords == ['']: keywords = []
        
        # Prep minimum DT
        if account.minimum_datetime:
            # Stored value here is UTC
            min_dt = utc.localize(account.minimum_datetime)
        else:
            min_dt = None
            
        # Wasn't already in the db                        
        if min_dt and created <= min_dt:
            if not quiet:
                print "   * Skipped because of time restrictions"
        else:
            # Remove userames if needed
            if twit_re.search(message) and not account.prepend_names:
                message = twit_re.search(message).groups()[1]
            
            if account.prepend_names:
                message = "@" + message
             
            # Check to see if this message contains any of the keywords
            if keywords:
                for keyword in keywords:
                    kpat = re.compile(r'%s(\s|$)' % keyword)
                    if kpat.search(message):
                        send_to_twitter = True
                        break
            else:
                send_to_twitter = False
    
            # Check to see if the message was directed at this account
            if account.philter_replies:
                if reply_re.search(message):
                    send_to_twitter = True
                    message = reply_re.sub('', message).strip()

            # TODO Strip Keywords only
            if account.strip_tags:
                if not quiet:
                    print "   * Removing tags"
                    print "     - (%s)(\s|$)" % ('|'.join(keywords),)
                
                message = re.sub(r'(%s)(\s|$)' % ('|'.join(keywords),), '', message)
                
            if account.append_tags:
                m = re.findall(tag_pat, message)
                if m:
                    # remove each hashtag
                    for match in m:
                        message = tag_re.sub('', message)
                    # clean up whitespace
                    message = message.strip()
                    # append each tag to message
                    for match in m:
                        message += " #%s" % (match,)

            if account.append_initials and source_feed.initials:
                message += " ^%s" % source_feed.initials

            # Clean up whitespace
            message = message.strip()
            # Remove double spaces left from replacements
            message = message.replace('  ', ' ')
            
        return send_to_twitter, message