from rest_framework.permissions import BasePermission

from users.models import User


class IsAuthenticatedSuperuser(BasePermission):
    """
    Allows access only to admin users.
    """

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == User.ADMIN
        )


class IsAnonymous(BasePermission):
    """
    Allows access only to anonymous users.
    """

    def has_permission(self, request, view):
        return bool(
            request.user and not
            request.user.is_authenticated
        )
