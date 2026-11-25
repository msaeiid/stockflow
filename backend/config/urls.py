"""URL configuration for StockFlow.

/api/...    REST API (inventory.urls, JWT auth, OpenAPI docs)
/admin/     Django admin
/static/    Django static files (WhiteNoise)
anything else: the React single-page app, when its build is present.
"""

from django.conf import settings
from django.contrib import admin
from django.http import FileResponse, Http404
from django.urls import include, path, re_path
from django.views.decorators.cache import never_cache
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


@never_cache
def spa_index(request, *args, **kwargs):
    """Serve the frontend's index.html for client-side routes (/login, /stock, ...)."""
    index = settings.FRONTEND_DIST / "index.html"
    if not index.is_file():
        raise Http404("Frontend build not found.")
    return FileResponse(index.open("rb"), content_type="text/html; charset=utf-8")


urlpatterns = [
    path("admin/", admin.site.urls),
    # Authentication endpoints (before the router include so they win)
    path("api/auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # API documentation endpoints
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("api/", include("inventory.urls")),
    # Everything that is not API, admin or static goes to the SPA.
    re_path(r"^(?!(?:api|admin|static)(?:/|$)).*$", spa_index, name="spa"),
]
