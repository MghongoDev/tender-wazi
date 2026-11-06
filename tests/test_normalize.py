from tender_wazi.normalize import (
    content_hash,
    jurisdiction,
    normalize_ppip,
    normalize_portal_b,
    parse_datetime,
)


def test_parse_datetime_reads_an_iso_string_with_an_offset():
    parsed = parse_datetime("2025-02-05T15:01:48+03:00")

    assert parsed is not None
    assert (parsed.year, parsed.month, parsed.day) == (2025, 2, 5)
    assert parsed.utcoffset().total_seconds() == 3 * 3600


def test_parse_datetime_reads_a_kenya_power_date():
    parsed = parse_datetime("03/11/2026")

    assert parsed is not None
    assert (parsed.day, parsed.month, parsed.year) == (3, 11, 2026)
    assert parsed.utcoffset().total_seconds() == 3 * 3600


def test_parse_datetime_reads_a_kenya_power_date_with_a_time():
    parsed = parse_datetime("03/12/2026, 10:00 am")

    assert parsed is not None
    assert (parsed.hour, parsed.minute) == (10, 0)


def test_parse_datetime_returns_none_for_input_it_cannot_read():
    assert parse_datetime(None) is None
    assert parse_datetime("") is None
    assert parse_datetime("not a date") is None


def test_jurisdiction_marks_a_county_buyer():
    assert jurisdiction("County Government of Nakuru") == "county"
    assert jurisdiction("Kenya National Library Service") == "national"
    assert jurisdiction(None) == "national"


def test_normalize_ppip_maps_the_fields():
    row = {
        "ocid": "ocds-5whusi-1",
        "buyer_name": "Kenya National Library Service",
        "title": "PROVISION OF GENERAL INSURANCE BROKERAGE SERVICES",
        "category_raw": "services",
        "procurement_method": "open",
        "published_at": "2025-02-05T15:01:48+03:00",
        "closing_at": "2021-06-10T00:00:00+03:00",
        "status": None,
        "value_amount": None,
        "currency": None,
    }

    out = normalize_ppip(row)

    assert out["source"] == "ppip"
    assert out["source_id"] == "ocds-5whusi-1"
    assert out["category"] == "services"
    assert out["jurisdiction"] == "national"
    assert out["published_at"] is not None
    assert out["source_url"] == "https://tenders.go.ke/ocds/ocds-5whusi-1"


def test_normalize_portal_b_maps_the_fields():
    row = {
        "source_id": "KP1/6A.1/OT/9/26/C09",
        "title": "TENDER DOCUMENT FOR PROCUREMENT OF DESIGN",
        "category_raw": None,
        "notice_type": None,
        "published_at_raw": "03/11/2026",
        "closing_at_raw": "03/12/2026, 10:00 am",
        "detail_url": "/tender/kp16a1ot926c09",
    }

    out = normalize_portal_b(row)

    assert out["source"] == "portal_b"
    assert out["source_id"] == "KP1/6A.1/OT/9/26/C09"
    assert out["buyer_name"] == "Kenya Power and Lighting Company"
    assert out["category"] == "other"
    assert out["published_at"] is not None
    assert out["closing_at"] is not None
    assert out["source_url"] == "https://kplc.co.ke/tender/kp16a1ot926c09"


def test_content_hash_is_stable_and_ignores_fetch_times():
    fields = {"title": "A", "buyer_name": "B", "closing_at": "2025-01-01T00:00:00+00:00"}

    assert content_hash(fields) == content_hash(dict(fields))
    assert content_hash({**fields, "fetched_at": "2026-01-01"}) == content_hash(fields)
