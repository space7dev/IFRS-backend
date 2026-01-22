from django.core.management.base import BaseCommand
from model_definitions.models import ReportType


class Command(BaseCommand):
    help = 'Add disclosure_report for PAA model'

    def handle(self, *args, **options):
        report_type, created = ReportType.objects.get_or_create(
            batch_model='PAA',
            report_type='disclosure_report',
            defaults={
                'is_enabled': True,
                'notes': 'Flexible format for publishing required financial disclosures.'
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Created disclosure_report for PAA'
                )
            )
        else:
            if not report_type.is_enabled:
                report_type.is_enabled = True
                report_type.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Enabled disclosure_report for PAA'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'Disclosure report for PAA already exists and is enabled'
                    )
                )
