import pytest
from datetime import date
from django.db import IntegrityError
from rest_framework.test import APIRequestFactory

from .models import FestivalEdition, Venue, Stage
from .views import FestivalEditionViewSet
from .serializers import FestivalEditionSerializer
from .services import edition_activated


@pytest.mark.django_db
def test_edition_date_validation_in_serializer():
    data = {
        "name": "Édition Test",
        "year": 2026,
        "start_date": date(2026, 7, 10),
        "end_date": date(2026, 7, 9),  # invalid
        "tagline": "",
        "hero_image": "",
        "is_active": False,
    }
    ser = FestivalEditionSerializer(data=data)
    assert not ser.is_valid()
    assert "end_date" in ser.errors


@pytest.mark.django_db
def test_stage_unique_together():
    edition = FestivalEdition.objects.create(
        name="Base",
        year=2024,
        start_date=date(2024, 7, 1),
        end_date=date(2024, 7, 2),
    )
    venue = Venue.objects.create(name="Hall A")
    Stage.objects.create(edition=edition, venue=venue, name="Main")
    with pytest.raises(IntegrityError):
        Stage.objects.create(edition=edition, venue=venue, name="Main")


@pytest.mark.django_db
def test_unique_activation_via_serializer_and_signal():
    calls = []

    def _receiver(sender, instance, payload, **kwargs):
        calls.append(payload)

    edition_activated.connect(_receiver, dispatch_uid="test_activation_signal")

    e1 = FestivalEdition.objects.create(name="Edition 2024", year=2024, start_date=date(2024, 7, 1), end_date=date(2024, 7, 2), is_active=True)
    e2 = FestivalEdition.objects.create(name="Edition 2025", year=2025, start_date=date(2025, 7, 1), end_date=date(2025, 7, 2), is_active=False)
    assert e1.is_active is True
    assert e2.is_active is False

    # Activate e2 via serializer update
    ser = FestivalEditionSerializer(instance=e2, data={"is_active": True}, partial=True)
    assert ser.is_valid(), ser.errors
    e2 = ser.save()

    e1.refresh_from_db()
    e2.refresh_from_db()
    assert e2.is_active is True
    assert e1.is_active is False
    assert len(calls) >= 1
    assert calls[-1]["id"] == e2.id
    assert calls[-1]["year"] == 2025


@pytest.mark.django_db
def test_activate_view_action():
    e1 = FestivalEdition.objects.create(name="Edition 2024", year=2024, start_date=date(2024, 7, 1), end_date=date(2024, 7, 2), is_active=True)
    e2 = FestivalEdition.objects.create(name="Edition 2025", year=2025, start_date=date(2025, 7, 1), end_date=date(2025, 7, 2), is_active=False)

    factory = APIRequestFactory()
    view = FestivalEditionViewSet.as_view({"post": "activate"})
    request = factory.post(f"/api/core/editions/{e2.id}/activate/", {})
    response = view(request, pk=str(e2.id))
    assert response.status_code == 200

    e1.refresh_from_db()
    e2.refresh_from_db()
    assert e2.is_active is True
    assert e1.is_active is False
    
    
    @pytest.mark.django_db
def test_summary_action_minimal():
    e = FestivalEdition.objects.create(name="Edition 2026", year=2026, start_date=date(2026, 7, 1), end_date=date(2026, 7, 2))
    factory = APIRequestFactory()
    view = FestivalEditionViewSet.as_view({"get": "summary"})
    request = factory.get(f"/api/core/editions/{e.id}/summary/")
    response = view(request, pk=str(e.id))
    assert response.status_code == 200
    data = response.data
    assert data["edition"]["year"] == 2026
    assert "stages" in data and "slots" in data and "news" in data and "sponsors" in data and "tickets" in data

@pytest.mark.django_db
def test_i18n_localized_fallbacks():
    e = FestivalEdition.objects.create(
        name="Nom FR par défaut",
        year=2027,
        start_date=date(2027, 7, 1), end_date=date(2027, 7, 2),
        name_i18n={"en": "English Name"},
        tagline="Accroche FR",
        tagline_i18n={"en": "English Tagline"},
    )
    factory = APIRequestFactory()
    view = FestivalEditionViewSet.as_view({"get": "retrieve"})
    req_en = factory.get(f"/api/core/editions/{e.id}/", HTTP_ACCEPT_LANGUAGE="en")
    resp_en = view(req_en, pk=str(e.id))
    assert resp_en.data["name_localized"] == "English Name"
    assert resp_en.data["tagline_localized"] == "English Tagline"

    req_fr = factory.get(f"/api/core/editions/{e.id}/", HTTP_ACCEPT_LANGUAGE="fr")
    resp_fr = view(req_fr, pk=str(e.id))
    assert resp_fr.data["name_localized"] == "Nom FR par défaut"
    assert resp_fr.data["tagline_localized"] == "Accroche FR"

