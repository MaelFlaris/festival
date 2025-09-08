from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GenreViewSet, ArtistViewSet, ArtistAvailabilityViewSet

router = DefaultRouter()
router.register(r'genres', GenreViewSet)
router.register(r'artists', ArtistViewSet)
router.register(r'availabilities', ArtistAvailabilityViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
