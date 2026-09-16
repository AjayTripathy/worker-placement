"""
Build per-pair human-readable reports from the auto-generated pair_trades /
position_sizing / borrow_rates inputs.

Each pair gets a Markdown file in reports/<YYYY_MM_DD>/ with:
  - Cohort + tier + composite
  - 1-line thesis
  - Full R/F(M)/M evidence triples per non-PASS claim on the short leg
  - Execution detail: shortability, IBKR borrow rate, hedge ratio,
    notional cap, conservative entry sizing, annualized carry cost

Also generates an index.md and copies the trade book + position sizing
sheets into the same folder for one-stop reading.

Usage:
    python3 -m verticals.public_co.build_pair_reports [--date 2026_05_17]

Reads:
    data/_pair_trades/{pairs.json, position_sizing.json, borrow_rates.json}
    data/_<cohort>_cohort/matrix.json
    data/_local/<TK>.scores.json
    data/_local/<TK>.plan.json  (when available)

Writes:
    reports/<date>/INDEX.md
    reports/<date>/TRADE_BOOK.md          (copied from REPORT_TRADE_BOOK_*.md)
    reports/<date>/PAIR_TRADES.md         (copied from data/_pair_trades/)
    reports/<date>/POSITION_SIZING.md     (copied)
    reports/<date>/borrow_rates.json      (copied)
    reports/<date>/pair_NN_SHORT_LONG.md  (one per pair)
"""
from __future__ import annotations

import argparse
import json
import shutil
from datetime import date as _date
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE / "data"
PAIRS_DIR = DATA / "_pair_trades"

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

ORDER = ["PASS", "MODERATE_UNDERDELIVERY", "SEVERE_UNDERDELIVERY",
         "RED_FLAG_NEGATIVE", "UNVERIFIABLE"]
SEV_BADGE = {
    "RED_FLAG_NEGATIVE":     "🔴 RED",
    "SEVERE_UNDERDELIVERY":  "🟠 SEVERE",
    "MODERATE_UNDERDELIVERY":"🟡 MOD",
    "PASS":                  "🟢 PASS",
    "UNVERIFIABLE":          "⚪ UNV",
}


def load_scores(ticker: str) -> dict | None:
    for variant in (ticker, ticker.lower(), ticker.upper()):
        p = DATA / "_local" / f"{variant}.scores.json"
        if p.exists():
            return json.loads(p.read_text())
    return None


def load_plan(ticker: str) -> dict | None:
    for variant in (ticker, ticker.lower(), ticker.upper()):
        p = DATA / "_local" / f"{variant}.plan.json"
        if p.exists():
            return json.loads(p.read_text())
    return None


def load_matrix_row(theme: str, ticker: str) -> dict | None:
    d = THEME_TO_DIR.get(theme)
    if not d:
        return None
    p = DATA / d / "matrix.json"
    if not p.exists():
        return None
    for r in json.loads(p.read_text()):
        if r["ticker"] == ticker:
            return r
    return None


def find_pair_sizing(sized: list[dict], short: str, long: str) -> dict | None:
    for p in sized:
        if p["short"] == short and p["long"] == long:
            return p
    return None


def render_evidence_block(scores: dict | None, plan: dict | None) -> list[str]:
    """Render the short-leg's non-PASS / non-UNV claims as R/F/M triples."""
    lines: list[str] = []
    if not scores:
        lines.append("_No scores.json available for this ticker._")
        return lines

    by_id = {c["claim_id"]: c for c in (plan or {}).get("claims", [])}
    contrib = [s for s in scores.get("scores", []) if s.get("severity") in
               ("RED_FLAG_NEGATIVE", "SEVERE_UNDERDELIVERY", "MODERATE_UNDERDELIVERY")]
    contrib.sort(key=lambda s: ORDER.index(s.get("severity"))
                 if s.get("severity") in ORDER else 99, reverse=True)

    if not contrib:
        lines.append("_No findings above PASS for this short leg — composite is driven entirely by UNVERIFIABLE claims._")
        return lines

    for sc in contrib:
        cid = sc.get("claim_id", "?")
        sev = sc.get("severity", "?")
        plan_claim = by_id.get(cid, {})
        claim_text = sc.get("claim_text") or plan_claim.get("claim_text", "")
        source_quote = plan_claim.get("source_quote", "")
        m_check = sc.get("M_check", "")
        m_value = sc.get("M_value", "")
        interp = sc.get("interpretation", "")

        lines.append(f"#### {SEV_BADGE.get(sev, sev)} — `{cid}`")
        if claim_text:
            lines.append(f"- **R (claim):** {str(claim_text)[:600]}")
        if source_quote:
            lines.append(f"- **Source quote:** _{str(source_quote)[:280]}_")
        if m_check:
            lines.append(f"- **F (M-source check):** {str(m_check)[:300]}")
        if m_value:
            lines.append(f"- **M (observed):** {str(m_value)[:400]}")
        if interp:
            lines.append(f"- **Why this severity:** {str(interp)[:600]}")
        # Promotion / rescore audit trail
        if sc.get("original_severity"):
            lines.append(f"- **Audit:** originally `{sc['original_severity']}` — adjusted by rescoring.")
        if sc.get("escalation_outcome"):
            lines.append(f"- **Audit:** escalator outcome `{sc['escalation_outcome']}` "
                         f"({sc.get('escalation_rationale','')[:200]})")
        lines.append("")
    return lines


