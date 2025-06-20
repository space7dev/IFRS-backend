from dj_rest_auth.registration.views import (
    ConfirmEmailView as DjrestConfirmEmailView,
    RegisterView as DjrestRegisterView,
)
from dj_rest_auth.views import (
    LoginView as DjrestLoginView,
    LogoutView as DjrestLogoutView,
    PasswordChangeView as DjrestPasswordChangeView,
    PasswordResetConfirmView as DjrestPasswordResetConfirmView,
    PasswordResetView as DjrestPasswordResetView,
    UserDetailsView as DjrestUserDetailsView,
)
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import (
    TokenRefreshView as RestTokenRefreshView,
)

from django.contrib.auth import get_user_model
from django.http import HttpRequest, JsonResponse

from .permissions import IsAuthenticatedSuperuser
from .serializers import (
    AdminViewsUserSerializer,
    InviteUserSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetSerializer,
    SpoofUserSerializer,
    TokenRefreshSerializer,
    UserDetailsSerializer,
)

User = get_user_model()


class UserDetailsView(DjrestUserDetailsView):
    """
    Reads and updates User Model fields.

    Accepts GET, PUT, PATCH methods.
    Default accepted fields: username, first_name, last_name
    Default display fields: pk, username, email, first_name, last_name
    Read-only fields: pk, email

    Returns UserModel fields.
    """

    serializer_class = UserDetailsSerializer

    def put(self, request, *args, **kwargs):
        res = super().put(request, *args, **kwargs)
        if res.status_code == status.HTTP_200_OK:
            res.data = {
                "detail": "Changes saved successfully.",
                "user": res.data
            }
        return res

    def patch(self, request, *args, **kwargs):
        res = super().patch(request, *args, **kwargs)
        if res.status_code == status.HTTP_200_OK:
            res.data = {
                "detail": "Changes saved successfully.",
                "user": res.data
            }
        return res


class UserAdminViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedSuperuser]
    queryset = User.objects.all()
    http_method_names = ["get", "patch", "put", "delete", "post"]

    def get_serializer_class(self):
        if self.action == "create":
            return InviteUserSerializer
        elif self.action == "spoof":
            return SpoofUserSerializer

        return AdminViewsUserSerializer

    def create(self, request, *args, **kwargs):
        """
        Creates a new User instance and sends a link to set a password to the email address.

        Accept the following POST parameters: email*, role*, firstName, lastName
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save(request=request)
        res_serializer = AdminViewsUserSerializer(user)
        headers = self.get_success_headers(res_serializer.data)
        res = Response(
            res_serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )
        res.data = {
            "detail": "Email sent to user with invite link.", "user": res.data}

        return res

    def list(self, request, *args, **kwargs):
        res = super().list(request, *args, **kwargs)
        if res.status_code == status.HTTP_200_OK:
            res.data = {"detail": "Users list fetched.", "users": res.data}

        return res

    def retrieve(self, request, *args, **kwargs):
        res = super().retrieve(request, *args, **kwargs)
        if res.status_code == status.HTTP_200_OK:
            res.data = {"detail": "User instance fetched.", "user": res.data}

        return res

    def update(self, request, *args, **kwargs):
        # partial_update has the same response structure as update
        res = super().update(request, *args, **kwargs)
        if res.status_code == status.HTTP_200_OK:
            res.data = {
                "detail": "Changes saved successfully.", "user": res.data}

        return res

    def destroy(self, request, *args, **kwargs):
        res = super().destroy(request, *args, **kwargs)
        if res.status_code == status.HTTP_204_NO_CONTENT:
            res.status_code == status.HTTP_200_OK
            res.data = {"detail": "User deleted successfully."}

        return res

    @action(detail=True, methods=["patch"])
    def toggle_active(self, request, pk=None):
        user = self.get_object()
        if user != request.user and not user.is_superuser:
            user.is_active = not user.is_active
            user.save()
            serializer = self.get_serializer(user)
            res = Response(
                {
                    "detail": "User active state toggled successfully.",
                    "user": serializer.data,
                },
                status=status.HTTP_200_OK,
            )

            return res
        else:
            res = {
                "detail": "You are not allowed to activate/deactivate superusers or yourself."
            }
            return Response(res, status=status.HTTP_403_FORBIDDEN)

    @action(detail=True, methods=["post"])
    def spoof(self, request, pk=None):
        """
        Creates access and refresh tokens to spoof a target user so superusers (only) can
        impersonate said user and troubleshoot.

        Spoofing other superusers or inactive users is forbidden.
        """
        target_user = self.get_object()
        if target_user != request.user and not target_user.is_superuser:
            if target_user.is_active:
                refresh = RefreshToken.for_user(target_user)
                serializer = UserDetailsSerializer(target_user)
                res = Response(
                    {
                        "access_token": str(refresh.access_token),
                        "refresh_token": str(refresh),
                        "user": serializer.data,
                        "detail": "User spoofing successful",
                    },
                    status=status.HTTP_200_OK,
                )

                return res
            else:
                res = {"detail": "You are not allowed to spoof inactive users."}
                return Response(res, status=status.HTTP_403_FORBIDDEN)
        else:
            res = {
                "detail": "You are not allowed to spoof other superusers or yourself."
            }
            return Response(res, status=status.HTTP_403_FORBIDDEN)


"""
Custom All Auth Authentication and Registration Views

