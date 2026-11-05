# Sources

Two sources feed Tender-wazi. Each section records the URL, who runs the source, its format, its update frequency, its terms, its robots.txt result, and the date checked. Checked on 5 November 2026.

## Source A: PPIP (OCDS)

- URL: https://tenders.go.ke/ocds
- Who runs it: the Public Procurement Regulatory Authority (PPRA), through the Public Procurement Information Portal (PPIP).
- Format: OCDS. Bulk downloads per year as gzipped JSON Lines, one contracting process per line. Excel and CSV are also available.
- Update frequency: daily, according to the OCP data registry. The registry retrieves monthly, so its files can lag.
- Terms: the OCP registry lists no licence and no publication policy. Read the portal's own terms before republishing in bulk.
- robots.txt: https://tenders.go.ke/robots.txt allows all crawlers ("User-agent: *" with an empty "Disallow").
- Date checked: 5 November 2026.
- OCP registry entry: https://data.open-contracting.org/en/publication/147
- Data range: July 2018 to October 2026. Counts: 262,961 tenders, 109,607 awards, 109,607 contracts, 818,997 parties. OCID prefix: ocds-5whusi.
- Bulk download URLs: `https://data.open-contracting.org/en/publication/147/download?name=YYYY.jsonl.gz`, one per year, plus `full.jsonl.gz`.
- Known quality issues, from the registry's review: empty `awards` and `contracts` arrays; extreme outliers in award and contract amounts; no buyer identifier scheme; an invalid supplier identifier scheme; some `parties` entries without names, where the names sit in `buyer.name` and `awards.supplier.name`.

## Source B: Kenya Power tender listing

- URL: https://kplc.co.ke/tender (the real listing). https://kplc.co.ke/eprocurement is a hub with two recent tenders; the first fixture captured that hub by mistake.
- Who runs it: Kenya Power and Lighting Company (KPLC), a state corporation.
- Format: server-rendered HTML on the first page. The listing shows Reference No. and Tender Title. Detail pages at `/tender/<slug>` show Tender Number, Tender Title, Publish Date, Closing Date, Eligibility, Pre Bid, a Download link and an Addendums table.
- Pagination: Laravel Livewire. Page 2 and beyond need POSTs to /livewire/update with a CSRF token and a component snapshot. A plain GET walk stops at page 1. There are 31 pages.
- Update frequency: not stated. Compare the newest entries against the previous run.
- Terms: the footer links to /data-privacy (an AI and data-privacy statement) and /quality-policy. Neither forbids automated access to the public listings. The /terms-and-conditions URL is 404. Contact customercare@kplc.co.ke or dpo@kplc.co.ke.
- robots.txt: https://kplc.co.ke/robots.txt allows all crawlers and lists a sitemap whose /tenders and /terms-and-conditions URLs are 404.
- Date checked: 5 November 2026.
- Reference numbers vary: KP1/..., KPI/..., KP11/..., and dot-separated forms. The slug carries a random suffix, so source_id must be the reference number, not the slug.
- Category and notice type: not stated on the page.
- Dates: DD/MM/YYYY, sometimes with a time, no timezone stated.
- The listing renders each entry twice, once for desktop and once for mobile, so dedupe by reference.
- Tech coverage: page 1 has one ICT tender of twelve. Low.
- Why this source: it is one buyer with a large IT budget, and its first page is server-rendered. The Livewire pagination is a documented limitation.

## Deferred: e-GP portal

- URL: https://egpkenya.go.ke/tender/search-tender
- Who runs it: the National Treasury, under the Public Procurement and Asset Disposal Act 2015 and Regulation 54 of the PPADR 2020.
- Status: live as of 5 November 2026, with 771 active tenders. It is the new system of record for government procurement.
- Format: a JavaScript single-page app. The listing is not in the HTML; it loads through an API. The terms page is at https://egpkenya.go.ke/terms-and-conditions.
- Why deferred: the guide's Source B is a server-rendered HTML portal. The e-GP needs its API or a headless browser, which is more work. Add it after the MVP, and re-check whether PPIP remains the system of record.

## Cross-check

- ke.opentender.eu offers downloadable Kenyan tender data (CSV, JSON, OCDS). Use it to sanity-check counts, not as a primary source.
