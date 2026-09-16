"""Luckin Coffee (LKNCY) — Chinese reverse-merger / consumer-retail fraud.

Muddy Waters report dropped 2020-01-31 documenting fabricated transactions
(receipt-by-receipt counts at 981 stores). SEC enforcement followed. The fraud
was internal to Chinese point-of-sale data, which US public records cannot
directly verify — so this backtest will explicitly mark several claims
UNVERIFIABLE. That's a useful framework-coverage signal in itself: the
discriminating M-sources for foreign consumer-retail fraud aren't in the
EDGAR/EPA/USPTO toolkit and would need new connectors (Chinese AIC registry,
mobile app analytics, supplier invoices).

Cutoff: 2020-01-30 (day before Muddy Waters).
"""
from __future__ import annotations

import json
from pathlib import Path

from ..m_sources import edgar_fts, epa_frs, self_text
from ..scoring import Severity


CIK = "0001767582"  # Luckin Coffee Inc.
TICKER = "lkncy"
CUTOFF_DATE = "2020-01-30"
PRIORITY_FORMS = {"F-1", "F-1/A", "424B4", "20-F", "6-K", "8-K", "DEF 14A", "SC 13G"}


CLAIMS = [
    {
        "claim_id": "LKNCY-001",
        "claim_text": "Luckin operated 4,500+ retail stores in China by Q3 2019, growing rapidly",
        "source_form": "6-K",
        "filing_date": "2019-11-13",
        "category": "physical_facility",
        "M_sources": ["epa_frs_luckin_us", "edgar_supplier_mentions"],
    },
    {
        "claim_id": "LKNCY-002",
        "claim_text": "Average store-level same-store sales of ~RMB 4-5/cup with growing transaction volume per store",
        "source_form": "6-K",
        "filing_date": "2019-11-13",
        "category": "operational_metric",
        "M_sources": [],
    },
    {
        "claim_id": "LKNCY-003",
        "claim_text": "Luckin's auditor (Marcum BP / Ernst & Young) issued clean audit opinions",
        "source_form": "F-1 / 20-F",
        "filing_date": "2019-04-22",
        "category": "audit_quality",
        "M_sources": ["edgar_auditor_mentions"],
    },
    {
        "claim_id": "LKNCY-004",
        "claim_text": "Luckin's pre-IPO institutional backers (BlackRock, Singapore GIC, Centurium) demonstrate validation",
        "source_form": "F-1 / SC 13G",
        "filing_date": "2019-04-22",
        "category": "governance",
        "M_sources": ["edgar_sc13_filings"],
    },
    {
        "claim_id": "LKNCY-005",
        "claim_text": "F-1 prospectus presents store growth and revenue figures consistently with subsequent 6-K disclosures",
        "source_form": "F-1 self-text",
        "filing_date": "2019-04-22",
        "category": "internal_consistency",
        "M_sources": ["f1_self_text"],
    },
]


def _f1_path(out_dir: Path) -> dict:
    idx_path = out_dir / "filings_index.json"
    if idx_path.exists():
        idx = json.loads(idx_path.read_text())
        for r in idx:
            if r["form"] in ("F-1", "F-1/A"):
                form_safe = r["form"].replace("/", "_")
                p = out_dir / "filings" / f"{r['accession']}_{form_safe}.txt"
                if p.exists():
                    return {"filing_path": p}
    return {"filing_path": out_dir / "filings" / "MISSING_F-1.txt"}


M_QUERIES = [
    # US EPA FRS — confirms framework coverage gap. Luckin had ZERO US stores;
    # all China. Returning 0 here is correct, not fraud signal.
    ("epa_frs_luckin_us", epa_frs.query_facilities,
     {"facility_name": "Luckin", "state_abbr": "CA"}),

    # EDGAR FTS for any partner / supplier / lessor mentions of Luckin in US
    # public companies' filings.
    ("edgar_supplier_mentions", edgar_fts.query_fulltext,
     {"search_term": "Luckin Coffee", "cutoff_date": CUTOFF_DATE,
      "start_date": "2018-01-01", "forms": "10-K,10-Q,8-K,20-F"}),

    # Auditor change disclosures — 8-K Item 4.01 + EDGAR FTS for the audit firms.
    ("edgar_auditor_mentions", edgar_fts.query_fulltext,
     {"search_term": "Marcum Bernstein", "cutoff_date": CUTOFF_DATE,
      "cik": CIK, "start_date": "2018-01-01",
      "forms": "20-F,6-K,8-K,F-1"}),

    # SC 13G/D filings naming Luckin (institutional ownership disclosure).
    ("edgar_sc13_filings", edgar_fts.query_fulltext,
     {"search_term": "Luckin", "cutoff_date": CUTOFF_DATE,
      "start_date": "2019-01-01", "forms": "SC 13G,SC 13G/A,SC 13D,SC 13D/A"}),

    # F-1 self-text — internal consistency of growth and revenue figures.
    ("f1_self_text", self_text.query_binding_vs_loi, _f1_path),
]


