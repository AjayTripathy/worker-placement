"""Runner — covenant tripwire screen filtered to BBB-tier universe.

Reads BBB obligor list from data/bbb_universe_obligor_list.json and runs
the screen only against those names. Outputs COVENANT_TRIPWIRE_BBB.md.
"""
from __future__ import annotations

import json
from pathlib import Path

from covenant_tripwire import run_screen

HERE = Path(__file__).parent
OUT_MD = HERE / "outputs" / "COVENANT_TRIPWIRE_BBB.md"
OUT_JSON = HERE / "outputs" / "covenant_tripwire_bbb_results.json"
BBB_LIST = HERE / "data" / "bbb_universe_obligor_list.json"

TIER_EMOJI = {
    "TRIPWIRED": "🔴",
    "RED":       "🟠",
    "ORANGE":    "🟡",
    "YELLOW":    "🟢",
    "GREEN":     "✅",
    "NO_DATA":   "⚪",
}


def format_pct(v):
    if v is None:
        return "n/a"
    return f"{v:+.1f}%"


def main():
    bbb_list = json.loads(BBB_LIST.read_text())["obligors"]
    out = run_screen(obligor_subset=bbb_list)
    OUT_JSON.parent.mkdir(exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, indent=2, default=str))

    lines = []
    lines.append("# Hospital Muni — Covenant Tripwire Screen (BBB-tier Universe)")
    lines.append("")
    lines.append(f"**Run date**: {out['evaluated_at']}  ")
    lines.append(f"**Obligors evaluated**: {out['n_obligors']} (BBB-tier and lower IG)  ")
    lines.append(f"**Methodology**: compare current days-cash-on-hand AND DSCR to obligor-specific Master Trust Indenture covenant minimums. Headroom = (current − minimum) / minimum × 100%. Tier bands: GREEN (>30%), YELLOW (15-30%), ORANGE (5-15%), RED (0-5%), TRIPWIRED (current < minimum).")
    lines.append("")
    lines.append("**Why BBB-tier matters**: the AA-tier pilot showed all GREEN because IG-tier names carry 100-500 days cash against 60-75 day covenants. BBB-tier obligors run much closer to covenant minimums — this is where tripwires actually fire.")
    lines.append("")

    dist = out['tier_distribution']
    lines.append("## Tier distribution")
    lines.append("")
    lines.append("| Tier | Count |")
    lines.append("|---|---|")
    for tier in ["TRIPWIRED", "RED", "ORANGE", "YELLOW", "GREEN", "NO_DATA"]:
        lines.append(f"| {TIER_EMOJI[tier]} {tier} | {dist.get(tier, 0)} |")
    lines.append("")

    # Compact summary table first
    lines.append("## Summary table")
    lines.append("")
    lines.append("| Obligor | Worst tier | Days cash (cur/cov) | DSCR all-inc (cur/cov) | DSCR op-only | Inv-inc dep |")
    lines.append("|---|---|---|---|---|---|")
    for r in out['results']:
        worst = f"{TIER_EMOJI[r['worst_tier']]} {r['worst_tier']}"
        per = r['per_covenant']
        dc = per.get('days_cash_on_hand', {})
        dc_str = f"{dc.get('current', '?')}/{dc.get('covenant_minimum', '?')}" if dc else "n/a"
        dsa = per.get('debt_service_coverage_all_income', {})
        dsa_str = f"{dsa.get('current', '?'):.2f}/{dsa.get('covenant_minimum', '?'):.2f}" if dsa and isinstance(dsa.get('current'), (int, float)) else "n/a"
        dso = per.get('debt_service_coverage_operating_only', {})
        dso_str = f"{dso.get('current', '?'):.2f}" if dso and isinstance(dso.get('current'), (int, float)) else "n/a"
        ii = per.get('investment_income_dependency', {})
        ii_str = f"{ii.get('dependency_pct', '?'):.0f}%" if ii else "n/a"
        lines.append(f"| {r['obligor']} | {worst} | {dc_str} | {dsa_str} | {dso_str} | {ii_str} |")
    lines.append("")

    lines.append("## Detailed results (sorted by severity)")
    lines.append("")
    for r in out['results']:
        lines.append(f"### {TIER_EMOJI[r['worst_tier']]} {r['obligor']} — {r['worst_tier']}")
        lines.append("")
        for cov_name, cov_data in r['per_covenant'].items():
            if "current" in cov_data and "covenant_minimum" in cov_data:
                cur = cov_data['current']
                cur_str = f"{cur:.3f}" if isinstance(cur, float) else str(cur)
                lines.append(f"- **{cov_name}**: current = {cur_str}, "
                             f"covenant min = {cov_data['covenant_minimum']}, "
                             f"headroom = {format_pct(cov_data['headroom_pct'])} "
                             f"({TIER_EMOJI.get(cov_data['tier'], '⚪')} {cov_data['tier']})")
                if cov_data.get("_note"):
                    lines.append(f"  - *{cov_data['_note']}*")
                if cov_data.get("covenant_source"):
                    conf = cov_data.get("covenant_confidence", "UNKNOWN")
                    lines.append(f"  - Source: {cov_data['covenant_source']} (confidence: {conf})")
            elif "dependency_pct" in cov_data:
                lines.append(f"- **{cov_name}**: {cov_data['dependency_pct']:.0f}% dependency")
                if cov_data.get("_note"):
                    lines.append(f"  - *{cov_data['_note']}*")
        if r.get("dscr_computation") and r["dscr_computation"].get("dscr_operating_only") is not None:
            d = r["dscr_computation"]
            lines.append(f"- *DSCR: op-only={d['dscr_operating_only']:.2f}x, all-income={d['dscr_all_income']:.2f}x; "
                         f"NOI ${d['noi_operating_only_usd']/1e6:.0f}M (op) / ${d['noi_all_income_usd']/1e6:.0f}M (all); "
                         f"annual debt svc ${d['annual_debt_service_usd']/1e6:.0f}M*")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Data quality notes")
    lines.append("")
    lines.append("- Covenant terms confidence: see per-row source citations. HIGH = direct from MTI/OS or rating agency quote; MEDIUM = trade press; LOW = industry-typical default.")
    lines.append("- Operating metrics confidence: same tagging. BBB-tier names disclose less than IG-tier, so MEDIUM/LOW more common.")
    lines.append("- Many BBB-tier names that landed as NO_DATA have missing operating metrics (revenue/margin not surfaced in search) — these are gaps not absences of signal.")
    lines.append("- DSCR is the binding covenant for IG-tier names; days-cash is the binding covenant for lower-tier names where liquidity erosion shows up first.")
    lines.append("")

    OUT_MD.write_text("\n".join(lines))
    print(f"Wrote {OUT_MD}")
    print(f"Wrote {OUT_JSON}")
    # Print summary to stdout
    print(f"\n=== TIER DISTRIBUTION ===")
    for tier in ["TRIPWIRED", "RED", "ORANGE", "YELLOW", "GREEN", "NO_DATA"]:
        print(f"  {tier}: {dist.get(tier, 0)}")


if __name__ == "__main__":
    main()
