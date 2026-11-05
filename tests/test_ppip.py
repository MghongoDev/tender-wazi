from tender_wazi.sources.ppip import normalize_category, parse_line


def first_line():
    with open("tests/fixtures/ppip_2025_sample.jsonl", encoding="utf-8") as fh:
        return fh.readline()


def test_parse_line_reads_the_ocid_buyer_and_title():
    row = parse_line(first_line())

    assert row["ocid"] == "ocds-5whusi-062929"
    assert row["buyer_name"] == "Kenya National Library Service"
    assert row["title"] == "PROVISION OF GENERAL INSURANCE BROKERAGE SERVICES"


def test_parse_line_reads_the_category_and_method():
    row = parse_line(first_line())

    assert row["category_raw"] == "services"
    assert row["procurement_method"] == "open"


def test_parse_line_reads_the_published_and_closing_dates():
    row = parse_line(first_line())

    assert row["published_at"] == "2025-02-05T15:01:48+03:00"
    assert row["closing_at"] == "2021-06-10T00:00:00+03:00"


def test_parse_line_keeps_missing_values_as_none():
    row = parse_line(first_line())

    assert row["value_amount"] is None
    assert row["currency"] is None
    assert row["status"] is None


def test_parse_line_falls_back_to_parties_when_buyer_has_no_name():
    line = (
        '{"ocid":"ocds-5whusi-x","buyer":{},'
        '"parties":[{"name":"County Buyer","roles":["buyer"]}],'
        '"tender":{"title":"Road works"}}'
    )

    row = parse_line(line)

    assert row["buyer_name"] == "County Buyer"


def test_normalize_category_maps_the_source_values():
    assert normalize_category("goods") == "goods"
    assert normalize_category("services") == "services"
    assert normalize_category("works") == "works"
    assert normalize_category("consultancy services") == "consultancy"


def test_normalize_category_sends_anything_unclear_to_other():
    assert normalize_category(None) == "other"
    assert normalize_category("") == "other"
    assert normalize_category("something else") == "other"
