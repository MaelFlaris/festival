from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SponsorTierViewSet, SponsorViewSet, SponsorshipViewSet

router = DefaultRouter()
router.register(r'tiers', SponsorTierViewSet, basename="sponsors-tiers")
router.register(r'sponsors', SponsorViewSet, basename="sponsors-sponsors")
router.register(r'sponsorships', SponsorshipViewSet, basename="sponsors-sponsorships")

urlpatterns = [
    path('', include(router.urls)),
]
