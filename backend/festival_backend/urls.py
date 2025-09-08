# backend/festival_backend/urls.py
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def health(_): return JsonResponse({"status": "ok"})

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/core/", include("apps.core.urls")),
    path("api/v1/lineup/", include("apps.lineup.urls")),
    path("api/v1/schedule/", include("apps.schedule.urls")),
    path("api/v1/sponsors/", include("apps.sponsors.urls")),
    path("api/v1/tickets/", include("apps.tickets.urls")),
    path("api/v1/cms/", include("apps.cms.urls")),
    path("api/v1/health/", health),
]
