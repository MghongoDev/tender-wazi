"""Quality checks: row validation, table checks, volume and schema drift.

Every bad row becomes a row in `rejects`; every load becomes a row in
`quality_runs`. Nothing is dropped silently.
"""

from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from typing import Any

import psycopg
from pydantic import BaseModel, ConfigDict, Field, field_validator

from tender_wazi.normalize import parse_datetime

ALLOWED_CURRENCY = {"KES", "USD", "EUR", "GBP"}
NULL_RATE_THRESHOLD = 0.20
SCHEMA_DRIFT_THRESHOLD = 0.90
VOLUME_WINDOW = 30
VOLUME_K = 2.0
MIN_VOLUME_PERIODS = 2

REQUIRED_FIELDS = [
    "title",
    "buyer_name",
    "category",
    "notice_type",
    "procurement_method",
    "status",
    "jurisdiction",
    "published_at",
    "closing_at",
    "value_amount",
    "currency",
    "source_url",
]


class RowModel(BaseModel):
    """A candidate notice, validated after normalization."""

    model_config = ConfigDict(extra="ignore")

    source: str
    source_id: str
    title: str
    buyer_name: str | None = None
    category: str | None = None
    category_raw: str | None = None
    notice_type: str | None = None
    procurement_method: str | None = None
    status: str | None = None
    jurisdiction: str | None = None
    published_at: datetime | None = None
    closing_at: datetime | None = None
    value_amount: Decimal | None = None
    currency: str | None = None
    source_url: str | None = None
    raw_id: int | None = None

    @field_validator("title")
    @classmethod
    def title_non_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("title must be present and non-empty")
        return v

    @field_validator("published_at", "closing_at")
    @classmethod
    def parse_date(cls, v):
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        parsed = parse_datetime(v)
        if parsed is None:
            raise ValueError("unreadable date")
        return parsed

    @field_validator("value_amount")
    @classmethod
    def amount_non_negative(cls, v):
        if v is not None and v < 0:
            raise ValueError("amount must be non-negative")
        return v

    @field_validator("currency")
    @classmethod
    def currency_allowed(cls, v):
        if v is not None and v not in ALLOWED_CURRENCY:
            raise ValueError(f"unknown currency {v!r}")
        return v


def validate_row(source: str, row: dict[str, Any]) -> tuple[bool, list[str]]:
    """Return (True, []) when the row passes, else (False, [reasons])."""
    try:
        RowModel.model_validate(row)
    except Exception as exc:  # pragma: no cover - pydantic reports every field
        return False, [str(exc)]
    return True, []


def record_rejects(
    conn: psycopg.Connection,
    source: str,
    source_id: str | None,
    raw_id: int | None,
    row: dict[str, Any],
    reason: str,
) -> int:
    """Insert a rejected row and return its primary key."""
    import psycopg  # noqa: F401 - keep the module's dependency visible

    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO rejects (source, source_id, raw_id, reason, row_json)"
            " VALUES (%s, %s, %s, %s, %s)",
            (source, source_id, raw_id, reason, json.dumps(row, sort_keys=True)),
        )
        cur.execute("SELECT LASTVAL()")
        return cur.fetchone()[0]


