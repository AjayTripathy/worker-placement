"""Deterministic composite recompute for small-cap honesty-alpha pilots.

LLM agents self-report a `composite` field in `pilot_<TICKER>.json` files,
and as of the 2026-05-24 30-name pilot, 3 of 30 (AMPH, HNI, SMPL) had
materially wrong self-reports — including SMPL tier-flipping NEUTRAL→SHORT
when recomputed. Several others (CCOI, FMC, KMPR, ROCK, SHAK, TRIP) had
smaller-but-nonzero drift driven by inconsistent denominators.

Canonical formula per STRATEGY_METHODOLOGY.md:

    composite = sum(SEV_WEIGHT[s] for s in rfm_tuples) / len(rfm_tuples)

where SEV_WEIGHT = {PASS:0, UNVERIFIABLE:0, MOD:1, SEV:2, RED:3}.

UNVERIFIABLE stays in the denominator with weight 0 — that's intentional:
the small-cap strategy treats coverage gaps as neutral, not as exclusion.
(This is DIFFERENT from jbook_exposure_aggregate.py, which drops UNV from
the denom for the J-Book/defense cohort. The two cohorts have different
calibrations and we keep the formulas separate.)

Usage:
    python3 -m verticals.public_co.recompute_pilot_composite \\
        [--dir DIR] [--write] [--quiet]

Without --write, prints a diff table only. With --write, overwrites the
`composite` and `scoring` fields in each pilot_*.json in place.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

SEV_WEIGHT = {
    "PASS": 0,
    "UNVERIFIABLE": 0,
    "MODERATE_UNDERDELIVERY": 1,
    "SEVERE_UNDERDELIVERY": 2,
    "RED_FLAG_NEGATIVE": 3,
}

TIER_LOOSE_LONG = 0.30
TIER_SHORT = 0.50


def tier_of(composite: float) -> str:
    if composite <= 0.20:
        return "STRICT_LONG"
    if composite <= TIER_LOOSE_LONG:
        return "LOOSE_LONG"
    if composite < TIER_SHORT:
        return "NEUTRAL"
    return "SHORT"


def recompute(pilot: dict) -> tuple[float, dict[str, int]] | None:
    tuples = pilot.get("rfm_tuples") or []
    if not tuples:
        return None
    counts = {k: 0 for k in SEV_WEIGHT}
    weighted = 0
    for t in tuples:
        sev = t.get("severity")
        if sev not in SEV_WEIGHT:
            continue
        counts[sev] += 1
        weighted += SEV_WEIGHT[sev]
    composite = weighted / len(tuples)
    counts["verifiable_claims"] = len(tuples)
    counts["weighted_sum"] = (
        f"(0*{counts['PASS']} + 1*{counts['MODERATE_UNDERDELIVERY']} + "
        f"2*{counts['SEVERE_UNDERDELIVERY']} + 3*{counts['RED_FLAG_NEGATIVE']}) / "
        f"{len(tuples)} = {weighted} / {len(tuples)}"
    )
    counts["composite"] = round(composite, 4)
    return composite, counts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dir",
        default="verticals/public_co/data/_smallcap_universe",
        help="Directory containing pilot_*.json files",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Overwrite composite + scoring fields in pilot files",
    )
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    pilot_dir = Path(args.dir)
    pilots = sorted(
        p for p in pilot_dir.glob("pilot_*.json")
        if "synthesis" not in p.name and "candidates" not in p.name
    )

    if not args.quiet:
        print(f"{'TK':6} {'old':>8}  {'new':>8}  {'delta':>7}  {'tier_was':12} -> {'tier_now':12}")
        print("-" * 70)

    drift = []
    tier_changes = []
    for p in pilots:
        d = json.loads(p.read_text())
        result = recompute(d)
        if result is None:
            continue
        new_composite, new_scoring = result
        old_composite = d.get("composite")
        old_tier = tier_of(old_composite) if isinstance(old_composite, (int, float)) else "UNKNOWN"
        new_tier = tier_of(new_composite)

        delta = (new_composite - old_composite) if isinstance(old_composite, (int, float)) else None
        ticker = d.get("ticker") or p.stem.replace("pilot_", "")

        if delta is None or abs(delta) > 1e-3:
            drift.append((ticker, old_composite, new_composite, delta))
        if old_tier != new_tier:
            tier_changes.append((ticker, old_tier, new_tier))

        if not args.quiet:
            d_str = f"{delta:+.3f}" if delta is not None else "  +new"
            old_str = f"{old_composite:.3f}" if isinstance(old_composite, (int, float)) else "  None"
            print(f"{ticker:6} {old_str:>8}  {new_composite:>8.3f}  {d_str:>7}  "
                  f"{old_tier:12} -> {new_tier:12}")

        if args.write:
            d["composite"] = round(new_composite, 4)
            d["scoring"] = new_scoring
            p.write_text(json.dumps(d, indent=2) + "\n")

    if not args.quiet:
        print()
        print(f"Drift: {len(drift)} / {len(pilots)} pilots (|Δ| > 0.001)")
        print(f"Tier changes: {len(tier_changes)}")
        for tk, was, now in tier_changes:
            print(f"  {tk}: {was} -> {now}")
        if args.write:
            print(f"\nWrote {len(pilots)} files in {pilot_dir}")
        else:
            print(f"\n(dry-run — pass --write to overwrite)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