def render_execution_block(sized: dict, borrow: dict | None) -> list[str]:
    lines: list[str] = []
    sh = sized["shortability"]
    s_da = sized.get("short_da") or {}
    l_da = sized.get("long_da") or {}
    h = sized["hedge"]
    n = sized["notional"]

    lines.append("### Shortability")
    lines.append(f"- **Tier:** `{sh['tier']}`")
    lines.append(f"- Price: ${sh.get('price') or 0:.2f}")
    lines.append(f"- Market cap: ${(sh.get('mcap') or 0)/1e9:.2f}B")
    lines.append(f"- Daily $ volume: ${(sh.get('daily_dollar_vol') or 0)/1e6:.2f}M")
    sf = sh.get("short_float_pct")
    lines.append(f"- Short float: {sf*100:.1f}%" if sf is not None else "- Short float: ?")
    for r in sh.get("reasons") or []:
        lines.append(f"- ⚠ {r}")
    lines.append("")

    if borrow and "error" not in borrow:
        lines.append("### IBKR borrow")
        fee = borrow.get("fee_pct")
        fee_s = f"{fee:.2f}%" if isinstance(fee, (int, float)) else "?"
        lines.append(f"- **Latest fee:** **{fee_s}** annualized "
                     f"({borrow.get('latest_date','?')})")
        avail = borrow.get("available_shares") or 0
        lines.append(f"- Shares available: {avail/1e6:.1f}M")
        avg30 = borrow.get("fee_30d_avg")
        max30 = borrow.get("fee_30d_max")
        avg30_s = f"{avg30:.2f}%" if isinstance(avg30, (int, float)) else "?"
        max30_s = f"{max30:.2f}%" if isinstance(max30, (int, float)) else "?"
        lines.append(f"- 30-day avg: {avg30_s}")
        lines.append(f"- 30-day max: {max30_s}")
        lines.append(f"- Trend: **{borrow.get('fee_trend','?')}**")
        lines.append("")
    elif borrow and "error" in borrow:
        lines.append("### IBKR borrow")
        lines.append(f"- ⚠ Not in IBKR lending universe ({borrow.get('error')}). "
                     "Genuine hard-to-borrow; specialty borrow desk required.")
        lines.append("")
    else:
        lines.append("### IBKR borrow")
        lines.append("- _no borrow data captured for this ticker_")
        lines.append("")

    lines.append("### Hedge ratio")
    sb = h.get("short_beta"); lb = h.get("long_beta")
    sb_s = f"{sb:.2f}" if sb is not None else "?"
    lb_s = f"{lb:.2f}" if lb is not None else "?"
    lines.append(f"- **Beta-neutral:** **{h['ratio']:.2f}×** (short β={sb_s}, long β={lb_s})")
    lines.append(f"- _Method: {h['method']}_")
    lines.append(f"- For every $1 long {sized['long']}, short ${h['ratio']:.2f} of {sized['short']}.")
    lines.append("")

    lines.append("### Notional cap (5% daily $ vol)")
    lines.append(f"- Short daily $ vol: ${(n.get('short_daily_dollar_vol') or 0)/1e6:.2f}M → cap ${(n.get('short_5pct_cap') or 0)/1e6:.2f}M")
    lines.append(f"- Long daily $ vol: ${(n.get('long_daily_dollar_vol') or 0)/1e6:.2f}M → cap ${(n.get('long_5pct_cap') or 0)/1e6:.2f}M")
    lines.append(f"- **Binding leg: {n.get('binding_leg')}**")
    lines.append(f"- **Max long-leg notional:** ${(n.get('max_long_notional_$') or 0)/1e6:.2f}M")
    lines.append("")

    # Conservative entry sizing (30% of cap)
    cap = n.get("max_long_notional_$") or 0
    long_entry = cap * 0.30
    short_entry = long_entry * h["ratio"]
    fee_pct = (borrow or {}).get("fee_pct")
    annual_carry = short_entry * (fee_pct / 100) if fee_pct else None

    lines.append("### Suggested conservative entry (30% of cap)")
    lines.append(f"- Long {sized['long']}: **${long_entry/1e6:.2f}M**")
    lines.append(f"- Short {sized['short']}: **${short_entry/1e6:.2f}M**")
    if annual_carry is not None:
        lines.append(f"- Annualized borrow carry on short: **${annual_carry:,.0f}/yr** "
                     f"({fee_pct}% × ${short_entry/1e6:.2f}M)")
    lines.append("")

    return lines


