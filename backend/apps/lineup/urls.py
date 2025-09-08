from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GenreViewSet, ArtistViewSet, ArtistAvailabilityViewSet

router = DefaultRouter()
router.register(r'genres', GenreViewSet, basename="lineup-genres")
router.register(r'artists', ArtistViewSet, basename="lineup-artists")
router.register(r'availabilities', ArtistAvailabilityViewSet, basename="lineup-availabilities")

urlpatterns = [
    path('', include(router.urls)),
]
