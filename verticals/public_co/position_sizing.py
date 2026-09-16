"""
Position-sizing + shortability pass for the top-N paired trades.

For each pair from data/_pair_trades/pairs.json, applies a selection
filter to surface high-conviction pairs (composite >= 0.75 AND
(>=1 RED_FLAG OR >=2 SEVERE), with concentration cap of 2 pairs per
long-side ticker), then computes:

  1. Shortability of the short leg
     - price < $5     : most retail brokers prohibit short
     - mcap < $50M    : typically HTB / no borrow
     - daily $ vol <$1M: liquidity gate fails for institutional size
     - short_float > 25%: squeeze risk
  2. Beta-neutral hedge ratio  =  short_beta / long_beta
     Interpretation: for every $X long the long-leg, short
     $(X * short_beta / long_beta) of the short-leg.
  3. Liquidity-based notional cap
     - default 5% of daily $ vol on the more-illiquid leg
     - this is the practical max $ size of the *long* leg before
       slippage / market-impact concerns dominate

Output: data/_pair_trades/POSITION_SIZING.md + position_sizing.json.

Data sources (all already on disk):
  - data/_pair_trades/pairs.json — paired short/long emissions
  - data/_discovery_advantage_cache/{TK}.json — finviz snapshot per ticker
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE / "data"
PAIRS_DIR = DATA / "_pair_trades"
DA_CACHE  = DATA / "_discovery_advantage_cache"


# Filter rules. Two tiers:
#   Tier 1 (high-conviction): composite >= TIER1_MIN_COMPOSITE
#                             AND (>=1 RED OR >=2 SEVERE)
#   Tier 2 (MOD-pattern, lower-conviction): composite >= TIER2_MIN_COMPOSITE
#                             AND >=2 MOD AND does not already qualify for Tier 1
TIER1_MIN_COMPOSITE = 0.75
TIER2_MIN_COMPOSITE = 0.60
MIN_RED             = 1
MIN_SEVE            = 2    # Tier 1 alternative gate
MIN_MOD             = 2    # Tier 2 gate (MODERATE-pattern)
MAX_LONG_COMP       = 0.3  # the long must look genuinely clean (excludes IONQ-style weak longs)
MAX_PAIRS_PER_LONG  = 2

# Shortability thresholds
PRICE_FLOOR       = 5.0
MCAP_FLOOR        = 50_000_000
DAILY_DOLLAR_VOL_FLOOR = 1_000_000
SHORT_FLOAT_SQUEEZE    = 0.25

# Liquidity-based notional cap
DAILY_VOL_PCT_CAP = 0.05  # 5% of daily $ vol


def load_pairs() -> list[dict]:
    return json.loads((PAIRS_DIR / "pairs.json").read_text())


def load_da(ticker: str) -> dict | None:
    p = DA_CACHE / f"{ticker}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text())


def load_matrix_row(theme: str, ticker: str) -> dict | None:
    """Find the per-ticker matrix.json row for a given theme."""
    THEME_TO_DIR = {
        "Defense-tech":             "_defense_cohort",
        "Lidar / ADAS":             "_lidar_cohort",
        "Nuclear / SMR":            "_nuclear_cohort",
        "Quantum computing":        "_quantum_cohort",
        "Hydrogen / fuel-cell":     "_hydrogen_cohort",
        "AI-DC / crypto-pivot":     "_dcpivot_cohort",
        "Solid-state battery":      "_ssbattery_cohort",
        "Robotics / autonomy":      "_robotics_cohort",
        "Cell/gene therapy":        "_cellgene_cohort",
        "Space / satcom":           "_space_cohort",
        "Fintech lending / BNPL":   "_fintech_cohort",
        "Retail distress":          "_retail_cohort",
    }
    d = THEME_TO_DIR.get(theme)
    if not d:
        return None
    p = DATA / d / "matrix.json"
    if not p.exists():
        return None
    rows = json.loads(p.read_text())
    for r in rows:
        if r["ticker"] == ticker:
            return r
    return None


def _tier(composite: float, red: int, seve: int, mod: int) -> str | None:
    """Classify a pair. Returns 'TIER1', 'TIER2', or None (does not qualify)."""
    tier1 = composite >= TIER1_MIN_COMPOSITE and (red >= MIN_RED or seve >= MIN_SEVE)
    if tier1:
        return "TIER1"
    tier2 = composite >= TIER2_MIN_COMPOSITE and mod >= MIN_MOD
    if tier2:
        return "TIER2"
    return None


def select_top(pairs: list[dict]) -> list[dict]:
    """Apply selection rules: composite + truth-signal-rich + clean long + concentration cap.
    Returns pairs annotated with tier classification."""
    candidates = []
    for p in pairs:
        theme = p["theme"]
        short_tk = p["short"]
        long_tk  = p["long"]

        short_row = load_matrix_row(theme, short_tk)
        long_row  = load_matrix_row(theme, long_tk)
        if not short_row:
            continue

        counts = short_row["severity_counts"]
        red  = counts.get("RED_FLAG_NEGATIVE", 0)
        seve = counts.get("SEVERE_UNDERDELIVERY", 0)
        mod  = counts.get("MODERATE_UNDERDELIVERY", 0)
        composite = short_row["composite_score"]

        tier = _tier(composite, red, seve, mod)
        if not tier:
            continue
        # Clean-long filter (applies to both tiers)
        if long_row and long_row["composite_score"] > MAX_LONG_COMP:
            continue

        candidates.append({
            **p,
            "tier":            tier,
            "short_composite": composite,
            "short_red":       red,
            "short_seve":      seve,
            "short_mod":       mod,
            "long_composite":  long_row["composite_score"] if long_row else None,
        })

    # Sort: Tier 1 first (by composite desc), then Tier 2 (by composite desc)
    candidates.sort(key=lambda x: (0 if x["tier"] == "TIER1" else 1, -x["short_composite"]))

    # Concentration cap: max N per long ticker (across tiers)
    per_long: dict[str, int] = {}
    selected = []
    for c in candidates:
        long_tk = c["long"]
        if per_long.get(long_tk, 0) >= MAX_PAIRS_PER_LONG:
            continue
        per_long[long_tk] = per_long.get(long_tk, 0) + 1
        selected.append(c)
    return selected


def shortability(da: dict | None) -> dict:
    """Return shortability tier + reasons for a short-leg ticker's DA snapshot."""
    if not da:
        return {"tier": "UNKNOWN", "reasons": ["no DA snapshot"]}

    price = da.get("price")
    mcap  = da.get("market_cap")
    vol   = da.get("avg_volume")
    sf    = da.get("short_float_pct")
    daily_dollar_vol = (price or 0) * (vol or 0)

    reasons = []
    if price is not None and price < PRICE_FLOOR:
        reasons.append(f"price ${price:.2f} < ${PRICE_FLOOR:.0f} (most retail brokers prohibit short)")
    if mcap is not None and mcap < MCAP_FLOOR:
        reasons.append(f"market cap ${mcap/1e6:.0f}M < ${MCAP_FLOOR/1e6:.0f}M (thin / no borrow expected)")
    if daily_dollar_vol < DAILY_DOLLAR_VOL_FLOOR:
        reasons.append(f"daily $ vol ${daily_dollar_vol/1e6:.2f}M < ${DAILY_DOLLAR_VOL_FLOOR/1e6:.0f}M (liquidity gate)")
    if sf is not None and sf > SHORT_FLOAT_SQUEEZE:
        reasons.append(f"short_float {sf*100:.0f}% > {SHORT_FLOAT_SQUEEZE*100:.0f}% (squeeze risk)")

    if not reasons:
        tier = "SHORTABLE"
    elif price is not None and price < 1:
        tier = "ESSENTIALLY_UNSHORTABLE"
    elif len(reasons) >= 3:
        tier = "ESSENTIALLY_UNSHORTABLE"
    elif len(reasons) == 2:
        tier = "HARD_TO_BORROW_OR_RETAIL_RESTRICTED"
    else:
        tier = "BORROW_AT_PREMIUM"

    return {
        "tier":             tier,
        "reasons":          reasons,
        "price":            price,
        "mcap":             mcap,
        "avg_volume":       vol,
        "daily_dollar_vol": daily_dollar_vol,
        "short_float_pct":  sf,
    }


