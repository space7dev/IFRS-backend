from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

from django.contrib.sites.shortcuts import get_current_site


class AccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        user = super(AccountAdapter, self).save_user(
            request, user, form, commit)
        user.phone = form.cleaned_data.get("phone", None)
        user.save()
        return user

    def get_email_confirmation_url(self, request, emailconfirmation):
        """Constructs the email confirmation (activation) url.
        """
        current_site = get_current_site(request)
        protocol = "https://" if request.is_secure() else "http://"
        url = f"{protocol}{current_site.domain}/confirm-email/{emailconfirmation.key}/"

        return url


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    pass