def render_pair_report(sized: dict, borrow_data: dict) -> str:
    short = sized["short"]
    long  = sized["long"]
    theme = sized["theme"]
    tier  = sized.get("tier", "?")

    short_scores = load_scores(short)
    short_plan = load_plan(short)
    short_row  = load_matrix_row(theme, short)
    long_row   = load_matrix_row(theme, long)
    borrow     = borrow_data.get(short.upper())

    lines: list[str] = []
    w = lines.append

    w(f"# SHORT **{short}** / LONG **{long}** — {theme}\n")
    w(f"**Tier:** {tier}   ·   **Composite (short):** {sized['short_composite']:.2f}   ·   "
      f"**Flags (short):** {sized['short_red']}R / {sized['short_seve']}S / {sized['short_mod']}M\n")

    if long_row:
        w(f"**Long-leg composite:** {long_row.get('composite_score',0):.2f} "
          f"(in-cohort cleanest follow)\n")

    if short_row and short_row.get("filing"):
        w(f"**Short-leg filing analyzed:** `{short_row['filing']}`\n")

    w("---\n")
    w("## Thesis\n")
    if tier == "TIER1":
        w("Tier 1 (high-conviction): composite ≥ 0.75 with at least one RED_FLAG or two "
          "SEVERE findings. The trade thesis is a **factual revision** — restatement, "
          "registry contradiction, regulator action, or counterparty churn that will be "
          "visible in subsequent filings within the 12-month falsification window.\n")
    else:
        w("Tier 2 (lower-conviction, MOD-pattern): composite 0.60–1.20 with ≥2 MODERATE "
          "findings and no RED_FLAG. The thesis is a **disclosure-quality re-rating** — "
          "the market eventually penalizes the multiple applied to filings where claims "
          "don't independently verify. Holding period typically 6–12 months; basket "
          "sizing preferred over single-name conviction.\n")

    w("---\n")
    w("## Evidence (R / F(M) / M)\n")
    lines.extend(render_evidence_block(short_scores, short_plan))

    w("---\n")
    w("## Execution\n")
    lines.extend(render_execution_block(sized, borrow))

    w("---\n")
    w("## Risk + falsification\n")
    w("- **Falsification window:** 12 months from cutoff (2026-05-16). Pair survives if "
      "either leg moves >50% against the thesis OR the divergence claim is corroborated "
      "post-cutoff and the pair returns ~0.")
    w("- **Suggested exit rule:** close on +20% adverse move on the short leg, OR "
      "6 months without confirming evidence, whichever comes first.")
    w("- **Hedge ratio reliability:** if either β was missing (default 1:1 fallback), the "
      "hedge is approximate. Watch correlation drift quarterly.")
    if borrow and "error" not in borrow:
        if borrow.get("fee_trend") == "rising":
            w("- **Borrow trend:** ⬆ **rising** — other shorts are crowding in, which often "
              "front-runs the thesis. If borrow keeps tightening, position may need to be sized down.")
        elif borrow.get("fee_trend") == "falling":
            w("- **Borrow trend:** ⬇ **falling** — earlier shorts have covered, suggesting "
              "either the thesis has played out (close) or the market is becoming complacent.")

    # Concentration warning
    w("")
    w("## Pair metadata")
    w(f"- Theme: {theme}")
    w(f"- Generated: 2026-05-17 from frozen position_sizing.json + borrow_rates.json")

    return "\n".join(lines)


