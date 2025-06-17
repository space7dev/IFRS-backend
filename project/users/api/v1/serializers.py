from allauth.account.adapter import get_adapter
from allauth.account.forms import (
    default_token_generator as allauth_token_generator,
)
from allauth.account.models import EmailAddress
from allauth.account.utils import (
    filter_users_by_email,
    url_str_to_user_pk,
    user_pk_to_url_str,
)
from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import (
    PasswordResetConfirmSerializer as DjrestPasswordResetConfirmSerializer,
    PasswordResetSerializer as DjrestPasswordResetSerializer,
)
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.exceptions import (
    AuthenticationFailed,
    InvalidToken,
    TokenBackendError,
)
from rest_framework_simplejwt.serializers import (
    TokenRefreshSerializer as RestTokenRefreshSerializer,
)
from rest_framework_simplejwt.state import token_backend

from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site
from django.db import transaction

from users.forms import ResetPasswordForm

from .fields import ChoiceField

User = get_user_model()

"""
User model serializers
"""


class AdminViewsUserSerializer(serializers.ModelSerializer):
    role = ChoiceField(choices=User.ROLE_CHOICES)

    class Meta:
        model = User
        fields = [
            'id',
            'first_name',
            'last_name',
            'email',
            'role',
            'is_active',
            'date_joined',
            'is_superuser',
            'is_staff'
        ]
        read_only_fields = ['date_joined', 'is_active',]


class InviteUserSerializer(serializers.ModelSerializer):
    role = ChoiceField(choices=User.ROLE_CHOICES, required=False)

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'role',
        ]
        extra_kwargs = {'email': {'required': True}}

    def validate_email(self, value):
        email = get_adapter().clean_email(value)
        self.users = filter_users_by_email(email)
        if self.users:
            raise ValidationError(
                "This email address is already in use by another user.")
        return email

    def create(self, validated_data):
        # Overriden to avoid duplicated empty username constraint
        return User(**validated_data)

    @transaction.atomic
    def save(self, **kwargs):
        """
        Create a new User instance and send a password set email.
        """
        request = kwargs.get("request")
        user = super().save()
        get_adapter(request).populate_username(request, user)
        user.save()
        EmailAddress.objects.create(
            user=user, email=user.email, primary=True, verified=False)
        self._send_invitation_link(user=user, request=request)
        return user

    def _send_invitation_link(self, user, request, **kwargs):
        """
        Send a link to the user after being invited to the site
        to Set the password when clicked. (Using allauth patterns)
        """
        current_site = get_current_site(request)
        email = self.validated_data["email"]
        token_generator = kwargs.get(
            "token_generator", allauth_token_generator)
        temp_key = token_generator.make_token(user)
        protocol = "https://" if request.is_secure() else "http://"
        uid = user_pk_to_url_str(user)
        url = f"{protocol}{current_site.domain}/password-recovery/confirm/{uid}/{temp_key}"
        context = {
            "current_site": current_site,
            "user": user,
            "password_reset_url": url,
            "request": request,
        }
        # Send the password reset email
        get_adapter(request).send_mail(
            "account/email/user_invite", email, context)


class SpoofUserSerializer(serializers.Serializer):
    pass


class UserRegisterSerializer(RegisterSerializer):

    def get_cleaned_data(self):
        data_dict = super().get_cleaned_data()
        return data_dict


class UserDetailsSerializer(serializers.ModelSerializer):
    role = ChoiceField(choices=User.ROLE_CHOICES)
    is_administrator = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'first_name',
            'last_name',
            'email',
            'role',
            'is_administrator'
        ]
        read_only_fields = ['role', 'is_administrator']

    def get_is_administrator(self, obj):
        return obj.is_administrator()


"""
Custom Serializers for overriden views (Dj-Rest-Auth)
"""


class PasswordResetSerializer(DjrestPasswordResetSerializer):
    password_reset_form_class = ResetPasswordForm

    def validate_email(self, value):
        self.reset_form = self.password_reset_form_class(
            data=self.initial_data)
        if not self.reset_form.is_valid():
            raise serializers.ValidationError(self.reset_form.errors["email"])

        return value


class PasswordResetConfirmSerializer(DjrestPasswordResetConfirmSerializer):
    """
    Serializer to request a password reset e-mail. This Serializer is
    modified to decode the b36 uid encoding instead of using b64 decoding
    to make it compatible with allauth implementation
    """

    def validate(self, attrs):
        self._errors = {}
        default_token_generator = allauth_token_generator

        # Decode the uidb36 to uid to get User object
        try:
            uid = url_str_to_user_pk(attrs['uid'])
            self.user = User._default_manager.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise ValidationError(
                {'uid': ['The password reset link has expired. Please request a new one.']})

        self.custom_validation(attrs)
        # Create SetPasswordForm instance
        self.set_password_form = self.set_password_form_class(
            user=self.user, data=attrs
        )
        if not self.set_password_form.is_valid():
            raise serializers.ValidationError(self.set_password_form.errors)
        if not default_token_generator.check_token(self.user, attrs['token']):
            raise ValidationError(
                {'token': ['The password reset link has expired. Please request a new one.']})
        else:
            # activate user
            self.user.is_active = True
            self.user.save()

        return attrs


class TokenRefreshSerializer(RestTokenRefreshSerializer):
    """
    Inherit from `TokenRefreshSerializer` and touch the database
    before re-issuing a new access token and ensure that the user
    exists and is active.
    Source: https://github.com/jazzband/djangorestframework-simplejwt/issues/193
    """

    error_msg = 'There was an error with your request, check your credentials and try again'

    def validate(self, attrs):
        try:
            token_payload = token_backend.decode(attrs['refresh'])
        except TokenBackendError:
            raise InvalidToken()

        try:
            user = get_user_model().objects.get(pk=token_payload['user_id'])
        except get_user_model().DoesNotExist:
            raise AuthenticationFailed(
                self.error_msg, 'no_active_account'
            )

        if not user.is_active:
            raise AuthenticationFailed(
                self.error_msg, 'no_active_account'
            )

        return super().validate(attrs)
