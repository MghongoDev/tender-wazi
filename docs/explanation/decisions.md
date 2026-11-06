# Decisions

Architecture decision records for the build. Each record states the decision, why it was made, and what it costs.

## ADR 0001: Versioned notices

A notice changes over time. Tender-wazi keeps every version. A version closes when a new one opens, so the old version's `valid_to` equals the new version's `valid_from`.

Why: the record must show what a notice said at each time, not only what it says now.

Consequences: a query for the current notices filters on `valid_to is null`.

## ADR 0002: The content hash covers business fields only

The hash covers title, buyer, category, notice type, method, status, jurisdiction, dates, value, currency and source URL. It never covers fetch times, `raw_id` or the sector label.

Why: re-fetching an unchanged notice must not create a new version. A changed sector label must not create a new version either, because the label is a guess.

Consequences: a change to a business field creates a version. A change to anything else does not.

## ADR 0003: The sector label stays out of tender_versions

The sector label is added later by the classify module.

Why: the label is a guess that improves over time. A guess must not create a new version of a notice.

Consequences: the label lives in its own table. `tender_versions` holds only what the source states.

## ADR 0004: Staging tables hold the parsed rows

`staging_ppip_tenders` and `staging_portal_b_tenders` hold the parsed rows before normalization.

Why: a load is idempotent and inspectable. The parsed rows are on disk before they become versions.

Consequences: the staging tables are a landing zone. They are not the record.

## ADR 0005: COPY for bulk loads

The load copies rows into a temp table, then upserts.

Why: row-by-row inserts were too slow. The first PPIP load with row-by-row inserts did not finish in seven minutes. With COPY it finished in twenty seconds.

Consequences: the load is fast. The temp table is dropped at the end of the transaction.

## ADR 0006: Kenya Power page 1 only

The Kenya Power scraper reads page 1 only.

Why: page 2 and beyond use Laravel Livewire. A scripted update returned 419 and 500 in testing.

Consequences: the record misses tenders on later pages. A later step can add a headless browser.

## ADR 0008: Classify from the title only

The classifier reads the title of each notice and matches it against the terms
in `config/sector_rules.yaml`. It never reads the buyer name or the raw payload.

Why: the buyer name is unreliable. An ICT agency buys furniture, and a ministry
of works buys software. The title names the work.

Consequences: the classifier is deterministic and re-runnable. A change to the
rules means a full re-run over every notice, because the labels live in
`tender_sector`, not in `tender_versions`.

## ADR 0007: The shared migration runner

The collect module owns `src/tender_wazi/migrate.py`. The curate module uses it.

Why: one runner for all migrations. A second runner would drift.

Consequences: the curate migrations live in `sql/migrations/` and run through the same command.

## ADR 0009: Quality checks run after every load
The quality module records a row in `quality_runs` for every load, and copies each
rejected row into `rejects`. It checks null rates, duplicate open versions, value
outliers, sector spread, volume drift and HTML schema drift.

Why: the pipeline must tell you when data is wrong or a source goes quiet, and must
not load bad data silently.

Consequences: a run that fails any check exits non-zero, so the daily workflow
notifies without extra tools.
