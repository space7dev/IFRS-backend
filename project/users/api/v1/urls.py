from rest_framework import routers

from django.urls import include, path, re_path
from django.views.generic import TemplateView

from .views import (
    ConfirmEmailView,
    LoginView,
    LogoutView,
    PasswordChangeView,
    PasswordResetConfirmView,
    PasswordResetView,
    RegisterView,
    TokenRefreshView,
    UserAdminViewSet,
    UserDetailsView,
)

router = routers.SimpleRouter()
router.register(r"users", UserAdminViewSet, basename="user")

api_patterns = [
    path("auth/", include([
        path("login/", LoginView.as_view(), name='rest_login'),
        path("logout/", LogoutView.as_view(), name='rest_logout'),
        path("password/change/", PasswordChangeView.as_view(),
             name='rest_password_change'),
        path("password/reset/", PasswordResetView.as_view(),
             name='rest_password_reset'),
        path("password/reset/confirm/", PasswordResetConfirmView.as_view(),
             name='rest_password_reset_confirm'),
        path("signup/", include([
            path("", RegisterView.as_view(), name='rest_register'),
            path("verify-email/", ConfirmEmailView.as_view(),
                 name='rest_verify_email'),

            # This url will be used for the email confirmation link sent to a user when registering
            re_path(
                r'^account-confirm-email/(?P<key>[-:\w]+)/$',
                TemplateView.as_view(),
                name='account_confirm_email'
            ),
        ])),
        path("token/refresh/", TokenRefreshView.as_view(), name='token_refresh'),
        path("user/", UserDetailsView.as_view(), name="rest_user_details"),
        path("", include('dj_rest_auth.urls')),
    ])),
]

api_patterns += router.urls
