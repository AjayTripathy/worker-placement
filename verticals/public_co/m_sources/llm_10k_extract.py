"""Universal 10-K extractor — pulls structured inputs for downstream m-sources.

WHY THIS EXISTS

Several cluster-specific m-sources need per-name curated inputs that don't
auto-populate from EDGAR submission metadata:

  REAL_ESTATE       → named-tenant table with rent% breakdown
  BUSINESS_SERVICES → named-customer concentration with revenue %
  COMMUNICATIONS    → KPI claims (residential customer count, ARPU,
                       aircraft online, etc.) for YoY comparison
  HEALTHCARE_PHARMA → Orange Book applicant_name mapping
  HEALTHCARE        → CMS CCN roster for operator's facilities

This module pulls each ticker's latest 10-K pre-cutoff, slices to the
sections of interest, and asks Claude to extract a structured JSON
payload matching a per-cluster schema.

CACHES

  data/_llm_extracts/{ticker}_{cluster}_{cutoff}.json

Idempotent: re-running won't re-call the LLM if the cache file exists.

USAGE

  from . import llm_10k_extract
  result = llm_10k_extract.extract(
      ticker="HPP",
      cik="0001479094",
      cluster="REAL_ESTATE",
      cutoff_date="2024-05-15",
  )
  # result["tenants"] = [{"name": "...", "rent_pct": 5.2, "cik": null}, ...]
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": [],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": False,
    "kind": "helper",
    "summary": "Universal 10-K structured extractor feeding downstream m-sources; infra, never dispatched.",
}

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Optional

from .. import edgar
from .. import filing_slice

CACHE_DIR = Path(__file__).parent.parent / "data" / "_llm_extracts"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

MODEL = os.environ.get("LLM_EXTRACT_MODEL", "claude-sonnet-4-5")
MAX_INPUT_CHARS = 100_000  # Conservative; 10-Ks can be huge
MAX_TOKENS_OUT = 3000

_KEY_FILE = Path("~/.anthropic_api_key").expanduser()
_SDK_CLIENT = None
if _KEY_FILE.exists():
    try:
        from anthropic import Anthropic
        _key = _KEY_FILE.read_text().strip()
        if _key.startswith("sk-ant-"):
            _SDK_CLIENT = Anthropic(api_key=_key)
    except Exception as e:
        print(f"[llm_10k_extract] SDK init failed: {e}", file=sys.stderr)


# ============================================================
# Per-cluster extraction prompts
# ============================================================

_BLINDING = (
    "BLINDING: You are extracting from a 10-K filed before a historical cutoff. "
    "Do not use any post-cutoff knowledge (subsequent bankruptcies, tenant defaults, "
    "etc.) — extract only what the filing actually says.\n\n"
)

PROMPTS = {
    "REAL_ESTATE": _BLINDING + """Extract the REIT's named-tenant exposure table from this 10-K excerpt.

Look in: Item 1 (Business), Item 7 (MD&A), Schedule III, supplemental
tenant tables, top-tenant rent rolls. The information is usually in a
"Top Tenants" or "Largest Tenants" table showing tenant name, annualized
base rent, and % of total rent.

Return STRICT JSON with this shape:
{
  "tenants": [
    {
      "name": "Tenant legal name (or trade name if more recognizable)",
      "rent_pct": 12.5,
      "annualized_base_rent_usd": 45000000,
      "n_properties": 8,
      "ticker_or_cik_if_public": "TICKER or null"
    },
    ...
  ],
  "total_rent_top_10_pct": 35.2,
  "_note": "Brief note about extraction confidence"
}

If no tenant table is present, return {"tenants": [], "_note": "..."}.
Output ONLY the JSON object, no preamble or markdown.""",

    "BUSINESS_SERVICES": _BLINDING + """Extract the issuer's named-customer concentration from this 10-K excerpt.

Look in: Item 1 (Business — Customers), Item 1A (Risk Factors — Customer
Concentration), Item 7 (MD&A). The information is usually one of:
- A specific named customer disclosed under the 10% SEC rule
- A list of largest customers by revenue %
- Segment-level customer concentration

Return STRICT JSON:
{
  "named_customers": [
    {
      "name": "Customer name (often a US Gov agency, large corporate, or healthcare system)",
      "revenue_pct": 18.0,
      "ticker_or_cik_if_public": "TICKER or null",
      "is_government": true,
      "is_contracting_vehicle": false
    },
    ...
  ],
  "top_5_customer_pct": 35.0,
  "top_1_customer_pct": 18.0,
  "is_revenue_recurring": true,
  "is_project_based": false,
  "_note": "..."
}

