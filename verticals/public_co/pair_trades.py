"""
Cross-cohort paired long/short trade aggregator.

Reads every per-cohort matrix.json under verticals/public_co/data/_*_cohort/.
For each name the v2 emitter would EMIT (composite >= 0.6 Truth_signal AND
discovery_advantage_tier != LOW), finds the cleanest in-cohort
pairing long:
  1. Prefer explicitly-marked controls (notes contain "**CONTROL**")
  2. Else the lowest-composite name in the same cohort
  3. Falls back to an external sector-beta long when no in-cohort
     clean option exists

Output: data/_pair_trades/PAIR_TRADES.md + pairs.json.

A note on hedge ratio: the framework's job is to surface the pair, not
to optimize the hedge. The PAIR_TRADES.md emits dollar-neutral 1:1
defaults with a stub note that the reader should adjust for beta
differential / liquidity / borrow cost.
"""
from __future__ import annotations

import importlib
import json
from datetime import datetime
from pathlib import Path

from .discovery_advantage import compute_discovery_advantage
from .forward_bet_emission import COMPOSITE_THRESHOLD, EMIT_DA_TIERS, MIN_FLAGS, is_truth_signal


HERE = Path(__file__).parent
DATA = HERE / "data"
OUT  = DATA / "_pair_trades"


# Cohort registry: subdir-name -> python module providing COHORT list.
# Used to identify control members (notes contain "**CONTROL**") + cohort theme.
COHORTS = [
    # (cohort_subdir,         python_module,                            theme,                        external_long_fallback)
    ("_defense_cohort",       "verticals.public_co.defense_cohort",     "Defense-tech",               "KTOS"),
    ("_lidar_cohort",         "verticals.public_co.lidar_cohort",       "Lidar / ADAS",               "MBLY"),
    ("_nuclear_cohort",       "verticals.public_co.nuclear_cohort",     "Nuclear / SMR",              "BWXT"),
    ("_quantum_cohort",       "verticals.public_co.quantum_cohort",     "Quantum computing",          "IBM"),
    ("_hydrogen_cohort",      "verticals.public_co.hydrogen_cohort",    "Hydrogen / fuel-cell",       "LIN"),
    ("_dcpivot_cohort",       "verticals.public_co.dcpivot_cohort",     "AI-DC / crypto-pivot",       "EQIX"),
    ("_ssbattery_cohort",     "verticals.public_co.ssbattery_cohort",   "Solid-state battery",        "ALB"),
    ("_robotics_cohort",      "verticals.public_co.robotics_cohort",    "Robotics / autonomy",        "TER"),
    ("_cellgene_cohort",      "verticals.public_co.cellgene_cohort",    "Cell/gene therapy",          "REGN"),
    ("_space_cohort",         "verticals.public_co.space_cohort",       "Space / satcom",             "IRDM"),
    ("_fintech_cohort",       "verticals.public_co.fintech_cohort",     "Fintech lending / BNPL",     "COF"),
    ("_retail_cohort",        "verticals.public_co.retail_cohort",      "Retail distress",            "TJX"),
]


def load_matrix(subdir: str) -> list[dict] | None:
    f = DATA / subdir / "matrix.json"
    if not f.exists():
        return None
    try:
        return json.loads(f.read_text())
    except json.JSONDecodeError:
        return None


def load_cohort_members(module_name: str) -> list:
    try:
        m = importlib.import_module(module_name)
        return m.COHORT
    except (ImportError, AttributeError):
        return []


def find_long_candidate(matrix: list[dict], cohort_members: list, *,
                         exclude_tickers: set[str]) -> dict | None:
    """Pick the cleanest pairing long from the cohort matrix.

    Priority: notes-marked CONTROL > lowest composite (with DA tier
    IN {HIGH, MED, LOW}, excluding UNKNOWN). UNKNOWN-tier names are
    excluded because finviz drops delisted / deregistered issuers
    (e.g. post-Chapter 11 LAZR) and a "long" against a delisted name
    is structurally broken.

    Returns the matrix row for the chosen long, or None if no
    cohort-internal candidate clears.
    """
    by_ticker = {m.ticker: m for m in cohort_members}

    candidates = []
    for row in matrix:
        if row["ticker"] in exclude_tickers:
            continue
        # Filter out delisted / deregistered (DA tier UNKNOWN)
        da = compute_discovery_advantage(row["ticker"])
        if da.get("tier") == "UNKNOWN":
            continue
        # Filter out anything that would itself EMIT (don't pair short with another short)
        if is_truth_signal(row):
            continue
        m = by_ticker.get(row["ticker"])
        is_control = bool(m and "**CONTROL**" in (m.notes or ""))
        candidates.append((row, is_control, da))

    if not candidates:
        return None

    # Prefer controls, then lowest composite
    candidates.sort(key=lambda x: (not x[1], x[0]["composite_score"]))
    return candidates[0][0]


