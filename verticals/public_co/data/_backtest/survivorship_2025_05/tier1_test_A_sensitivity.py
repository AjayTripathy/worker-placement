"""Tier 1 / Test A — sensitivity sweep over deterministic-screen thresholds.

Probes whether the +49 pp framework-vs-deterministic gap is robust to
plausible alternative threshold choices, or an artifact of where I put
the covenant-hits / auditor-tier cutoffs.

Sweeps three axes:
  - Allow CLEAN_TIER_2_TENURE in addition to CLEAN_BIG4_TENURE
  - Covenant-hits threshold ∈ {3, 5, 10, 20, no_filter}
  - Drop the dividend-cut check (it never fires anyway — 10-K narrative
    rarely contains the disclosure)

For each variant: deterministic basket return + size + overlap with
framework. Surfaces whether any plausible deterministic configuration
matches the framework's basket return.
"""
import json
import re
import statistics
from pathlib import Path

HERE = Path(__file__).parent
DET = HERE / "deterministic_local.json"
SYNTH = HERE / "synthesis.json"
DATA_ROOT = Path(__file__).resolve().parents[2]


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


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def scan_10k(ticker: str) -> dict:
    tkl = ticker.lower()
    d = DATA_ROOT / tkl / "filings_2025_05_15"
    if not d.exists():
        return {"have_10k": False, "covenant_hits": None}
    files = list(d.glob("*_10K.txt"))
    if not files:
        return {"have_10k": False, "covenant_hits": None}
    text = _strip_html(files[0].read_text(errors="ignore"))
    return {
        "have_10k": True,
        "covenant_hits": len(COVENANT_RE.findall(text)),
    }


def main():
    det = json.loads(DET.read_text())
    synth = json.loads(SYNTH.read_text())
    framework_long_tickers = {r["ticker"] for r in synth if r["tier"] in ("STRICT_LONG", "LOOSE_LONG") and r["forward_return"] is not None}
    framework_long_rets = [r["forward_return"] for r in synth if r["tier"] in ("STRICT_LONG", "LOOSE_LONG") and r["forward_return"] is not None]
    framework_mean = statistics.mean(framework_long_rets)

    # Pre-scan all
    scans = {d["ticker"]: scan_10k(d["ticker"]) for d in det}

    print("=" * 100)
    print("TIER 1 / TEST A — Sensitivity sweep")
    print("=" * 100)
    print(f"Framework LOOSE_LONG: n={len(framework_long_tickers)}, mean={framework_mean*100:+.1f}%")
    print()

    variants = []
    for include_tier2 in (False, True):
        for cov_thresh in (3, 5, 10, 20, None):
            auditor_ok = ("CLEAN_BIG4_TENURE",) if not include_tier2 else ("CLEAN_BIG4_TENURE", "CLEAN_TIER_2_TENURE")

            picks = []
            for d in det:
                fr = d.get("forward_return")
                if fr is None:
                    continue
                if d["going_concern_signal"] != "NO_GOING_CONCERN":
                    continue
                if d["auditor_signal"] not in auditor_ok:
                    continue
                if cov_thresh is not None:
                    ch = scans[d["ticker"]]["covenant_hits"]
                    if ch is not None and ch > cov_thresh:
                        continue
                picks.append(d)

            tickers = {p["ticker"] for p in picks}
            rets = [p["forward_return"] for p in picks]
            mean_r = statistics.mean(rets) if rets else None
            overlap = tickers & framework_long_tickers
            row = {
                "include_tier2": include_tier2,
                "covenant_threshold": cov_thresh,
                "n_picks": len(picks),
                "mean_return": mean_r,
                "n_overlap": len(overlap),
                "delta_vs_framework_pp": (mean_r - framework_mean) if mean_r is not None else None,
                "tickers": sorted(tickers),
            }
            variants.append(row)

    fmt = "{:>6}  {:>8}  {:>6}  {:>9}  {:>9}  {:>10}"
    print(fmt.format("Tier2", "cov_thr", "n", "mean_ret", "overlap", "delta_vs_F"))
    print("-" * 70)
    for v in variants:
        cov = "none" if v["covenant_threshold"] is None else str(v["covenant_threshold"])
        m = f"{v['mean_return']*100:+.1f}%" if v["mean_return"] is not None else "  n/a"
        d_pp = f"{v['delta_vs_framework_pp']*100:+.1f}pp" if v["delta_vs_framework_pp"] is not None else "  n/a"
        print(fmt.format(str(v["include_tier2"]), cov, v["n_picks"], m, v["n_overlap"], d_pp))

    out = HERE / "tier1_test_A_sensitivity.json"
    out.write_text(json.dumps(variants, indent=2))
    print(f"\nSaved to {out}")


if __name__ == "__main__":
    main()