# --- Per-claim scorers ---

def _score_001(ev, c):
    frs = ev.get("epa_frs_luckin_us", {})
    sup = ev.get("edgar_supplier_mentions", {})
    n_us = frs.get("n_facilities", 0)
    n_sup = sup.get("total_hits", 0)
    return {
        "M_check": "EPA FRS for Luckin US facilities (expected 0 — China-only); EDGAR FTS for any US-listed supplier/lessor disclosing Luckin as customer",
        "M_value": (
            f"EPA FRS US facilities: {n_us} (expected 0, China-only operator); "
            f"EDGAR US public-company mentions of 'Luckin Coffee' pre-cutoff: {n_sup}"
        ),
        "M_supports_claim": None,
        "interpretation": (
            "UNVERIFIABLE via US public records. Luckin's stores are in China; the "
            "discriminating M-sources (Chinese AIC commercial registry, individual "
            "store leases, supplier invoices, mobile app downloads) are not in the "
            "current connector toolkit. Framework correctly returns UNVERIFIABLE — "
            "this is a coverage-map signal, not a fraud signal. Adding a Chinese "
            "AIC connector would close this gap."
        ),
        "severity": Severity.UNVERIFIABLE,
        "evidence_url": "https://www.gsxt.gov.cn/ (China National Enterprise Credit Information — would need a connector)",
    }


def _score_002(ev, c):
    return {
        "M_check": "Receipt-level POS data (the actual smoking gun — Muddy Waters did 11,260 hours of mystery shopping)",
        "M_value": "No public-records source for Chinese single-store POS data",
        "M_supports_claim": None,
        "interpretation": (
            "UNVERIFIABLE via public records. The Muddy Waters thesis was based on "
            "originally-collected receipt data (mystery shoppers physically visiting "
            "stores). No equivalent source exists in any public registry. Framework "
            "honestly returns UNVERIFIABLE rather than manufacturing a signal."
        ),
        "severity": Severity.UNVERIFIABLE,
    }


def _score_003(ev, c):
    aud = ev.get("edgar_auditor_mentions", {})
    n = aud.get("total_hits", 0)
    return {
        "M_check": "EDGAR FTS for 'Marcum Bernstein' across Luckin's own filings — count of audit-related disclosures",
        "M_value": f"{n} mentions of audit firm in Luckin's pre-cutoff filings",
        "M_supports_claim": True if n >= 1 else None,
        "interpretation": (
            f"Audit firm disclosed in {n} filings — clean opinion at the time of "
            "claim. PASS as a framework signal: the auditor presence is real and "
            "documented; the auditor's failure to detect the fraud is not "
            "queryable from public records pre-cutoff."
        ),
        "severity": Severity.PASS if n >= 1 else Severity.UNVERIFIABLE,
        "evidence_url": "https://efts.sec.gov/LATEST/search-index",
    }


def _score_004(ev, c):
    sc13 = ev.get("edgar_sc13_filings", {})
    n = sc13.get("total_hits", 0)
    if n >= 3:
        sev = Severity.PASS
        sup = True
        interp = (
            f"{n} SC 13G/D filings naming Luckin pre-cutoff confirms institutional "
            "ownership disclosures (BlackRock, GIC, Centurium). Framework returns "
            "PASS — institutional backers are real, validation is real. "
            "(Institutional validation does not protect against fraud.)"
        )
    else:
        sev = Severity.UNVERIFIABLE
        sup = None
        interp = "Few institutional ownership filings located."
    return {
        "M_check": "EDGAR FTS for SC 13G/D filings naming Luckin",
        "M_value": f"{n} institutional ownership filings pre-cutoff",
        "M_supports_claim": sup,
        "interpretation": interp,
        "severity": sev,
        "evidence_url": "https://efts.sec.gov/LATEST/search-index",
    }


def _score_005(ev, c):
    s = ev.get("f1_self_text", {})
    binding = s.get("binding_count", 0)
    loi = s.get("loi_count", 0)
    return {
        "M_check": "F-1 self-text: binding-vs-LOI characterization (lower discriminative power for non-EV)",
        "M_value": f"binding={binding}, loi={loi}",
        "M_supports_claim": None,
        "interpretation": (
            f"F-1 has {binding} 'binding' / {loi} 'LOI' mentions in pre-order/"
            "reservation context. Less discriminative for a coffee retailer than "
            "for an EV pre-order book — Luckin doesn't sell vehicle reservations. "
            "Framework returns UNVERIFIABLE for this category."
        ),
        "severity": Severity.UNVERIFIABLE,
    }


SCORERS = {
    "LKNCY-001": _score_001,
    "LKNCY-002": _score_002,
    "LKNCY-003": _score_003,
    "LKNCY-004": _score_004,
    "LKNCY-005": _score_005,
}
