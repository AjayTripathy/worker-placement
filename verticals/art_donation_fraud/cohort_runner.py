"""
Cohort runner for art_donation_fraud (v1).

Pipeline:
  1. Stream all "Gift of" records from Met + MoMA bulk CSVs since min_year.
  2. Aggregate by normalized donor name → portfolio features.
  3. Apply AUCTION_TO_DONATION_MATCH rule to each donor's portfolio.
  4. Produce findings JSON + a polished fraud report.

The §170(e)(7) recapture rule is NOT yet wired (requires a museum deaccession
connector — see connectors_to_add.md).
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from core.models import GapResult, Record
from verticals.art_donation_fraud.rules import RULES
from verticals.art_donation_fraud.rules.auction_to_donation import (
    HIGH_MARKET_VOLATILITY, apply as auction_apply,
)
from verticals.art_donation_fraud.sources import met_bulk_csv, moma_bulk_csv

HIGH_VAL_CLS = {
    "Paintings", "Painting", "Sculpture", "Sculptures",
    "Drawings", "Drawing", "Prints", "Print",
    "Photographs", "Photograph",
}

HERE = Path(__file__).parent
OUT  = HERE / "audit_v1"


def load_all_gifts(min_year: int) -> list[Record]:
    print(f"[1/3] Loading Met + MoMA gifts since {min_year}…", file=sys.stderr)
    recs: list[Record] = []
    for rec in met_bulk_csv.iter_gifts(min_year, HIGH_VAL_CLS):
        recs.append(rec)
    n_met = len(recs)
    print(f"      → Met: {n_met:,}", file=sys.stderr)
    for rec in moma_bulk_csv.iter_gifts(min_year, HIGH_VAL_CLS):
        recs.append(rec)
    n_moma = len(recs) - n_met
    print(f"      → MoMA: {n_moma:,}", file=sys.stderr)
    print(f"      → total: {len(recs):,}", file=sys.stderr)
    return recs


def aggregate_donors(recs: list[Record]) -> dict:
    """Return {donor_norm: portfolio_features_dict}."""
    print(f"[2/3] Aggregating by donor…", file=sys.stderr)
    by_donor: dict[str, dict] = defaultdict(lambda: {
        "donor_raw_variants": set(),
        "works": [],
        "years": Counter(),
        "museums": Counter(),
        "departments": Counter(),
        "classifications": Counter(),
        "artists": Counter(),
        "high_vol_works": 0,
    })
    for r in recs:
        d = r.data
        key = d["donor_name_normalized"]
        if not key:
            continue
        p = by_donor[key]
        p["donor_raw_variants"].add(d["donor_name_raw"])
        p["works"].append({
            "museum":     d["museum"],
            "object_id":  d["object_id"],
            "title":      d["title"],
            "artist":     d["artist"],
            "department": d["department"],
            "classification": d["classification"],
            "accession_year": d["accession_year"],
            "credit_line":    d["credit_line"],
            "url":            d["object_url"],
            "is_highlight":   d.get("is_highlight", False),
        })
        p["years"][d["accession_year"]] += 1
        p["museums"][d["museum"]] += 1
        p["departments"][d["department"]] += 1
        p["classifications"][d["classification"]] += 1
        p["artists"][d["artist"]] += 1
        if d["department"] in HIGH_MARKET_VOLATILITY:
            p["high_vol_works"] += 1
    print(f"      → {len(by_donor):,} distinct normalized donors", file=sys.stderr)
    return dict(by_donor)


def compute_portfolio_features(portfolio: dict) -> dict:
    total = len(portfolio["works"])
    if total == 0:
        return {}
    cluster_max = max(portfolio["years"].values()) if portfolio["years"] else 0
    return {
        "portfolio_works":              total,
        "portfolio_years":              len(portfolio["years"]),
        "portfolio_year_range":         (min(portfolio["years"]), max(portfolio["years"])) if portfolio["years"] else (None, None),
        "portfolio_museums":            list(portfolio["museums"].keys()),
        "portfolio_n_museums":          len(portfolio["museums"]),
        "portfolio_top_departments":    portfolio["departments"].most_common(3),
        "portfolio_top_artists":        portfolio["artists"].most_common(5),
        "portfolio_high_vol_share":     portfolio["high_vol_works"] / total,
        "portfolio_cluster_year_share": cluster_max / total,
        "portfolio_cluster_year":       portfolio["years"].most_common(1)[0][0] if portfolio["years"] else None,
        "portfolio_highlights":         sum(1 for w in portfolio["works"] if w["is_highlight"]),
    }


def score_donors(by_donor: dict) -> list[dict]:
    print(f"[3/3] Applying AUCTION_TO_DONATION_MATCH rule…", file=sys.stderr)
    rule = next(r for r in RULES if r.rule_id == "AUCTION_TO_DONATION_MATCH")
    findings: list[dict] = []
    for donor, portfolio in by_donor.items():
        if not portfolio["works"]:
            continue
        feats = compute_portfolio_features(portfolio)
        # Build a synthetic GapResult to feed the rule (per-portfolio, not per-work)
        meta = {
            **feats,
            "donor_name_normalized": donor,
        }
        gap = GapResult(
            entity_id=donor,
            regulated_value=Decimal(0),
            market_value=Decimal(0),
            expected_regulated=Decimal(0),
            raw_gap=Decimal(0),
            gap_pct=0.0,
            gap_direction="unknown",
            data_quality_flags=[],
            metadata=meta,
        )
        match = auction_apply(rule, gap, [])
        findings.append({
            "donor":                     donor,
            "donor_raw_variants":        sorted(portfolio["donor_raw_variants"]),
            "n_works":                   feats["portfolio_works"],
            "year_range":                feats["portfolio_year_range"],
            "n_distinct_years":          feats["portfolio_years"],
            "museums":                   feats["portfolio_museums"],
            "top_departments":           feats["portfolio_top_departments"],
            "top_artists":               feats["portfolio_top_artists"],
            "high_vol_share":            feats["portfolio_high_vol_share"],
            "cluster_year":              feats["portfolio_cluster_year"],
            "cluster_year_share":        feats["portfolio_cluster_year_share"],
            "n_highlights":              feats["portfolio_highlights"],
            "rule_matched":              match.matched,
            "rule_confidence":           match.confidence,
            "rule_explanation":          match.explanation,
            "sample_works":              portfolio["works"][:10],
        })
    findings.sort(key=lambda f: (-int(f["rule_matched"]), -f["rule_confidence"], -f["n_works"]))
    return findings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-year", type=int, default=2010)
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    recs = load_all_gifts(args.min_year)
    by_donor = aggregate_donors(recs)
    findings = score_donors(by_donor)

    raw = OUT / "donor_findings.json"
    raw.write_text(json.dumps(findings, indent=2, default=str))
    print(f"Wrote {len(findings):,} donor findings → {raw}", file=sys.stderr)


if __name__ == "__main__":
    main()
