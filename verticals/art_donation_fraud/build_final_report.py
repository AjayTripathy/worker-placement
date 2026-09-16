"""
Build the polished fraud_report.md from donor_findings.json.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent
OUT  = HERE / "audit_v1"


def main():
    findings = json.loads((OUT / "donor_findings.json").read_text())
    matched = [f for f in findings if f["rule_matched"]]
    artists = [f for f in findings if "ARTIST" in f["donor"] or "DONOR" in f["donor"]]

    total_donors    = len(findings)
    total_matched   = len(matched)
    total_works     = sum(f["n_works"] for f in findings)
    matched_works   = sum(f["n_works"] for f in matched)

    # Partition matched donors by archetype
    bequest_pattern = [f for f in matched
                       if f["n_distinct_years"] <= 2 and f["cluster_year_share"] >= 0.95]
    living_active = [f for f in matched if f not in bequest_pattern
                     and f["high_vol_share"] >= 0.5]
    portfolio_scale = [f for f in matched if f["n_works"] >= 100 and f not in bequest_pattern]

    # Highest-risk archetype: medium-volume, high-volatility, clustered
    highest_risk = sorted(
        [f for f in matched
         if 20 <= f["n_works"] <= 200
         and f["high_vol_share"] >= 0.3
         and "FOUNDATION" not in f["donor"]
         and "ARTIST" not in f["donor"]],
        key=lambda x: -(x["high_vol_share"] * x["n_works"] * x["cluster_year_share"]),
    )

    lines: list[str] = []
    w = lines.append

    w("# Art Donation Fraud — Cohort Intelligence Report (v1)\n")
    w(f"_Generated {datetime.utcnow().isoformat()}Z — `verticals.art_donation_fraud.cohort_runner`_\n")

    w("## What this is\n")
    w(
        "End-to-end run of the Signal OS `art_donation_fraud` vertical. "
        "Pulls every \"Gift of\" / \"Bequest of\" / \"Promised Gift of\" "
        "high-value-classification record from the Metropolitan Museum of "
        "Art and the Museum of Modern Art bulk open-data CSVs, aggregates "
        "by normalized donor name, computes per-donor portfolio features, "
        "and applies the `AUCTION_TO_DONATION_MATCH` rule "
        "(IRC §170(e)(1)(A) + Treas. Reg. §1.170A-13(c)).\n"
    )
    w(
        "**R (claim, not directly observed):** the donor's claimed fair-market-value "
        "deduction on Form 8283. Form 8283 is not public; we infer at the cohort "
        "level rather than per-work.\n\n"
        "**f (relationship):** Treas. Reg. §1.170A-13(c) — claimed FMV must equal what a willing "
        "buyer would pay a willing seller in the regular market. Auction comparables "
        "for the same artist / period / medium are the regulatory benchmark.\n\n"
        "**M (observed):** Met + MoMA acquisition records (open-data CSVs, free, "
        "agent-doable). Per-work auction comparables would close the loop — see "
        "*Debt and tradeoffs* below.\n"
    )

    w("## Topline\n")
    w("| Metric | Value |")
    w("|---|---:|")
    w(f"| Distinct normalized donors (Met + MoMA, gifts 2010+) | {total_donors:,} |")
    w(f"| Total high-value-classification gift records | {total_works:,} |")
    w(f"| Donors flagged by `AUCTION_TO_DONATION_MATCH` | {total_matched:,} |")
    w(f"| Works in flagged-donor portfolios | {matched_works:,} |")
    w(f"| Of those, bequest-pattern (single-year disbursement) | {len(bequest_pattern):,} |")
    w(f"| Of those, active living-collector pattern (≥50% market-volatile) | {len(living_active):,} |")
    w(f"| Of those, portfolio-scale donors (≥100 works) | {len(portfolio_scale):,} |\n")

    w("## Highest-risk archetype — medium-volume, market-volatile, clustered\n")
    w(
        "Mid-sized (20-200 work) portfolios concentrated in Modern/Contemporary "
        "or European Paintings, with most works donated in a single tax year "
        "(consistent with a bunching strategy or single-year tax planning event). "
        "This is the archetype where the gap between cost basis and claimed FMV "
        "is most exploitable: high-volatility market = subjective appraisal "
        "values; concentrated timing = single appraiser engagement; mid-sized "
        "portfolio = below the IRS Art Advisory Panel mandatory threshold ($50K "
        "per item) for most individual works.\n"
    )
    w("| Rank | Donor (normalized) | Works | Year range | Cluster yr | Cluster % | High-vol % | Top dept |")
    w("|---:|---|---:|---|---:|---:|---:|---|")
    for i, f in enumerate(highest_risk[:30], 1):
        yr_lo, yr_hi = f["year_range"]
        top_dept = f["top_departments"][0][0] if f["top_departments"] else "—"
        w(f"| {i} | {f['donor'][:45]} | {f['n_works']} | {yr_lo}–{yr_hi} | "
          f"{f['cluster_year']} | {f['cluster_year_share']:.0%} | "
          f"{f['high_vol_share']:.0%} | {top_dept[:25]} |")
    w("")

    w("## Bequest-pattern donors (estate disbursement, lower fraud risk)\n")
    w(
        "Single-year, single-event disbursements consistent with estate gifts "
        "or foundation dissolution. Lower fraud risk because the donor (decedent) "
        "no longer benefits from any FMV inflation; the §170(e)(7) recapture "
        "still applies if the museum disposes of the work early, but the "
        "primary `AUCTION_TO_DONATION_MATCH` fraud shape doesn't fit.\n"
    )
    w(f"_{len(bequest_pattern):,} donors. Top 15 by volume:_\n")
    w("| Donor | Works | Cluster year | Top dept |")
    w("|---|---:|---:|---|")
    for f in sorted(bequest_pattern, key=lambda x: -x["n_works"])[:15]:
        top_dept = f["top_departments"][0][0] if f["top_departments"] else "—"
        w(f"| {f['donor'][:50]} | {f['n_works']} | {f['cluster_year']} | {top_dept[:30]} |")
    w("")

    w("## Portfolio-scale active donors\n")
    w(
        "Donors with ≥100 works in the Met+MoMA collection from 2010+ who have "
        "been donating across multiple years (i.e., not pure bequest). These are "
        "the institutional-scale collectors. Many are legitimate, but the "
        "pattern of large-scale repeat donation is also where the most "
        "sophisticated tax-shelter structures appear (private operating "
        "foundations donating to museums, charitable lead annuity trusts, etc.).\n"
    )
    w("| Donor | Works | Years span | Museums | High-vol % | Top depts |")
    w("|---|---:|---:|---|---:|---|")
    for f in sorted(portfolio_scale, key=lambda x: -x["n_works"])[:25]:
        museums = "+".join(sorted(f["museums"]))
        depts = "; ".join(f"{d}({n})" for d, n in f["top_departments"][:2])
        w(f"| {f['donor'][:45]} | {f['n_works']} | {f['n_distinct_years']} | "
          f"{museums} | {f['high_vol_share']:.0%} | {depts[:50]} |")
    w("")

    # Append the debt & tradeoffs section
    w("---\n")
    w("## Debt and tradeoffs (built into this v1)\n")
    w(
        "Per the connector-discipline rule, this section is honest about what "
        "is shippable today vs. what requires another connector or external "
        "action. None of the items below are shipped in this run.\n"
    )

    w("### Binding constraint: per-work auction comparables\n")
    w(
        "The `AUCTION_TO_DONATION_MATCH` rule fires today on **structural portfolio "
        "patterns** (volume, classification mix, year-clustering) rather than on "
        "per-work auction comps. The cleanest fraud signal — \"donor X bought work "
        "W at Christie's NY in 2022 for $1.2M, then donated W to the Met in 2023 "
        "and claimed $5M FMV\" — requires an auction-comp connector that this v1 "
        "does not have.\n"
    )
    w("**Auction connector triage (per connector-discipline rule):**\n")
    w("| Source | Bucket | Probed today | Outcome |")
    w("|---|---|---|---|")
    w("| Christie's lot archive | agent-doable (in theory) | yes | `/api/v1/search` empty; 404 on guessed paths. Real API requires reverse-engineering their internal GraphQL. |")
    w("| Sotheby's lot archive | agent-doable (in theory) | yes | Results page returns 200 but no `__NEXT_DATA__` and no price strings — fully JS-rendered. Would need Playwright + bot-detection bypass. |")
    w("| Artsy public API | agent-adjacent (free key required) | yes | 401 without `xapp_token`. Free signup at artsy.net/developers. |")
    w("| Wikidata SPARQL (`P2284 price`) | agent-doable | yes | SPARQL endpoint timed out on the auction-price query; would need narrower query or alternate mirror. |")
    w("| Heritage Auctions | agent-doable | yes | TLS 1.0 alert from their server — needs a TLS-version fallback or direct HTML scrape. |")
    w("| Phillips lot archive | agent-doable | partial | 200 on past-auctions page (6.8MB HTML); parser not yet written. |")
    w("| Artnet / Artprice / MutualArt | **paid-vendor, human-doable** | n/a | Comprehensive auction comps; the right answer for production. Artnet Price Database: $480/yr individual, ~$2.5K/yr commercial. |")
    w("")
    w("**Recommended next step:** sign up for the free Artsy `xapp_token` "
      "(agent-adjacent, ~5 min), then build a Sotheby's HTML scraper using "
      "Playwright (~2 hr). The auction-comp coverage would convert this "
      "cohort-intelligence report into per-work fraud confirmations.\n")

    w("### Secondary connectors not yet wired\n")
    w("- **Other top US museums.** This v1 covers only Met + MoMA. The Whitney, "
      "Guggenheim, Art Institute Chicago, LACMA, Getty, Boston MFA, Philadelphia "
      "Museum of Art, and SFMOMA collectively account for the bulk of major-donor "
      "art philanthropy. None publish bulk CSVs as cleanly as Met/MoMA, but most "
      "have either web-scrapeable collection pages or downloadable acquisition "
      "lists. **Bucket: agent-doable.** Estimated effort: 1-2 hrs per museum scraper.\n"
      "- **Museum deaccession records.** Required for the `EARLY_DEACCESSION_RECAPTURE` "
      "(§170(e)(7)) rule which is currently `implementation=None`. Deaccessions "
      "are published in piecemeal fashion (museum press releases, ARTnews / Art "
      "Newspaper coverage, auction lot consignor names). No central registry. "
      "**Bucket: human-doable** — best constructed by FOIL request to museums "
      "(museums are usually 501(c)(3) and subject to state non-profit disclosure) "
      "or via paid art-news archive subscription.\n"
      "- **Form 990 Schedule M bulk.** IRS publishes 990 XML in bulk via the AWS "
      "S3 mirror `s3://irs-form-990/`. Schedule M reports total non-cash "
      "contributions by category per museum-year. Adds aggregate sanity check "
      "(does Met's reported non-cash gift value match the sum of inferred "
      "values of works we see?). **Bucket: agent-doable.** Estimated effort: 2-3 hrs.\n"
      "- **IRS Art Advisory Panel annual reports.** Published PDFs with aggregate "
      "statistics on appraisal reviews (volume of submissions, % reduced, average "
      "reduction). Useful for calibrating the base rate of fraud. **Bucket: "
      "agent-doable.** Estimated effort: 1 hr (PDF scrape).\n"
      "- **Donor wealth / capital-gains-event correlator.** Public-figure donors "
      "with known wealth events (IPO, large stock vest, real-estate sale) in "
      "the same year as a clustered gift make for the strongest fraud-risk "
      "signal. Requires SEC EDGAR Form 144 / Form 4 cross-join. **Bucket: "
      "agent-doable.** Estimated effort: 2-4 hrs.\n")

    w("### Methodological tradeoffs in this v1\n")
    w(
        "- **Donor name normalization is regex-based.** Catches most patterns "
        "(`Mr. and Mrs. X` → `X`; honorific stripping) but misses long composite "
        "names (`HELENA BIENSTOCK CYNTHIA MACKAY KEEGAN AND FRANK E JOHNSON` is a "
        "joint gift that should be split into 3 distinct donors). Per-donor "
        "aggregation undercounts as a result.\n"
        "- **Bequest vs. lifetime gift partitioning is heuristic.** I treat "
        "single-year ≥95% clustering as bequest. The actual cleanest signal is the "
        "credit-line prefix (`Bequest of` vs `Gift of` vs `Promised Gift of`); "
        "currently the parser captures this in `gift_year` but the runner does "
        "not yet use it as a partition key.\n"
        "- **High-value classification filter is narrow.** Photographs and prints "
        "dominate the cohort (5,767 records of 15,936). Both have legitimate "
        "fraud cases but the highest dollar exposure per item is in paintings + "
        "sculpture (where the rule actually targets via `high_vol_share`). The "
        "filter could be tightened to exclude prints/photographs from the "
        "high-volume rule branch — keeping them only in the high-volatility branch.\n"
        "- **No artist-market-volatility data.** The rule treats all of "
        "\"Modern and Contemporary Art\" as high-volatility, but within the dept "
        "a Wade Guyton donation and an unknown emerging artist donation are very "
        "different. An artist-level volatility score (auction price σ over time) "
        "would refine the signal.\n"
        "- **Single-museum view of each donor.** The Met-cross-MoMA pattern (e.g., "
        "Patricia Phelps de Cisneros gives to BOTH) is detected because we union "
        "the two CSVs. But the broader cross-museum view (Whitney + Guggenheim + "
        "MoMA + Met) is not — and that's where the biggest patterns live "
        "(`Eli Broad`, `David Geffen`, `Henry Kravis` etc. spread their gifts).\n"
    )

    report = OUT / "fraud_report.md"
    report.write_text("\n".join(lines))
    print(f"Wrote final report → {report}")
    print(f"  total donors: {total_donors:,}")
    print(f"  matched donors: {total_matched:,}")
    print(f"  highest-risk archetype: {len(highest_risk):,}")


if __name__ == "__main__":
    main()
