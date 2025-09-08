import subprocess
import time
import uuid

import pytest
from datetime import date
from django.core.cache import caches
from django.test import override_settings
from rest_framework.test import APIRequestFactory

from apps.core.models import FestivalEdition
from apps.cms.models import Page
from apps.cms.services import current_public_cache_version
from apps.cms.views import PublicPageViewSet


@pytest.fixture(scope="session")
def redis_url():
    """Start a disposable Redis container for cache testing."""
    name = f"test-redis-{uuid.uuid4().hex}"
    try:
        subprocess.run(
            ["docker", "run", "-d", "-p", "6380:6379", "--name", name, "redis:7-alpine"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip("Docker or Redis image not available")
    time.sleep(1)
    yield "redis://127.0.0.1:6380/0"
    subprocess.run(["docker", "rm", "-f", name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)


@pytest.fixture
def redis_cache(redis_url):
    with override_settings(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.redis.RedisCache",
                "LOCATION": redis_url,
            }
        }
    ):
        cache = caches["default"]
        cache.clear()
        yield cache
        cache.clear()


@pytest.mark.django_db
def test_public_pages_cache_invalidation(redis_cache):
    edition = FestivalEdition.objects.create(
        name="Ed 2025",
        year=2025,
        start_date=date(2025, 7, 1),
        end_date=date(2025, 7, 2),
    )
    page = Page.objects.create(
        edition=edition,
        slug="about",
        title="About",
        body_md="",
        status="published",
    )
    factory = APIRequestFactory()
    params = {"edition": str(edition.id)}
    view = PublicPageViewSet.as_view({"get": "list"})
    req1 = factory.get("/api/cms/public/pages/", params)
    resp1 = view(req1)
    assert resp1.status_code == 200
    assert resp1.data[0]["title"] == "About"
    v1 = current_public_cache_version()
    key1 = f"cms:pages:v{v1}:{hash(frozenset(params.items()))}"
    assert redis_cache.get(key1) is not None

    # Update page -> should bump cache version and invalidate
    page.title = "About Updated"
    page.save()
    v2 = current_public_cache_version()
    assert v2 > v1
    req2 = factory.get("/api/cms/public/pages/", params)
    resp2 = view(req2)
    assert resp2.status_code == 200
    assert resp2.data[0]["title"] == "About Updated"
    # Old cache remains but is versioned
    assert redis_cache.get(key1)[0]["title"] == "About"