def hedge_ratio(short_beta: float | None, long_beta: float | None) -> dict:
    """Beta-neutral hedge ratio (short/long).

    If you go long $X of the long-leg, short $X * short_beta / long_beta of
    the short-leg to be approximately beta-neutral.
    """
    if short_beta is None or long_beta is None or long_beta <= 0:
        return {
            "ratio": 1.0,
            "method": "default 1:1 (missing beta data)",
            "short_beta": short_beta,
            "long_beta":  long_beta,
        }
    return {
        "ratio": short_beta / long_beta,
        "method": "beta-neutral (short_beta / long_beta)",
        "short_beta": short_beta,
        "long_beta":  long_beta,
    }


def notional_cap(short_da: dict | None, long_da: dict | None) -> dict:
    """Liquidity-based cap on the *long-leg* notional, in $."""
    s_price = (short_da or {}).get("price") or 0
    s_vol   = (short_da or {}).get("avg_volume") or 0
    l_price = (long_da  or {}).get("price") or 0
    l_vol   = (long_da  or {}).get("avg_volume") or 0
    s_dollar = s_price * s_vol
    l_dollar = l_price * l_vol
    cap_short = s_dollar * DAILY_VOL_PCT_CAP
    cap_long  = l_dollar * DAILY_VOL_PCT_CAP
    binding = min(cap_short, cap_long) if cap_short and cap_long else (cap_short or cap_long)
    return {
        "short_daily_dollar_vol": s_dollar,
        "long_daily_dollar_vol":  l_dollar,
        "short_5pct_cap":  cap_short,
        "long_5pct_cap":   cap_long,
        "binding_leg":     "short" if cap_short < cap_long else "long",
        "max_long_notional_$": binding,
    }


