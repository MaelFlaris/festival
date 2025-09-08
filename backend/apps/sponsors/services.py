# apps/sponsors/services.py
from __future__ import annotations

from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from django.conf import settings
from django.db.models import Sum

from .metrics import AMOUNT_SUM_EUR, VISIBLE_TOTAL
from .models import Sponsor, SponsorTier, Sponsorship

# ---- Webhook dispatch (fallback no-op) -------------------------------------

def _dispatch_webhook(event: str, payload: dict) -> None:
    try:
        from apps.common.services import dispatch_webhook  # type: ignore
    except Exception:
        dispatch_webhook = None
    if dispatch_webhook:
        try:
            dispatch_webhook(event, payload)
        except Exception:
            pass

# ---- Metrics recompute -----------------------------------------------------

def recompute_metrics():
    # Visible per tier
    for tier in SponsorTier.objects.all():
        cnt = Sponsorship.objects.filter(tier=tier, visible=True).count()
        VISIBLE_TOTAL.labels(tier_slug=tier.slug).set(cnt)
    # Amount per edition
    for ed in Sponsorship.objects.values_list("edition_id", flat=True).distinct():
        total = Sponsorship.objects.filter(edition_id=ed).aggregate(s=Sum("amount_eur"))["s"] or Decimal("0")
        AMOUNT_SUM_EUR.labels(edition=str(ed)).set(float(total))

# ---- Stats helpers ---------------------------------------------------------

def stats_summary(edition_id: Optional[int] = None) -> Dict:
    qs = Sponsorship.objects.select_related("tier").all()
    if edition_id:
        qs = qs.filter(edition_id=edition_id)

    by_tier = {}
    for s in qs:
        key = s.tier.slug
        item = by_tier.setdefault(key, {"tier": s.tier.display_name, "slug": s.tier.slug, "rank": s.tier.rank, "count": 0, "visible": 0, "amount_eur": 0.0})
        item["count"] += 1
        item["visible"] += 1 if s.visible else 0
        if s.amount_eur:
            item["amount_eur"] += float(s.amount_eur)

    total_amount = sum(v["amount_eur"] for v in by_tier.values())
    total_visible = sum(v["visible"] for v in by_tier.values())
    return {
        "edition": edition_id,
        "total_visible": total_visible,
        "total_amount_eur": round(total_amount, 2),
        "tiers": sorted(by_tier.values(), key=lambda x: x["rank"]),
    }

# ---- S3 presign (optional) -------------------------------------------------

def presign_contract_put(key: str, content_type: str) -> dict:
    try:
        import boto3
    except Exception:
        return {"supported": False, "reason": "boto3_not_installed"}

    bucket = getattr(settings, "SPONSORS_S3_BUCKET", None)
    region = getattr(settings, "SPONSORS_S3_REGION", None)
    prefix = getattr(settings, "SPONSORS_S3_PREFIX", "contracts/")
    if not bucket or not region:
        return {"supported": False, "reason": "missing_config"}

    s3 = boto3.client("s3", region_name=region)
    object_key = f"{prefix}{key}"
    url = s3.generate_presigned_url(
        ClientMethod="put_object",
        Params={"Bucket": bucket, "Key": object_key, "ContentType": content_type},
        ExpiresIn=900,
    )
    return {"supported": True, "url": url, "object_url": f"https://{bucket}.s3.{region}.amazonaws.com/{object_key}"}

# ---- Public grouping -------------------------------------------------------

def public_grouped_by_edition(edition_id: int) -> Dict:
    tiers = SponsorTier.objects.order_by("rank").all()
    items = []
    for t in tiers:
        sponsors = Sponsorship.objects.select_related("sponsor").filter(
            edition_id=edition_id, tier=t, visible=True
        ).order_by("order", "sponsor__name")
        sponsors_data = [
            {"id": sp.sponsor_id, "name": sp.sponsor.name, "logo": sp.sponsor.logo, "website": sp.sponsor.website}
            for sp in sponsors
        ]
        if sponsors_data:
            items.append({"tier": t.display_name, "slug": t.slug, "rank": t.rank, "sponsors": sponsors_data})
    return {"edition": edition_id, "tiers": items}
