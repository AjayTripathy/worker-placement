"""
Build PREDICTIONS.md from predictions.json — concrete forward bets with
falsification criteria.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE / "data" / "_distress_sift"


def runway_tier(rec: dict) -> tuple[str, str]:
    rw = rec.get("runway_months")
    if rw is None:
        return ("UNKNOWN", "⚪")
    if rw < 6:    return ("CRITICAL", "🔴")
    if rw < 12:   return ("WARN", "🟠")
    if rw < 24:   return ("WATCH", "🟡")
    return ("OK", "🟢")


def forward_prediction(rec: dict) -> str:
    """One-paragraph specific prediction with falsification date + observable."""
    tier, _ = runway_tier(rec)
    cash = rec.get("cash") or 0
    burn = rec.get("monthly_burn")
    rw = rec.get("runway_months")
    report = rec.get("report_date", "?")

    if not rec.get("ok"):
        return "Insufficient XBRL data for forward prediction."

    # Falsification date = report_date + 12 months
    try:
        rd = datetime.fromisoformat(report)
        fal_date = (rd + timedelta(days=365)).date().isoformat()
    except Exception:
        fal_date = "(unable to compute)"

    if tier == "CRITICAL":
        return (
            f"**Forward bet:** by **{fal_date}** this company will have done at "
            f"least one of: (a) filed Chapter 11 / Chapter 7 / receivership; "
            f"(b) executed another reverse stock split; (c) raised another "
            f"≥10%-dilutive equity offering; (d) been delisted from its primary "
            f"exchange. Implied runway as of {report} is {rw:.1f} months "
            f"(cash ${cash/1e6:.1f}M ÷ monthly burn ${burn/1e6:.2f}M).  \n"
            f"**Falsification:** if by {fal_date} the company is still listed on the "
            f"same exchange, has not split, has not raised ≥10% dilutive equity, "
            f"and has not entered bankruptcy proceedings, this prediction is wrong."
        )
    if tier == "WARN":
        return (
            f"**Forward bet:** by **{fal_date}** this company will need at least "
            f"one capital raise of ≥10% dilution to avoid going-concern crystallization. "
            f"Implied runway as of {report} is {rw:.1f} months.  \n"
            f"**Falsification:** if by {fal_date} the company has not raised additional "
            f"equity AND remains current on filings AND has not had a reverse split, "
            f"this prediction is wrong."
        )
    if tier == "WATCH":
        return (
            f"**Forward bet:** this company has ≥12 months of cash runway despite "
            f"the going-concern + reverse-split + ATM signals — the multi-signal "
            f"sift produced a false-positive here. **Survives** through {fal_date} "
            f"absent operational shocks.  \n"
            f"**Falsification:** if by {fal_date} the company is in bankruptcy, "
            f"delisted, or has done another reverse split, the WATCH tier was "
            f"too lenient."
        )
    if tier == "OK":
        return (
            f"**Forward bet:** false-positive from the sift. Cash position "
            f"(${cash/1e6:.0f}M) covers >24 months of burn. The going-concern "
            f"qualifier reflects auditor caution, not imminent solvency event.  \n"
            f"**Falsification:** if by {fal_date} this company has filed Chapter 11, "
            f"the sift was right and the cash/burn analysis missed something."
        )
    return "Forward prediction unavailable."


def main():
    rows = json.loads((DATA / "predictions.json").read_text())
    critical = [r for r in rows if runway_tier(r)[0] == "CRITICAL"]
    warn     = [r for r in rows if runway_tier(r)[0] == "WARN"]
    watch    = [r for r in rows if runway_tier(r)[0] == "WATCH"]
    ok       = [r for r in rows if runway_tier(r)[0] == "OK"]
    unk      = [r for r in rows if runway_tier(r)[0] == "UNKNOWN"]

    lines: list[str] = []
    w = lines.append

    w("# Public-co Distress Predictions — Forward Test (v1)\n")
    w(f"_Generated {datetime.utcnow().isoformat()}Z — `verticals.public_co.distress_sift` + `distress_deepread`_\n")

    w("## What this is\n")
    w(
        "Concrete forward bets on a cohort of US-listed public companies that "
        "concentrate multiple distress fingerprints in their SEC filings. "
        "Built by:\n\n"
        "1. Sweeping the SEC EDGAR full-text search (EFTS) API for six distinct "
        "distress phrases in filings since 2026-01-01 (going-concern qualifier, "
        "reverse stock split, change in auditor, minimum-bid-price deficiency, "
        "at-the-market offering, stock-for-services payment).\n"
        "2. Aggregating by CIK and filtering to companies with ≥3 distinct "
        "distress signals concentrated in a single 5-month window.\n"
        "3. Pulling each company's most recent XBRL-tagged financial facts via "
        "the SEC's free `companyfacts` API to compute cash position, trailing-"
        "quarter operating burn, and implied runway in months.\n"
        "4. Producing per-company forward predictions with explicit falsification "
        "criteria (date + observable outcome).\n"
    )
    w("**The signal:** companies in the critical (<6 mo runway) tier have a "
      "materially higher base rate of bankruptcy / further reverse-split / "
      "delisting / large-dilution events over the following 12 months than "
      "the broader Russell 3000 distress cohort. Whether the framework's "
      "discrimination is real on this specific cohort is the testable claim.\n")

    w("## Topline\n")
    w("| Tier | Count |")
    w("|---|---:|")
    w(f"| 🔴 CRITICAL (<6 mo runway) | {len(critical)} |")
    w(f"| 🟠 WARN (6-12 mo runway) | {len(warn)} |")
    w(f"| 🟡 WATCH (12-24 mo runway — multi-signal but adequately funded) | {len(watch)} |")
    w(f"| 🟢 OK (24+ mo runway — sift false-positive) | {len(ok)} |")
    w(f"| ⚪ UNKNOWN (XBRL data unavailable) | {len(unk)} |\n")

    w("## CRITICAL tier — sub-6-month runway, multiple signals\n")
    w("Forward bets are highest-conviction here. Listed in order of recency of latest report.\n")
    critical.sort(key=lambda r: r.get("report_date","") or "", reverse=True)
    for r in critical:
        cik = r["cik"]
        company = r["company"]
        signals = ", ".join(sorted(r["signals"]))
        cash = r.get("cash") or 0
        burn = r.get("monthly_burn") or 0
        rw = r.get("runway_months") or 0
        report = r.get("report_date", "?")
        w(f"### {company} (CIK {cik})\n")
        w(f"- **Signals concentrated 2026-01-01 → present:** {signals}")
        w(f"- **Cash + equivalents (as of {report}):** ${cash/1e6:,.1f}M")
        w(f"- **Trailing-quarter operating burn:** ${burn*3/1e6:,.2f}M (≈ ${burn/1e6:,.2f}M/mo)")
        w(f"- **Implied runway:** {rw:.1f} months")
        w(f"- **EDGAR filings:** https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}\n")
        w(forward_prediction(r))
        w("")

    w("## WARN tier — 6-12 month runway\n")
    w("Capital raise required within a year; bankruptcy possible but not imminent.\n")
    for r in sorted(warn, key=lambda r: r.get("runway_months") or 0):
        cik = r["cik"]; company = r["company"]
        rw = r.get("runway_months") or 0
        cash = r.get("cash") or 0; burn = r.get("monthly_burn") or 0
        report = r.get("report_date", "?")
        w(f"- **{company}** (CIK {cik}) — cash ${cash/1e6:,.1f}M, burn ${burn/1e6:,.2f}M/mo, runway {rw:.1f} mo (as of {report})")
    w("")

    w("## WATCH tier — 12-24 month runway despite multi-signal\n")
    w("Sift surfaced these via the distress-phrase search but XBRL says they are "
      "adequately funded. Either the sift signal is forward-looking (reverse split "
      "to maintain listing, ATM filed but unused) OR the financial picture is "
      "deteriorating below what the most recent XBRL filing shows.\n")
    for r in sorted(watch, key=lambda r: r.get("runway_months") or 0):
        cik = r["cik"]; company = r["company"]
        rw = r.get("runway_months") or 0
        cash = r.get("cash") or 0; burn = r.get("monthly_burn") or 0
        w(f"- **{company}** (CIK {cik}) — cash ${cash/1e6:,.1f}M, burn ${burn/1e6:,.2f}M/mo, runway {rw:.1f} mo")
    w("")

    w("## OK tier — sift false-positives\n")
    w("Multi-signal hits but cash position > 24 months of burn. Acknowledged as "
      "sift false-positives. Useful for understanding the rule's noise floor.\n")
    for r in sorted(ok, key=lambda r: -(r.get("cash") or 0)):
        cik = r["cik"]; company = r["company"]
        cash = r.get("cash") or 0
        w(f"- **{company}** (CIK {cik}) — cash ${cash/1e6:,.1f}M; reasons for distress signals not solvency-driven")
    w("")

    w("## How to read this — and debt/tradeoffs\n")
    w(
        "**What this is:** a structural distress-pattern screen producing per-"
        "company concrete forward bets. The bets fall in three shapes: "
        "(a) bankruptcy / reverse split / large-dilution / delisting within 12 "
        "months of the latest 10-Q for CRITICAL tier; (b) capital raise required "
        "for WARN; (c) survival prediction for WATCH/OK.\n"
    )
    w(
        "**What this is NOT:** a fraud signal. None of the cohort is being "
        "accused of any wrongdoing. Going-concern qualifiers and ATM offerings "
        "are legal and disclosed. The prediction is about *outcome*, not "
        "*malfeasance*.\n"
    )
    w("### Debt + tradeoffs in v1\n")
    w(
        "- **Single-source XBRL.** Cash and burn come from the most recent XBRL-"
        "tagged 10-Q. Companies file XBRL inconsistently; some concepts (e.g., "
        "`CashAndCashEquivalentsAtCarryingValue` vs. `Cash` vs. composite "
        "concept) can mismatch. Cross-check with the actual 10-Q text before "
        "trading on the signal.\n"
        "- **Operating burn is trailing-quarter only.** A company may have "
        "accelerated cost cuts after the latest quarter end that this signal "
        "misses. Some of the CRITICAL tier may have already raised since the "
        "report date (`Aprea Therapeutics` is the obvious OK example — they did "
        "raise post-quarter).\n"
        "- **EDGAR full-text search caps at 1,000 hits per query.** The "
        "`reverse_split` query maxed out — there are >1,000 reverse-split mentions "
        "in 2026 YTD. The sift undercounts. Tighter date-window queries would catch more.\n"
        "- **No insider-selling cross-join yet.** The `public_co` vertical has "
        "EDGAR Form 4 / Form 144 access; cross-referencing with concentrated "
        "insider selling in the same window would tighten the signal further.\n"
        "- **No market-cap or volume filter.** Several names in the cohort are "
        "essentially shell companies with <$10M market cap; these survive on "
        "dilution indefinitely without ever filing bankruptcy. A market-cap "
        "floor of $25M would meaningfully tighten the actionable cohort.\n"
        "- **Calibration is structural, not empirical.** The <6-month, 6-12, "
        "12-24 thresholds are author-declared. A held-out cohort of prior "
        "distress cases would let us tune them to maximize precision on the "
        "12-month bankruptcy outcome (the Layer 3 Rule 6 violation).\n"
    )
    w("### What the right next step is\n")
    w(
        "1. **Pre-register the predictions.** Hash this file's contents and "
        "commit the hash to git or a public timestamp service so the falsification "
        "criteria can't be moved later.\n"
        "2. **Wire Form 4 / Form 144 cross-join.** The `public_co/edgar.py` already "
        "fetches XML; add a Form 4/144 parser to surface concentrated insider "
        "exits in the same date window.\n"
        "3. **Add market-cap / float filter.** Pull from XBRL `EntityCommonStockSharesOutstanding` "
        "and current price (Yahoo / Polygon free tier). Filter cohort to >$25M cap.\n"
        "4. **Compute Layer 3 Rule 5 (stock-for-services) per company.** Already "
        "in `SIGNAL_QUERIES`; surface the explicit equity-for-services dollar "
        "amount from each company's MD&A.\n"
    )

    out = DATA / "PREDICTIONS.md"
    out.write_text("\n".join(lines))
    print(f"Wrote → {out}")
    print(f"  CRITICAL: {len(critical)}  WARN: {len(warn)}  WATCH: {len(watch)}  OK: {len(ok)}  UNK: {len(unk)}")


if __name__ == "__main__":
    main()