def build_sizing(pairs: list[dict]) -> list[dict]:
    out = []
    for p in pairs:
        s_da = load_da(p["short"])
        l_da = load_da(p["long"])
        short = shortability(s_da)
        hedge = hedge_ratio(
            short_beta=(s_da or {}).get("beta"),
            long_beta=(l_da  or {}).get("beta"),
        )
        cap = notional_cap(s_da, l_da)
        out.append({
            "theme":             p["theme"],
            "short":             p["short"],
            "long":              p["long"],
            "tier":              p["tier"],
            "short_composite":   p["short_composite"],
            "short_red":         p["short_red"],
            "short_seve":        p["short_seve"],
            "short_mod":         p["short_mod"],
            "long_composite":    p["long_composite"],
            "shortability":      short,
            "hedge":              hedge,
            "notional":          cap,
            "short_da":          s_da,
            "long_da":           l_da,
        })
    return out


def _render_pair_table(rows: list[dict], starting_index: int = 1) -> list[str]:
    lines: list[str] = []
    lines.append("| # | SHORT | LONG | Comp | Flags | Long comp | Shortability | Beta-neutral hedge | Max long notional ($) |")
    lines.append("|---:|---|---|---:|---|---:|---|---:|---:|")
    for i, p in enumerate(rows, starting_index):
        flags = f"{p['short_red']}R/{p['short_seve']}S/{p['short_mod']}M"
        long_comp = f"{p['long_composite']:.2f}" if p["long_composite"] is not None else "?"
        tier = p["shortability"]["tier"]
        ratio = p["hedge"]["ratio"]
        cap = p["notional"]["max_long_notional_$"] or 0
        lines.append(
            f"| {i} | **{p['short']}** | {p['long']} | {p['short_composite']:.2f} | "
            f"{flags} | {long_comp} | {tier} | {ratio:.2f} | ${cap/1e6:.2f}M |"
        )
    return lines


