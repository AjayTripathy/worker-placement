"""Spike test for the megacap-namecheck connector.

Hypothesis: the connector differentiates real megacap partnerships
from inflated/fabricated ones via 8-K/10-K/10-Q mention frequency on
the MEGACAP'S side (asymmetric from H7's small-cap-side test).

Test panel:
  REAL partnerships (positive controls):
    - Plug Power (PLUG) × Amazon (warrants deal, public PR cadence)
    - Plug Power × Walmart (warrants deal)
    - Anthropic × Amazon — N/A (private)
    - SES AI × Hyundai-Kia (real automotive partnership) [non-US, skip]

  INFLATED partnerships (alleged):
    - Lordstown (RIDE) × major fleet operators (Hindenburg flagged)
    - Nikola (NKLA) × GM (announced then dramatically reduced post-
      Hindenburg)
    - Hyzon (HYZN) × claimed truck-fleet partners

  FABRICATED partnerships:
    - Akazoo (now-delisted) × Sony / Universal / Warner Music
      (SEC enforcement 2020 for revenue + customer fabrication)

  CONTROL — small-caps with NO megacap partnership claim:
    - HDSN (Hudson Technologies, refrigerants — no megacap pairing)
    - LRHC (La Rosa Holdings, real estate — no megacap pairing)

Expectation: real partnerships should hit on the relevant megacap CIK
with multiple filings; inflated should hit lightly; fabricated should
hit zero; controls should hit zero (no claim, no expected presence).
"""
from __future__ import annotations

import json
from pathlib import Path

from verticals.public_co.m_sources.megacap_namecheck import (
    query_megacap_mentions,
)


HERE = Path(__file__).parent
CUTOFF = "2026-05-18"

# Pairs: (label, small_cap_full_name, megacap_subset, expected_band)
PANEL = [
    # REAL
    ("REAL_PLUG_AMZN",   "Plug Power",
     ["Amazon"], "RECURRING_RELATIONSHIP"),
    ("REAL_PLUG_WMT",    "Plug Power",
     ["Walmart"], "RECURRING_RELATIONSHIP"),

    # ALLEGED INFLATED
    ("INFLATED_NKLA_GM", "Nikola Corporation",
     ["GeneralMotors"], "?"),
    ("INFLATED_NKLA_GM_alt", "Nikola",
     ["GeneralMotors"], "?"),
    ("INFLATED_RIDE",    "Lordstown Motors",
     ["GeneralMotors", "Ford", "Boeing"], "?"),

    # FABRICATED
    ("FAB_AKAZOO",       "Akazoo",
     ["Amazon", "Microsoft", "Apple", "Alphabet"], "INFLATION_SUSPECT"),

    # CONTROLS — fresh-universe names with no megacap partnership claim
    ("CTRL_HDSN",        "Hudson Technologies",
     ["Amazon", "Microsoft", "Apple", "Walmart"], "INFLATION_SUSPECT"),
    ("CTRL_LRHC",        "La Rosa Holdings",
     ["Amazon", "Microsoft", "Apple", "Walmart"], "INFLATION_SUSPECT"),
    ("CTRL_KULR",        "KULR Technology",
     ["Amazon", "Microsoft", "Apple", "Tesla", "Nvidia"], "?"),

    # FRESH-UNIVERSE EXTRAS: do any of these names hit megacap filings?
    ("FRESH_PESI",       "Perma-Fix Environmental",
     ["GeneralMotors", "Boeing", "LockheedMartin", "ExxonMobil"], "?"),
    ("FRESH_CDNA",       "CareDx",
     ["JNJ", "Pfizer"], "?"),

    # HIGH-END (real ecosystem / major investment) — calibrates upper threshold
    ("REAL_NVDA_AMZN",   "Nvidia",
     ["Amazon"], "RECURRING_RELATIONSHIP"),
    ("REAL_ANTHRP_AMZN", "Anthropic",
     ["Amazon"], "RECURRING_RELATIONSHIP"),
    ("REAL_INTEL_MSFT",  "Intel",
     ["Microsoft"], "RECURRING_RELATIONSHIP"),
]


def main():
    out = []
    print(f"{'label':22s} {'small_cap':25s} {'megacaps':30s} {'total':>5s}  signal")
    print("=" * 105)
    for label, name, subset, expected in PANEL:
        res = query_megacap_mentions(
            small_cap_name=name,
            cutoff_date=CUTOFF,
            megacap_subset=subset,
            window_days=3650,
        )
        total = res["total_hits_across_megacaps"]
        sig = res["signal"]
        # Per-megacap counts inline
        per_mc = ", ".join(
            f"{mc}={d['total_hits']}" for mc, d in res["by_megacap"].items()
        )
        print(f"  {label:20s} {name:25s} {per_mc:30s} {total:>5d}  {sig}  (expect {expected})")
        out.append({
            "label": label,
            "small_cap_name": name,
            "megacap_subset": subset,
            "expected": expected,
            "result": res,
        })

    (HERE / "spike_results.json").write_text(json.dumps(out, indent=2, default=str))
    print(f"\nWrote {HERE / 'spike_results.json'}")


if __name__ == "__main__":
    main()
