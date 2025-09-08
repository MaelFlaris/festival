from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    FestivalEditionViewSet, VenueViewSet, 
    StageViewSet, ContactViewSet
)

router = DefaultRouter()
router.register(r'editions', FestivalEditionViewSet)
router.register(r'venues', VenueViewSet)
router.register(r'stages', StageViewSet)
router.register(r'contacts', ContactViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
