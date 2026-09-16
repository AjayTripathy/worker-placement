"""Multi-venue disclosure consistency auditor.

Sibling concept to claim_evolution.py:

- claim_evolution: ONE focal claim → walk FORWARD through EDGAR → classify each
  subsequent reference. Forward-looking, EDGAR-only.

- multi_venue_disclosure_consistency: ONE underlying fact pattern → gather
  PRIOR time-locked disclosures of that pattern across MULTIPLE venues
  (conference posters, prior 10-Ks, ClinicalTrials.gov versions, NI 43-101
  reports, FDA briefings, press releases) → time-order → cross-classify
  against the CURRENT focal disclosure. Backward-looking, venue-pluralistic.

Same LLM classifier (disclosure_classifier.classify) — different ingestion +
different directional semantics.

## R/M independence

Each prior disclosure is a time-locked R. Once a poster was presented at
CTOS 2025 Nov 13, the issuer cannot retroactively rewrite it. That makes
prior-R independent of current-R via the time axis — exactly the R/M
independence requirement satisfied. The "M" here is the prior disclosure,
serving as the comparator against current R.

## What fires the detector

Multiple AFFIRMED across venues = consistent disclosure → no fire (clean).
Any TERMINATED or substantive AMENDED across venues = NARRATIVE DRIFT
detected → fire with severity based on:
- # of inconsistencies
- Magnitude of cohort/scope changes
- Whether the drift is consistent direction (suggests selective updating)

## Use cases this enables (beyond biotech)

| Asset class       | Fact pattern              | Venues to compare                                   |
|-------------------|---------------------------|------------------------------------------------------|
| Biotech IPO       | Clinical trial readout    | S-1 ↔ ASCO ↔ CTOS ↔ AACR ↔ ClinicalTrials.gov vers. |
| Mining IPO        | Mineral reserve estimate  | S-1 ↔ NI 43-101 technical report ↔ SME/AIME poster   |
| PE-backed IPO     | Deal-size + use-of-proceeds | S-1 ↔ Form D ↔ pitch deck ↔ press release          |
| Defense IPO       | Contract revenue scope    | S-1 ↔ DoD press release ↔ usaspending.gov           |
| Bank IPO          | Credit quality / NPL      | S-1 ↔ prior Call Reports ↔ FDIC reports             |

## Ingestion adapters

v1 ships with:
- `ingest_manual(disclosures)` — caller provides list of {venue, date, text, url}
- `ingest_clinicaltrials_gov_history(nct_id)` — REAL adapter using CT.gov
  version history endpoint (returns per-version snapshot of protocol)

v2+ adapters (stubs with TODO):
- ingest_asco_meeting_library
- ingest_aacr_abstracts
- ingest_ctos_proceedings
- ingest_ni_43_101_reports
- ingest_dod_press_releases
"""
from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Optional

from . import disclosure_classifier

APPLIES_TO = {
    "sic_codes": [2834, 2836, 8731, 3841, 3845, 1041, 1044, 3812, 3721, 3728, 6020],
    "sic_prefixes": ["283", "384", "873", "104", "381", "372", "602"],
    "issuer_features": [
        "clinical_trial_program",
        "diagnostics_or_lab_business",
        "mineral_resource_estimate",
        "pe_sponsor_control",
        "mentions_dod_program",
        "credit_quality_disclosure",
    ],
    "asset_classes": ["corporate_ipo_dd"],
    # PROMOTED UNIVERSAL 2026-08-11 (FVRR miss): transcript-vs-vetted-document divergence is
    # not sector-specific — FVRR's "$1,000+ projects grew 34%/25% on a gross order amount
    # basis" existed ONLY in the call transcript; the vetted 6-K exhibit said client COUNT.
    # The original SIC-gated contract (biotech/mining/defense, where the detector was born)
    # meant no bench was ever ASSIGNED the venue diff on a services name. Recall-floor
    # lesson: key on the verification attribute (load-bearing claim cited from a spoken/
    # secondary venue), not on the sector where the detector was invented.
    "applies_universally": True,
    "kind": "m_source",
    "summary": "Cross-venue, cross-time consistency auditor — compares current focal disclosure against prior time-locked R from conference proceedings / prior filings / CT.gov history / NI 43-101 / etc. Same R/M independence framework as Pentagon J-Book, except the independence axis is time (not source). UNIVERSAL LEG (2026-08-11): also diffs transcript-sourced quantitative claims against the vetted document (PR/filing text now inlined in every evidence pack); fires on basis-shift (count vs dollars, adjusted vs GAAP, cohort redefinition) between the spoken and vetted venue.",
    "verification_question": "For the issuer's current focal claim about underlying fact pattern X, do the prior time-locked public disclosures of X across all venues (conferences, prior filings, version history) tell a consistent story — or has the narrative shifted in a self-serving way between cutoffs? AND: for any load-bearing quantitative claim cited from a call transcript, does the vetted document (release/filing) state the same claim on the same basis — or does the marketed takeaway diverge from the vetted disclosure (FVRR class: dollars in the transcript, count in the release)?",
}


