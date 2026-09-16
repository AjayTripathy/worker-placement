"""Dispatch-prompt generator for IPO DD sub-agents.

Given an IPO record (from ipo_pipeline output enriched with proceeds), produces
a self-contained dispatch prompt for a general-purpose sub-agent to do deep
Mode A + Mode B DD.

Used by the orchestrator after pre-flight validation. The prompt is designed to
be hostile-validator: the agent's job is to find what's WRONG with the deal, not
to summarize what the deal says about itself.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Ensure repo root on sys.path for cross-vertical imports
_REPO_ROOT = Path(__file__).parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from knowledge_graph.dispatch import relevant_for_issuer


# Lightweight feature-extraction from raw S-1 prose. Keys MUST match the feature
# names referenced in detector APPLIES_TO blocks (issuer_features /
# must_have_any_feature / anti_features). Otherwise the gates are inert.
#
# When you add a new detector with a new issuer_feature, add the corresponding
# keyword set here — or the dispatch matcher won't have anything to gate on,
# and the detector becomes dead code in any dispatch that doesn't manually pass
# extra_features.
_FEATURE_KEYWORDS = {
    # --- USG / defense customer-base features (used by pentagon_jbook) ---
    "mentions_dod_program":      ["dod", "department of defense", "pentagon"],
    "mentions_darpa":            ["darpa", "advanced research projects agency"],
    "mentions_navy":             ["u.s. navy", " navy ", "department of the navy"],
    "mentions_army":             ["u.s. army", " army ", "department of the army"],
    "mentions_air_force":        ["u.s. air force", "air force", "usaf"],
    "mentions_space_force":      ["u.s. space force", "space force", "ussf"],
    "mentions_nro":              ["national reconnaissance office", "nro "],
    "primary_contractor_to_dod_prime": ["prime contractor", "boeing", "lockheed martin",
                                         "raytheon", "northrop grumman", "general dynamics",
                                         "l3harris"],
    # --- USG / DOE customer-base features (used by doe_budget) ---
    "mentions_doe_program":      ["department of energy", "doe office"],
    "mentions_office_of_science": ["office of science"],
    "mentions_ascr":             ["ascr", "advanced scientific computing research"],
    "mentions_bes":              ["basic energy sciences", " bes "],
    "mentions_fes":              ["fusion energy sciences"],
    "mentions_hep":              ["high energy physics"],
    "mentions_nnsa":             ["nnsa", "national nuclear security administration"],
    "mentions_arpa_e":           ["arpa-e", "arpa e "],
    "mentions_nqi":              ["national quantum initiative", "nqi center", "nqi research center"],
    "mentions_quantum_initiative": ["national quantum initiative", "quantum initiative"],
    "mentions_q_next":           ["q-next", "qnext"],
    "mentions_qsa":              ["quantum systems accelerator"],
    "mentions_c2qa":             ["c2qa", "co-design center for quantum advantage"],
    "mentions_qsc":              ["quantum science center"],
    "mentions_sqms":             ["sqms", "superconducting quantum materials"],
    "mentions_national_lab":     ["national laboratory", "national lab", "argonne",
                                   "oak ridge", "fermilab", "brookhaven", "los alamos",
                                   "lawrence berkeley", "lawrence livermore", "sandia"],
    "government_customer_concentration_above_5pct": [
        # Proxy keywords; precise numeric extraction is the agent's job
        "government customer", "u.s. government accounted for",
        "federal agency accounted for",
    ],
    # --- Capital-structure features (used by various IPO detectors) ---
    "upc_tra_structure": ["up-c structure", "tax receivable agreement",
                          "tra parties", "common units of"],
    "egc_status": ["emerging growth company", "jobs act", "smaller reporting company"],
    "pe_sponsor_control": [
        "controlled company", "private equity", "blackstone", "kkr", "carlyle",
        "tpg ", "apollo global", "silver lake", "vista equity", "thoma bravo",
        "hellman & friedman", "advent international", "bain capital",
        "warburg pincus", "ge equity", "general atlantic",
    ],
    "common_control_merger_disclosed": [
        "common control", "common-control merger", "common control transaction",
        "transaction between entities under common control",
    ],
    "follow_on_offering": [
        "follow-on offering", "follow on offering", "secondary offering",
        "lockup expiration", "lock-up expiration",
    ],
    # --- Biotech / clinical features (used by clinical detectors) ---
    "clinical_trial_program": [
        "clinicaltrials.gov", "nct0", "nct1", "nct2", "nct3", "nct4", "nct5",
        "nct6", "nct7", "nct8", "nct9", "phase 1", "phase 2", "phase 3",
        "phase i ", "phase ii ", "phase iii", "investigational new drug",
        " ind ", "ind filing", "clinical trial",
    ],
    "sponsor_developer_biotech": [
        "drug candidate", "lead candidate", "product candidate",
        "investigational compound", "wholly-owned program",
        "preclinical program",
    ],
    "diagnostics_or_lab_business": [
        "clinical laboratory", "diagnostic test", "molecular diagnostic",
        "next-generation sequencing", "next generation sequencing", " ngs ",
        "in vitro diagnostic", "ivd ", "lab-developed test", "ldt ",
    ],
    "molecular_profiling_business": [
        "molecular profiling", "circulating tumor dna", "ctdna",
        "comprehensive genomic profiling", "tumor profiling",
        "biomarker analysis", "germline sequencing",
    ],
    "patient_referral_business": [
        "patient navigation", "treatment referral", "actionable treatment",
        "treatment leads", "actionable lead",
        "patient eligibility", "referral pathway",
    ],
    # --- Geography / archetype features (used by chinese_smallcap detector) ---
    "cayman_or_bvi_holdco": [
        "cayman islands", "incorporated in the cayman islands",
        "british virgin islands", " bvi ",
    ],
    "asia_operating_jurisdiction": [
        "hong kong", "singapore", "malaysia", "shanghai", "shenzhen",
        "beijing", "taiwan", "tokyo", "south korea", " seoul ",
        "guangzhou", "kuala lumpur",
    ],
}


def infer_features_from_text(text: str) -> set[str]:
    """Keyword-scan a body of text (S-1 prose, etc.) for issuer features.

    Returns a set of feature names matching the APPLIES_TO vocabulary used
    by detectors throughout the knowledge graph. Case-insensitive substring
    match — fast and lossy. The agent can populate or correct features at
    runtime; this function exists so the orchestrator can route a graph-driven
    dispatch even when an S-1 is available but no LLM extraction has been run.
    """
    if not text:
        return set()
    t = text.lower()
    feats = set()
    for feat, kws in _FEATURE_KEYWORDS.items():
        if any(k in t for k in kws):
            feats.add(feat)
    return feats


def slugify(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")[:40]


def build_dispatch_prompt(ipo: dict, out_dir: str = "/Users/ajay/Desktop/ipo_eval_2026_05_29",
                          extra_features: set | None = None) -> tuple[str, str]:
    """Produce (slug, prompt_text) for an IPO record.

    Detectors + M-sources are pulled from the knowledge graph via
    `relevant_for_issuer(issuer)` — no hardcoded list. The orchestrator can
    pass `extra_features` (set of feature strings) to extend what the issuer
    profile declares (e.g., from a quick S-1 prose scan or LLM extraction).
    """
    name = (ipo.get("metadata", {}).get("name") or ipo.get("company_name", "?")).strip()
    cik = ipo.get("cik", "?").lstrip("0") or "0"
    acc = (ipo.get("proceeds", {}) or {}).get("accession") or ipo.get("_accession", "").split(":")[0]
    proceeds = (ipo.get("proceeds", {}) or {}).get("proposed_proceeds_usd", 0)
    sic_desc = ipo.get("metadata", {}).get("sicDescription", "?")
    sic_code = ipo.get("metadata", {}).get("sic") or ""
    tickers = ", ".join(ipo.get("metadata", {}).get("tickers", [])) or "—"
    exchanges = ", ".join(filter(None, ipo.get("metadata", {}).get("exchanges", []))) or "—"
    file_date = ipo.get("file_date", "?")
    file_form = (ipo.get("forms", [""]) or [""])[0]

    slug = slugify(name)
    acc_nodash = (acc or "").replace("-", "")
    base_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik) if cik.isdigit() else cik}/{acc_nodash}/" if acc_nodash else "(no accession)"
    out_path = f"{out_dir}/{slug}"

    # Build the issuer profile + query the graph for relevant detectors / M-sources
    features = set(extra_features or set())
    # Always-applicable conservative defaults for IPO DD
    features.add("egc_status")  # most fresh IPOs claim EGC; agent verifies
    features.add("follow_on_offering")  # generic; lockup detector is cheap to evaluate
    issuer_profile = {
        "name": name,
        "cik": cik,
        "sic": str(sic_code),
        "asset_classes": {"corporate_ipo_dd"},
        "features": features,
    }
    applicable = relevant_for_issuer(issuer_profile)

    # Build the inline catalog block
    detector_lines = []
    msource_lines = []
    for it in applicable:
        line = f"  - **{it['name']}** ({it['vertical']}): {it['summary']}"
        if it.get("verification_question"):
            line += f"\n      _R/M gap_: {it['verification_question']}"
        if it["kind"] == "m_source":
            msource_lines.append(line)
        else:
            detector_lines.append(line)
    detectors_block = "\n".join(detector_lines) if detector_lines else "  (no detectors matched)"
    msources_block = "\n".join(msource_lines) if msource_lines else "  (no external M-sources matched)"

    prompt = f"""# IPO Due Diligence: {name}