def render_index(sized_pairs: list[dict], borrow_data: dict) -> str:
    lines = []
    w = lines.append
    w("# Signal OS — Trade Book Index (2026-05-17)\n")
    w("Curated point-in-time report folder.\n")
    w("## Top-level documents")
    w("- [TRADE_BOOK.md](TRADE_BOOK.md) — executability-focused report (the headline read)")
    w("- [POSITION_SIZING.md](POSITION_SIZING.md) — two-tier sized sheet for all 12 pairs")
    w("- [PAIR_TRADES.md](PAIR_TRADES.md) — full emit list (15 pairs across 12 cohorts)")
    w("- `borrow_rates.json` — frozen IBKR borrow snapshot")
    w("")
    w("## Per-pair reports")
    w("Each file: cohort + tier + composite + R/F(M)/M evidence + shortability + IBKR borrow + hedge ratio + notional cap + suggested entry + carry cost + falsification rules.\n")

    tier1 = [p for p in sized_pairs if p["tier"] == "TIER1"]
    tier2 = [p for p in sized_pairs if p["tier"] == "TIER2"]

    w("### Tier 1 (high-conviction, factual-revision thesis)\n")
    for i, p in enumerate(tier1, 1):
        b = borrow_data.get(p["short"].upper(), {})
        fee = b.get("fee_pct", "?")
        avail = b.get("available_shares") or 0
        fee_s = f"{fee:.2f}%" if isinstance(fee, (int, float)) else "n/a"
        cap = (p["notional"]["max_long_notional_$"] or 0) / 1e6
        sh_tier = p["shortability"]["tier"]
        fname = f"pair_{i:02d}_{p['short']}_{p['long']}.md"
        w(f"- [{p['short']} / {p['long']}](./{fname}) — {p['theme']}, comp **{p['short_composite']:.2f}**, "
          f"borrow {fee_s}, cap ${cap:.2f}M, shortability `{sh_tier}`")
    w("")

    w("### Tier 2 (MOD-pattern, disclosure-quality re-rating)\n")
    for i, p in enumerate(tier2, len(tier1)+1):
        b = borrow_data.get(p["short"].upper(), {})
        fee = b.get("fee_pct", "?")
        fee_s = f"{fee:.2f}%" if isinstance(fee, (int, float)) else "n/a"
        cap = (p["notional"]["max_long_notional_$"] or 0) / 1e6
        sh_tier = p["shortability"]["tier"]
        fname = f"pair_{i:02d}_{p['short']}_{p['long']}.md"
        w(f"- [{p['short']} / {p['long']}](./{fname}) — {p['theme']}, comp **{p['short_composite']:.2f}**, "
          f"borrow {fee_s}, cap ${cap:.2f}M, shortability `{sh_tier}`")
    w("")

    w("## Notes")
    w("- These reports are generated from `data/_pair_trades/{pairs,position_sizing,borrow_rates}.json` "
      "plus the per-ticker `data/_local/<TK>.{plan,queries,scores}.json` files. Re-run the "
      "pipeline (`pair_trades` → `position_sizing` → `build_pair_reports`) to refresh.")
    w("- The data/_pair_trades/ source-of-truth files remain in place; this folder is a "
      "curated read-only artifact for a specific point in time.")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=_date.today().strftime("%Y_%m_%d"))
    args = ap.parse_args()

    out_dir = HERE / "reports" / args.date
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load inputs
    sized = json.loads((PAIRS_DIR / "position_sizing.json").read_text())
    borrow = json.loads((PAIRS_DIR / "borrow_rates.json").read_text())

    # Order: Tier 1 (by composite desc), then Tier 2 (by composite desc)
    tier1 = sorted([p for p in sized if p["tier"] == "TIER1"],
                   key=lambda x: -x["short_composite"])
    tier2 = sorted([p for p in sized if p["tier"] == "TIER2"],
                   key=lambda x: -x["short_composite"])
    ordered = tier1 + tier2

    # Render per-pair files
    for i, p in enumerate(ordered, 1):
        report = render_pair_report(p, borrow)
        fname = f"pair_{i:02d}_{p['short']}_{p['long']}.md"
        (out_dir / fname).write_text(report)

    # Copy the auto-generated source-of-truth files into the report folder
    # so the bundle is self-contained. TRADE_BOOK.md is hand-written and
    # lives canonically in reports/<date>/TRADE_BOOK.md — we do NOT
    # overwrite it on re-run; the user edits it in place.
    for src, dst in [
        (PAIRS_DIR / "POSITION_SIZING.md", out_dir / "POSITION_SIZING.md"),
        (PAIRS_DIR / "PAIR_TRADES.md",     out_dir / "PAIR_TRADES.md"),
        (PAIRS_DIR / "borrow_rates.json",  out_dir / "borrow_rates.json"),
    ]:
        if src.exists():
            shutil.copyfile(src, dst)

    # Index
    (out_dir / "INDEX.md").write_text(render_index(ordered, borrow))

    n_files = len(list(out_dir.iterdir()))
    print(f"Wrote {n_files} files to {out_dir}/")


if __name__ == "__main__":
    main()
