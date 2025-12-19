from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from .views import home

_V1_PATTERNS = [
    path("api/v1/", include("cellular.api.v1.urls")),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'), 
    # --- Swagger / OpenAPI (v1) ---
    path("api/v1/schema/", SpectacularAPIView.as_view(patterns=_V1_PATTERNS), name="schema-v1"),
    path(
        "api/v1/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema-v1"),
        name="swagger-ui-v1",
    ),
    path(
        "api/v1/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema-v1"),
        name="redoc-v1",
    ),

    # --- Legacy schema redirects (keep old URLs working) ---
    path("api/schema/", RedirectView.as_view(pattern_name="schema-v1", permanent=False), name="schema"),
    path(
        "api/schema/swagger-ui/",
        RedirectView.as_view(pattern_name="swagger-ui-v1", permanent=False),
        name="swagger-ui",
    ),
    path("api/schema/redoc/", RedirectView.as_view(pattern_name="redoc-v1", permanent=False), name="redoc"),

    # --- API endpoints ---
    path("api/v1/", include("cellular.api.v1.urls")),
    path("api/", include("cellular.urls")),  # legacy alias
]
