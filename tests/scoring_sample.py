"""Apply the agent's first-pass labels, then score the tech filter.

Writes tests/sector_labels.csv with a filled true_sectors column, then prints
precision and miss rate on the tech label. Anything left unlabelled is flagged
so the reviewer can settle it before the figure is treated as measured.
"""

from __future__ import annotations

import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sector_labels_labels as labels

CSV_PATH = "tests/sector_labels.csv"


def load_rows(path: str) -> list[dict[str, str]]:
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def write_rows(rows: list[dict[str, str]], path: str) -> None:
    fieldnames = ["source", "source_id", "title", "rule_sectors", "true_sectors"]
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def is_tech(row: dict[str, str]) -> bool:
    return "ict_data_tech" in row.get("true_sectors", "").split(";")


def main() -> None:
    rows = load_rows(CSV_PATH)
    missing: list[str] = []
    counted = 0

    for row in rows:
        sectors = labels.TRUE_SECTORS.get(row["source_id"])
        if sectors is None:
            missing.append(row["source_id"])
            continue
        row["true_sectors"] = ";".join(sectors)
        counted += 1

    if missing:
        print(f"unlabelled source_ids ({len(missing)}): {', '.join(sorted(missing))}")

    write_rows(rows, CSV_PATH)

    # Tagged vs not-tagged is taken from the rules column, not position.
    tagged = [r for r in rows if "ict_data_tech" in r.get("rule_sectors", "").split(";")]
    untagged = [r for r in rows if "ict_data_tech" not in r.get("rule_sectors", "").split(";")]

    tp = sum(1 for r in tagged if is_tech(r))          # tagged and truly tech
    precision = tp / len(tagged) if tagged else 0.0

    fn = sum(1 for r in untagged if is_tech(r))         # not-tagged but truly tech
    miss_rate = fn / len(untagged) if untagged else 0.0

    print(f"labelled rows: {counted}")
    print(f"tagged rows (rules said ict_data_tech): {len(tagged)}")
    print(f"not-tagged rows: {len(untagged)}")
    print(f"precision of the tech label: {precision:.3f} ({tp}/{len(tagged)})")
    print(f"miss rate on the not-tagged set: {miss_rate:.3f} ({fn}/{len(untagged)})")


if __name__ == "__main__":
    main()