def _render_pair_detail(p: dict, idx: int) -> list[str]:
    lines: list[str] = []
    w = lines.append
    tier_badge = "**[Tier 1]**" if p["tier"] == "TIER1" else "**[Tier 2 — MOD-pattern]**"
    w(f"### {idx}. SHORT **{p['short']}** / LONG **{p['long']}**  ({p['theme']})  {tier_badge}\n")

    long_comp_s = f"{p['long_composite']:.2f}" if p['long_composite'] is not None else "n/a"
    w(f"**Truth_signal:** composite {p['short_composite']:.2f}, "
      f"{p['short_red']} RED_FLAG, {p['short_seve']} SEVERE, {p['short_mod']} MODERATE  "
      f"(long {p['long']} composite {long_comp_s})")
    if p["tier"] == "TIER2":
        w("")
        w("**Conviction note:** this pair's composite is driven by MODERATE_UNDERDELIVERY flags "
          "(disclosure-quality issues — typically counterparty 10-Ks silent on the claimed "
          "relationship, or quantitative claims with weak corroboration) rather than RED_FLAG "
          "or SEVERE patterns. Lower conviction than Tier 1; treat as a softer disclosure-quality "
          "trade, not a hard-contradiction short.")
    w("")

    sh = p["shortability"]
    s_da = p["short_da"] or {}
    l_da = p["long_da"] or {}

    w(f"**Short leg ({p['short']}) shortability — {sh['tier']}:**")
    w(f"- price: ${sh.get('price') or 0:.2f}")
    w(f"- market cap: ${(sh.get('mcap') or 0)/1e9:.2f}B")
    w(f"- daily $ vol: ${sh.get('daily_dollar_vol', 0)/1e6:.2f}M")
    sf = sh.get("short_float_pct")
    sf_s = f"{sf*100:.1f}%" if sf is not None else "?"
    w(f"- short_float: {sf_s}")
    if sh.get("reasons"):
        w("- **gating concerns:**")
        for r in sh["reasons"]:
            w(f"  - {r}")
    if not s_da.get("avg_volume") or not s_da.get("market_cap"):
        missing = [k for k in ("avg_volume", "market_cap", "beta") if not s_da.get(k) and s_da.get(k) is not 0]
        w(f"- _data-completeness warning: short-leg DA cache missing {missing}; "
          f"shortability tier and sizing degraded._")
    w("")

    w(f"**Long leg ({p['long']}) snapshot:**")
    w(f"- price: ${l_da.get('price') or 0:.2f}")
    w(f"- market cap: ${(l_da.get('market_cap') or 0)/1e9:.2f}B")
    l_vol_dollar = (l_da.get('price') or 0) * (l_da.get('avg_volume') or 0)
    w(f"- daily $ vol: ${l_vol_dollar/1e6:.2f}M")
    # Surface a data-completeness warning when the long-leg DA cache is
    # incomplete — the notional cap and hedge ratio will be unreliable.
    if not l_da.get("avg_volume") or not l_da.get("market_cap") or l_da.get("beta") is None:
        missing = [k for k in ("avg_volume", "market_cap", "beta") if not l_da.get(k) and l_da.get(k) is not 0]
        w(f"- _data-completeness warning: long-leg DA cache missing {missing}; "
          f"notional cap and hedge ratio degraded._")
    w("")

    h = p["hedge"]
    sb = h.get("short_beta")
    lb = h.get("long_beta")
    sb_s = f"{sb:.2f}" if sb is not None else "?"
    lb_s = f"{lb:.2f}" if lb is not None else "?"
    w(f"**Beta-neutral hedge ratio:** **{h['ratio']:.2f}** "
      f"(short β={sb_s}, long β={lb_s}; {h['method']})")
    w(f"- For every $1.00 long {p['long']}, short ${h['ratio']:.2f} of {p['short']} to be beta-neutral.")
    w("")

    n = p["notional"]
    w(f"**Liquidity-based notional cap:**")
    w(f"- short daily $ vol: ${n['short_daily_dollar_vol']/1e6:.2f}M → 5% = ${n['short_5pct_cap']/1e6:.2f}M")
    w(f"- long  daily $ vol: ${n['long_daily_dollar_vol']/1e6:.2f}M → 5% = ${n['long_5pct_cap']/1e6:.2f}M")
    w(f"- **binding leg: {n['binding_leg']}**, max long-leg notional ≈ ${(n['max_long_notional_$'] or 0)/1e6:.2f}M")
    w("")
    w("---\n")
    return lines