## Filing metadata (do not assume — verify each)

- **Company name:** {name}
- **CIK:** {cik}
- **Filing form:** {file_form}  ·  Filed: {file_date}
- **Accession:** {acc}
- **Filing folder (live EDGAR):** {base_url}
- **SIC:** {sic_code} ({sic_desc})
- **Tickers:** {tickers}  ·  Exchanges: {exchanges}
- **Proposed maximum aggregate offering price (PMAOP):** ${proceeds/1e6:,.1f}M

## Your role

You are a hostile institutional buyside DD validator. Your job is not to summarize what the company says about itself. Your job is to find what is WRONG with the deal — material omissions, factual misrepresentations, related-party value transfers, accounting structures that disadvantage the public-float, and comparison-class valuation problems.

The Signal OS framework treats this as a "lying detector" not a fundamental analyst. Re-detecting honestly-disclosed bad news isn't alpha — the contribution is EXCLUSION of liars.

## Mode A — claim verification (must do)

Pull 5-10 specific factual claims from the S-1 prospectus summary, MD&A, and risk-factors. For each claim:
1. State the claim verbatim with section/page citation.
2. Identify the independent public source that can verify or refute it (SEC EDGAR submissions, ClinicalTrials.gov v2, Form D, USPTO, FDA, court records, competitor 10-K, etc.).
3. Verify with the source. Record `verified | refuted | unverifiable`.
4. If refuted: quote both the claim and the contradicting evidence side-by-side.

