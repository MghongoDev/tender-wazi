import pytest

from tender_wazi.sources.portal_b import parse_detail, parse_listing


def read(name):
    with open(f"tests/fixtures/{name}", encoding="utf-8") as fh:
        return fh.read()


def test_parse_listing_reads_reference_title_and_detail_url():
    rows = parse_listing(read("kplc_tender_listing.html"))

    assert len(rows) == 9  # 12 entries, three of them repeated references
    ids = [row["source_id"] for row in rows]
    assert len(ids) == len(set(ids))
    assert rows[0]["source_id"] == "KP1/9A.2/OT/020/ICT/26-27"
    assert rows[0]["detail_url"].startswith("/tender/")


def test_parse_listing_strips_the_tender_number_prefix():
    rows = parse_listing(read("kplc_tender_listing.html"))

    assert all(not row["source_id"].lower().startswith("tender no") for row in rows)


def test_parse_detail_reads_the_fields():
    row = parse_detail(read("kplc_tender_detail.html"))

    assert row["source_id"] == "KP1/6A.1/OT/9/26/C09"
    assert "TENDER DOCUMENT" in row["title"]
    assert row["published_at_raw"] == "03/11/2026"
    assert row["closing_at_raw"].startswith("03/12/2026")
    assert row["category_raw"] is None
    assert row["notice_type"] is None
    assert any("01M6NFDQJ0SY06VTYH0BWF0J9D.pdf" in url for url in row["document_links"])


def test_parse_detail_on_a_broken_page_raises_a_clear_error():
    with pytest.raises(ValueError, match="reference"):
        parse_detail("<html><body>nothing here</body></html>")
