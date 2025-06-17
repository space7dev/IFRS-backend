from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('backend/', include([
        path('admin/', include('admin_honeypot.urls', namespace='admin_honeypot')),
        path('411/', admin.site.urls),
        # API Urls set
        path("api/", include("api.urls")),
        path("users/", include("users.urls")),
    ])),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
