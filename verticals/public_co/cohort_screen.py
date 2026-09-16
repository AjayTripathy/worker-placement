"""Generic EV-cohort screening harness for base-rate analysis.

Runs a standardized battery of M-source queries on each name and produces a
single severity score, so we can ask: of N companies the screen flags as
fraud-shaped, how many actually turned out fraud / failed?

The cohort is post-deSPAC EV/mobility names from 2020-2022. Each entry is
labelled with a +6mo cutoff (matching the same maturity stage we tested
NKLA/RIDE/RIVN/LCID at) and a ground-truth outcome based on what happened by
mid-2025 (bankruptcy, SEC enforcement, short-report takedown, or alive).

Output: cohort_results.json + a printed confusion matrix.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from .m_sources import edgar_fts, epa_frs, nhtsa


HERE = Path(__file__).parent
DATA = HERE / "data" / "_cohort"
DATA.mkdir(exist_ok=True, parents=True)


# (ticker, cik, name_for_search, brand_for_nhtsa_frs, factory_state,
#  cutoff_date, outcome_label, outcome_detail)
#
# Outcome label space:
#   FRAUD     — Hindenburg/MW/Wolfpack/etc. report landed; SEC action eventually
#   BANKRUPT  — chapter 11/7 by mid-2025, no fraud charges per se
#   ALIVE     — operating, hasn't blown up
#
# Cutoff = ~6 months post-deSPAC/IPO (so claims are still partly forward-looking,
#  same as NKLA/RIDE/RIVN/LCID test windows).
COHORT = [
    # known frauds (Hindenburg/MW/Wolfpack/SEC enforcement)
    ("NKLA", "0001731289", "Nikola",     "Nikola",     "AZ", "2020-09-09", "FRAUD",    "Hindenburg 2020-09-10; founder Trevor Milton convicted"),
    ("RIDE", "0001759546", "Lordstown",  "Lordstown",  "OH", "2021-03-11", "FRAUD",    "Hindenburg 2021-03-12; bankrupt 2023-06; SEC enforcement"),
    ("HYZN", "0001716583", "Hyzon",      "Hyzon",      "NY", "2022-01-15", "FRAUD",    "Blue Orca 2021-09; SEC charges 2024; Nasdaq delisting 2024; bankruptcy 2024-12"),
    ("MULN", "0001499961", "Mullen",     "Mullen",     "CA", "2022-05-15", "FRAUD",    "Hindenburg 2023-04; multiple short reports; reverse splits"),

    # bankrupted/cratered without explicit fraud charge
    ("FSR",  "0001720990", "Fisker",     "Fisker",     "CA", "2021-04-30", "BANKRUPT", "Bankruptcy 2024-06; production failures, governance issues"),
    ("GOEV", "0001750153", "Canoo",      "Canoo",      "OK", "2021-06-30", "BANKRUPT", "Bankruptcy 2025-01; chronic cash burn"),
    ("ARVL", "0001835059", "Arrival",    "Arrival",    "NC", "2021-09-30", "BANKRUPT", "Bankruptcy 2024-02; never reached production"),
    ("LEV",  "0001834974", "Lion Electric","Lion",     "IL", "2021-11-30", "BANKRUPT", "Bankruptcy 2024-12"),
    ("PTRA", "0001820630", "Proterra",   "Proterra",   "CA", "2021-12-31", "BANKRUPT", "Bankruptcy 2023-08; restructured"),
    ("FFIE", "0001805521", "Faraday Future","Faraday Future","CA","2022-01-30","BANKRUPT","Penny stock; multiple reverse splits, near-bankruptcy"),

    # alive at maturity-stage cutoff and still operating mid-2025
    ("RIVN", "0001874178", "Rivian",     "Rivian",     "IL", "2022-04-30", "ALIVE",    "Producing R1T/R1S/EDV at scale"),
    ("LCID", "0001811210", "Lucid",      "Lucid",      "AZ", "2022-03-15", "ALIVE",    "Producing Air; PIF strategic backing"),
    ("CHPT", "1777393",    "ChargePoint","ChargePoint","CA", "2021-08-30", "ALIVE",    "Charging network operator; struggling but operating"),
    ("EVGO", "1821159",    "EVgo",       "EVgo",       "CA", "2022-01-31", "ALIVE",    "Charging network operator; alive"),
    ("QS",   "1811414",    "QuantumScape","QuantumScape","CA","2021-05-31", "ALIVE",    "Solid-state battery R&D; Scorpion Capital short report 2021 didn't kill it"),
]


def screen_company(ticker: str, cik: str, name: str, brand: str,
                   state: str, cutoff: str) -> dict:
    """Run the standard EV-screen battery for one company."""
    results: dict = {"ticker": ticker, "cutoff": cutoff}

    # NHTSA: complete-vehicle vs Incomplete Vehicle test
    print(f"  [{ticker}] NHTSA...", file=sys.stderr)
    n = nhtsa.query_manufacturer(brand)
    types_l: list[str] = []
    matched = []
    for m in n.get("manufacturers", []):
        nm = (m.get("mfr_name") or "").upper()
        if brand.upper() in nm:
            matched.append(m)
            types_l.extend((t or "").lower() for t in m.get("vehicle_types", []))
    results["nhtsa_n_matching_mfgs"] = len(matched)
    results["nhtsa_types"] = sorted(set(types_l))
    results["nhtsa_complete_vehicle"] = (
        any(t in types_l for t in ("truck", "passenger car", "multipurpose passenger vehicle (mpv)"))
        and "incomplete vehicle" not in types_l
    )
    results["nhtsa_incomplete"] = "incomplete vehicle" in types_l

    # EPA FRS: factory-existence test
    print(f"  [{ticker}] EPA FRS in {state}...", file=sys.stderr)
    f = epa_frs.query_facilities(brand, state)
    results["frs_n_facilities"] = f.get("n_facilities", 0)
    factory_like = [
        x for x in f.get("facilities", [])
        if any(k in (x.get("facility_name") or "").upper()
               for k in ("FACTORY", "PLANT", "ASSEMBLY", "MANUFACTURING", "POWERTRAIN"))
    ]
    results["frs_n_factory_named"] = len(factory_like)

    # EDGAR FTS: counterparty disclosure across other US filers
    print(f"  [{ticker}] EDGAR external mentions...", file=sys.stderr)
    e = edgar_fts.query_fulltext(
        search_term=name, cutoff_date=cutoff, start_date="2018-01-01",
        forms="10-K,10-Q,8-K,DEF 14A,20-F",
    )
    if "error" in e:
        # one retry — EDGAR FTS sometimes 500s transiently
        time.sleep(2)
        e = edgar_fts.query_fulltext(
            search_term=name, cutoff_date=cutoff, start_date="2018-01-01",
            forms="10-K,10-Q,8-K,DEF 14A,20-F",
        )
    results["edgar_external_mentions"] = e.get("total_hits") or 0
    if "error" in e:
        results["edgar_error"] = e["error"]

    # Restrict the external test to "exclude self CIK" — counterparty mentions only
    # The fulltext API doesn't support a NOT-cik filter directly, so we use the
    # raw count above and accept that the company's own filings inflate it.

    return results


def score_profile(p: dict) -> dict:
    """Map a screen profile to a severity score and binary prediction.

    Score weights (out of 10):
      - NHTSA Incomplete Vehicle (chassis/glider, not complete OEM):  +4
      - NHTSA not registered as complete vehicle:                     +2
      - EPA FRS zero facilities in claimed state:                     +3
      - EPA FRS no factory-named facilities:                          +1
      - EDGAR external mentions == 0:                                 +3
      - EDGAR external mentions < 10 (thin counterparty):             +1
    """
    score = 0
    flags: list[str] = []

    if p.get("nhtsa_incomplete"):
        score += 4
        flags.append(f"NHTSA Incomplete Vehicle ({p['nhtsa_types']})")
    elif not p.get("nhtsa_complete_vehicle"):
        if p.get("nhtsa_n_matching_mfgs", 0) == 0:
            score += 2
            flags.append("NHTSA: not registered as manufacturer")
        else:
            score += 1
            flags.append(f"NHTSA: registered but not complete vehicle ({p['nhtsa_types']})")

    if p.get("frs_n_facilities", 0) == 0:
        score += 3
        flags.append(f"EPA FRS: zero facilities in claimed state")
    elif p.get("frs_n_factory_named", 0) == 0:
        score += 1
        flags.append(f"EPA FRS: {p['frs_n_facilities']} sites but none factory-named")

    n_ext = p.get("edgar_external_mentions", 0)
    if n_ext == 0:
        score += 3
        flags.append("EDGAR: zero counterparty mentions")
    elif n_ext < 10:
        score += 1
        flags.append(f"EDGAR: only {n_ext} counterparty mentions")

    return {
        "severity_score": score,
        "predicted_fraud": score >= 5,
        "flags": flags,
    }


def run_cohort() -> list[dict]:
    out: list[dict] = []
    for ticker, cik, name, brand, state, cutoff, outcome, detail in COHORT:
        print(f"\n=== {ticker} ({outcome}) ===", file=sys.stderr)
        profile = screen_company(ticker, cik, name, brand, state, cutoff)
        scored = score_profile(profile)
        out.append({
            **profile,
            "name": name,
            "outcome": outcome,
            "outcome_detail": detail,
            **scored,
        })
        time.sleep(0.5)
    (DATA / "cohort_results.json").write_text(json.dumps(out, indent=2, default=str))
    print(f"\nWrote {len(out)} cohort results to {DATA}", file=sys.stderr)
    return out


def confusion_matrix(results: list[dict]) -> None:
    """Predicted (fraud-flagged) vs Actual (FRAUD/BANKRUPT/ALIVE).

    Two definitions of 'actual bad':
      - Strict: only FRAUD outcomes count as positive
      - Loose: FRAUD + BANKRUPT both count as positive
    """
    print()
    print("=" * 100)
    print(f"{'Ticker':<8} {'Score':<6} {'Pred':<8} {'Outcome':<10} {'Flags'}")
    print("-" * 100)
    for r in sorted(results, key=lambda x: -x["severity_score"]):
        flags_short = "; ".join(r["flags"]) or "(none)"
        if len(flags_short) > 60:
            flags_short = flags_short[:57] + "..."
        pred = "FRAUD" if r["predicted_fraud"] else "CLEAN"
        print(f"{r['ticker']:<8} {r['severity_score']:>2}/10  {pred:<8} {r['outcome']:<10} {flags_short}")
    print("=" * 100)

    for label, positive_set in [
        ("Strict (FRAUD only)", {"FRAUD"}),
        ("Loose (FRAUD + BANKRUPT)", {"FRAUD", "BANKRUPT"}),
    ]:
        tp = sum(1 for r in results if r["predicted_fraud"] and r["outcome"] in positive_set)
        fp = sum(1 for r in results if r["predicted_fraud"] and r["outcome"] not in positive_set)
        tn = sum(1 for r in results if not r["predicted_fraud"] and r["outcome"] not in positive_set)
        fn = sum(1 for r in results if not r["predicted_fraud"] and r["outcome"] in positive_set)
        n = tp + fp + tn + fn
        precision = tp / (tp + fp) if (tp + fp) else float("nan")
        recall = tp / (tp + fn) if (tp + fn) else float("nan")
        specificity = tn / (tn + fp) if (tn + fp) else float("nan")
        print(f"\n  {label}:  TP={tp}  FP={fp}  TN={tn}  FN={fn}  (n={n})")
        print(f"    Precision (of flagged, % truly bad):  {precision:.0%}")
        print(f"    Recall    (of bad, % flagged):        {recall:.0%}")
        print(f"    Specificity (of good, % cleared):     {specificity:.0%}")


def main() -> None:
    results = run_cohort()
    confusion_matrix(results)


if __name__ == "__main__":
    main()
