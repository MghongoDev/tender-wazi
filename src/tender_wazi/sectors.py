import re
from pathlib import Path

import yaml

DEFAULT_RULES_PATH = "config/sector_rules.yaml"


def load_rules(path: str = DEFAULT_RULES_PATH) -> tuple[str, dict]:
    """Read the rules file and compile the term lists for each sector."""
    cfg = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    rules = {}
    for sector, spec in cfg["sectors"].items():
        include = [re.compile(rf"\b(?:{term})\b", re.IGNORECASE) for term in spec["any"]]
        exclude = [
            re.compile(rf"\b(?:{term})\b", re.IGNORECASE)
            for term in spec.get("not", [])
        ]
        rules[sector] = (include, exclude)
    return cfg["version"], rules


def classify(text: str, rules: dict) -> tuple[list[str], list[str]]:
    """Return the sectors that match a title, and the terms that matched.

    A sector matches when one of its terms appears and none of its excluding
    terms does. A title that matches nothing falls back to other.
    """
    text = text or ""
    sectors = []
    matched = []
    for sector, (include, exclude) in rules.items():
        hits = [m.group(0) for rx in include if (m := rx.search(text))]
        if hits and not any(rx.search(text) for rx in exclude):
            sectors.append(sector)
            matched += hits
    return sectors or ["other"], matched


def store_sectors(conn, rows, rules_version):
    """Upsert one label row per notice. Never touches tender_versions."""
    with conn.cursor() as cur:
        cur.execute(
            "CREATE TEMP TABLE sector_incoming (source text, source_id text, "
            "sectors text[], matched_terms text[], rules_version text) ON COMMIT DROP"
        )
        with cur.copy(
            "COPY sector_incoming (source, source_id, sectors, matched_terms, rules_version) "
            "FROM STDIN"
        ) as copy:
            for row in rows:
                copy.write_row(
                    (
                        row["source"],
                        row["source_id"],
                        row["sectors"],
                        row["matched_terms"],
                        rules_version,
                    )
                )
        cur.execute(
            "INSERT INTO tender_sector (source, source_id, sectors, matched_terms, rules_version) "
            "SELECT source, source_id, sectors, matched_terms, rules_version FROM sector_incoming "
            "ON CONFLICT (source, source_id) DO UPDATE "
            "SET sectors = EXCLUDED.sectors, matched_terms = EXCLUDED.matched_terms, "
            "rules_version = EXCLUDED.rules_version, classified_at = now()"
        )
    conn.commit()
