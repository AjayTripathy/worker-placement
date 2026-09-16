"""Tier 1 / Test A — Deterministic-screen ablation.

Applies a purely deterministic LONG screen to the same 64 scored names
and compares its picks to the LLM framework's LOOSE_LONG basket.

DETERMINISTIC SCREEN (deterministic-only, no LLM):
  PASS if ALL hold:
    1. going_concern_signal == NO_GOING_CONCERN
       (from m_sources/going_concern_detector.py against cached 10-K)
    2. auditor_signal == CLEAN_BIG4_TENURE
       (continuous Big-4 tenure — implicitly satisfies "no Item 4.01 8-K"
        change-of-auditor disclosure)
    3. <=3 hits on "covenant/forbearance/credit-modification" regex in 10-K
       (proxy for "no covenant amendment 24mo")
    4. <=0 hits on "dividend suspended/eliminated/reduced" regex in 10-K
       (proxy for "no dividend cut")

LIMITATIONS:
  - #3 and #4 use 10-K text scanning, not 8-K filings; coverage of
    dividend cuts especially is weak in 10-K narrative. Many dividend
    suspensions happen via 8-K/press release with no 10-K acknowledgment.
  - #2's CLEAN_BIG4_TENURE excludes CLEAN_TIER_2_TENURE (4 names) by
    construction — Big-4 only is stricter than RESUME_NEXT.md text.

OUTPUT:
  - Overlap matrix: framework LONG picks vs deterministic LONG picks
  - Return-spread on disagreements (framework-only, det-only, both)
  - Bottom-line: does deterministic screen capture most of the alpha,
    or does the LLM contribute marginally beyond rule-based filters?

Usage:
    python3 verticals/public_co/data/_backtest/survivorship_2025_05/tier1_test_A_ablation.py
"""
import json
import re
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = Path(__file__).resolve().parents[5]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from core.control_suite import basket_overlap

DET = HERE / "deterministic_local.json"
SYNTH = HERE / "synthesis.json"
DATA_ROOT = Path(__file__).resolve().parents[2]  # verticals/public_co/data


COVENANT_RE = re.compile(
    r"(amendment\s+(?:no\.?\s*\d+\s+)?to\s+(?:the\s+|our\s+)?(?:senior\s+)?(?:secured\s+)?credit\s+(?:agreement|facility)"
    r"|amended\s+(?:and\s+restated\s+)?(?:our\s+)?credit\s+(?:agreement|facility)"
    r"|covenant\s+waiver"
    r"|waived\s+(?:the\s+)?(?:financial\s+)?covenant"
    r"|forbearance\s+agreement"
    r"|in\s+default\s+(?:of|under)\s+(?:the\s+|our\s+)?(?:credit|loan|debt)"
    r"|technical\s+default"
    r"|debt\s+modification)",
    re.IGNORECASE,
)

DIVIDEND_RE = re.compile(
    r"(suspended\s+(?:our|the)\s+(?:quarterly\s+|cash\s+)?dividend"
    r"|dividend\s+(?:was|has\s+been)\s+suspended"
    r"|reduced\s+(?:our|the)\s+(?:quarterly\s+|cash\s+)?dividend"
    r"|eliminated\s+(?:our|the)\s+(?:quarterly\s+|cash\s+)?dividend"
    r"|cut\s+(?:our|the)\s+(?:quarterly\s+|cash\s+)?dividend"
    r"|discontinue(?:d)?\s+(?:our|the)\s+(?:quarterly\s+|cash\s+)?dividend"
    r"|dividend\s+suspension)",
    re.IGNORECASE,
)


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def scan_10k(ticker: str) -> dict:
    """Return covenant + dividend hit counts for the cached 10-K."""
    tkl = ticker.lower()
    d = DATA_ROOT / tkl / "filings_2025_05_15"
    if not d.exists():
        return {"have_10k": False, "covenant_hits": None, "dividend_hits": None}
    files = list(d.glob("*_10K.txt"))
    if not files:
        return {"have_10k": False, "covenant_hits": None, "dividend_hits": None}
    text = files[0].read_text(errors="ignore")
    text = _strip_html(text)
    return {
        "have_10k": True,
        "covenant_hits": len(COVENANT_RE.findall(text)),
        "dividend_hits": len(DIVIDEND_RE.findall(text)),
        "10k_len": len(text),
    }


COVENANT_THRESHOLD = 3  # > this many = covenant-stress
DIVIDEND_THRESHOLD = 0  # > this many = dividend-action disclosure


def deterministic_long(d: dict, scan: dict) -> tuple[bool, dict]:
    """Return (passes, reasons-dict)."""
    reasons = {
        "no_gc": d["going_concern_signal"] == "NO_GOING_CONCERN",
        "clean_big4": d["auditor_signal"] == "CLEAN_BIG4_TENURE",
        "no_covenant_stress": (scan["covenant_hits"] is None) or (scan["covenant_hits"] <= COVENANT_THRESHOLD),
        "no_dividend_cut": (scan["dividend_hits"] is None) or (scan["dividend_hits"] <= DIVIDEND_THRESHOLD),
        "have_10k": scan["have_10k"],
    }
    passes = all([reasons["no_gc"], reasons["clean_big4"], reasons["no_covenant_stress"], reasons["no_dividend_cut"]])
    return passes, reasons


