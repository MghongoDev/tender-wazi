# Capability Map: Tender-wazi

Seven modules. Each owns its own data and tests. Build in dependency order. This map is the index of what exists. Module specs live alongside it as SPEC-<module>.md.

| Module | Responsibility | Depends on |
|---|---|---|
| platform | Repo, Neon project and branches, credentials, object storage, Render services | — |
| collect | PPIP OCDS reader, HTML portal scraper, polite HTTP client, raw payloads, raw_manifest, docs/reference/sources.md, fixtures | platform |
| curate | Staging tables, normalize to one schema, versioned upserts, tender_seen, tender_lineage, SQL migrations | platform, collect |
| classify | Sector rules YAML, classifier, rules version, hand-labelled sample, measured precision and miss rate | curate |
| quality | Row and table checks, rejects, quality_runs, volume and schema drift, source_health | curate, classify |
| serve | Read-only FastAPI API, api views, api_reader role, facet counts, static frontend | platform, curate, classify, quality |
| ops | Daily GitHub Actions run, CI and migration workflows, rate limiting, terms and attribution, README and docs | all six |

Build order: platform, collect, curate, classify, quality, serve, ops.

serve is delivered in two parts. A thin slice (health endpoint and a basic tenders list with sector labels) ships right after classify, before quality, to find deployment problems early. The full API and frontend follow quality.

Key interfaces:

- platform to all: Neon connection strings (direct and pooled), object storage credentials, Render services.
- collect to curate: raw_manifest rows and object keys. Curate never re-fetches.
- curate to classify, quality, serve: tender_versions (open and closed), tender_seen, tender_lineage.
- classify to serve: tender_sector (sectors, matched_terms, rules_version).
- quality to serve: source_health, quality_runs.
- ops runs and deploys all six. Nothing depends on ops.
- The migration runner (src/tender_wazi/migrate.py) is shared: collect bootstraps it and curate's migrations use it.

Approved by the user on 5 November 2026.
