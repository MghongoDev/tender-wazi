# Sector method

## Taxonomy

Ten sectors, each present in `tender_sector.sectors` as a text array: `ict_data_tech`,
`works_construction`, `health_medical`, `education_training`, `agriculture_environment`,
`energy_utilities`, `transport_vehicles`, `professional_services`, `general_supplies`,
`other`. A notice can carry several.

## Rules

- Rules file: `config/sector_rules.yaml`, version `2026-11-a`.
- Terms are regex fragments, matched on whole words, case-insensitive; each sector has an
  optional `not` list of excluding terms.
- The classifier reads the title only. It never uses the buyer name or the raw payload.

## Labelled sample

One hundred tenders the rules tagged `ict_data_tech`, and one hundred the rules did not,
drawn at random across both sources (PPIP and Kenya Power). The agent produced a first pass;
the reviewer settled one row that the agent could not judge from the title alone (see below).
This is a first pass, not a final measurement: the sample is small and the labels are the
agent's read of the title.

## Measured precision and miss rate

Rules version `2026-11-a`:

- Precision of the tech label: 100% (100/100). Every tender the rules tagged `ict_data_tech`
  was truly tech.
- Miss rate: 4% (4/100). Four tech tenders the rules missed.

The misses were: Microsoft 365 (framework contract), a desktop-computer purchase, website
support, and a single-aisle RFID security system. All are software, hardware, or a digital
system, so the fix is to broaden the technical terms, not to retag.

## Flags for review

The agent could not settle one title from the text alone:

- `PROPOSED COMPLETION OF KIAWAROGA HOSPITAL (PHASE II)` — a hospital construction project,
  but the title gives no sector. Recorded as `health_medical` by the agent; a reader may
  override.

The agent's table of first-pass labels is in `tests/sector_labels.csv` with the rule labels
in `rule_sectors` and the agent's labels in `true_sectors`.
