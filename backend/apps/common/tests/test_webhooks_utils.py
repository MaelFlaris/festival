from __future__ import annotations

import base64
import hashlib
import hmac
from unittest.mock import patch

from django.test import TestCase, override_settings

from apps.common import services as common_services


class WebhookUtilsTests(TestCase):
    def test_signature_header_ok(self):
        secret = "shh"
        url = "http://example.com/hook"
        payload = {"hello": "world"}

        captured = {}

        def fake_urlopen(req, timeout=None):
            captured["headers"] = dict(req.headers)
            captured["data"] = req.data
            class R:
                headers = {}
            return R()

        with override_settings(COMMON_WEBHOOK_URLS=[url], COMMON_WEBHOOK_SECRET=secret):
            with patch.object(common_services._urlreq, "urlopen", side_effect=fake_urlopen):
                common_services.dispatch_webhook("evt", payload)

        body = captured["data"]
        mac = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).digest()
        expected = "sha256=" + base64.b16encode(mac).decode("ascii").lower()
        assert captured["headers"]["X-Common-Signature"] == expected
        assert captured["headers"]["X-Common-Event"] == "evt"

    def test_bad_scheme_ignored(self):
        with override_settings(COMMON_WEBHOOK_URLS=["ftp://invalid"], COMMON_WEBHOOK_SECRET=None):
            with patch.object(common_services._urlreq, "urlopen") as mocked:
                common_services.dispatch_webhook("evt", {"x": 1})
                mocked.assert_not_called()

    def test_timeout_no_raise(self):
        with override_settings(COMMON_WEBHOOK_URLS=["http://example.org/h"], COMMON_WEBHOOK_SECRET=None):
            with patch.object(common_services._urlreq, "urlopen", side_effect=Exception("timeout")):
                # Should not raise
                common_services.dispatch_webhook("evt", {"x": 1})

