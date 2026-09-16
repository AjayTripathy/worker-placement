"""Regenerate blinded views of the test set from _unblinded/.

The unblinded sources contain post-cutoff outcomes (`forward_return`,
`price_2026_05_15`, `date_removed`, `reason`, `date`). Scoring agents
must never see those. This script reads from `_unblinded/`, strips
the post-cutoff fields, and writes the result to the same filenames
at the top of the directory.

POST-CUTOFF FIELDS (always stripped):
  - forward_return
  - price_2026_05_15
  - date_removed
  - reason
  - date  (only present in sp600_removals.json — it's the removal date)

PRE-CUTOFF FIELDS (kept):
  - ticker, cik, company, sector, industry
  - group  (NOTE: the membership label "delisted_or_distressed" is
            itself post-cutoff information; keeping it preserves the
            experimental design but represents a known residual leak.
            See TIER1_RESULTS.md.)
  - price_2025_05_15, drawdown_2025_05_15, high_trailing
  - filing_path, filing_date, accession  (agent_manifest only)
  - category (sp600_removals only — describes removal type)
  - cutoff_date, measurement_date, notes (test_universe only — top-level)

Run:
    python3 verticals/public_co/data/_backtest/survivorship_2025_05/build_blinded.py
"""
import json
from pathlib import Path

HERE = Path(__file__).parent
UNB = HERE / "_unblinded"

LEAK_FIELDS = {"forward_return", "price_2026_05_15", "date_removed", "reason", "date"}


def strip(record: dict) -> dict:
    return {k: v for k, v in record.items() if k not in LEAK_FIELDS}


def blind_list_of_records(path_in: Path, path_out: Path):
    data = json.loads(path_in.read_text())
    blinded = [strip(r) for r in data]
    path_out.write_text(json.dumps(blinded, indent=2))
    print(f"  {path_out.name}: stripped from {len(data)} records")


def blind_dict_of_records(path_in: Path, path_out: Path):
    data = json.loads(path_in.read_text())
    blinded = {tk: strip(r) for tk, r in data.items()}
    path_out.write_text(json.dumps(blinded, indent=2))
    print(f"  {path_out.name}: stripped from {len(data)} records")


def blind_test_universe(path_in: Path, path_out: Path):
    """test_universe.json has a different shape: top-level dict with
    cohort lists nested inside. Strip fields inside each cohort list."""
    data = json.loads(path_in.read_text())
    blinded = {}
    for k, v in data.items():
        if isinstance(v, list):
            blinded[k] = [strip(r) for r in v]
        else:
            blinded[k] = v
    path_out.write_text(json.dumps(blinded, indent=2))
    print(f"  {path_out.name}: stripped")


def main():
    print("Building blinded views from _unblinded/...")
    blind_list_of_records(UNB / "combined_test_set.json", HERE / "combined_test_set.json")
    blind_list_of_records(UNB / "control_survivors.json", HERE / "control_survivors.json")
    blind_list_of_records(UNB / "sp600_removals.json",   HERE / "sp600_removals.json")
    blind_dict_of_records(UNB / "agent_manifest.json",   HERE / "agent_manifest.json")
    blind_test_universe(UNB / "test_universe.json",      HERE / "test_universe.json")
    print("\nDone. Run verify_blinded.py to confirm no leak fields remain.")


if __name__ == "__main__":
    main()
