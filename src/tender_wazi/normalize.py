import hashlib
import json
from datetime import datetime, timedelta, timezone

from tender_wazi.sources.ppip import normalize_category

NAIROBI = timezone(timedelta(hours=3))

BUSINESS_FIELDS = (
    "title",
    "buyer_name",
    "category",
    "category_raw",
    "notice_type",
    "procurement_method",
    "status",
    "jurisdiction",
    "published_at",
    "closing_at",
    "value_amount",
    "currency",
    "source_url",
)


def parse_datetime(raw):
    """Read an ISO string with an offset, or a Kenya Power DD/MM/YYYY date."""
    if not raw:
        return None
    raw = raw.strip()
    try:
        parsed = datetime.fromisoformat(raw)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=NAIROBI)
    except ValueError:
        pass
    for fmt in ("%d/%m/%Y", "%d/%m/%Y, %I:%M %p", "%d/%m/%Y %H:%M"):
        try:
            return datetime.strptime(raw, fmt).replace(tzinfo=NAIROBI)
        except ValueError:
            continue
    return None


def jurisdiction(buyer_name):
    """National unless the buyer name names a county."""
    if buyer_name and "county" in buyer_name.lower():
        return "county"
    return "national"


def content_hash(fields):
    """Hash the business fields only, so re-fetching an unchanged notice matches."""
    payload = json.dumps(
        {key: str(fields.get(key)) for key in BUSINESS_FIELDS}, sort_keys=True
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def normalize_ppip(row):
    return {
        "source": "ppip",
        "source_id": row["ocid"],
        "title": row.get("title"),
        "buyer_name": row.get("buyer_name"),
        "category": normalize_category(row.get("category_raw")),
        "category_raw": row.get("category_raw"),
        "notice_type": None,
        "procurement_method": row.get("procurement_method"),
        "status": row.get("status"),
        "jurisdiction": jurisdiction(row.get("buyer_name")),
        "published_at": parse_datetime(row.get("published_at")),
        "closing_at": parse_datetime(row.get("closing_at")),
        "value_amount": row.get("value_amount"),
        "currency": row.get("currency"),
        "source_url": f"https://tenders.go.ke/ocds/{row['ocid']}",
    }


def normalize_portal_b(row):
    return {
        "source": "portal_b",
        "source_id": row["source_id"],
        "title": row.get("title"),
        "buyer_name": "Kenya Power and Lighting Company",
        "category": normalize_category(row.get("category_raw")),
        "category_raw": row.get("category_raw"),
        "notice_type": row.get("notice_type"),
        "procurement_method": None,
        "status": None,
        "jurisdiction": "national",
        "published_at": parse_datetime(row.get("published_at_raw")),
        "closing_at": parse_datetime(row.get("closing_at_raw")),
        "value_amount": None,
        "currency": None,
        "source_url": f"https://kplc.co.ke{row['detail_url']}",
    }
