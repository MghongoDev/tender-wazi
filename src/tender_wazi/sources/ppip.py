import json

from tender_wazi.http import PoliteClient
from tender_wazi.raw import save_raw

CATEGORY_MAP = {
    "goods": "goods",
    "works": "works",
    "services": "services",
    "consultancy": "consultancy",
    "consultancy services": "consultancy",
    "non consultancy services": "services",
    "non-consultancy services": "services",
}


def parse_line(line: str) -> dict:
    """Turn one OCDS contracting process (one JSONL line) into a flat dict."""
    cp = json.loads(line)
    tender = cp.get("tender") or {}
    buyer = cp.get("buyer") or {}
    if not buyer.get("name"):
        buyer = next(
            (p for p in cp.get("parties", []) if "buyer" in p.get("roles", [])), {}
        )
    value = tender.get("value") or {}
    period = tender.get("tenderPeriod") or {}
    return {
        "ocid": cp.get("ocid"),
        "buyer_name": buyer.get("name"),
        "title": tender.get("title"),
        "category_raw": tender.get("mainProcurementCategory"),
        "procurement_method": tender.get("procurementMethod"),
        "published_at": cp.get("date"),
        "closing_at": period.get("endDate"),
        "status": tender.get("status"),
        "value_amount": value.get("amount"),
        "currency": value.get("currency"),
    }


def normalize_category(raw: str | None) -> str:
    """Map the source's own category to the small normalized set."""
    if not raw:
        return "other"
    return CATEGORY_MAP.get(raw.strip().lower(), "other")


def download_year(conn, bucket, year: int) -> tuple[int, bytes]:
    """Fetch one year of the PPIP bulk file, save it raw, return its id and bytes."""
    url = f"https://data.open-contracting.org/en/publication/147/download?name={year}.jsonl.gz"
    response = PoliteClient().get(url)
    raw_id = save_raw(conn, bucket, "ppip", url, response.content, response.status_code)
    return raw_id, response.content
