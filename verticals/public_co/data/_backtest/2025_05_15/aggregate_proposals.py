"""Aggregate creative_extensions across all fresh-universe tickers.

For each source_label across all 8 tickers' _proposed_sources/*.json
files, count occurrences and list which tickers proposed it. Output a
ranked backlog of next-connector-to-build candidates.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).parent
PROP_DIR = HERE / "_proposed_sources"


# Pattern-based semantic grouping. Each (regex, group_label) pair
# folds many specific instances ("HCAD", "Montgomery County PA Assessor",
# "Maricopa County assessor") into one bucket ("county_assessor").
_GROUP_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"county\s+(parcel|assessor|property|gis|recorder)", re.I), "county_assessor_or_parcel"),
    (re.compile(r"(hcad|maricopa|tarrant|montgomery county|st\.?\s*lucie|harris county|alameda county|santa barbara county)", re.I), "county_assessor_or_parcel"),
    (re.compile(r"(state).{0,10}(department of state|secretary of state)", re.I), "state_business_registry"),
    (re.compile(r"\b(acra|bizfile|companies registry|cayman|bvi|singapore registr|registro|gazette|companies house)\b", re.I), "foreign_business_registry"),
    (re.compile(r"(state|tceq|cdphe|adeq|calepa|deq|epa permits?|air permit|hazwaste|rcra)", re.I), "state_environmental_permits"),
    (re.compile(r"(license board|state license|real.?estate license|broker license)", re.I), "state_license_board"),
    (re.compile(r"\b(uspto.*(assignment|tess)|trademark|patent assignment)", re.I), "uspto_assignment_or_tess"),
    (re.compile(r"(epo|espacenet|wipo|jp.?patent|china national intellectual)", re.I), "foreign_patent_registry"),
    (re.compile(r"\b(linkedin|indeed|crunchbase)\b", re.I), "linkedin_or_employment_proxy"),
    (re.compile(r"\b(satellite|sentinel|planet labs|maxar|landsat)", re.I), "satellite_imagery"),
    (re.compile(r"\b(customs|bills?\s*of\s*lading|cbp|tradenet|importyeti|panjiva|importgenius)", re.I), "customs_bol"),
    (re.compile(r"\b(sbir|sttr|sbir\.gov|topic.id)", re.I), "sbir_grants_registry"),
    (re.compile(r"\b(darpa|afrl|dsip|dod (program|cooperative)|dtic|osti)", re.I), "dod_dod_program_offices"),
    (re.compile(r"\b(usaid|world bank|idb|euro)", re.I), "foreign_aid_or_multilateral"),
    (re.compile(r"\b(nasa|jpl|techport|ntrs|nspires)", re.I), "nasa_program_data"),
    (re.compile(r"\b(nrc|nuclear regulatory)", re.I), "nrc_nuclear"),
    (re.compile(r"\b(fpds|dibbs|gsa advantage|usaspending|sam\.gov|gsa schedule)", re.I), "fpds_dibbs_gsa"),
    (re.compile(r"\b(fda 510|510\(k\)|fda device|fda drug|fda food|orange book|fda establishment)", re.I), "fda_device_or_drug"),
    (re.compile(r"\b(cms|lcd|ncd|medicare|medicaid)", re.I), "cms_payer_coverage"),
    (re.compile(r"\b(pacer|recap|district court|lawsuit|litigation docket)", re.I), "pacer_litigation"),
    (re.compile(r"\b(pcaob|sec inspections|audit firm)", re.I), "pcaob_audit_quality"),
    (re.compile(r"\b(bls|qcew|county business pattern|census|asm|annual survey)", re.I), "bls_or_census_aggregates"),
    (re.compile(r"\b(unos|organ transplant|registry)", re.I), "clinical_or_industry_registry"),
    (re.compile(r"\b(form 4|insider transaction|sec form)", re.I), "sec_form4_insider"),
    (re.compile(r"\b(on.?chain|bitcoin|blockchain|btc|onchain)", re.I), "on_chain_crypto"),
    (re.compile(r"\b(bis entity|export license|ofac|sanctions)", re.I), "bis_export_or_sanctions"),
    (re.compile(r"\b(phmsa|pipeline)", re.I), "phmsa_pipeline"),
    (re.compile(r"\b(ul product|ul certif|nrtl|underwriter)", re.I), "ul_or_safety_cert"),
    (re.compile(r"\b(nasdaq|listing compliance|deficiency notice)", re.I), "exchange_listing_compliance"),
    (re.compile(r"\b(ahri|aaml|industry directory|trade association|consortium roster)", re.I), "trade_assoc_directory"),
    (re.compile(r"\b(faa.*(registry|airworthiness|part 21|part 107|aircraft)|n.?number)", re.I), "faa_registry"),
    (re.compile(r"\b(epa frs|epa tri|ghgrp|epa snap|section 608)", re.I), "epa_registry_specific"),
]


def normalize(label: str) -> str:
    """Group labels semantically. Falls back to lowercase if no pattern."""
    for pat, group in _GROUP_PATTERNS:
        if pat.search(label):
            return group
    s = re.sub(r"\(.*?\)", "", label).strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def main():
    by_source: dict[str, dict] = {}
    by_ticker: dict[str, int] = {}
    for f in sorted(PROP_DIR.glob("*.creative_extensions.json")):
        ticker = f.name.split(".")[0]
        data = json.loads(f.read_text())
        n = len(data.get("extensions", []))
        by_ticker[ticker] = n
        for ext in data.get("extensions", []):
            label_raw = ext.get("source_label", "")
            key = normalize(label_raw)
            if not key:
                continue
            slot = by_source.setdefault(key, {
                "label_examples": set(),
                "tickers":        set(),
                "domains":        set(),
                "claim_types":    set(),
                "sample_rationale": None,
            })
            slot["label_examples"].add(label_raw)
            slot["tickers"].add(ticker)
            if ext.get("domain"):
                slot["domains"].add(ext["domain"])
            if ext.get("claim_type_taxonomy"):
                slot["claim_types"].add(ext["claim_type_taxonomy"])
            if not slot["sample_rationale"]:
                slot["sample_rationale"] = ext.get("rationale")

    # Per-ticker totals
    print(f"{'='*80}\nPER-TICKER PROPOSAL COUNTS\n{'='*80}")
    for tk, n in sorted(by_ticker.items(), key=lambda x: -x[1]):
        print(f"  {tk}: {n} creative_extensions")
    print(f"\nTotal proposals: {sum(by_ticker.values())} across "
          f"{len(by_ticker)} tickers")

    # Sources ranked by # tickers they appeared in (multi-ticker = high-leverage)
    print(f"\n{'='*80}\nMULTI-TICKER PROPOSALS (high-leverage build candidates)"
          f"\n{'='*80}")
    multi = [(k, v) for k, v in by_source.items() if len(v["tickers"]) >= 2]
    multi.sort(key=lambda x: (-len(x[1]["tickers"]), x[0]))
    print(f"{'rank':>4} {'label':50s} {'#tk':>3} {'tickers':40s} domains")
    for i, (key, slot) in enumerate(multi[:30], 1):
        canonical = sorted(slot["label_examples"], key=len)[0][:48]
        print(f"  {i:>2}. {canonical:50s} {len(slot['tickers']):>3d} "
              f"{','.join(sorted(slot['tickers'])):40s} "
              f"{','.join(sorted(slot['domains']))[:30]}")

    print(f"\nTotal unique sources proposed: {len(by_source)}")
    print(f"Multi-ticker (2+): {len(multi)}")
    print(f"Single-ticker: {len(by_source) - len(multi)}")

    # Save
    out = {
        "by_ticker": dict(sorted(by_ticker.items(), key=lambda x: -x[1])),
        "ranked_sources": [
            {
                "label":      sorted(slot["label_examples"], key=len)[0],
                "all_labels": sorted(slot["label_examples"]),
                "n_tickers":  len(slot["tickers"]),
                "tickers":    sorted(slot["tickers"]),
                "domains":    sorted(slot["domains"]),
                "claim_types":sorted(slot["claim_types"]),
                "sample_rationale": slot["sample_rationale"],
            }
            for key, slot in sorted(by_source.items(),
                                     key=lambda x: -len(x[1]["tickers"]))
        ],
    }
    (HERE / "proposals_backlog.json").write_text(
        json.dumps(out, indent=2, default=str))
    print(f"\nWrote {HERE / 'proposals_backlog.json'}")


if __name__ == "__main__":
    main()
