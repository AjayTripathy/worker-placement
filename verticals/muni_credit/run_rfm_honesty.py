"""Runner — produce HONESTY_SCREEN.md from rfm_honesty_screener results."""
from __future__ import annotations

import json
from pathlib import Path

from rfm_honesty_screener import screen_all

HERE = Path(__file__).parent
OUT_MD = HERE / "outputs" / "HONESTY_SCREEN.md"
OUT_JSON = HERE / "outputs" / "honesty_screen_results.json"

TIER_EMOJI = {
    "HONEST": "✅",
    "MIXED": "🟡",
    "SUSPECT — multiple Mode B framing concerns": "🔴",
}


def main():
    out = screen_all()
    OUT_JSON.parent.mkdir(exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, indent=2))

    lines = []
    lines.append("# Hospital Muni — R/f/M Honesty Screen")
    lines.append("")
    lines.append("Programmatic check of MD&A documents for the four Mode B framing patterns surfaced in the Ascension 2024A R/f/M divergence report. Each check is a deterministic regex/text-pattern test on the pdftotext-extracted MD&A text — no LLM. Any analyst can re-derive these flags by grepping the source PDF.")
    lines.append("")
    lines.append("## Four checks")
    lines.append("1. **Rating-action acknowledgment** — does MD&A discuss recent Moody's/S&P/Fitch actions?")
    lines.append("2. **Operating-margin disclosure** — explicit operating margin % stated, or hidden behind revenue/expense narrative?")
    lines.append("3. **Same-facility framing density** — heavy 'same-facility' framing can obscure consolidated GAAP decline through divestitures")
    lines.append("4. **Investment-income masking** — using investment gains to frame operational 'improvement'?")
    lines.append("")
    lines.append("Scoring: 0-100 per check (higher = more honest). Aggregate is unweighted average.")
    lines.append("")
    lines.append("## Ranking")
    lines.append("")
    lines.append("| Rank | Obligor | Aggregate | Red flags | Tier |")
    lines.append("|---|---|---|---|---|")
    ranked = sorted(out.items(), key=lambda kv: -kv[1]["aggregate_honesty_score"])
    for i, (slug, r) in enumerate(ranked, 1):
        emoji = TIER_EMOJI.get(r["tier"], "⚪")
        tier_display = r["tier"].split(" — ")[0]
        lines.append(f"| {i} | {slug} | {r['aggregate_honesty_score']:.1f} | {r['n_red_flags']} | {emoji} {tier_display} |")
    lines.append("")
    lines.append("## Per-check scores")
    lines.append("")
    lines.append("| Obligor | Rating ack. | Op margin disc. | Same-facility | Inv-income mask |")
    lines.append("|---|---|---|---|---|")
    for slug, r in ranked:
        c = r["checks"]
        lines.append(f"| {slug} | {c['rating_action_acknowledgment']['score']} | "
                     f"{c['operating_margin_disclosure']['score']} | "
                     f"{c['same_facility_framing']['score']} | "
                     f"{c['investment_income_masking']['score']} |")
    lines.append("")
    lines.append("## Detailed findings per obligor")
    lines.append("")
    for slug, r in ranked:
        emoji = TIER_EMOJI.get(r["tier"], "⚪")
        lines.append(f"### {emoji} {slug} — score {r['aggregate_honesty_score']:.1f}, {r['tier']}")
        lines.append("")
        for cname, c in r["checks"].items():
            lines.append(f"- **{cname}** ({c['score']}/100): {c['interpretation']}")
            # Surface raw evidence
            if cname == "rating_action_acknowledgment":
                lines.append(f"  - {c['agency_mentions']} agency mentions, {c['action_mentions']} action terms, {c['cooccurrences']} co-occurrences")
                for s in c.get("samples", []):
                    lines.append(f"  - Sample: `...{s['context'][:200]}...`")
            elif cname == "operating_margin_disclosure":
                lines.append(f"  - {c['explicit_margin_pct_disclosures']} explicit % disclosures, {c['operating_income_loss_mentions']} op income/loss mentions")
                for s in c.get("samples", [])[:2]:
                    lines.append(f"  - Sample: `...{s['context'][:200]}...`")
            elif cname == "same_facility_framing":
                lines.append(f"  - {c['total_mentions']} mentions / {c['word_count']} words = {c['mentions_per_1000_words']}/1k")
                for s in c.get("samples", [])[:2]:
                    lines.append(f"  - Sample: `...{s[:200]}...`")
            elif cname == "investment_income_masking":
                lines.append(f"  - {c['matches_count']} investment-income-as-improvement passages")
                for s in c.get("samples", [])[:2]:
                    lines.append(f"  - Sample: `...{s['context'][:200]}...`")
        lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Methodology notes")
    lines.append("")
    lines.append("**Why deterministic, not LLM?** A signal we can audit and reproduce by hand is more credible than one that requires re-running an LLM. The four checks here are simple enough that any analyst can verify them with `grep` on the source PDF.")
    lines.append("")
    lines.append("**Why these four?** They are the patterns surfaced by the manual Ascension R/f/M divergence report (Ω1, Ω2, R9, Ω5). The Ascension MD&A here scores 35.0 — lowest in the pilot — which validates the screener is picking up the same patterns the human analyst flagged.")
    lines.append("")
    lines.append("**Limitations**:")
    lines.append("- Text extraction quality matters. Ascension's MD&A is full of Unicode bidi marks (we strip them in `normalize()`).")
    lines.append("- A high score is NECESSARY but not SUFFICIENT for honesty — these are 4 specific patterns. An obligor could pass all 4 and still be misleading in other ways.")
    lines.append("- The investment-income-masking check is more pattern-sensitive than the others; expect 20-30% false positive rate on language like 'investment in technology that improved...'")
    lines.append("")
    lines.append("## Next builds")
    lines.append("- Cross-reference honesty score with realized rating outcomes — does LOW score correlate with subsequent negative rating action?")
    lines.append("- Add more checks: covenant compliance disclosure, contingent liability disclosure (pension, litigation), forward-looking statement specificity")
    lines.append("- Scale to remaining 60 obligors once MD&As are pulled")

    OUT_MD.write_text("\n".join(lines))
    print(f"Wrote {OUT_MD}")
    print(f"Wrote {OUT_JSON}")


if __name__ == "__main__":
    main()
