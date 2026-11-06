import os

import psycopg
import pytest

from tender_wazi.store import store_batch


def make_row(source_id, title):
    return {
        "source": "test",
        "source_id": source_id,
        "title": title,
        "buyer_name": "Buyer",
        "category": "goods",
        "category_raw": "goods",
        "notice_type": None,
        "procurement_method": "open",
        "status": None,
        "jurisdiction": "national",
        "published_at": None,
        "closing_at": None,
        "value_amount": None,
        "currency": None,
        "source_url": f"https://example.test/{source_id}",
        "raw_id": None,
    }


@pytest.fixture
def conn():
    connection = psycopg.connect(os.environ["DATABASE_URL_DIRECT"])
    yield connection
    with connection.cursor() as cur:
        cur.execute("delete from tender_seen where source = 'test'")
        cur.execute("delete from tender_versions where source = 'test'")
    connection.commit()
    connection.close()


def test_a_changed_notice_creates_one_new_version(conn):
    store_batch(conn, [make_row("test-1", "First title")])
    store_batch(conn, [make_row("test-1", "Second title")])

    with conn.cursor() as cur:
        cur.execute(
            "select version_no, valid_to from tender_versions "
            "where source = 'test' and source_id = 'test-1' order by version_no"
        )
        rows = cur.fetchall()

    assert len(rows) == 2
    assert rows[0][1] is not None
    assert rows[1][1] is None


def test_an_unchanged_notice_creates_no_new_version(conn):
    store_batch(conn, [make_row("test-2", "Same title")])
    store_batch(conn, [make_row("test-2", "Same title")])

    with conn.cursor() as cur:
        cur.execute(
            "select count(*) from tender_versions where source = 'test' and source_id = 'test-2'"
        )
        assert cur.fetchone()[0] == 1


def test_tender_seen_records_the_first_and_last_run(conn):
    store_batch(conn, [make_row("test-3", "A title")])

    with conn.cursor() as cur:
        cur.execute(
            "select first_seen_at, last_seen_at from tender_seen "
            "where source = 'test' and source_id = 'test-3'"
        )
        first_seen, last_seen = cur.fetchone()

    assert first_seen is not None
    assert last_seen is not None
