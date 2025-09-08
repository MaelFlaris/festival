from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PageViewSet, FAQItemViewSet, NewsViewSet,
    PublicPageViewSet, PublicNewsViewSet,
    preview_create, preview_resolve, sitemap_edition,
)

router = DefaultRouter()
router.register(r'pages', PageViewSet, basename="cms-pages")
router.register(r'faqs', FAQItemViewSet, basename="cms-faqs")
router.register(r'news', NewsViewSet, basename="cms-news")

public = DefaultRouter()
public.register(r'pages', PublicPageViewSet, basename="cms-public-pages")
public.register(r'news', PublicNewsViewSet, basename="cms-public-news")

urlpatterns = [
    path('', include(router.urls)),
    path('public/', include(public.urls)),
    path('preview', preview_create, name="cms-preview-create"),
    path('preview/resolve', preview_resolve, name="cms-preview-resolve"),
    path('sitemap/<int:edition_id>.xml', sitemap_edition, name="cms-sitemap-edition"),
]