# ── Disclosure record schema ─────────────────────────────────────────

@dataclass
class Disclosure:
    venue: str                       # "S-1" | "ASCO 2025 poster" | "CT.gov v15" | "NI 43-101 (Behre Dolbear, 2024)" | ...
    date: str                        # ISO YYYY-MM-DD
    text: str                        # the disclosure snippet (typically 500-3000 chars)
    source_url: Optional[str] = None
    venue_credibility_tier: str = "STANDARD"   # PRIMARY | STANDARD | PROMOTIONAL — affects severity weight


# ── Ingestion adapters ──────────────────────────────────────────────

HEADERS = {"User-Agent": "Signal OS DD Pipeline ajay@example.com"}


def ingest_manual(disclosures: list[dict]) -> list[Disclosure]:
    """v1 ingestion: caller supplies dicts. Most flexible; used when the
    orchestrator (or sub-agent) has already retrieved conference data and
    wants this module to just do the comparison."""
    out = []
    for d in disclosures:
        out.append(Disclosure(
            venue=d["venue"],
            date=d["date"],
            text=d["text"],
            source_url=d.get("source_url"),
            venue_credibility_tier=d.get("venue_credibility_tier", "STANDARD"),
        ))
    return out


def ingest_clinicaltrials_gov_history(nct_id: str) -> list[Disclosure]:
    """REAL adapter: fetches the version history for a CT.gov trial and returns
    one Disclosure per prior version. Each version's "study record" is the
    time-locked R as it stood at version-N's posting date.

    Uses CT.gov INTERNAL API: /api/int/studies/{nct_id}/history (returns JSON
    with one entry per version + moduleLabels describing what changed). The
    public v2 API does not expose history; the int endpoint is what powers
    the CT.gov web UI's "History of Changes" tab.
    """
    url = f"https://clinicaltrials.gov/api/int/studies/{nct_id}/history"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.loads(r.read())
    except Exception as e:
        print(f"CT.gov history fetch error for {nct_id}: {e}", file=sys.stderr)
        return []
    out = []
    for v in d.get("changes", []):
        version = v.get("version", "?")
        ver_date = v.get("date", "")
        # Each version has a summary of what changed; pull the full study record
        # for the version if we want full text comparison
        version_url = f"https://clinicaltrials.gov/study/{nct_id}?tab=history&studyVersion={version}"
        # For v1, we capture the version summary + date; full-record diff is v2 work
        summary = json.dumps(v, default=str)[:2000]
        out.append(Disclosure(
            venue=f"ClinicalTrials.gov v{version}",
            date=ver_date,
            text=summary,
            source_url=version_url,
            venue_credibility_tier="PRIMARY",  # CT.gov is regulator-mandated, primary source
        ))
    return out


def ingest_asco_meeting_library(sponsor_name: str, indication: str,
                                 year_min: int = 2020) -> list[Disclosure]:
    """TODO v2: ASCO Meeting Library has a structured search; can pull
    abstracts matching sponsor + indication + year range. v1 stub returns
    empty list; caller should use ingest_manual() for ASCO data."""
    return []


