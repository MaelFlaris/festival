# apps/common/urls.py
from django.urls import path
from .views import AddressValidateView, SlugPreviewView

urlpatterns = [
    path("address/validate", AddressValidateView.as_view(), name="common-address-validate"),
    path("slug/preview", SlugPreviewView.as_view(), name="common-slug-preview"),
]