def emit_pairs() -> tuple[list[dict], str]:
    pairs: list[dict] = []
    lines: list[str] = []
    w = lines.append

    w("# Signal OS — Cross-Cohort Paired Long/Short Trade Sheet\n")
    w(f"_Generated {datetime.utcnow().isoformat()}Z — cutoff varies per cohort_\n")
    w("**Construction:** for every name the v3 forward-bet emitter would EMIT")
    w(f"(Truth_signal: red>=1 OR severe>=2 OR (composite>={COMPOSITE_THRESHOLD} AND n_flags>={MIN_FLAGS});")
    w("AND discovery_advantage_tier != LOW),")
    w("the cleanest in-cohort long candidate is paired against it. Long candidates")
    w("are picked in priority order: notes-marked **CONTROL** > lowest-composite")
    w("in-cohort name > an external sector-beta long as a fallback.\n")
    w("**Hedge ratio default is dollar-neutral 1:1.** The framework's job is to")
    w("surface the pair, not to optimize the hedge. Adjust for beta differential,")
    w("borrow cost, liquidity, and your own market view.\n")
    w("**Falsification window is 12 months** from each cohort's cutoff date.")
    w("A pair survives if EITHER leg moves >50% against the thesis, OR neither")
    w("leg moves materially and the divergence claim is corroborated post-cutoff.\n")

    w("## Pairs\n")

    total = 0
    for subdir, module_name, theme, fallback in COHORTS:
        matrix = load_matrix(subdir)
        if not matrix:
            continue
        cohort_members = load_cohort_members(module_name)

        # Find EMITs
        emits = []
        for row in matrix:
            da = compute_discovery_advantage(row["ticker"])
            row["_da"] = da
            if is_truth_signal(row) and da.get("tier") in EMIT_DA_TIERS:
                emits.append(row)

        if not emits:
            continue

        w(f"### {theme}\n")
        for short_row in emits:
            short_tk = short_row["ticker"]
            long_row = find_long_candidate(matrix, cohort_members,
                                           exclude_tickers={short_tk})
            long_tk     = long_row["ticker"] if long_row else None
            long_da     = compute_discovery_advantage(long_tk) if long_tk else None
            external    = long_tk is None or is_truth_signal(long_row)
            if external:
                # Fallback: use the registered external sector-beta long
                long_tk  = fallback
                long_da  = compute_discovery_advantage(long_tk)
                long_row = None

            sda  = short_row["_da"]
            sf_s = f"{sda.get('short_float_pct')*100:.1f}%" if sda.get("short_float_pct") is not None else "?"
            io_s = f"{sda.get('inst_own_pct')*100:.0f}%"     if sda.get("inst_own_pct")    is not None else "?"

            w(f"#### SHORT **{short_tk}** / LONG **{long_tk}**")
            w(f"- **Short leg:** {short_tk} ({short_row['company']})")
            w(f"  - Composite: {short_row['composite_score']:.2f}   "
              f"PASS={short_row['severity_counts']['PASS']} "
              f"MOD={short_row['severity_counts']['MODERATE_UNDERDELIVERY']} "
              f"SEVE={short_row['severity_counts']['SEVERE_UNDERDELIVERY']} "
              f"RED={short_row['severity_counts']['RED_FLAG_NEGATIVE']} "
              f"UNV={short_row['severity_counts']['UNVERIFIABLE']}")
            w(f"  - Discovery_advantage: {sda.get('tier')} "
              f"(short_float={sf_s}, inst_own={io_s}, recom={sda.get('recom')})")
            w(f"  - Filing analyzed: `{short_row.get('filing')}`")

            if long_row:
                lf_s = f"{long_da.get('short_float_pct')*100:.1f}%" if long_da and long_da.get("short_float_pct") is not None else "?"
                lio_s = f"{long_da.get('inst_own_pct')*100:.0f}%"   if long_da and long_da.get("inst_own_pct")    is not None else "?"
                w(f"- **Long leg (in-cohort):** {long_tk} ({long_row['company']})")
                w(f"  - Composite: {long_row['composite_score']:.2f}  "
                  f"(in-cohort {'control' if any('**CONTROL**' in (m.notes or '') and m.ticker == long_tk for m in cohort_members) else 'cleanest follow'})")
                w(f"  - Discovery_advantage: {long_da.get('tier') if long_da else '?'} "
                  f"(short_float={lf_s}, inst_own={lio_s})")
            else:
                w(f"- **Long leg (external sector-beta fallback):** {long_tk}")
                w(f"  - Used because no clean in-cohort long was available "
                  f"(all in-cohort names themselves would Truth_signal under the "
                  f"current emit rule).")

            w(f"- **Pair thesis:** short the {theme} name where R - f(M) divergence "
              f"is high AND the bear case isn't already crowded; long the {theme} "
              f"name where the framework finds no divergence (sector-beta hedge).")
            w(f"- **Hedge ratio:** dollar-neutral 1:1 default; adjust for beta, "
              f"borrow cost, and liquidity.")
            w(f"- **Falsification:** within 12 months, the short leg either "
              f"materially restates the flagged claims, files distress paperwork, "
              f"or trades >50% lower; OR the divergence claim is corroborated "
              f"by counterparty disclosure and the pair returns ~0.")
            w("")

            pairs.append({
                "theme":      theme,
                "short":      short_tk,
                "long":       long_tk,
                "long_source": "in-cohort" if long_row else "external-fallback",
                "short_composite": short_row["composite_score"],
                "short_da":   sda,
                "long_da":    long_da,
            })
            total += 1

    w(f"\n---\n**{total} paired trades emitted** across {len(COHORTS)} cohorts.\n")
    return pairs, "\n".join(lines)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pairs, report = emit_pairs()
    (OUT / "PAIR_TRADES.md").write_text(report)
    (OUT / "pairs.json").write_text(json.dumps(pairs, indent=2, default=str))
    print(f"Wrote {OUT / 'PAIR_TRADES.md'}")
    print(f"Wrote {OUT / 'pairs.json'}")
    print(f"\nPairs emitted: {len(pairs)}")
    for p in pairs:
        print(f"  SHORT {p['short']:>5} / LONG {p['long']:>5}  ({p['theme']})  comp={p['short_composite']:.2f}")


if __name__ == "__main__":
    main()