Reasons:
- Add or overwrite 'detail' property as a success message to display in FE.
- Change undesired default behavior
- Change docstring at will (reflects in API documentation or swagger)
"""


class LoginView(DjrestLoginView):
    """
    Check the credentials and return the REST Token
    if the credentials are valid and authenticated.
    Calls Django Auth login method to register User ID
    in Django session framework

    Accept the following POST parameters: email*, password*
    Return the REST Framework Token Object's key.
    """

    def get_response(self):
        res = super().get_response()
        if res.status_code == status.HTTP_200_OK:
            res.data["detail"] = "Login Successful."
            
            user_serializer = UserDetailsSerializer(self.user)
            res.data["user"] = user_serializer.data

        return res


class LogoutView(DjrestLogoutView):
    """
    Calls Django logout method and delete the Token object
    assigned to the current User object.
    """

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "refresh": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Refresh token to blacklist after logout.",
                ),
            },
        )
    )
    def post(self, request, *args, **kwargs):
        return self.logout(request)

    def logout(self, request):
        res = super().logout(request)
        if res.status_code == status.HTTP_200_OK:
            res.data["detail"] = "Logout Successful."

        return res


class PasswordChangeView(DjrestPasswordChangeView):
    """
    Calls Django Auth SetPasswordForm save method.

    Accepts the following POST parameters: new_password1, new_password2
    Returns the success/fail message.
    """

    def post(self, request, *args, **kwargs):
        res = super().post(request, *args, **kwargs)
        if res.status_code == status.HTTP_200_OK:
            res.data["detail"] = "New password has been set."

        return res


class PasswordResetView(DjrestPasswordResetView):
    """
    Calls Django Auth PasswordResetForm save method.

    Accepts the following POST parameters: email
    Returns the success/fail message.
    """

    serializer_class = PasswordResetSerializer

    def post(self, request, *args, **kwargs):
        res = super().post(request, *args, **kwargs)
        if res.status_code == status.HTTP_200_OK:
            res.data["detail"] = "Password reset e-mail has been sent."

        return res


class PasswordResetConfirmView(DjrestPasswordResetConfirmView):
    """
    Performs password reset link confirmation by checking
    uid and token, then resets the user password.

    Accepts the following POST parameters: token, uid, new_password1,
    new_password2

    Returns the success/fail message.
    """

    serializer_class = PasswordResetConfirmSerializer

    def post(self, request, *args, **kwargs):
        res = super().post(request, *args, **kwargs)
        if res.status_code == status.HTTP_200_OK:
            res.data["detail"] = "Your password was reset successfully."

        return res


class RegisterView(DjrestRegisterView):
    def create(self, request, *args, **kwargs):
        res = super().create(request, *args, **kwargs)
        if res.status_code == status.HTTP_201_CREATED:
            res.data[
                "detail"
            ] = "User registration successful. Email validation link sent."
            
            user_serializer = UserDetailsSerializer(self.user)
            res.data["user"] = user_serializer.data

        return res


class ConfirmEmailView(DjrestConfirmEmailView):
    def post(self, request, *args, **kwargs):
        res = super().post(request, *args, **kwargs)
        if res.status_code == status.HTTP_200_OK:
            res.data["detail"] = "Your email was verified successfully."

        return res


class TokenRefreshView(RestTokenRefreshView):
    """
    Using custom serializer to avoid refreshing access token for inactive or deleted
    users.
    """

    serializer_class = TokenRefreshSerializer