def table_checks(conn: psycopg.Connection, source: str) -> dict[str, Any]:
    """Row and table checks for one source, after a load."""
    result: dict[str, Any] = {
        "null_rates": {},
        "duplicates": 0,
        "outliers": 0,
        "sector_spread": {},
    }
    KEY_FIELDS = ("published_at", "closing_at", "value_amount", "currency")
    with conn.cursor() as cur:
        for field in KEY_FIELDS:
            cur.execute(
                f"SELECT COUNT(*) FROM tender_versions WHERE source = %s AND {field} IS NULL",
                (source,),
            )
            n = cur.fetchone()[0]
            cur.execute(
                "SELECT COUNT(*) FROM tender_versions WHERE source = %s",
                (source,),
            )
            total = cur.fetchone()[0]
            result["null_rates"][field] = round(n / total, 4) if total else 0.0

        cur.execute(
            "SELECT COUNT(*) FROM ("
            "  SELECT source_id FROM tender_versions"
            "  WHERE source = %s AND valid_to IS NULL"
            "  GROUP BY source_id HAVING COUNT(*) > 1"
            ") AS dup",
            (source,),
        )
        result["duplicates"] = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM tender_versions v"
            " WHERE source = %s"
            " AND value_amount IS NOT NULL"
            " AND value_amount > ("
            "   SELECT percentile_disc(0.99) WITHIN GROUP (ORDER BY value_amount)"
            "   FROM tender_versions WHERE source = %s"
            " )",
            (source, source),
        )
        result["outliers"] = cur.fetchone()[0]

        cur.execute(
            "SELECT sector, COUNT(*) FROM ("
            "  SELECT UNNEST(COALESCE(s.sectors, ARRAY['other'])) AS sector"
            "  FROM tender_sector s WHERE s.source = %s"
            ") AS t GROUP BY sector",
            (source,),
        )
        result["sector_spread"] = dict(cur.fetchall())
    return result


def record_quality_run(
    conn: psycopg.Connection,
    source: str,
    ok: bool,
    message: str,
    results: dict[str, Any],
) -> int:
    """Record one quality run and return its primary key."""
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO quality_runs (source, ok, message, null_rates, duplicates,"
            " outliers, sector_spread, volume_drift, schema_drift)"
            " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                source,
                ok,
                message,
                json.dumps(results["null_rates"], sort_keys=True),
                results["duplicates"],
                results["outliers"],
                json.dumps(results["sector_spread"], sort_keys=True),
                results.get("volume_drift"),
                json.dumps(results.get("schema_drift"), sort_keys=True),
            ),
        )
        cur.execute("SELECT LASTVAL()")
        return cur.fetchone()[0]


def volume_alert(daily: list[tuple[datetime, int]], window: int = VOLUME_WINDOW,
                 k: float = VOLUME_K) -> bool:
    """daily is a list of (date, count) tuples, oldest first.

    Flag the last day when it is more than k standard deviations below the mean
    of the trailing window. A fall of two standard deviations below the
    thirty-day mean is a source going quiet.
    """
    if len(daily) < 2:
        return False
    prior = [count for _, count in daily[-window - 1:-1]]
    current = daily[-1][1]
    if len(prior) < MIN_VOLUME_PERIODS:
        return False
    mean = sum(prior) / len(prior)
    variance = sum((x - mean) ** 2 for x in prior) / len(prior)
    std = variance ** 0.5
    return current < mean - k * std


def check_schema_drift(records: list[dict[str, Any]],
                       required: list[str] | None = None) -> dict[str, Any]:
    """How many of the required fields matched on the last run.

    A required field that matched on less than 90% of pages fails the run.
    """
    required = required or ["source_id", "title", "published_at_raw", "closing_at_raw"]
    n = len(records)
    if n == 0:
        return {"failed": True, "rates": {field: None for field in required}}
    rates = {}
    for field in required:
        matched = sum(1 for r in records if r.get(field))
        rates[field] = round(matched / n, 4)
    return {"failed": any(r < SCHEMA_DRIFT_THRESHOLD for r in rates.values()),
            "rates": rates}


def apply_row_checks(conn: psycopg.Connection, rows: list[dict[str, Any]],
                     source: str) -> int:
    """Validate every row and record a reject for each failure.

    Returns the number of rows that failed.
    """
    rejected = 0
    for row in rows:
        ok, reasons = validate_row(source, row)
        if not ok:
            record_rejects(
                conn,
                source,
                row.get("source_id"),
                row.get("raw_id"),
                row,
                "; ".join(reasons),
            )
            rejected += 1
    return rejected