If no customer concentration is disclosed, return {"named_customers": [], "_note": "..."}.
Output ONLY the JSON.""",

    "COMMUNICATIONS": _BLINDING + """Extract the operating KPI claims from this 10-K excerpt that would be
verifiable against external data.

Look in: Item 1 (Business — Operating Statistics), Item 7 (MD&A
segment results). For a cable / satellite / wireless / in-flight wifi
operator the KPIs are things like:
  - Residential primary service units (PSUs)
  - Total broadband subscribers
  - Average revenue per user (ARPU)
  - Aircraft online / equipped (for in-flight wifi)
  - Total connected devices
  - Spectrum holdings (MHz-POPs)

Return STRICT JSON:
{
  "kpis": [
    {
      "metric": "Residential broadband subscribers",
      "value_latest": 950000,
      "period_latest": "2023-12-31",
      "value_prior": 1010000,
      "period_prior": "2022-12-31",
      "yoy_change_pct": -5.9
    },
    ...
  ],
  "_note": "..."
}

If no clean KPI table is found, return {"kpis": [], "_note": "..."}.
Output ONLY the JSON.""",

    "TECH_SOFTWARE_SERVICES": _BLINDING + """Extract the SaaS issuer's revenue-quality KPIs.

Look in: Item 1, Item 7 (MD&A). Target metrics:
  - Net Revenue Retention (NRR) / Gross Revenue Retention (GRR)
  - Annual Recurring Revenue (ARR) growth
  - Customer count by segment
  - Top-customer concentration (10% rule disclosure)
  - Bookings/billings

Return STRICT JSON:
{
  "kpis": [
    {"metric": "Net Revenue Retention", "value_latest": 105.0, "period_latest": "2023-12-31",
     "value_prior": 115.0, "period_prior": "2022-12-31"},
    ...
  ],
  "named_customers": [...],
  "_note": "..."
}

Output ONLY the JSON.""",

    "HEALTHCARE_SERVICES": _BLINDING + """Extract the healthcare operator's facility roster and Medicare CCNs.

Look in: Item 1 (Business — Properties), Item 2 (Properties),
supplemental schedules. We want the list of provider facilities with
their CMS Certification Numbers (CCNs) when disclosed, or facility
names + state for later POS-file lookup.

Return STRICT JSON:
{
  "facilities": [
    {
      "name": "Facility name",
      "state": "TX",
      "city": "Austin",
      "ccn": "455123",
      "facility_type": "snf"
    },
    ...
  ],
  "n_total_facilities": 142,
  "_note": "..."
}

Output ONLY the JSON.""",

    "HOSPITAL_CAFR": _BLINDING + """Extract consolidated financial-statement KPIs from a hospital
system's Continuing Disclosure / CAFR / Audited Financial Statements.

Look in: Consolidated Balance Sheet, Consolidated Statement of Operations,
Notes on Cash + Investments, Footnotes on long-term debt, Management Discussion.

For academic medical centers + integrated health systems, these
consolidated statements include investment income + research income +
endowment cash that CMS HCRIS facility-level cost reports omit.

Return STRICT JSON:
{
  "fiscal_year_end": "2024-06-30",
  "total_operating_revenue": 5800000000,
  "total_operating_expense": 5650000000,
  "operating_margin_pct": 2.6,
  "total_net_income_consolidated": 450000000,
  "total_margin_pct": 7.8,
  "cash_and_short_term_investments": 1500000000,
  "long_term_investments_unrestricted": 8200000000,
  "days_cash_on_hand_consolidated": 580,
  "total_long_term_debt": 4200000000,
  "debt_service_coverage_ratio": 4.2,
  "investment_income_pct_of_total_margin": 65,
  "research_grants_revenue": 350000000,
  "_note": "extraction confidence + source page references"
}

Output ONLY the JSON.""",

    "HEALTHCARE_PHARMA": _BLINDING + """Extract pharma-specific KPIs and Orange-Book-relevant info.

Return STRICT JSON:
{
  "marketed_drugs": [
    {"trade_name": "Korlym", "active_ingredient": "mifepristone", "fda_app_no": "NDA202107",
     "orange_book_applicant_name": "Corcept Therapeutics Inc"},
    ...
  ],
  "pipeline_assets": [
    {"asset_code": "CORT118335", "phase": "Phase 3", "indication": "Cushing's syndrome"},
    ...
  ],
  "revenue_concentration_pct": 95.0,
  "_note": "..."
}

