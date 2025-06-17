from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Set site to production"

    def handle(self, *args, **kwargs):
        self.stdout.write("Setting site to production")
        mysite = Site.objects.get(pk=1)
        mysite.name = "production"
        mysite.domain = "example.com"
        mysite.save()
