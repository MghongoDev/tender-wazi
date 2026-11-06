import argparse
import gzip
import os

import boto3
import psycopg

from tender_wazi.http import PoliteClient
from tender_wazi.migrate import migrate
from tender_wazi.normalize import normalize_portal_b, normalize_ppip
from tender_wazi.sectors import classify, load_rules, store_sectors
from tender_wazi.sources.portal_b import collect as collect_portal_b
from tender_wazi.sources.ppip import download_year, parse_line
from tender_wazi.store import load_portal_b_staging, load_ppip_staging, store_batch


def _bucket():
    s3 = boto3.resource("s3", endpoint_url=os.environ.get("AWS_ENDPOINT_URL_S3"))
    return s3.Bucket(os.environ["RAW_BUCKET"])  # type: ignore[reportAttributeAccessIssue]


def run_ppip(year: int) -> None:
    """Fetch one year of PPIP data, then stage, normalize and version it."""
    conn = psycopg.connect(os.environ["DATABASE_URL_DIRECT"])
    bucket = _bucket()
    raw_id, body = download_year(conn, bucket, year)
    print(f"saved raw {raw_id} ({len(body)} bytes)")

    rows = [
        parse_line(line)
        for line in gzip.decompress(body).decode("utf-8").splitlines()
        if line.strip()
    ]
    for row in rows:
        row["raw_id"] = raw_id
    load_ppip_staging(conn, rows)

    normalized = [normalize_ppip(row) for row in rows]
    store_batch(conn, normalized)
    print(f"staged and stored {len(normalized)} contracting processes")

    counts: dict[str, int] = {}
    for row in normalized:
        counts[row["category"]] = counts.get(row["category"], 0) + 1
    for category, n in sorted(counts.items()):
        print(f"  {category}: {n}")
    conn.close()


def run_portal_b(max_details: int | None = None) -> None:
    """Fetch the Kenya Power listing, then stage, normalize and version it."""
    conn = psycopg.connect(os.environ["DATABASE_URL_DIRECT"])
    bucket = _bucket()
    client = PoliteClient(min_interval=2.0)
    rows = collect_portal_b(conn, bucket, client, max_details)
    load_portal_b_staging(conn, rows)

    normalized = [normalize_portal_b(row) for row in rows]
    store_batch(conn, normalized)
    print(f"staged and stored {len(normalized)} notices")
    conn.close()


def run_classify() -> None:
    """Label every current notice with sectors."""
    version, rules = load_rules()
    conn = psycopg.connect(os.environ["DATABASE_URL_DIRECT"])
    with conn.cursor() as cur:
        cur.execute(
            "select source, source_id, title from tender_versions where valid_to is null"
        )
        fetched = cur.fetchall()
    rows = []
    for source, source_id, title in fetched:
        sectors, matched = classify(title, rules)
        rows.append(
            {
                "source": source,
                "source_id": source_id,
                "sectors": sectors,
                "matched_terms": matched,
            }
        )
    store_sectors(conn, rows, version)
    print(f"labeled {len(rows)} notices with rules version {version}")
    conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(prog="tender_wazi")
    sub = parser.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run")
    run.add_argument("--source", choices=["ppip", "portal_b"], required=True)
    run.add_argument("--year", type=int, default=2025)
    run.add_argument("--max-pages", type=int, default=None)

    sub.add_parser("migrate")
    sub.add_parser("classify")
    args = parser.parse_args()

    if args.cmd == "migrate":
        migrate(os.environ["DATABASE_URL_DIRECT"])
    elif args.cmd == "classify":
        run_classify()
    elif args.source == "ppip":
        run_ppip(args.year)
    else:
        run_portal_b(args.max_pages)


if __name__ == "__main__":
    main()
