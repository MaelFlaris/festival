from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SponsorTierViewSet, SponsorViewSet, SponsorshipViewSet

router = DefaultRouter()
router.register(r'tiers', SponsorTierViewSet)
router.register(r'sponsors', SponsorViewSet)
router.register(r'sponsorships', SponsorshipViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
