from rest_framework.permissions import BasePermission


class HasSessionUserIDHeader(BasePermission):
    """
    Allows requests with 'Session-User-ID' header
    """

    def has_permission(self, request, view):
        return bool(
            request.headers.get('Session-User-ID')
        )
