from datetime import timedelta

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.utils import timezone


class Command(BaseCommand):
    help = 'Sends a test email to specified input email and template file with path, like "python3 manage.py testemail myemail@email.com registration/email/invited_user_message.html"'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str)
        parser.add_argument('file_name', type=str)

    def handle(self, *args, **options):
        email = options.get('email', None)
        file = options.get('file_name', None)
        current_site = Site.objects.get(id=1)
        context = {
            "password_reset_url": "{{ password_reset_url }}",
            "current_site": current_site,
        }
        subject_context = {
            "subject": "{{ subject }}"
        }
        html = render_to_string(file, context)
        subject = render_to_string(file.replace(
            "message.html", "subject.txt"), subject_context)
        subject = " ".join(subject.splitlines()).strip()
        send_mail(
            subject,
            'Email send as text not html.',
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
            html_message=html
        )
