from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from twittersmash.models import Message, Feed, TwitterAccount

class MessageAdmin(admin.ModelAdmin):
    list_display = ('feed', 'message', 'tweeted', 'sent_to_twitter')

class FeedAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'last_checked', 'polling_rate')

class TwitterAccountAdmin(admin.ModelAdmin):
    list_display = ('username', 'philter', 'minimum_datetime', 'strip_tags', 'prepend_names', 'active')
   
admin.site.register(Message, MessageAdmin)
admin.site.register(Feed, FeedAdmin)
admin.site.register(TwitterAccount, TwitterAccountAdmin)
