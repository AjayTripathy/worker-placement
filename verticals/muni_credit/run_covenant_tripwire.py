"""Runner — produces COVENANT_TRIPWIRE.md from the screen output."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from covenant_tripwire import run_screen

HERE = Path(__file__).parent
OUT_MD = HERE / "outputs" / "COVENANT_TRIPWIRE.md"
OUT_JSON = HERE / "outputs" / "covenant_tripwire_results.json"


TIER_EMOJI = {
    "TRIPWIRED": "🔴",   # technical default
    "RED":       "🟠",
    "ORANGE":    "🟡",
    "YELLOW":    "🟢",   # within tolerance but worth monitoring
    "GREEN":     "✅",
    "NO_DATA":   "⚪",
}


def format_pct(v):
    if v is None:
        return "n/a"
    return f"{v:+.1f}%"


def main():
    out = run_screen()
    OUT_JSON.parent.mkdir(exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, indent=2))

    lines = []
    lines.append("# Hospital Muni — Covenant Tripwire Screen")
    lines.append("")
    lines.append(f"**Run date**: {out['evaluated_at']}  ")
    lines.append(f"**Obligors evaluated**: {out['n_obligors']}  ")
    lines.append(f"**Methodology**: compare current days-cash-on-hand (and DSCR where available) to obligor-specific Master Trust Indenture covenant minimums. Headroom = (current − minimum) / minimum × 100%. Tier bands: GREEN (>30%), YELLOW (15-30%), ORANGE (5-15%), RED (0-5%), TRIPWIRED (current < minimum).")
    lines.append("")

    dist = out['tier_distribution']
    lines.append("## Tier distribution")
    lines.append("")
    lines.append("| Tier | Count |")
    lines.append("|---|---|")
    for tier in ["TRIPWIRED", "RED", "ORANGE", "YELLOW", "GREEN", "NO_DATA"]:
        lines.append(f"| {TIER_EMOJI[tier]} {tier} | {dist.get(tier, 0)} |")
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
                    lines.append(f"  - Covenant source: {cov_data['covenant_source']} (confidence: {conf})")
            elif "dependency_pct" in cov_data:
                lines.append(f"- **{cov_name}**: {cov_data['dependency_pct']:.0f}% dependency")
                if cov_data.get("_note"):
                    lines.append(f"  - *{cov_data['_note']}*")
        if r.get("dscr_computation"):
            d = r["dscr_computation"]
            if d.get("dscr_operating_only") is not None:
                lines.append(f"- *DSCR detail: operating-only = {d['dscr_operating_only']:.2f}x, "
                             f"all-income = {d['dscr_all_income']:.2f}x; "
                             f"NOI = ${d['noi_operating_only_usd']/1e6:.0f}M (operating) / "
                             f"${d['noi_all_income_usd']/1e6:.0f}M (all-income); "
                             f"annual debt service ${d['annual_debt_service_usd']/1e6:.0f}M*")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Data quality notes")
    lines.append("")
    lines.append("1. **Current metrics (days cash)**: from `data/cafr_overrides.json`. **HAND-CURATED**, not yet primary-source verified. Subject to the same caveat as `realized_outcomes_2023_2025.json` — see verified-outcomes re-verification work.")
    lines.append("2. **Covenant terms**: from `data/covenant_terms.json`. Each covenant has a confidence tag (HIGH/MEDIUM/LOW). LOW = industry-typical default, not obligor-specific MTI quote.")
    lines.append("3. **DSCR not yet wired up**: would require Net Operating Income (from HCRIS/CAFR) and Annual Debt Service (from debt schedule). Pilot only evaluates days-cash-on-hand covenant.")
    lines.append("4. **Forward-looking**: a tripwire flag is a signal of NEAR-TERM (months not years) covenant pressure, not a long-term credit-deterioration signal like the 4-axis composite.")
    lines.append("")
    lines.append("## Next builds")
    lines.append("- DSCR computation from HCRIS NPR + bond debt service schedule")
    lines.append("- MADS coverage")
    lines.append("- Continuous monitoring vs snapshot (alert when an obligor crosses a tier boundary)")
    lines.append("- LLM extraction of covenants from full Official Statements for the remaining 60 obligors")

    OUT_MD.write_text("\n".join(lines))
    print(f"Wrote {OUT_MD}")
    print(f"Wrote {OUT_JSON}")


if __name__ == "__main__":
    main()
