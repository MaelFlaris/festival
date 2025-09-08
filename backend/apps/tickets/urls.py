from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TicketTypeViewSet

router = DefaultRouter()
router.register(r'types', TicketTypeViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