def render_report(sized: list[dict]) -> str:
    lines: list[str] = []
    w = lines.append

    tier1 = [p for p in sized if p["tier"] == "TIER1"]
    tier2 = [p for p in sized if p["tier"] == "TIER2"]

    w("# Signal OS — Paired Trades: Position Sizing + Shortability Pass\n")
    w("Two tiers, both pulled from `PAIR_TRADES.md`:\n")
    w(f"- **Tier 1 (high-conviction):** short composite >= {TIER1_MIN_COMPOSITE} "
      f"AND (>=1 RED_FLAG_NEGATIVE OR >={MIN_SEVE} SEVERE_UNDERDELIVERY)")
    w(f"- **Tier 2 (lower-conviction, MOD-pattern):** short composite >= {TIER2_MIN_COMPOSITE} "
      f"AND >={MIN_MOD} MODERATE_UNDERDELIVERY (and doesn't already qualify for Tier 1)")
    w(f"- Both tiers require long composite <= {MAX_LONG_COMP} (clean control) and max "
      f"{MAX_PAIRS_PER_LONG} pairs per long-side ticker.\n")

    w("## Why Tier 2 scores are softer\n")
    w("A composite in the **0.60–0.74** range with no RED_FLAG and <2 SEVERE typically "
      "reflects a different *kind* of finding than the Tier-1 pattern. Tier 1 captures "
      "**hard contradictions** — counterparty disclosures or registries flatly contradict "
      "the filing's claim (RED_FLAG) or the filing materially overstates a verifiable "
      "metric (SEVERE). Tier 2 captures **disclosure-quality issues**:\n")
    w("- **Heuristic 7 firing** — the focal company names a Tier-1 counterparty at material "
      "$-scale, but the counterparty's 10-K returns 0 hits for the focal company / product. "
      "Counterparties don't unilaterally hide material partnerships, so silence is meaningful, "
      "but it could also be a search-coverage artifact (different naming convention, "
      "filing-date offset, etc.). MODERATE rather than RED because the absence-of-evidence "
      "isn't conclusive.")
    w("- **Filing-discipline gaps** — claimed regulatory filings (ABS-15G cadence, sales-agent "
      "underwriting agreements, etc.) not located in the expected SEC submission window. "
      "Often a CIK-scope or form-type-naming issue, occasionally a real disclosure miss.")
    w("- **Quantitative claims with weak corroboration** — specific $-amounts or percentages "
      "named in the filing where the M-side registry has *some* data but the data doesn't "
      "directly compare (different scope, different perimeter, different reporting cadence).\n")
    w("**Trade thesis difference:** Tier 1 shorts are betting on a **factual revision** "
      "(restatement, customer churn, regulator action). Tier 2 shorts are betting on a "
      "**disclosure-quality re-rating** — the market eventually penalizes the multiple "
      "applied to filings where claims don't independently verify. Tier 2 trades typically "
      "need a longer holding period and benefit more from being part of a basket than "
      "from a concentrated single-name bet.\n")

    w("**Hedge ratio** is beta-neutral: short_beta / long_beta. Interpretation: for every "
      "$X long the long-leg, short $(X × ratio) of the short-leg.")
    w(f"**Notional cap** is {int(DAILY_VOL_PCT_CAP*100)}% of the more-illiquid leg's daily $ volume.")
    w(f"**Shortability tier** flags the short-leg's practical executability: sub-$5 retail-broker "
      "prohibition, sub-$50M mcap HTB territory, daily $ vol below $1M liquidity gate, "
      "short_float >25% squeeze risk.\n")

    w(f"## Tier 1 — high-conviction ({len(tier1)} pairs)\n")
    if tier1:
        lines.extend(_render_pair_table(tier1, starting_index=1))
    else:
        w("_(no pairs qualified)_")
    w("")

    w(f"## Tier 2 — lower-conviction, MOD-pattern ({len(tier2)} pairs)\n")
    if tier2:
        lines.extend(_render_pair_table(tier2, starting_index=len(tier1)+1))
        w("")
        w("_Flag column: R/S/M = RED_FLAG / SEVERE / MODERATE counts. Tier 2 rows show a "
          "0/0/N or 0/1/N pattern — the composite is built from MODERATEs, not from hard "
          "contradictions._")
    else:
        w("_(no pairs qualified)_")
    w("")

    w("## Per-pair detail\n")
    idx = 1
    for p in tier1 + tier2:
        lines.extend(_render_pair_detail(p, idx))
        idx += 1

    w("## Aggregate position-book considerations\n")
    long_counts: dict[str, int] = {}
    for p in sized:
        long_counts[p["long"]] = long_counts.get(p["long"], 0) + 1
    stacked = [(tk, n) for tk, n in long_counts.items() if n > 1]
    if stacked:
        w("**Long-side concentration (multiple pairs sharing same long):**\n")
        for tk, n in stacked:
            w(f"- **{tk}** appears in {n} pairs — {n}× exposure on the long side. "
              f"Reduce per-pair sizing proportionally OR diversify to external long.")
        w("")
    untouched = sum(1 for p in sized if not p["shortability"]["reasons"])
    w(f"**Cleanly executable pairs (no shortability gating concerns):** {untouched} of {len(sized)}.")
    w(f"**Tier mix:** {len(tier1)} Tier 1 + {len(tier2)} Tier 2 = {len(sized)} total.\n")
    w("**Reminder:** the framework's 12-month falsification window means slow-bleeding shorts "
      "that move <50% in either direction stay non-falsified. Consider an exit rule (e.g. "
      "close on +20% or after 6 months without confirmation). Tier 2 pairs in particular "
      "may benefit from a wider time window and basket sizing.")
    return "\n".join(lines)


def main():
    pairs = load_pairs()
    selected = select_top(pairs)
    print(f"Selected {len(selected)} of {len(pairs)} pairs after filtering + concentration cap")
    for s in selected:
        print(f"  [{s['tier']}] SHORT {s['short']:>5} / LONG {s['long']:>5}  ({s['theme']})  "
              f"comp={s['short_composite']:.2f}  RED={s['short_red']}  SEVE={s['short_seve']}  MOD={s['short_mod']}")

    sized = build_sizing(selected)
    report = render_report(sized)

    PAIRS_DIR.mkdir(parents=True, exist_ok=True)
    (PAIRS_DIR / "POSITION_SIZING.md").write_text(report)
    (PAIRS_DIR / "position_sizing.json").write_text(json.dumps(sized, indent=2, default=str))
    print(f"\nWrote {PAIRS_DIR / 'POSITION_SIZING.md'}")
    print(f"Wrote {PAIRS_DIR / 'position_sizing.json'}")


if __name__ == "__main__":
    main()
