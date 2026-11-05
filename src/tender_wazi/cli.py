import argparse
import gzip
import os

import boto3
import psycopg

from tender_wazi.http import PoliteClient
from tender_wazi.migrate import migrate
from tender_wazi.sources.portal_b import collect as collect_portal_b
from tender_wazi.sources.ppip import download_year, normalize_category, parse_line


def run_ppip(year: int) -> None:
    """Fetch one year of PPIP data, save it raw, and print the parsed counts."""
    conn = psycopg.connect(os.environ["DATABASE_URL_DIRECT"])
    s3 = boto3.resource("s3", endpoint_url=os.environ.get("AWS_ENDPOINT_URL_S3"))
    bucket = s3.Bucket(os.environ["RAW_BUCKET"])  # type: ignore[reportAttributeAccessIssue]

    raw_id, body = download_year(conn, bucket, year)
    print(f"saved raw {raw_id} ({len(body)} bytes)")

    text = gzip.decompress(body).decode("utf-8")
    rows = [parse_line(line) for line in text.splitlines() if line.strip()]
    print(f"parsed {len(rows)} contracting processes")

    counts: dict[str, int] = {}
    for row in rows:
        category = normalize_category(row["category_raw"])
        counts[category] = counts.get(category, 0) + 1
    for category, n in sorted(counts.items()):
        print(f"  {category}: {n}")

    conn.close()


def run_portal_b(max_details: int | None = None) -> None:
    """Fetch the Kenya Power listing and its detail pages, saving every raw payload."""
    conn = psycopg.connect(os.environ["DATABASE_URL_DIRECT"])
    s3 = boto3.resource("s3", endpoint_url=os.environ.get("AWS_ENDPOINT_URL_S3"))
    bucket = s3.Bucket(os.environ["RAW_BUCKET"])  # type: ignore[reportAttributeAccessIssue]
    client = PoliteClient(min_interval=2.0)
    saved = collect_portal_b(conn, bucket, client, max_details)
    print(f"saved {saved} detail pages")
    conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(prog="tender_wazi")
    sub = parser.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run")
    run.add_argument("--source", choices=["ppip", "portal_b"], required=True)
    run.add_argument("--year", type=int, default=2025)
    run.add_argument("--max-pages", type=int, default=None)

    sub.add_parser("migrate")
    args = parser.parse_args()

    if args.cmd == "migrate":
        migrate(os.environ["DATABASE_URL_DIRECT"])
    elif args.source == "ppip":
        run_ppip(args.year)
    else:
        run_portal_b(args.max_pages)


if __name__ == "__main__":
    main()
