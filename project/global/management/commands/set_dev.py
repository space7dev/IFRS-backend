from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Set site to development API scaffold"

    def handle(self, *args, **kwargs):
        self.stdout.write("Setting site to vue.ideamaker.agency")
        mysite = Site.objects.get(pk=1)
        mysite.name = "Dev API Scaffold"
        mysite.domain = "vue.ideamaker.agency"
        mysite.save()