def ingest_aacr_abstracts(sponsor_name: str, indication: str,
                           year_min: int = 2020) -> list[Disclosure]:
    """TODO v2: AACR abstract database. v1 stub returns empty list."""
    return []


def ingest_ctos_proceedings(sponsor_name: str, indication: str,
                             year_min: int = 2020) -> list[Disclosure]:
    """TODO v2: CTOS proceedings (desmoid + soft-tissue sarcoma focal).
    v1 stub returns empty list."""
    return []


def ingest_ni_43_101_reports(issuer_name: str, project_name: str,
                              year_min: int = 2015) -> list[Disclosure]:
    """TODO v2: NI 43-101 technical reports on SEDAR+ (Canadian) or filed
    as exhibits to SEC F-1/20-F. v1 stub returns empty list."""
    return []


def ingest_dod_press_releases(contractor_name: str, program: str,
                               year_min: int = 2018) -> list[Disclosure]:
    """TODO v2: DoD contract awards via defense.gov/News/Contracts/. v1 stub
    returns empty list."""
    return []


# ── Core consistency analyzer ────────────────────────────────────────

def audit_disclosure_chain(
    fact_pattern: str,
    focal_disclosure: Disclosure,
    prior_disclosures: list[Disclosure],
    max_classify: int = 8,
) -> dict:
    """Compare a focal (current) disclosure against a list of prior time-locked
    disclosures of the same underlying fact pattern. Classify each prior vs
    focal pairing as AFFIRMED / AMENDED / TERMINATED / UNRELATED. Aggregate
    into consistency verdict.

    Returns:
      {
        "fact_pattern": str,
        "focal": {venue, date, ...},
        "n_prior_disclosures": int,
        "n_classified": int,
        "classifications": [
          {prior_venue, prior_date, classification, reasoning, ...}, ...
        ],
        "classification_counts": {AFFIRMED, AMENDED, TERMINATED, UNRELATED},
        "consistency_verdict": "CONSISTENT" | "AFFIRMED_ACROSS_VENUES" |
                                "NARRATIVE_DRIFT_DETECTED" | "TERMINATION_INCONSISTENCY" |
                                "INSUFFICIENT_PRIOR_DISCLOSURES" | "LLM_UNAVAILABLE",
        "severity": "LOW" | "MEDIUM" | "HIGH" | "RED" | None,
      }
    """
    if not disclosure_classifier.is_available():
        return {"fact_pattern": fact_pattern,
                "consistency_verdict": "LLM_UNAVAILABLE",
                "reason": disclosure_classifier.unavailable_reason(),
                "severity": None}
    if not prior_disclosures:
        return {"fact_pattern": fact_pattern,
                "consistency_verdict": "INSUFFICIENT_PRIOR_DISCLOSURES",
                "severity": None}

    # Time-order priors ascending
    priors_sorted = sorted(prior_disclosures, key=lambda d: d.date or "")
    capped = priors_sorted[:max_classify]

    findings = []
    n_aff = n_amd = n_trm = n_unr = 0
    for prior in capped:
        # Build the snippet: focal's claim + prior's claim, side-by-side
        snippet = (
            f"CURRENT focal disclosure ({focal_disclosure.venue}, {focal_disclosure.date}):\n"
            f"{focal_disclosure.text[:1500]}\n\n"
            f"PRIOR disclosure ({prior.venue}, {prior.date}):\n"
            f"{prior.text[:1500]}\n\n"
            f"Test whether PRIOR is AFFIRMED, AMENDED, TERMINATED, or UNRELATED by CURRENT."
        )
        cls = disclosure_classifier.classify(
            search_term=fact_pattern,
            snippet=snippet,
            venue=prior.venue,
            disclosure_date=prior.date,
        )
        if "error" in cls:
            findings.append({
                "prior_venue":     prior.venue,
                "prior_date":      prior.date,
                "prior_source_url": prior.source_url,
                "classification":  "ERROR",
                "reasoning":       cls.get("error", ""),
            })
            continue
        c = cls["classification"]
        if c == "AFFIRMED":   n_aff += 1
        elif c == "AMENDED":  n_amd += 1
        elif c == "TERMINATED": n_trm += 1
        else:                  n_unr += 1
        findings.append({
            "prior_venue":      prior.venue,
            "prior_date":       prior.date,
            "prior_source_url": prior.source_url,
            "prior_credibility": prior.venue_credibility_tier,
            "classification":   c,
            "reasoning":        cls.get("reasoning", ""),
        })

    n_classified = n_aff + n_amd + n_trm + n_unr
    verdict = None
    severity = None
    if n_trm > 0:
        verdict = "TERMINATION_INCONSISTENCY"
        severity = "RED"
    elif n_amd >= 2:
        verdict = "NARRATIVE_DRIFT_DETECTED"
        severity = "HIGH"
    elif n_amd == 1:
        verdict = "NARRATIVE_DRIFT_DETECTED"
        severity = "MEDIUM"
    elif n_aff > 0 and n_amd == 0 and n_trm == 0:
        verdict = "AFFIRMED_ACROSS_VENUES"
        severity = None  # no-fire — consistent disclosure
    else:
        verdict = "CONSISTENT"  # all UNRELATED — nothing material in priors
        severity = None

    return {
        "fact_pattern":             fact_pattern,
        "focal_venue":              focal_disclosure.venue,
        "focal_date":               focal_disclosure.date,
        "n_prior_disclosures":      len(prior_disclosures),
        "n_classified":             n_classified,
        "classifications":          findings,
        "classification_counts":    {"AFFIRMED": n_aff, "AMENDED": n_amd,
                                      "TERMINATED": n_trm, "UNRELATED": n_unr},
        "consistency_verdict":      verdict,
        "severity":                 severity,
        "llm_model":                disclosure_classifier.model_name(),
    }


