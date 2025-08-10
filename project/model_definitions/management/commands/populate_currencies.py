from django.core.management.base import BaseCommand
from model_definitions.models import Currency


class Command(BaseCommand):
    help = 'Populate currency data'

    def handle(self, *args, **options):
        currencies_data = [
            ('USD', 'United States Dollar'),
            ('CAD', 'Canadian Dollar'),
            ('EUR', 'Euro'),
            ('GBP', 'British Pound Sterling'),
            ('JPY', 'Japanese Yen'),
            ('CNY', 'Chinese Yuan Renminbi'),
            ('AUD', 'Australian Dollar'),
            ('NZD', 'New Zealand Dollar'),
            ('CHF', 'Swiss Franc'),
            ('HKD', 'Hong Kong Dollar'),
            ('SGD', 'Singapore Dollar'),
            ('ZAR', 'South African Rand'),
            ('INR', 'Indian Rupee'),
            ('BRL', 'Brazilian Real'),
            ('BSD', 'Bahamian Dollar'),
            ('MXN', 'Mexican Peso'),
            ('NOK', 'Norwegian Krone'),
            ('SEK', 'Swedish Krona'),
            ('DKK', 'Danish Krone'),
            ('KRW', 'South Korean Won'),
            ('RUB', 'Russian Ruble'),
            ('AED', 'UAE Dirham'),
            ('SAR', 'Saudi Riyal'),
            ('TRY', 'Turkish Lira'),
            ('IDR', 'Indonesian Rupiah'),
            ('THB', 'Thai Baht'),
            ('PHP', 'Philippine Peso'),
            ('MYR', 'Malaysian Ringgit'),
            ('TWD', 'Taiwan Dollar'),
            ('PLN', 'Polish Zloty'),
            ('CZK', 'Czech Koruna'),
            ('HUF', 'Hungarian Forint'),
            ('ARS', 'Argentine Peso'),
            ('CLP', 'Chilean Peso'),
            ('COP', 'Colombian Peso'),
            ('EGP', 'Egyptian Pound'),
            ('NGN', 'Nigerian Naira'),
            ('PKR', 'Pakistani Rupee'),
            ('VND', 'Vietnamese Dong'),
            ('KES', 'Kenyan Shilling'),
            ('GHS', 'Ghanaian Cedi'),
            ('BDT', 'Bangladeshi Taka'),
            ('UYU', 'Uruguayan Peso'),
            ('BGN', 'Bulgarian Lev'),
            ('RON', 'Romanian Leu'),
            ('ISK', 'Icelandic Krona'),
            ('LKR', 'Sri Lankan Rupee'),
            ('MAD', 'Moroccan Dirham'),
            ('QAR', 'Qatari Riyal'),
            ('OMR', 'Omani Rial'),
        ]

        created_count = 0
        updated_count = 0

        for code, name in currencies_data:
            currency, created = Currency.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created currency: {code} - {name}')
                )
            else:
                if currency.name != name:
                    currency.name = name
                    currency.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'Updated currency: {code} - {name}')
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed currencies. Created: {created_count}, Updated: {updated_count}'
            )
        ) 