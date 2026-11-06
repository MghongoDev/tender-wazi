# Tender-wazi

An open record of Kenyan public tenders. Tender-wazi pulls notices from public sources, keeps every raw payload, and serves a versioned, searchable API.

## Status

Early build. The platform, collect and curate modules are built. The classify, quality, serve and ops modules are next. See CAPABILITY-MAP.md.

## What it does

- Collects notices from PPIP and Kenya Power.
- Saves every raw payload in object storage.
- Normalizes both sources into one schema.
- Versions every notice, so the record shows what a notice said at each time.

## Quick start

```
uv sync
cp .env.example .env   # fill in the values
uv run python -m tender_wazi migrate
uv run python -m tender_wazi run --source ppip --year 2025
uv run pytest -q
```

See SPEC-platform.md for the environment setup.

## Configuration

Copy `.env.example` to `.env` and fill in the values.

| Key | Purpose |
|---|---|
| `DATABASE_URL_DIRECT` | The direct Postgres connection for the load. |
| `DATABASE_URL` | The pooled connection for the read-only role. |
| `RAW_BUCKET` | The object storage bucket for raw payloads. |
| `AWS_ACCESS_KEY_ID` | The storage credential. |
| `AWS_SECRET_ACCESS_KEY` | The storage credential. |
| `AWS_ENDPOINT_URL_S3` | The storage endpoint. |
| `AWS_REGION` | The storage region. |

Never commit `.env`. See SPEC-platform.md.

## Layout

- `docs/reference/` — sources and the data dictionary.
- `docs/how-to/` — task recipes, including the load.
- `docs/explanation/` — decisions.
- `SPEC-*.md` — the module specifications.
- `CAPABILITY-MAP.md` — the module map.
- `GLOSSARY.md` — the domain vocabulary.

## Sector classification

The classify module labels every notice with one or more sectors from the ten
sector taxonomy. Rules live in `config/sector_rules.yaml` and are versioned.
The label is stored in `tender_sector`, never in `tender_versions`, so
improving the rules never creates a new version.

See `docs/sector-method.md` for the taxonomy, rules and the measured precision.

## Modules

See CAPABILITY-MAP.md for the module map and the build order.

## Tests

```
uv run pytest -q
```

The store tests need `.env`. They run against the dev database.
