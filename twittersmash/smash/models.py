from django.db import models
from django.db.models import permalink
from django.utils.translation import gettext_lazy as _

class Feed(models.Model):
	"""A feed of tweets"""
	name = models.CharField(blank=True,  max_length=80)
	url = models.URLField(_('url'), blank=True, verify_exists=True)
	last_checked = models.DateTimeField(_('last checked'), blank=True, null=True)
	polling_rate = models.IntegerField(_('polling rate'), blank=True, null=True, default=15)

	class Meta:
		ordering = ['-last_checked',]
		verbose_name, verbose_name_plural = _('feed'), _('feeds')

	def __unicode__(self):
		return self.name

	def _get_absolute_url(self):
		return ('feed_detail', (), {})
	get_absolute_url = permalink(_get_absolute_url)

class Message(models.Model):
	"""A tweet, essentially. Used for caching, mostly."""
	feed = models.ForeignKey(Feed)
	tweeted = models.DateTimeField(_('tweeted'), blank=True, null=True)
	guid = models.CharField(_('guid'), blank=True,	max_length=255)
	message = models.CharField(_('message'), blank=True,  max_length=140)

	class Meta:
		ordering = ['-tweeted',]
		verbose_name, verbose_name_plural = _('message'), _('messages')

	def __unicode__(self):
		return self.message

	def _get_absolute_url(self):
		return ('message_detail', (), {})
	get_absolute_url = permalink(_get_absolute_url)

class TwitterAccount(models.Model):
	"""A Twitter account is fed by multiple twitter feeds"""
	username = models.CharField(_('username'), blank=True,	max_length=80)
	password = models.CharField(_('password'), blank=True,	max_length=80)
	feeds = models.ManyToManyField(Feed)

	class Meta:
		ordering = ['username',]
		verbose_name, verbose_name_plural = _('twitter account'), _('twitter accounts')

	def __unicode__(self):
		return self.username

	def _get_absolute_url(self):
		return ('twitteraccount_detail', (), {})
	get_absolute_url = permalink(_get_absolute_url)
