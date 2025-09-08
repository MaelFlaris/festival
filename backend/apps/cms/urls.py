from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PageViewSet, FAQItemViewSet, NewsViewSet

router = DefaultRouter()
router.register(r'pages', PageViewSet)
router.register(r'faqs', FAQItemViewSet)
router.register(r'news', NewsViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
