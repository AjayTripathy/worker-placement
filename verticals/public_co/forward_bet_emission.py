"""
Shared forward-bet emission logic across all public_co cohort aggregators.

Two changes from the legacy inline emission in defense/lidar/nuclear_aggregate:

1. **Composite threshold lowered 1.5 -> 0.6.** The legacy threshold was
   over-restrictive: it only emitted on the explicit Nikola-pattern
   (RED_FLAG present) or a near-RED composite. Empirically (lidar and
   nuclear cohorts), the framework rarely scores any name >= 1.5 unless
   the divergence is outright fraud. Lowering to 0.6 surfaces names with
   3-4 MODERATEs (which is what the framework actually produces on real
   distress fingerprints), and lets the Discovery_advantage gate prune
   the crowded shorts.

2. **Discovery_advantage second-pass gate.** A bet only emits if
   discovery_advantage_tier IS NOT LOW (i.e., HIGH, MED, or UNKNOWN
   passes; only LOW is suppressed). LOW-tier names (already-crowded
   shorts: high SI, high inst-ownership + analyst coverage) are
   suppressed even when the framework's Truth_signal is high. UNKNOWN
   tier (finviz fetch failed) is **passed through** as of the
   fresh-universe 2025-05-15 backtest: KULR was DA=UNKNOWN and would
   have been +120% pair P&L, far better than the EMIT-set mean. The
   prior reasoning that "UNKNOWN means bear case already played out"
   was wrong empirically — UNKNOWN is more often a finviz fetch gap
   on legitimately small-cap names that the framework most wants to
   evaluate.

The two-pass discipline mirrors the defense-cohort commit's reasoning:
"ONDS 33% short float and RCAT 20% short float = bear case already
crowded, framework's signals are real but not novel. AIRO 10.88% short
float + recent EPS/revenue miss = genuinely novel discovery."
"""
from __future__ import annotations

from datetime import datetime

from .discovery_advantage import compute_discovery_advantage


COMPOSITE_THRESHOLD = 0.10
MIN_FLAGS = 2

# DA tiers that PASS the second-pass gate. LOW is the only suppressed
# tier; UNKNOWN passes through (see module docstring).
EMIT_DA_TIERS = {"HIGH", "MED", "UNKNOWN"}


def is_truth_signal(row: dict) -> bool:
    """Dual-gate emission rule:

      EITHER  red_flags >= 1  OR  severe >= 2           # hard-contradiction path
              (any single RED or two SEVEREs override the composite gate)
      OR      composite >= COMPOSITE_THRESHOLD  AND
              (red + severe + moderate) >= MIN_FLAGS    # density + mass

    The hard-contradiction path keeps a single concrete contradiction
    actionable even on plans with few claims. The density+mass path
    rejects single-flag composites driven by 1 MOD on an 8-claim plan
    (~0.06) — which is exactly where chemistry-vs-electrolytic ambiguity
    and substring-noise false positives live in the deterministic scorer.
    """
    sc = row.get("severity_counts", {}) or {}
    red = sc.get("RED_FLAG_NEGATIVE", 0)
    sev = sc.get("SEVERE_UNDERDELIVERY", 0)
    mod = sc.get("MODERATE_UNDERDELIVERY", 0)
    if red >= 1 or sev >= 2:
        return True
    n_flags = red + sev + mod
    return row.get("composite_score", 0.0) >= COMPOSITE_THRESHOLD and n_flags >= MIN_FLAGS


