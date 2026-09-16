# Pentagon J-Book program corpus

Backing data for `verticals/public_co/m_sources/pentagon_jbook.py`. Each entry in `programs.json` is one Pentagon program (or Program Element) the connector can answer questions about.

## What's a J-Book?

Each service comptroller publishes annual budget-justification books with per-program funding tables across past, current, and planned future fiscal years. Public PDFs:

- **Air Force / Space Force:** https://www.saffm.hq.af.mil/Budget/
- **Army:** https://www.asafm.army.mil/Budget-Materials/
- **Navy:** https://www.secnav.navy.mil/fmc/fmb/Pages/
- **OSD aggregate:** https://comptroller.defense.gov/Budget-Materials/

The relevant J-Books for forward-funding-status questions:

- **R-2 RDT&E** — research, development, test, and evaluation (where most quantum / space / new-tech programs live)
- **P-1 / P-40 Procurement** — production buys (where established satellite programs live)
- **O-1 O&M** — operations and maintenance

For each program element (PE), tables show: prior-year actuals, current-year, FY+1 through FY+5, with narrative.

## Schema

Each program entry in `programs.json`:

```json
{
  "program_id":          "kebab-case unique identifier",
  "program_name":        "canonical name",
  "synonyms":            ["alternative names", "abbreviations"],
  "pe_number":           "PE number without 'PE ' prefix, e.g. '1206410SF'",
  "project":             "project number within the PE (optional)",
  "service":             "Army / Navy / Air Force / Space Force / Defense",
  "agency":              "specific agency (SDA, AFRL, DARPA, etc.)",
  "description":         "1-paragraph plain-language summary",
  "funding_history": {
    "FY2024": { "funded_M": 100, "note": "actuals" },
    "FY2025": { "funded_M": 0,   "note": "unfunded" },
    "FY2026": { "funded_M": 0 }
  },
  "status":              "FUNDED_GROWING | FUNDED_STEADY | FUNDED_SHRINKING | "
                         "UNFUNDED_THIS_YEAR | UNFUNDED_TWO_PLUS_YEARS | TERMINATED",
  "termination_announced": false,
  "primary_contractors": ["company A", "company B"],
  "replacement_program": "name of replacement, if any",
  "replacement_pe":      "PE number of replacement",
  "replacement_sole_source": "vendor if replacement is sole-source",
  "earmark_secured":     false,
  "earmark_sponsors_no_longer_in_power": false,
  "sole_source":         false,
  "documented_in":       ["J-Book reference + page numbers"],
  "source_urls":         ["URLs to news / J-Book PDFs"],
  "_provenance":         "where the data was extracted from"
}
```

Most fields are optional; only `program_id`, `program_name`, and `funding_history` are strictly required. The connector derives `status` automatically from `funding_history` if not explicitly set.

## How the connector matches

`query_program_funding()` accepts:

- `program_name` — substring match (case-insensitive) against `program_name` + `synonyms`
- `pe_number` — normalized match (strips `PE `, dots, whitespace) against `pe_number`
- `contractor_name` — substring match against `primary_contractors`

Match precedence when multiple programs match: priority by `status` (TERMINATED > UNFUNDED_TWO_PLUS_YEARS > UNFUNDED_THIS_YEAR > FUNDED_SHRINKING > FUNDED_STEADY > FUNDED_GROWING). This biases the connector toward surfacing the most actionable result first.

## Status enum

| Status | Meaning | Scorer signal |
|---|---|---|
| `FUNDED_GROWING` | Y-over-Y funding increasing | PASS |
| `FUNDED_STEADY` | Y-over-Y funding ~stable (±15%) | PASS |
| `FUNDED_SHRINKING` | Funded but declining | MODERATE_UNDERDELIVERY |
| `UNFUNDED_THIS_YEAR` | One-year gap (could be CR timing) | MODERATE_UNDERDELIVERY |
| `UNFUNDED_TWO_PLUS_YEARS` | Sustained de-funding | **SEVERE_UNDERDELIVERY** |
| `TERMINATED` | Officially killed | **RED_FLAG_NEGATIVE** |
| `NOT_FOUND` | Program not in corpus | UNVERIFIABLE |

The `UNFUNDED_TWO_PLUS_YEARS` signal is the canonical YSS/IONQ catch.

## Extending the corpus

For now, extraction is manual:

1. Open the relevant J-Book PDF (usually a few hundred pages).
2. Find the program by name or PE number in the table of contents.
3. Read the R-2 / R-2A exhibit for the PE: it has a funding table by FY plus narrative.
4. Encode as a JSON entry in `programs.json`. Include synonyms — small-cap 10-Ks rarely name the program element exactly.
5. List primary contractors. These show up in the J-Book narrative and in usaspending; cross-check.

Future automation (`scripts/ingest_jbook.py`, not yet built): parse the R-2 exhibit tables programmatically. R-2 exhibits have a fairly consistent format. The hard part is mapping `funded` vs `unfunded ceiling` (the IONQ "Total Contract Value" trick) — narrative text indicates this.

## Coverage gaps to know

- **R-2 vs P-1 split.** RDT&E programs are in R-2; procurement programs are in P-1 / P-40. A small-cap may be funded in RDT&E but the production buys move to P-1 — separate exhibits. We currently model both via the same schema.
- **Classified annex.** Some programs are funded through classified line items not visible in unclassified J-Books. A `NOT_FOUND` result for a heavily-classified-revenue small-cap may indicate classified coverage rather than de-funding.
- **CR (Continuing Resolution) timing.** When budgets pass under CR rather than full appropriation, prior-year funding levels carry forward by default. `UNFUNDED_THIS_YEAR` could reflect CR timing rather than actual program death; that's why it scores MODERATE rather than SEVERE.
- **Earmark / political-add programs.** When a program is funded via congressional plus-up rather than Pentagon request, its future is tied to the political viability of its sponsors. Flag `earmark_secured: true` and `earmark_sponsors_no_longer_in_power: true` to capture this risk.
- **Service-specific PE numbering.** PE numbers have a service suffix: `SF` = Space Force, `AF` = Air Force (pre-SF separation), `A` = Army, `N` = Navy, `DW` = Defense-wide. Match normalization should preserve this.

## Currently seeded programs (as of 2026-05-19)

| Program ID | Program | Status | Why seeded |
|---|---|---|---|
| `t3-transport-layer` | Tranche 3 Transport Layer (PWSA) | UNFUNDED_TWO_PLUS_YEARS | YSS short report 2026-05-11 |
| `sda-transport-t0-t2` | SDA Transport Layer T0-T2 | FUNDED_SHRINKING | YSS backlog disambiguation |
| `space-data-network-sdn` | Space Data Network (SDN) | FUNDED_GROWING (SpaceX sole-source) | YSS report — the replacement |
| `afrl-quantum-networking-ionq` | AFRL Quantum Networking | UNFUNDED_TWO_PLUS_YEARS | IONQ short report 2026-02-04 |
| `afrl-qubitekk-contract` | AFRL Qubitekk Quantum Networking | FUNDED_STEADY | IONQ report — distinguishes from above |
| `umd-quantum-funded-by-ionq` | UMD Quantum (IONQ subcontractor) | UNFUNDED_THIS_YEAR | IONQ report |
| `sda-tracking-layer-t3` | Tranche 3 Tracking Layer | FUNDED_STEADY | YSS report — disambiguates T3 Transport vs T3 Tracking |
