# backend/festival_backend/urls.py
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect

def health(_): return JsonResponse({"status": "ok"})

def metrics(_request):
    try:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    except Exception:
        return JsonResponse({"detail": "prometheus_client not installed"}, status=501)
    data = generate_latest()
    return HttpResponse(data, content_type=CONTENT_TYPE_LATEST)
# nouvel index API
def api_index(_request):
    return redirect("/api/v1/")

# index v1 lisible
def api_v1_index(request):
    base = request.build_absolute_uri("/")
    return JsonResponse({
        "version": "v1",
        "endpoints": {
            "core":     base + "api/v1/core/",
            "authx":    base + "api/v1/authx/",
            "lineup":   base + "api/v1/lineup/",
            "schedule": base + "api/v1/schedule/",
            "sponsors": base + "api/v1/sponsors/",
            "tickets":  base + "api/v1/tickets/",
            "cms":      base + "api/v1/cms/",
            "health":   base + "api/v1/health/",
            "api-auth": base + "api-auth/",
            "metrics":  base + "metrics/",
        }
    })

# DRF browsable API auth (login/logout)
# Use the official include with a proper namespace so templates can reverse
# 'rest_framework:login' and 'rest_framework:logout'.

urlpatterns = [
    path("admin/", admin.site.urls),

    # index API
    path("api/", api_index),        # <- /api redirige vers /api/v1/
    path("api/v1/", api_v1_index),  # <- /api/v1/ affiche une petite liste d’entrées

    # tes apps
    path("api/v1/core/", include("apps.core.urls")),
    path("api/v1/authx/", include("apps.authx.urls")),
    path("api/v1/lineup/", include("apps.lineup.urls")),
    path("api/v1/schedule/", include("apps.schedule.urls")),
    path("api/v1/sponsors/", include("apps.sponsors.urls")),
    path("api/v1/tickets/", include("apps.tickets.urls")),
    path("api/v1/cms/", include("apps.cms.urls")),
    path("api/v1/health/", health),

    # DRF login pour le browsable API
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),

    # métriques
    path("metrics/", metrics),  # si tu as ajouté la vue metrics
    path("api/common/", include("apps.common.urls")),
]
