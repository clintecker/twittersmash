from django.core.management.base import BaseCommand

class Command(BaseCommand):
	help = "Deletes all messages "

	def handle(self, *args, **options):
		from smash.models import Message
		a = Message.objects.all()
		a.delete()