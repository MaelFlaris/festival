from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    GenreViewSet, ArtistViewSet, ArtistAvailabilityViewSet,
    GenreAdminViewSet, ArtistAdminViewSet, ArtistAvailabilityAdminViewSet,
)

router = DefaultRouter()
router.register(r'genres', GenreViewSet, basename="lineup-genres")
router.register(r'artists', ArtistViewSet, basename="lineup-artists")
router.register(r'availabilities', ArtistAvailabilityViewSet, basename="lineup-availabilities")

admin_router = DefaultRouter()
admin_router.register(r'genres', GenreAdminViewSet, basename="lineup-admin-genres")
admin_router.register(r'artists', ArtistAdminViewSet, basename="lineup-admin-artists")
admin_router.register(r'availabilities', ArtistAvailabilityAdminViewSet, basename="lineup-admin-availabilities")

urlpatterns = [
    path('', include(router.urls)),
    path('admin/', include(admin_router.urls)),
]