def emission_lines(matrix: list[dict], cutoff: str) -> list[str]:
    """Return lines of markdown for the "Forward predictions" section.

    matrix is the cohort_aggregate output: list of per-ticker dicts each with
    keys {ticker, company, composite_score, severity_counts, ...}.
    cutoff is the analysis cutoff date "YYYY-MM-DD".
    """
    lines: list[str] = []
    w = lines.append

    falsification = f"{int(cutoff[:4]) + 1}-{cutoff[5:]}"

    w("## Forward predictions (12-month falsification window)\n")
    w(f"Falsification date: **{falsification}**\n")
    w(
        f"**Emission rule (v4):** a bet emits iff Truth_signal AND "
        f"`discovery_advantage_tier != LOW` (i.e., HIGH, MED, or UNKNOWN "
        f"all pass). Truth_signal is `red_flags >= 1` OR `severe >= 2` "
        f"(hard-contradiction path) OR `composite_score >= "
        f"{COMPOSITE_THRESHOLD}` AND `red + severe + moderate >= "
        f"{MIN_FLAGS}` (density + mass). Discovery_advantage source: "
        f"finviz.com short_float + inst_own + recom. See "
        f"`discovery_advantage.py` for tier rules.\n"
    )

    for r in matrix:
        ticker         = r["ticker"]
        composite      = r["composite_score"]
        red_flags      = r["severity_counts"].get("RED_FLAG_NEGATIVE", 0)
        severe_count   = r["severity_counts"].get("SEVERE_UNDERDELIVERY", 0)
        ts  = is_truth_signal(r)

        # Discovery_advantage lookup (cached after first call per ticker)
        da = compute_discovery_advantage(ticker)
        da_tier  = da.get("tier", "UNKNOWN")
        sf       = da.get("short_float_pct")
        io       = da.get("inst_own_pct")
        recom    = da.get("recom")

        sf_s   = f"{sf*100:.1f}%" if sf is not None else "?"
        io_s   = f"{io*100:.0f}%" if io is not None else "?"
        rec_s  = f"{recom:.2f}" if recom is not None else "?"

        w(f"### {ticker}")
        w(
            f"- Composite: **{composite:.2f}**   "
            f"RED_FLAGs: {red_flags}   SEVERE: {severe_count}   "
            f"→ Truth_signal: {'YES' if ts else 'no'}"
        )
        w(
            f"- Discovery_advantage: **{da_tier}**   "
            f"short_float={sf_s}   inst_own={io_s}   recom={rec_s}"
        )

        if ts and da_tier in EMIT_DA_TIERS:
            w(f"- **Decision: EMIT bearish forward bet.**")
            if red_flags > 0:
                w(
                    f"  - **Forward bet:** within 12 months of {cutoff}, at "
                    f"least one of the following occurs: (a) the next "
                    f"10-K/10-Q/20-F materially restates the RED_FLAG "
                    f"claim; (b) the company announces a strategic pivot "
                    f"away from the disputed claim; (c) the counterparty "
                    f"publicly contradicts the company's representation; "
                    f"(d) the company files Form 15-12G / 25-NSE / Chapter "
                    f"11; (e) the stock falls >50% from cutoff price."
                )
            else:
                w(
                    f"  - **Forward bet:** within 12 months, the underlying "
                    f"claims will (a) be revised down in the next 10-K / "
                    f"20-F, (b) be supplanted by a different headline "
                    f"figure that obscures the original gap, or (c) "
                    f"trigger short-seller / analyst coverage that reflects "
                    f"the framework's findings."
                )
            w(
                f"  - **Falsification:** if by {falsification} the claims "
                f"are corroborated by matching counterparty / registry "
                f"disclosure AND the stock is within ±20% of cutoff price "
                f"AND no analyst or short-seller has independently "
                f"identified the same divergence, the prediction is wrong."
            )
        elif ts and da_tier == "LOW":
            w(
                f"- **Decision: SUPPRESS** — Truth_signal present but "
                f"Discovery_advantage LOW (crowded short, already-known "
                f"bear case). Framework's edge is in novel divergence; "
                f"this signal is real but not actionable as alpha. "
                f"Recorded as a confirmation, not a bet."
            )
        elif ts and da_tier == "UNKNOWN":
            w(
                f"- **Decision: SUPPRESS (data unavailable)** — Truth_signal "
                f"present but finviz couldn't price the discovery side "
                f"(often because the issuer is delisted / deregistered, "
                f"e.g. Form 15-12G already filed). Bearish reality is "
                f"likely already in the filings; treat as confirmation, "
                f"not bet."
            )
        else:
            w(
                f"- **Decision: no bet.** Composite {composite:.2f} < "
                f"{COMPOSITE_THRESHOLD} and no RED_FLAG — framework didn't "
                f"find divergence at the level that justifies a forward "
                f"position."
            )
        w("")

    return lines


def emit_to_report(matrix: list[dict], cutoff: str) -> str:
    """Convenience: render the emission section as a single markdown string."""
    return "\n".join(emission_lines(matrix, cutoff))
