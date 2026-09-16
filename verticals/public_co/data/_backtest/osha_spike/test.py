"""OSHA Form 300A spike — does establishment headcount data
differentiate inflated from real factory-output claims?

Test panel mixes:
  - Known large manufacturers (LMT, Boeing, GM) — expected REGISTERED
  - Defense small-caps with claimed manufacturing (AIRO, KTOS, RCAT)
  - Fresh-universe names with operational claims (KULR, HDSN, PESI,
    ALMU, KLIC)
  - Controls without manufacturing footprint (LRHC, Akazoo)

For each test case we record:
  - n establishments matching the company name
  - sum of annual_average_employees
  - top NAICS codes / states
  - signal band

The hypothesis: REAL manufacturing companies have multi-establishment
footprints with hundreds-to-thousands of employees per site. Inflated
'manufacturing' claims show up as 0 or 1 establishments with low
headcount.
"""
from __future__ import annotations

import json
from pathlib import Path

from verticals.public_co.m_sources.osha_establishments import query_establishments


HERE = Path(__file__).parent

PANEL = [
    # KNOWN large manufacturers — calibrate REGISTERED_EMPLOYER
    ("LMT",   "Lockheed Martin"),
    ("NOC",   "Northrop Grumman"),
    ("BA",    "Boeing"),
    ("GM",    "General Motors"),

    # Defense small-caps with claimed manufacturing
    ("AIRO_grp",   "AIRO Group"),
    ("AIRO_only",  "AIRO"),
    ("KTOS",  "Kratos"),
    ("RCAT",  "Red Cat"),
    ("KSCP",  "Knightscope"),
    ("ONDS",  "Ondas"),

    # Fresh-universe operational claimants
    ("PESI",  "Perma-Fix"),
    ("KULR",  "KULR"),
    ("HDSN",  "Hudson Technologies"),
    ("ALMU",  "Aeluma"),
    ("KLIC",  "Kulicke"),

    # Controls
    ("LRHC",  "La Rosa Holdings"),
    ("CWCO",  "Consolidated Water"),
    ("AKAZOO","Akazoo"),

    # AIRO Phoenix specifically — address-based check
    ("AIRO_phx_city", None, {"city": "PHOENIX", "state": "AZ", "naics_prefix": "3364"}),
]


def main():
    rows = []
    print(f"{'label':18s} {'name':25s} {'n_est':>5s} {'emps':>7s} {'top_naics':25s} {'states':25s}  signal")
    print("=" * 130)
    for entry in PANEL:
        if len(entry) == 3:
            label, name, extra = entry
            r = query_establishments(company_name=name, **extra)
        else:
            label, name = entry
            r = query_establishments(company_name=name)
        n = r.get("n_matches", 0)
        emps = r.get("total_employees", 0)
        top_naics = list(r.get("naics_breakdown", {}).items())[:2]
        top_states = list(r.get("by_state", {}).items())[:3]
        sig = r.get("signal", "?")
        nm_disp = name or "(addr-only)"
        print(f"  {label:16s} {nm_disp:25s} {n:>5d} {emps:>7d}  "
              f"{str(top_naics)[:23]:25s} {str(top_states)[:23]:25s}  {sig}")
        rows.append({"label": label, "company_name": name, "result": r})

    (HERE / "spike_results.json").write_text(json.dumps(rows, indent=2, default=str))
    print(f"\nWrote {HERE / 'spike_results.json'}")


if __name__ == "__main__":
    main()