# ── Detector interface (fires?-style for graph dispatch) ─────────────

def evaluate(obligor_name: str, data: dict) -> dict:
    """Detector-shape wrapper around audit_disclosure_chain().

    Data shape:
    {
      "fact_pattern": "NCT05919264 — FOG-001 in desmoid tumors",
      "focal_disclosure": {"venue": "S-1", "date": "2026-05-19",
                            "text": "...", "source_url": "..."},
      "prior_disclosures": [
        {"venue": "ASCO 2025 poster", "date": "2025-06-01", "text": "...", ...},
        {"venue": "CTOS 2025 poster", "date": "2025-11-15", "text": "...", ...},
        {"venue": "ClinicalTrials.gov v12", "date": "2025-08-10", "text": "...", ...},
        ...
      ],
    }
    """
    fact = data.get("fact_pattern")
    focal_d = data.get("focal_disclosure")
    priors_d = data.get("prior_disclosures") or []
    if not fact or not focal_d:
        return {"fires": False, "reason": "INSUFFICIENT_DATA",
                "evidence": {"fact_pattern": fact, "has_focal": bool(focal_d)}}
    focal = Disclosure(**focal_d) if not isinstance(focal_d, Disclosure) else focal_d
    priors = ingest_manual(priors_d) if priors_d and isinstance(priors_d[0], dict) else priors_d
    result = audit_disclosure_chain(fact, focal, priors)
    severity = result.get("severity")
    fires = severity is not None
    return {
        "fires": fires,
        "reason": result.get("consistency_verdict", "UNKNOWN"),
        "severity": severity,
        "evidence": result,
    }


if __name__ == "__main__":
    # Demo: ingest CT.gov history for Parabilis FOG-001
    if len(sys.argv) > 1 and sys.argv[1] == "ctgov-history":
        nct = sys.argv[2] if len(sys.argv) > 2 else "NCT05919264"
        history = ingest_clinicaltrials_gov_history(nct)
        print(f"Found {len(history)} prior CT.gov versions for {nct}")
        for h in history[:5]:
            print(f"  v={h.venue}  date={h.date}  url={h.source_url}")
