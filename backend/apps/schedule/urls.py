# backend/apps/schedule/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SlotViewSet, ics_export

router = DefaultRouter()
router.register(r'slots', SlotViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('ics/', ics_export, name='schedule-ics'),
]
