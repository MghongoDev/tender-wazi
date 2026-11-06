# Glossary

## Notice
One tender notice from one source. A notice has one or more versions.

## Version
One snapshot of a notice at one time. `version_no` starts at 1 and increases by one per change.

## Open version
The current version of a notice. It is the only version with a null `valid_to`.

## Content hash
A sha256 over the business fields of a version. Re-fetching an unchanged notice gives the same hash, so no new version is created.

## Source
A publisher of tenders. Tender-wazi reads PPIP and Kenya Power. See docs/reference/sources.md.

## Source id
The identifier a source gives a notice. PPIP uses the `ocid`. Kenya Power uses the reference number.

## Staging table
The landing zone for parsed rows. `staging_ppip_tenders` and `staging_portal_b_tenders`.

## Lineage
The full history of a notice. `tender_lineage` joins every version to the raw payload it came from.

## Raw payload
The saved bytes a fetch returned. Raw payloads live in object storage and are never edited.

## OCID
Open Contracting Identifier. The PPIP publication's prefix is `ocds-5whusi`.

## OCDS
Open Contracting Data Standard. The format PPIP publishes.

## Jurisdiction
Whether a notice is national or county. Tender-wazi infers it from the buyer name.

## Category
The normalized procurement category: goods, works, services, consultancy or other.

## Sector label
A later, finer classification. The classify module adds it. It is not part of `tender_versions`.