Output ONLY the JSON.""",
}


# ============================================================
# Filing fetch helpers
# ============================================================

def _fetch_10k_text(cik: str, cutoff_date: str) -> Optional[tuple[str, str, str]]:
    """Fetch the most recent 10-K filed before cutoff. Returns
    (accession, filing_date, text) or None."""
    try:
        company, filings = edgar.list_filings(cik)
    except Exception as e:
        return None
    candidates = sorted(
        [f for f in filings
         if f.get("form") in ("10-K", "10-K/A")
         and f.get("filing_date", "") <= cutoff_date],
        key=lambda f: f.get("filing_date", ""),
        reverse=True,
    )
    if not candidates:
        return None
    f = candidates[0]
    primary = f.get("primary_document") or f.get("primary_doc")
    if not primary:
        return None
    try:
        text = edgar.fetch_filing_clean(cik, f["accession"], primary)
    except Exception:
        return None
    if not text:
        return None
    return f["accession"], f["filing_date"], text


def _llm_call(system: str, user: str) -> str:
    if _SDK_CLIENT is None:
        raise RuntimeError(
            f"Anthropic API key not present at {_KEY_FILE}. "
            "Create the file with your sk-ant- key (0600 perms)."
        )
    backoffs = [2, 5, 12, 30]
    for attempt, delay in enumerate([0] + backoffs):
        if delay:
            time.sleep(delay)
        try:
            resp = _SDK_CLIENT.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS_OUT,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            return "".join(b.text for b in resp.content
                           if getattr(b, "type", None) == "text").strip()
        except Exception as e:
            msg = str(e)
            transient = any(s in msg.lower() for s in
                            ("overloaded", "rate_limit", "timeout", "529"))
            if transient and attempt < len(backoffs):
                print(f"  [LLM retry after {delay}s: {msg[:80]}]", file=sys.stderr)
                continue
            raise


def _extract_json(text: str) -> Any:
    import re
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if m:
        text = m.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Find first balanced {...}
    i = text.find("{")
    if i >= 0:
        depth = 0
        for j in range(i, len(text)):
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[i:j+1])
                    except json.JSONDecodeError:
                        break
    raise ValueError(f"could not parse JSON from LLM response: {text[:200]!r}")


# ============================================================
# Public API
# ============================================================

def extract(
    ticker: str,
    cik: str,
    cluster: str,
    cutoff_date: str,
    *,
    force: bool = False,
) -> dict[str, Any]:
    """Extract per-cluster structured payload from the issuer's 10-K.

    Cached at data/_llm_extracts/{ticker}_{cluster}_{cutoff_date}.json.
    """
    cache_file = CACHE_DIR / f"{ticker}_{cluster}_{cutoff_date}.json"
    if cache_file.exists() and not force:
        return json.loads(cache_file.read_text())

    if cluster not in PROMPTS:
        return {"error": f"no extraction prompt for cluster {cluster}"}

    fetched = _fetch_10k_text(cik, cutoff_date)
    if fetched is None:
        # Don't cache transient fetch failures
        return {"error": "no 10-K fetched", "ticker": ticker, "cluster": cluster}
    accession, filing_date, raw_text = fetched

    text = filing_slice.strip_html(raw_text)
    text = filing_slice.slice_filing(text, budget_chars=MAX_INPUT_CHARS)

    system = PROMPTS[cluster]
    user = f"Ticker: {ticker}\nCIK: {cik}\nFiling: 10-K accession {accession} filed {filing_date}\nCutoff: {cutoff_date}\n\n=== 10-K excerpt ===\n{text}"

    try:
        raw = _llm_call(system, user)
        payload = _extract_json(raw)
    except Exception as e:
        # Don't cache transient LLM failures
        return {"error": f"LLM call failed: {type(e).__name__}: {e}",
                "ticker": ticker, "cluster": cluster}

    result = {
        "ticker":        ticker,
        "cik":           cik,
        "cluster":       cluster,
        "cutoff_date":   cutoff_date,
        "filing_accession": accession,
        "filing_date":   filing_date,
        "payload":       payload,
    }
    cache_file.write_text(json.dumps(result, indent=2, default=str))
    return result


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", required=True)
    ap.add_argument("--cik", required=True)
    ap.add_argument("--cluster", required=True)
    ap.add_argument("--cutoff", default="2024-05-15")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    print(json.dumps(extract(args.ticker, args.cik, args.cluster, args.cutoff,
                              force=args.force), indent=2, default=str))
