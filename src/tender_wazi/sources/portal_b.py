import re

from bs4 import BeautifulSoup

from tender_wazi.raw import save_raw

# Page 2 and beyond use Laravel Livewire (POST /livewire/update with a CSRF
# token and a component snapshot). A scripted update returned 419 and 500 in
# testing, so this module collects page 1 only. See docs/reference/sources.md.
LISTING_URL = "https://kplc.co.ke/tender"
BASE_URL = "https://kplc.co.ke"
ENTRY_SELECTOR = "div.flex.flex-row.gap-8.pt-4"
REFERENCE_PREFIX = re.compile(r"^tender\s+no\.?\s*", re.IGNORECASE)


def _value_after_label(scope, label):
    """Read the value div that follows a label div, as the KPLC pages are laid out."""
    element = scope.find(string=lambda s: s and s.strip() == label)
    if element is None:
        return None
    label_div = element.find_parent("div")
    if label_div is None:
        return None
    value_div = label_div.find_next_sibling("div")
    if value_div is None:
        return None
    return value_div.get_text(" ", strip=True)


def _clean_reference(raw):
    if not raw:
        return None
    return REFERENCE_PREFIX.sub("", raw.strip()).strip()


def parse_listing(html: str) -> list[dict]:
    """Read the Kenya Power listing into one row per reference number.

    The page renders each entry twice, once for desktop and once for mobile,
    so rows are deduped by reference.
    """
    soup = BeautifulSoup(html, "lxml")
    rows = []
    seen = set()
    for entry in soup.select(ENTRY_SELECTOR):
        source_id = _clean_reference(_value_after_label(entry, "Reference No."))
        title = _value_after_label(entry, "Tender Title")
        link = entry.find("a", href=True)
        if not source_id or not link:
            continue
        if source_id in seen:
            continue
        seen.add(source_id)
        rows.append({"source_id": source_id, "title": title, "detail_url": link["href"]})
    return rows


def parse_detail(html: str) -> dict:
    """Read one Kenya Power detail page. Raises ValueError if the reference is missing."""
    soup = BeautifulSoup(html, "lxml")
    heading = soup.find("h1")
    source_id = heading.get_text(" ", strip=True) if heading else None
    if not source_id:
        raise ValueError("no reference number (h1) on the page")
    return {
        "source_id": _clean_reference(source_id),
        "title": _value_after_label(soup, "Tender Title"),
        "published_at_raw": _value_after_label(soup, "Publish Date"),
        "closing_at_raw": _value_after_label(soup, "Closing Date"),
        "category_raw": _value_after_label(soup, "Procurement Category"),
        "notice_type": _value_after_label(soup, "Notice Type"),
        "document_links": [
            a["href"]
            for a in soup.find_all("a", href=True)
            if a.get_text(" ", strip=True).lower() == "download"
        ],
    }


def collect(conn, bucket, client, max_details=None) -> list[dict]:
    """Fetch the listing and its detail pages, saving every raw payload.

    Returns the parsed detail rows, each carrying its raw_id.
    """
    response = client.get(LISTING_URL)
    save_raw(conn, bucket, "portal_b", LISTING_URL, response.content, response.status_code)
    rows = parse_listing(response.text)
    parsed = []
    for index, row in enumerate(rows):
        if max_details is not None and index >= max_details:
            break
        url = BASE_URL + row["detail_url"]
        detail = client.get(url)
        raw_id = save_raw(conn, bucket, "portal_b", url, detail.content, detail.status_code)
        record = parse_detail(detail.text)
        record["raw_id"] = raw_id
        record["detail_url"] = row["detail_url"]
        parsed.append(record)
    return parsed