## Mode B — implied verification (must do)

For this asset class, what claims SHOULD a real institutional buyer want to see verified that are NOT addressed in the S-1? Identify 3-5 such gaps. Examples:
- For biotech: enrolling competitor trials at the same indication
- For Up-C structures: TRA termination payment in change-of-control
- For PE-backed IPOs: pre-IPO dividend recap
- For dual-class: voting concentration post-IPO and sunset provision (or lack)
- For RPT-heavy: aggregate lease/service payments to insider entities

The Signal OS knowledge graph identified the following detectors as relevant for this issuer profile (SIC {sic_code}, features={sorted(features)}):

{detectors_block}

External M-sources (cross-vertical verifiers) the graph flagged as applicable:

{msources_block}

Run each detector / M-source against this filing. Note which fire and with what severity (RED / HIGH / MEDIUM / LOW / not-applicable). Don't manufacture fires — say not-applicable when the structure doesn't exist. For M-sources, the R/M gap framing above tells you what the verification question is: compare the issuer's claim (R) against the authoritative external record (M).

## Output

Save to `{out_path}/`:

1. `{out_path}/verification.json` — structured Mode A + Mode B findings:
   ```
   {{
     "company_name": "...",
     "cik": "...",
     "verdict": "BUY | WAIT | DECLINE",
     "confidence": "LOW | MEDIUM | HIGH",
     "top_3_red_flags": [{{"flag": "...", "severity": "...", "source": "..."}}],
     "mode_a_findings": [{{"claim": "...", "source": "...", "result": "verified|refuted|unverifiable", "evidence": "..."}}],
     "mode_b_findings": [{{"gap": "...", "what_should_be_disclosed": "...", "why_it_matters": "..."}}],
     "detector_fires": {{"dual_class_voting_concentration": {{"fires": true, "severity": "HIGH", "evidence": "..."}}, ...}},
     "comparable_companies": ["...", "..."],
     "estimated_fair_value_vs_ipo_ask": "comp-implied $X vs IPO ask $Y = Z% of ask",
     "lockup_expiration_dates": ["..."],
     "key_risks_buried_in_risk_factors": ["..."],
     "time_spent_minutes": N
   }}
   ```

