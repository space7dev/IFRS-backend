from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Set site to localhost"

    def handle(self, *args, **kwargs):
        self.stdout.write("Setting site to localhost:8000")
        mysite = Site.objects.get(pk=1)
        mysite.name = "localhost"
        mysite.domain = "localhost:8000"
        mysite.save()
