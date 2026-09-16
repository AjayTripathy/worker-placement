"""ai_behavior_tells — informed-behavior member of the AI-break ensemble.

Aggregates the behavior of parties holding PRIVATE information about the cycle, instead of
modeling the cycle: insiders, round negotiators, lenders, accountants. Composition rule per
the detector doctrine: UNION of narrow high-precision tells, never a weighted average —
each tell fires rarely and means something when it does.

THE TELLS (state: FIRED / QUIET / UNKNOWN — unknowns are reported, never guessed):
  T1 insider_sale_clusters   AUTOMATED: yfinance insider transactions for NVDA/ORCL/SMCI/
                             VRT/CRWV — net-sale intensity last 90d vs prior 90d (>2x and
                             >=3 distinct officers = FIRED). Routine 10b5-1 drip = QUIET.
  T2 round_structure         MANUAL: ratchets/seniority/guarantees in any new lab round
                             (the sophisticated money pricing the tail while the headline
                             mark says otherwise). Update via `python3 -m desk.models.ai_behavior_tells set T2 fired|quiet "note"`.
  T3 originate_to_distribute MANUAL: lenders securitizing AI-infra loans (CRWV DDTL 5.0
                             securitization May-26 per the article [UNVERIFIED]) — the
                             lender wanting OUT is the tell. Currently: suspected-fired
                             pending verification.
  T4 depreciation_extension  MANUAL: hyperscalers extending server useful lives again
                             (margin masking). Several extended 2020-2025; a NEW extension
                             during decel = FIRED.
  T5 lab_employee_tenders    MANUAL: OpenAI/Anthropic employee secondary-sale behavior —
                             oversubscribed seller interest at flat marks = FIRED.
  T6 auditor_or_metric_swap  MANUAL: any AI-complex name discontinuing a disclosure metric
                             mid-decel (the ACN GenAI-bookings pattern) or auditor change.

    python3 -m desk.models.ai_behavior_tells            # run + write JSON
    python3 -m desk.models.ai_behavior_tells set T3 fired "DDTL 5.0 securitization verified via ..."
Writes desk/data/ai_ensemble/behavior_tells.json. State file keeps manual tells across runs.
"""
from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1].parent
OUT = ROOT / "desk" / "data" / "ai_ensemble" / "behavior_tells.json"
STATE = ROOT / "desk" / "data" / "ai_behavior_tells_state.json"

NAMES = ["NVDA", "ORCL", "SMCI", "VRT", "CRWV"]

MANUAL_DEFAULTS = {
    "T2_round_structure": {"state": "UNKNOWN", "note": "no post-Mar-26 round terms examined yet"},
    "T3_originate_to_distribute": {"state": "UNKNOWN",
                                   "note": "article claims CRWV DDTL 5.0 securitized May-26 — UNVERIFIED; verify before firing"},
    "T4_depreciation_extension": {"state": "QUIET",
                                  "note": "2020-25 extensions are old news/priced; tell = a NEW extension announced during decel"},
    "T5_lab_employee_tenders": {"state": "UNKNOWN", "note": "no tender-behavior source wired"},
    "T6_auditor_or_metric_swap": {"state": "QUIET",
                                  "note": "ACN discontinued GenAI-bookings metric (scan-8 court) — services-sector, adjacent not core; watching for a core-complex instance"},
}


def _state():
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"manual": dict(MANUAL_DEFAULTS)}


def _insider_tell():
    """T1: net insider-sale intensity, last 90d vs prior 90d, per name."""
    try:
        import yfinance as yf
        import pandas as pd
    except Exception:
        return {"state": "UNKNOWN", "note": "yfinance unavailable"}
    fired, detail = [], {}
    for t in NAMES:
        try:
            tx = yf.Ticker(t).insider_transactions
            if tx is None or tx.empty:
                detail[t] = "no data"
                continue
            tx = tx.copy()
            dcol = next((c for c in tx.columns if "Date" in str(c)), None)
            scol = next((c for c in tx.columns if "Share" in str(c)), None)
            tcol = next((c for c in tx.columns if "Text" in str(c) or "Transaction" in str(c)), None)
            if not (dcol and scol):
                detail[t] = "unparsed schema"
                continue
            tx[dcol] = pd.to_datetime(tx[dcol], errors="coerce")
            now = pd.Timestamp.now()
            sells = tx[tx[tcol].astype(str).str.contains("Sale", case=False, na=False)] if tcol else tx
            recent = sells[sells[dcol] > now - pd.Timedelta(days=90)]
            prior = sells[(sells[dcol] <= now - pd.Timedelta(days=90)) & (sells[dcol] > now - pd.Timedelta(days=180))]
            r, p = abs(recent[scol].sum()), abs(prior[scol].sum())
            officers = recent.index.nunique() if recent.index.name else len(set(recent.index))
            ratio = (r / p) if p else (float("inf") if r else 0)
            detail[t] = {"recent_90d_shares": int(r), "prior_90d_shares": int(p),
                         "ratio": round(ratio, 2) if ratio != float("inf") else "inf",
                         "distinct_sellers_recent": int(officers)}
            if p and ratio > 2 and officers >= 3:
                fired.append(t)
        except Exception as e:
            detail[t] = f"error {type(e).__name__}"
    return {"state": "FIRED" if fired else "QUIET", "fired_names": fired, "detail": detail,
            "note": "sale-intensity 90d vs prior-90d; >2x with >=3 sellers = fired"}


def main():
    st = _state()
    t1 = _insider_tell()
    tells = {"T1_insider_sale_clusters": t1, **st["manual"]}
    n_fired = sum(1 for v in tells.values() if v.get("state") == "FIRED")
    n_unknown = sum(1 for v in tells.values() if v.get("state") == "UNKNOWN")
    state = "RED" if n_fired >= 2 else ("AMBER" if n_fired == 1 else "GREEN")
    out = {"member": "behavior_tells", "asof": datetime.date.today().isoformat(),
           "state": state, "reading": tells,
           "P_break_by_2027": None, "P_break_by_2028": None,
           "notes": [f"{n_fired}/6 tells fired, {n_unknown} UNKNOWN (coverage gap, not evidence of quiet)",
                     "union composition: any 2 independent tells firing = RED regardless of the others",
                     "no timing distribution by design — tells shift the ensemble's P, they don't date it"]}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1))
    STATE.write_text(json.dumps(st, indent=1))
    print(f"=== BEHAVIOR TELLS: {state} ({n_fired} fired / {n_unknown} unknown) ===")
    for k, v in tells.items():
        print(f"  {k:28} {v.get('state', '?'):8} {v.get('note', '')[:90]}")
        if k.startswith("T1") and isinstance(v.get("detail"), dict):
            for t, d in v["detail"].items():
                print(f"      {t:6} {d}")


def set_tell(tell: str, state: str, note: str):
    st = _state()
    key = next((k for k in st["manual"] if k.startswith(tell)), None)
    assert key, f"unknown tell {tell}; use T2-T6"
    st["manual"][key] = {"state": state.upper(), "note": note,
                         "set": datetime.date.today().isoformat()}
    STATE.write_text(json.dumps(st, indent=1))
    print(f"[behavior_tells] {key} -> {state.upper()} ({note})")
    main()


if __name__ == "__main__":
    if len(sys.argv) > 3 and sys.argv[1] == "set":
        set_tell(sys.argv[2], sys.argv[3], " ".join(sys.argv[4:]))
    else:
        main()
