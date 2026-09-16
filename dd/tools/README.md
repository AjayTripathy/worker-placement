# dd/tools — buyside DD utilities

Helpers to run *before* analytic content review on any data room. Catches the kind of structural disclosure gaps that are easy to miss when you dive straight into the spreadsheet math.

## `audit_xlsx.py` — column-completeness audit

Built after the Reawaken Capital DD (2026-05-22) where a pipeline xlsx column titled "Address (Zillow Link)" was populated with city + zip only, making the entire pipeline unverifiable against public records. Took a user prompt to catch on the original review. This script catches it in seconds.

### Usage

```bash
python3 dd/tools/audit_xlsx.py path/to/data_room.xlsx
```

Optional flags:
- `--sheet SHEET_NAME` — specific sheet (default: first)
- `--json` — raw JSON output for downstream tooling

Exit code:
- `0` — no columns flagged (clean)
- `1` — one or more columns flagged

### What it catches

| Flag | What triggers it |
|---|---|
| `HEADER_PROMISE_VIOLATED` | Column header advertises a content type (address, URL, email, phone, date, EIN, etc.) but <50% of cells match the expected pattern |
| `EXPECTED_HYPERLINKS_MISSING` | Header contains "link" / "url" but column has zero hyperlinks |
| `IDENTIFIER_NOT_UNIQUE` | Header implies per-row identifier (address, ID, key, accession) but <50% of rows have unique values |
| `LOW_POPULATION` | <50% of effective data rows have a value (effective rows = max populated count across columns; trailing blank rows are ignored) |
| `SUSPECT_REDACTION` | Cell pattern suggests partial redaction — e.g., "City, ST ZIP" in an Address column, or runs of `***` / `XXX` / `---` |

### Workflow

1. **First action on any data-room xlsx**: run this.
2. If anything fires HEADER_PROMISE_VIOLATED, EXPECTED_HYPERLINKS_MISSING, or SUSPECT_REDACTION on a verifiable-claim column (address, deal ID, EIN, etc.), **stop and flag it at the top of the DD report**. The data room itself is non-verifiable on that dimension and that finding outranks any analytic content.
3. Then proceed with content review.

### Extending

The expectation rules live in `EXPECTATIONS` (header keyword → predicate + description). To add a new field type:

```python
EXPECTATIONS[("lat", "latitude")] = (
    lambda v: bool(re.match(r"-?\d{1,3}\.\d+", v or "")),
    "decimal latitude",
)
```

Identifier headers live in `IDENTIFIER_HEADER_TOKENS` — add tokens whose columns should have unique-per-row values.

Suspect-redaction patterns are hardcoded in the body of `audit_column()`; add new patterns there.