def main():
    det = json.loads(DET.read_text())
    synth = json.loads(SYNTH.read_text())
    framework = {r["ticker"]: r for r in synth}

    print("=" * 96)
    print("TIER 1 / TEST A — Deterministic-screen ablation")
    print("=" * 96)

    det_rows = []
    for d in det:
        tk = d["ticker"]
        scan = scan_10k(tk)
        passes, reasons = deterministic_long(d, scan)
        fr = d.get("forward_return")
        det_rows.append({
            "ticker": tk,
            "company": d.get("company"),
            "group": d.get("group"),
            "forward_return": fr,
            "gc_signal": d["going_concern_signal"],
            "aud_signal": d["auditor_signal"],
            "covenant_hits": scan["covenant_hits"],
            "dividend_hits": scan["dividend_hits"],
            "have_10k": scan["have_10k"],
            "det_long": passes,
            "fail_reasons": [k for k, v in reasons.items() if not v and k != "have_10k"],
        })

    det_long = [r for r in det_rows if r["det_long"] and r["forward_return"] is not None]
    framework_long_tickers = {r["ticker"] for r in synth if r["tier"] in ("STRICT_LONG", "LOOSE_LONG") and r["forward_return"] is not None}
    det_long_tickers = {r["ticker"] for r in det_long}

    print()
    print(f"Deterministic LONG basket: n={len(det_long_tickers)} of 65")
    print(f"  Tickers: {sorted(det_long_tickers)}")
    print()
    print(f"Framework LOOSE_LONG basket: n={len(framework_long_tickers)}")
    print(f"  Tickers: {sorted(framework_long_tickers)}")
    print()

    ov = basket_overlap(det_long_tickers, framework_long_tickers)
    both, only_det, only_fmw = ov["both"], ov["only_a"], ov["only_b"]
    print("OVERLAP:")
    print(f"  Both:          n={len(both):2}  {sorted(both)}")
    print(f"  Det-only:      n={len(only_det):2}  {sorted(only_det)}")
    print(f"  Framework-only:n={len(only_fmw):2}  {sorted(only_fmw)}")
    print()

    def basket_return(tickers):
        rets = []
        for tk in tickers:
            r = framework.get(tk) or next((x for x in det if x["ticker"] == tk), None)
            if r and r.get("forward_return") is not None:
                rets.append(r["forward_return"])
        return rets

    both_rets = basket_return(both)
    only_det_rets = basket_return(only_det)
    only_fmw_rets = basket_return(only_fmw)
    det_all_rets = basket_return(det_long_tickers)
    fmw_all_rets = basket_return(framework_long_tickers)

    def line(label, rets):
        if not rets:
            print(f"  {label:36} n=0")
            return
        print(f"  {label:36} n={len(rets):2}  mean={statistics.mean(rets)*100:+7.1f}%  median={statistics.median(rets)*100:+7.1f}%")

    print("RETURNS:")
    line("Framework LOOSE_LONG basket",     fmw_all_rets)
    line("Deterministic LONG basket",       det_all_rets)
    line("  agreement (both)",              both_rets)
    line("  det-only (framework excluded)", only_det_rets)
    line("  framework-only (det excluded)", only_fmw_rets)

    # Marginal contribution: among the names framework includes but det excludes,
    # how do their returns compare to det-only names?
    print()
    if only_fmw_rets and only_det_rets:
        delta = statistics.mean(only_fmw_rets) - statistics.mean(only_det_rets)
        print(f"  Marginal LLM lift (fmw-only minus det-only) = {delta*100:+.1f} pp")
    if fmw_all_rets and det_all_rets:
        delta_total = statistics.mean(fmw_all_rets) - statistics.mean(det_all_rets)
        print(f"  Total basket delta (fmw minus det)         = {delta_total*100:+.1f} pp")

    print()
    print("FRAMEWORK LOOSE_LONG picks that FAIL det screen (why?):")
    for tk in sorted(only_fmw):
        row = next(r for r in det_rows if r["ticker"] == tk)
        fr = row["forward_return"]
        fr_s = f"{fr*100:+.1f}%" if fr is not None else "  null"
        print(f"  {tk:6}  fwd={fr_s:>8}  fail={row['fail_reasons']}  gc={row['gc_signal']}  aud={row['aud_signal']}  cov={row['covenant_hits']} div={row['dividend_hits']}")

    print()
    print("DET-ONLY picks that framework rated SHORT/NEUTRAL (why?):")
    for tk in sorted(only_det):
        f = framework.get(tk, {})
        fr = f.get("forward_return")
        fr_s = f"{fr*100:+.1f}%" if fr is not None else "  null"
        print(f"  {tk:6}  fwd={fr_s:>8}  framework_tier={f.get('tier'):12}  composite={f.get('composite_recomputed', 0):.3f}")

    # Save
    out = HERE / "tier1_test_A_results.json"
    out.write_text(json.dumps({
        "det_long_basket": sorted(det_long_tickers),
        "framework_long_basket": sorted(framework_long_tickers),
        "both": sorted(both),
        "only_det": sorted(only_det),
        "only_framework": sorted(only_fmw),
        "framework_basket_mean": statistics.mean(fmw_all_rets) if fmw_all_rets else None,
        "det_basket_mean": statistics.mean(det_all_rets) if det_all_rets else None,
        "marginal_llm_lift_pp": (statistics.mean(only_fmw_rets) - statistics.mean(only_det_rets)) if (only_fmw_rets and only_det_rets) else None,
        "total_basket_delta_pp": (statistics.mean(fmw_all_rets) - statistics.mean(det_all_rets)) if (fmw_all_rets and det_all_rets) else None,
        "det_rows": det_rows,
    }, indent=2))
    print(f"\nSaved to {out}")


if __name__ == "__main__":
    main()
