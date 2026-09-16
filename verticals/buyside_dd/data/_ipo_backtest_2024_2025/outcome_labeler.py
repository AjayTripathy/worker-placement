"""Survivorship-free adverse-outcome labels from EDGAR (no price source).

These are the HARD adverse events, all indexed under the issuer CIK and all
immune to price-survivorship (a delisted name keeps its Form 25 forever):

  - DELISTED      Form 25 / 25-NSE filed after the IPO
  - DEREGISTERED  Form 15-12B / 15-12G / 15-15D (going dark)
  - BANKRUPTCY    8-K Item 1.03 (bankruptcy or receivership)
  - RESTATEMENT   8-K Item 4.02 (non-reliance on prior financials)
  - AUDITOR_EXIT  8-K Item 4.01 (auditor change) — weak signal, recorded not scored

Foreign private issuers (6-K/20-F) don't file 8-Ks; delisting/deregistration
still appear under their CIK, so the DELISTED label is the cross-filer anchor.

MERGER / TAKE-PRIVATE is NOT adverse: shareholders are cashed out, not wiped.
A delisting that coincides with a going-private / acquisition is reclassified
as merger_delist and excluded from hard_adverse. Structured anchors:
  - SC 13E3 / DEFM14A           domestic going-private / merger proxy
  - CB / CB/A                   FPI tender-offer / business-combination notice
  - 8-K Item 2.01              completion of acquisition (ambiguous -> only counts
                                if filed within 120d before the delist/dereg date)

Price-based drawdown is a SEPARATE layer (needs a survivorship-free price feed)
and is added by price_labeler.py.

Run: python3 verticals/buyside_dd/data/_ipo_backtest_2024_2025/outcome_labeler.py
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from collections import Counter
from datetime import date
from pathlib import Path

HERE = Path(__file__).parent
COHORT = HERE / "cohort.json"
OUT = HERE / "outcomes_edgar.json"

UA = {"User-Agent": "SignalOS research 4tripathy@gmail.com"}

DELIST_FORMS = {"25", "25-NSE"}
DEREG_FORMS = {"15-12B", "15-12G", "15-15D"}
# Unambiguous going-private / acquisition forms (company is the target).
MERGER_FORMS = {"SC 13E3", "SC 13E3/A", "DEFM14A", "DEFM14C", "DEFM14-A",
                "CB", "CB/A"}
MERGER_8K_WINDOW_DAYS = 120  # 8-K 2.01 only counts as merger if near the delist


def _subs(cik: int) -> dict:
    url = f"https://data.sec.gov/submissions/CIK{cik:010d}.json"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def _first_after(recent: dict, forms_wanted: set, ipo_date: str) -> str | None:
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    hits = [dates[i] for i, f in enumerate(forms)
            if f in forms_wanted and i < len(dates) and dates[i] > ipo_date]
    return min(hits) if hits else None


def _first_8k_item(recent: dict, item_code: str, ipo_date: str) -> str | None:
    forms = recent.get("form", [])
    items = recent.get("items", [])
    dates = recent.get("filingDate", [])
    hits = []
    for i, f in enumerate(forms):
        if f != "8-K":
            continue
        it = items[i] if i < len(items) else ""
        d = dates[i] if i < len(dates) else ""
        if it and item_code in it and d > ipo_date:
            hits.append(d)
    return min(hits) if hits else None


def label_one(rec: dict) -> dict:
    cik = int(rec["cik"])
    ipo_date = rec["ipo_date"]
    d = _subs(cik)
    recent = d.get("filings", {}).get("recent", {})
    delisted = _first_after(recent, DELIST_FORMS, ipo_date)
    dereg = _first_after(recent, DEREG_FORMS, ipo_date)
    bankruptcy = _first_8k_item(recent, "1.03", ipo_date)
    restatement = _first_8k_item(recent, "4.02", ipo_date)
    auditor_exit = _first_8k_item(recent, "4.01", ipo_date)
    dates = recent.get("filingDate", [])
    latest = max(dates) if dates else None

    # Merger / take-private signal: unambiguous going-private forms, OR an 8-K
    # Item 2.01 (completion of acquisition) filed within 120d before the delist.
    merger_form = _first_after(recent, MERGER_FORMS, ipo_date)
    acq_801 = _first_8k_item(recent, "2.01", ipo_date)
    exit_date = delisted or dereg
    acq_near_exit = bool(
        acq_801 and exit_date
        and acq_801 <= exit_date
        and (date.fromisoformat(exit_date) - date.fromisoformat(acq_801)).days
            <= MERGER_8K_WINDOW_DAYS
    )
    merger_signal = merger_form or (acq_801 if acq_near_exit else None)
    merger_delist = bool(exit_date and merger_signal)

    # A merger-driven delist is NOT adverse; bankruptcy/restatement always are.
    adverse_delist = bool(exit_date) and not merger_delist
    hard_adverse = bool(bankruptcy or restatement or adverse_delist)
    return {
        "cik": rec["cik"],
        "ticker": (rec["tickers"] or [None])[0],
        "company_name": rec["company_name"],
        "ipo_date": ipo_date,
        "sic": rec.get("sic"),
        "delisted_date": delisted,
        "deregistered_date": dereg,
        "bankruptcy_date": bankruptcy,
        "restatement_date": restatement,
        "auditor_exit_date": auditor_exit,
        "merger_form_date": merger_form,
        "acq_completion_date": acq_801,
        "merger_delist": merger_delist,
        "latest_filing_date": latest,
        "hard_adverse": hard_adverse,
    }


def main() -> None:
    cohort = json.loads(COHORT.read_text())["cohort"]
    out, errors = [], 0
    for i, rec in enumerate(cohort):
        try:
            out.append(label_one(rec))
        except Exception as e:
            print(f"  [{i+1}/{len(cohort)}] ERR {rec['company_name'][:40]}: {e}", file=sys.stderr)
            errors += 1
        if i % 25 == 24:
            n_adv = sum(1 for o in out if o["hard_adverse"])
            print(f"  {i+1}/{len(cohort)} | hard-adverse so far {n_adv} | err {errors}", file=sys.stderr)
        time.sleep(0.15)

    counts = {
        "delisted": sum(1 for o in out if o["delisted_date"]),
        "deregistered": sum(1 for o in out if o["deregistered_date"]),
        "bankruptcy": sum(1 for o in out if o["bankruptcy_date"]),
        "restatement": sum(1 for o in out if o["restatement_date"]),
        "auditor_exit": sum(1 for o in out if o["auditor_exit_date"]),
        "merger_delist": sum(1 for o in out if o["merger_delist"]),
        "any_hard_adverse": sum(1 for o in out if o["hard_adverse"]),
    }
    OUT.write_text(json.dumps(
        {"n": len(out), "n_errors": errors, "counts": counts, "labels": out}, indent=2))
    print("\n=== EDGAR HARD-ADVERSE COUNTS ===", file=sys.stderr)
    for k, v in counts.items():
        print(f"  {k:<18} {v:>4}  ({v/max(1,len(out))*100:.1f}%)", file=sys.stderr)
    print(f"Wrote {OUT.name}", file=sys.stderr)


if __name__ == "__main__":
    main()
