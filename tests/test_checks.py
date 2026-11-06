import os

import psycopg
import pytest

from tender_wazi import checks


def make_ppip_row(source_id="ocid-1", title="Test PPIP title", **overrides):
    row = {
        "source": "ppip",
        "source_id": source_id,
        "title": title,
        "buyer_name": None,
        "category": "works",
        "category_raw": None,
        "notice_type": None,
        "procurement_method": "open",
        "status": None,
        "jurisdiction": "national",
        "published_at": None,
        "closing_at": None,
        "value_amount": None,
        "currency": None,
        "source_url": "https://tenders.go.ke/ocds/ocid-1",
    }
    row.update(overrides)
    return row


def make_portal_b_row(**overrides):
    row = {
        "source": "portal_b",
        "source_id": "KP1/6A.1/OT/9/26/C09",
        "title": "TEST TENDER",
        "buyer_name": "Kenya Power and Lighting Company",
        "category": "works",
        "category_raw": None,
        "notice_type": "Call for Tenders",
        "procurement_method": None,
        "status": None,
        "jurisdiction": "national",
        "published_at": None,
        "closing_at": None,
        "value_amount": None,
        "currency": None,
        "source_url": "https://kplc.co.ke/tender/KP1-6A.1-OT-9-26-C09",
    }
    row.update(overrides)
    return row


@pytest.fixture
def conn():
    connection = psycopg.connect(os.environ["DATABASE_URL_DIRECT"])
    yield connection
    connection.close()


# --- Row validation ------------------------------------------------------


def test_ppip_row_passes_validation():
    ok, errors = checks.validate_row("ppip", make_ppip_row())
    assert ok
    assert errors == []


def test_ppip_row_missing_title():
    ok, errors = checks.validate_row("ppip", make_ppip_row(title=None))
    assert not ok
    assert errors


def test_ppip_row_negative_amount():
    ok, errors = checks.validate_row("ppip", make_ppip_row(value_amount=-1))
    assert not ok
    assert errors


def test_ppip_row_unknown_currency():
    ok, errors = checks.validate_row("ppip", make_ppip_row(currency="XXX"))
    assert not ok
    assert errors


def test_ppip_row_unreadable_date():
    ok, errors = checks.validate_row("ppip", make_ppip_row(published_at="not a date"))
    assert not ok
    assert errors


def test_portal_b_row_passes_validation():
    ok, errors = checks.validate_row("portal_b", make_portal_b_row())
    assert ok
    assert errors == []


# --- Volume alert --------------------------------------------------------


def test_volume_alert_flags_low_volume():
    daily = [
        ("2026-01-01", 1000),
        ("2026-01-02", 1000),
        ("2026-01-03", 5),
    ]
    assert checks.volume_alert(daily) is True


def test_volume_alert_normal_volume():
    daily = [
        ("2026-01-01", 100),
        ("2026-01-02", 100),
        ("2026-01-03", 110),
    ]
    assert checks.volume_alert(daily) is False


# --- Schema drift --------------------------------------------------------


def test_schema_drift_passes():
    records = [
        {"source_id": "x", "title": "y",
         "published_at_raw": "01/01/2026", "closing_at_raw": "01/02/2026"},
        {"source_id": "x", "title": "y",
         "published_at_raw": "01/01/2026", "closing_at_raw": "01/02/2026"},
    ]
    result = checks.check_schema_drift(records)
    assert result["failed"] is False
    assert result["rates"]["source_id"] == 1.0


def test_schema_drift_fails_on_missing_field():
    records = [
        {"source_id": "x", "title": "y",
         "published_at_raw": "01/01/2026", "closing_at_raw": "01/02/2026"},
        {"source_id": "x", "title": "y"},
    ]
    result = checks.check_schema_drift(records)
    assert result["failed"] is True
    assert result["rates"]["published_at_raw"] == 0.5


# --- Record functions ----------------------------------------------------


def test_quality_run_recorded(conn):
    pk = checks.record_quality_run(
        conn,
        "ppip",
        True,
        "ok",
        {
            "null_rates": {},
            "duplicates": 0,
            "outliers": 0,
            "sector_spread": {},
        },
    )
    with conn.cursor() as cur:
        cur.execute("SELECT ok, message FROM quality_runs WHERE run_id = %s", (pk,))
        stored_ok, message = cur.fetchone()
    assert stored_ok
    assert message == "ok"


def test_rejects_recorded(conn):
    row = make_ppip_row()
    pk = checks.record_rejects(
        conn,
        "ppip",
        "ocid-1",
        None,
        row,
        "title must be present and non-empty",
    )
    with conn.cursor() as cur:
        cur.execute(
            "SELECT source, reason FROM rejects WHERE reject_id = %s", (pk,)
        )
        source, reason = cur.fetchone()
    assert source == "ppip"
    assert "title" in reason


# --- Table checks --------------------------------------------------------


def test_table_checks_null_rate(conn):
    from tender_wazi.store import store_batch

    store_batch(conn, [make_ppip_row("ppip-1", "First title")])
    tables = checks.table_checks(conn, "ppip")
    assert tables["null_rates"]["closing_at"] == 1.0
    assert tables["duplicates"] == 0


def test_table_checks_duplicate_open_versions(conn):
    from tender_wazi.store import store_batch

    store_batch(conn, [make_ppip_row("ppip-1", "First title")])
    store_batch(conn, [make_ppip_row("ppip-1", "Second title")])
    tables = checks.table_checks(conn, "ppip")
    assert tables["duplicates"] == 0  # the unique index keeps one open version