2. `{out_path}/dd_report.md` — analyst-facing report. Required sections in this order:
   - **Header**: issuer, ticker, filing accession, lead underwriters, indication/sector, report date
   - **Methodology note** (one paragraph): explain the R → f(M) → Finding structure used below
   - **Recommendation**: BUY/WAIT/DECLINE with the pricing-anchored subscribe condition (e.g., "subscribe at or below $X post-money; pass at any premium")
   - **Company snapshot**: 1 paragraph + pipeline/cash status
   - **Material Findings**: EVERY finding presented in the R/f(M)/Finding format:
     * **R (Claim):** the issuer's verbatim or near-verbatim claim, with explicit filing-section citation
     * **Source:** S-1 page / section / line citation
     * **f (Method):** the independent verification test you ran (which detector, which external query, which figure-read)
     * **M (Authority):** the specific external source URL/DB you measured against (ClinicalTrials.gov NCT URL, FDA Drugs@FDA URL, Pentagon J-Book PE number, SEC EDGAR submissions JSON, etc.)
     * **Finding:** VERIFIED / REFUTED / UNVERIFIABLE / CONSISTENT / INCONSISTENT / AFFIRMED ACROSS VENUES, with the actual evidence — not just a verdict
   - **Clinical/Operational Data Summary**: tabulated key metrics with explicit denominator transparency
   - **Competitive Landscape**: fuller-than-S-1 table with sources for each competitor entry
   - **Valuation**: comp-anchored fair value band with named comps + their EVs + sources
   - **Catalysts to Watch**: time-ordered table with what-to-watch-for column
   - **Conclusion**: anchored recommendation + reconsider triggers + the strongest single observation about disclosure quality

The R/f(M)/Finding structure is mandatory for every material finding. It forces every finding to show its work. If a reader disagrees with a conclusion, they can re-run the exact same check against the exact same source. Analysts trust reports that cite their work; they discount reports that hand-wave.

Avoid in the report: detector internal names ("dual_class_voting_concentration fired RED"), Signal OS framework jargon ("APPLIES_TO graph dispatched"), version-counter language ("v6 mitigator extraction"). The reader is an institutional analyst, not a Signal OS developer.

## Discipline

- **Entity resolution first:** the deck's subject is rarely the right query subject. For PE-backed IPOs, find the SPONSOR. For RPT-heavy, find the COUNTERPARTY. For comps, find the trading multiples.
- **No fabrication:** if you can't verify a claim, write "unverifiable" — don't infer.
- **Cite everything:** every Mode-A finding needs an explicit URL or filing section.
- **Time-box: 45-60 minutes.**

