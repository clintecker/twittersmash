from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from smash.models import Message, Feed, TwitterAccount

class MessageAdmin(admin.ModelAdmin):
    list_display = ('feed', 'message', 'tweeted',)

class FeedAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'last_checked', 'polling_rate')

class TwitterAccountAdmin(admin.ModelAdmin):
    list_display = ('username',)
   
admin.site.register(Message, MessageAdmin)
admin.site.register(Feed, FeedAdmin)
admin.site.register(TwitterAccount, TwitterAccountAdmin)
