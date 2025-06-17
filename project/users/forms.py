from allauth.account.adapter import get_adapter
from allauth.account.forms import (
    ResetPasswordForm as DefaultResetPasswordForm,
    default_token_generator as allauth_token_generator,
)
from allauth.account.utils import user_pk_to_url_str

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site

User = get_user_model()


class ResetPasswordForm(DefaultResetPasswordForm):
    """
    Modification of the Django password reset form (used by dj-rest-auth views)
    to encode the uid as b36 (instead of b64) and token with allauth token generator
    """

    def save(self, request, **kwargs):
        current_site = get_current_site(request)
        email = self.cleaned_data["email"]
        token_generator = allauth_token_generator

        for user in self.users:
            temp_key = token_generator.make_token(user)
            uid = user_pk_to_url_str(user)
            protocol = "https://" if request.is_secure() else "http://"
            url = f"{protocol}{current_site.domain}/password-recovery/confirm/{uid}/{temp_key}"
            context = {
                "current_site": current_site,
                "user": user,
                "password_reset_url": url,
                "request": request,
                "domain": current_site.domain,
                "protocol": protocol
            }
            get_adapter(request).send_mail(
                'account/email/password_reset', email, context)

        return self.cleaned_data["email"]