### Mitigating-factor extraction (deterministic detector inputs)

Several detectors now consume **structured mitigating-factor booleans** to deterministically tier severity. When you extract data for a detector that has these fields, populate them honestly — defaults are conservative (worst-case) when absent.

- `dual_class_voting_concentration`: `sunset_clause_years` (int|null), `sunset_trigger` (`"founder_death"|"below_threshold"|"fixed_date"|null`), `coordinated_voting_agreement_exists` (bool), `independent_chair` (bool)
- `related_party_transaction_velocity`: `audit_committee_rpt_approval_policy_pre_ipo` (bool), `arms_length_pricing_benchmarks_provided` (bool), `rpt_disclosed_in_aggregate_dollar_terms` (bool), `rpt_majority_described_as_market_terms` (bool). 3+ true → one-tier downgrade; 4 true → two-tier downgrade. SpaceX case (all false) stays RED.
- `common_control_merger_accounting`: per absorbed entity — `separate_financial_statements_provided` (bool — full mitigation), `pro_forma_combined_disclosure_provided` (bool), `carve_out_financials_provided` (bool), `pre_combination_audited_years_provided` (int). 2+ partial mitigations → one-tier downgrade.
- `lockup_expiration_calendar`: `insider_public_hold_commitments_pct_of_insider_shares` (float), `insider_hold_commitment_additional_years` (int). ≥50% of insider shares + ≥1 yr additional hold → one-tier downgrade.

These detectors are pure logic — no LLM sentiment classification. The agent's job is to find the booleans in the S-1 (governance section for sunset/policy, RPT section for benchmarks, M&A footnotes for pro-forma/carve-out, lockup section for hold commitments) and populate the data shape. The detector deterministically tiers severity from there.

### Figure-level reading (universal — applies to every DD)

S-1 / F-1 / DRS filings routinely encode quantitative claims **only in figures** — waterfall plots, swim plots, Kaplan-Meier curves, market-share donuts, mineral-resource maps, customer-mix charts, subscriber-growth bars, qubit-roadmap diagrams. The chart is the disclosure; the underlying numbers live in pixel-space and are absent from any extractable table.

For every quantitative claim you verify in Mode A:

1. Locate the supporting figure (S-1 prose typically references "Figure X" or "Figure X.Y").
2. Check whether the filing contains a data table with the same numerical content as the figure. If yes, the table is your evidence — done.
3. If no equivalent table exists — i.e., the chart is the *only* disclosure of the numbers — **fetch the image and read it directly**. Use:

   ```python
   from verticals.buyside_dd.edgar_figure_extractor import extract_figure
   result = extract_figure(cik=CIK, accession=ACC, s1_html_path=S1_PATH, figure_number=N)
   # result["local_path"] is a downsized PNG ready for Read
   ```

   Then use `Read` on `result["local_path"]` — Claude's multimodal capability will surface the chart contents as image data. Count bars, read axis values, identify markers, enumerate per-element data.

4. Compare the figure's pixel-level data against the prose claim. A waterfall plot showing all bars "On Treatment" (arrow markers) directly answers whether dropouts exist in the response-evaluable cohort. A mineral-resource map's color-coded zones directly answer reserve concentration. A subscriber pie-chart's slice fractions directly answer customer concentration.

The chart is regulated disclosure. Text-grep alone is insufficient when material claims live in figures without supporting tables.

Begin now. Save outputs to `{out_path}/` (mkdir as needed).
"""
    return slug, prompt


if __name__ == "__main__":
    import json, sys
    if len(sys.argv) > 1:
        rec = json.load(open(sys.argv[1]))
    else:
        rec = json.load(sys.stdin)
    slug, prompt = build_dispatch_prompt(rec)
    print(f"=== SLUG: {slug} ===")
    print(prompt)
