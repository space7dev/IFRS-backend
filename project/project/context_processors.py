from django.conf import settings


# You can add more templates in the dict
def email(request):
    kwargs = {
        'email_contact': settings.CUSTOMER_SERVICE,
    }
    return kwargs
