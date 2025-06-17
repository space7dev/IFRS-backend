from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Set site to staging"

    def handle(self, *args, **kwargs):
        self.stdout.write("Setting site to staging")
        mysite = Site.objects.get(pk=1)
        mysite.name = "staging"
        mysite.domain = "staging.example.com"
        mysite.save()
