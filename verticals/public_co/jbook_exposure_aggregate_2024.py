"""
2024 backtest aggregator for the J-Book exposure cohort.

Reads `<TICKER>.jbook.2024.input.json` + `.jbook.2024.scores.json` and
produces matrix + PREDICTIONS.md, alongside a forward-vs-backtest diff
showing which RED/SEVE flags are pre-knowable from the 2024-09-01 cutoff
versus which only appear with 2026-05-20 cutoff (= leaked-by-time).
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from .jbook_exposure_cohort import COHORT

CUTOFF = "2024-09-01"
HERE  = Path(__file__).parent
LOCAL = HERE / "data" / "_local"
OUT   = HERE / "data" / "_jbook_exposure_cohort_2024"

SEVERITY_ORDER = ["PASS", "MODERATE_UNDERDELIVERY", "SEVERE_UNDERDELIVERY",
                  "RED_FLAG_NEGATIVE", "UNVERIFIABLE"]
SEVERITY_WEIGHT = {"PASS": 0.0, "UNVERIFIABLE": 0.0,
                    "MODERATE_UNDERDELIVERY": 1.0,
                    "SEVERE_UNDERDELIVERY": 2.0,
                    "RED_FLAG_NEGATIVE": 3.0}


def load_ticker_backtest(ticker: str):
    inp = LOCAL / f"{ticker}.jbook.2024.input.json"
    sco = LOCAL / f"{ticker}.jbook.2024.scores.json"
    if not inp.exists() or not sco.exists():
        return None
    return {"input": json.loads(inp.read_text()),
             "scores": json.loads(sco.read_text())}


def load_ticker_forward(ticker: str):
    inp = LOCAL / f"{ticker}.jbook.input.json"
    sco = LOCAL / f"{ticker}.jbook.scores.json"
    if not inp.exists() or not sco.exists():
        return None
    return {"input": json.loads(inp.read_text()),
             "scores": json.loads(sco.read_text())}


def severity_counts(scores):
    c = Counter(s.get("severity", "UNKNOWN") for s in scores)
    return {k: c.get(k, 0) for k in SEVERITY_ORDER}


def composite_score(scores):
    counted = [s for s in scores if s.get("severity") != "UNVERIFIABLE"]
    if not counted:
        return 0.0
    return sum(SEVERITY_WEIGHT.get(s.get("severity"), 0) for s in counted) / max(1, len(counted))


def jbook_hit_count(scores):
    return sum(1 for s in scores if "jbook" in (s.get("M_check") or "").lower())


def build_matrix():
    out = []
    for m in COHORT:
        bt = load_ticker_backtest(m.ticker)
        fw = load_ticker_forward(m.ticker)
        if not bt:
            out.append({"ticker": m.ticker, "company": m.name, "status": "NOT_RUN_BACKTEST"})
            continue
        bs = bt["scores"].get("scores", [])
        fs = fw["scores"].get("scores", []) if fw else []
        out.append({
            "ticker": m.ticker, "cik": m.cik, "company": m.name, "status": "OK",
            "n_claims":   len(bt["input"].get("claims", [])),
            "n_jbook_hits": jbook_hit_count(bs),
            "filing":     bt["input"].get("filing"),
            "backtest_severity_counts":  severity_counts(bs),
            "backtest_composite":        composite_score(bs),
            "forward_severity_counts":   severity_counts(fs) if fs else None,
            "forward_composite":         composite_score(fs) if fs else None,
            "delta_composite":           (composite_score(bs) - composite_score(fs)) if fs else None,
            "red_flag_claims":  [s for s in bs if s.get("severity") == "RED_FLAG_NEGATIVE"],
            "severe_claims":    [s for s in bs if s.get("severity") == "SEVERE_UNDERDELIVERY"],
            "moderate_claims":  [s for s in bs if s.get("severity") == "MODERATE_UNDERDELIVERY"],
        })
    out.sort(key=lambda r: (
        0 if r.get("status") == "OK" else 1,
        -(r.get("backtest_composite") or 0),
    ))
    return out


def write_report(matrix):
    OUT.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    w = lines.append
    completed = [r for r in matrix if r.get("status") == "OK"]
    pending   = [r for r in matrix if r.get("status") != "OK"]

    w(f"# J-Book Exposure Cohort — 2024 Backtest\n")
    w(f"_Generated {datetime.utcnow().isoformat()}Z — backtest cutoff {CUTOFF}_\n")
    w(f"_{len(completed)} completed, {len(pending)} not-run_\n")

    w("## Methodology — backtest mode\n")
    w("Same subagent + same M-source catalog as the 2026-05-20 forward test, "
       "with two changes:\n\n"
       "1. Cutoff set to 2024-09-01. Each subagent picks the most-recent pre-cutoff "
       "filing (typically Feb-Apr 2024 10-Ks for FY 2023 fiscal year).\n"
       "2. `cutoff_date=\"2024-09-01\"` passed to every pentagon_jbook + doe_budget "
       "query. The corpus filters out FY 2025+ funding rows that wouldn't have been "
       "knowable in fall 2024.\n\n"
       "**Limitation:** the corpus _vintage_ is FY 2026 (programs that exist in our "
       "JSON are 2026-era PEs). We cannot replicate PEs that have since been renamed/"
       "consolidated. The cutoff filter is best-effort but not historically perfect.\n")

    w("## Backtest composite ranking\n")
    w("| Rank | Ticker | Company | Filing | Claims | JBook hits | "
      "PASS | MOD | SEVE | RED | UNV | BT Composite | FW Composite | Δ |")
    w("|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for i, r in enumerate(completed, 1):
        sc = r["backtest_severity_counts"]
        fwc = r.get("forward_composite")
        delta = r.get("delta_composite")
        fw_str  = f"{fwc:.2f}"   if fwc   is not None else "-"
        dlt_str = f"{delta:+.2f}" if delta is not None else "-"
        w(f"| {i} | {r['ticker']} | {r['company'][:30]} | "
          f"{(r['filing'] or '?')[:30]} | "
          f"{r['n_claims']} | {r['n_jbook_hits']} | "
          f"{sc['PASS']} | {sc['MODERATE_UNDERDELIVERY']} | "
          f"{sc['SEVERE_UNDERDELIVERY']} | {sc['RED_FLAG_NEGATIVE']} | "
          f"{sc['UNVERIFIABLE']} | {r['backtest_composite']:.2f} | "
          f"{fw_str} | {dlt_str} |")
    if pending:
        w(f"\n_Pending: {', '.join(r['ticker'] for r in pending)}_")
    w("")

    w("## Interpretation\n")
    w("**Δ** column = backtest composite − forward composite. Positive Δ means the "
      "framework reads MORE severe at 2024 cutoff than at 2026 cutoff (rare, would "
      "suggest the program eventually got refunded). Negative Δ means the forward "
      "view exposes more divergence than was knowable in fall 2024 (expected for "
      "tickers whose programs only got de-funded after the cutoff).\n\n"
      "**The interesting cases are the ones where the backtest already showed "
      "SEVERE/RED.** Those are framework hits with pre-knowable evidence — what we'd "
      "have flagged in fall 2024 with the same pipeline.\n")

    w("## Per-ticker backtest findings\n")
    for r in completed:
        w(f"### {r['ticker']} — {r['company']}\n")
        w(f"- **Filing analyzed:** `{r['filing']}`")
        w(f"- **Claims:** {r['n_claims']}  (J-Book M-source fired on {r['n_jbook_hits']})")
        sc = r['backtest_severity_counts']
        w(f"- **Severity:** PASS={sc['PASS']}, MOD={sc['MODERATE_UNDERDELIVERY']}, "
          f"SEVE={sc['SEVERE_UNDERDELIVERY']}, RED={sc['RED_FLAG_NEGATIVE']}, "
          f"UNV={sc['UNVERIFIABLE']}")
        fwc = r.get('forward_composite')
        fwc_str = f"{fwc:.2f}" if fwc is not None else "-"
        w(f"- **Composite (backtest):** {r['backtest_composite']:.2f}  (forward: {fwc_str})\n")
        if r["red_flag_claims"]:
            w("#### 🔴 RED_FLAG_NEGATIVE (pre-knowable at 2024-09-01)")
            for s in r["red_flag_claims"]:
                w(f"- **{s.get('claim_id','?')}** — {s.get('claim_text','')[:230]}")
                w(f"  - M-check: `{s.get('M_check','?')}`")
                w(f"  - M-value: {str(s.get('M_value',''))[:280]}")
                w(f"  - Interp: {s.get('interpretation','')[:400]}\n")
        if r["severe_claims"]:
            w("#### 🟠 SEVERE_UNDERDELIVERY (pre-knowable at 2024-09-01)")
            for s in r["severe_claims"]:
                w(f"- **{s.get('claim_id','?')}** — {s.get('claim_text','')[:230]}")
                w(f"  - Interp: {s.get('interpretation','')[:400]}\n")
        w("")

    (OUT / "PREDICTIONS.md").write_text("\n".join(lines))
    (OUT / "matrix.json").write_text(json.dumps(matrix, indent=2, default=str))
    print(f"Wrote {OUT}/PREDICTIONS.md ({len(completed)} backtest tickers)")


def main():
    write_report(build_matrix())


if __name__ == "__main__":
    main()
