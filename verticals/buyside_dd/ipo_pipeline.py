"""IPO pipeline fetcher for Signal OS DD evaluation.

Pulls recent S-1 / S-1/A / F-1 / F-1/A / DRS / DRS/A filings from SEC EDGAR,
filters out SPACs / blank checks / ETFs / shells / micro-cap re-listings,
classifies remaining operating companies by SIC sector, maps each to suggested
Signal OS DD detector agents, and outputs a structured queue ready for DD
dispatch.

Usage:
  python3 -m verticals.buyside_dd.ipo_pipeline [--days N] [--out PATH]

Default: last 30 days, output to /Users/ajay/Desktop/ipo_pipeline_queue.json.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from datetime import date, timedelta
from pathlib import Path

EDGAR_FULLTEXT = "https://efts.sec.gov/LATEST/search-index"
EDGAR_SUBMISSIONS = "https://data.sec.gov/submissions/CIK{:010d}.json"

# Forms that signal a forthcoming IPO
IPO_FORMS = ["S-1", "S-1/A", "F-1", "F-1/A", "DRS", "DRS/A"]

# Patterns indicating a SPAC / blank-check entity (skip)
SPAC_PATTERNS = re.compile(
    r"\b(ACQUISITION CORP|ACQUISITION COMPANY|HOLDINGS CORP|ACQUISITION HOLDINGS|"
    r"BLANK CHECK|CAPITAL CORP III?|CAPITAL CORP IV|CAPITAL CORP V|"
    r"BLUE WATER|HARBOR CORP|SENSEI HARBOR|CIRCLE CAPITAL CORP|"
    r"INVESTMENT PARTNERS|SPECIAL PURPOSE)\b",
    re.IGNORECASE,
)

# Patterns indicating ETF / fund (skip)
FUND_PATTERNS = re.compile(
    r"\b(ETF|TRUST|FUND|GRAYSCALE|ISHARES|VANECK|WISDOMTREE|"
    r"BITWISE|VALKYRIE|STAKING)\b",
    re.IGNORECASE,
)

# Patterns indicating tiny shell / re-listings or non-IPO filings (heuristic, skip)
SHELL_PATTERNS = re.compile(
    r"\b(SHELL|SUBSIDIARY TRUST|MEDALLION|EALIXIR|MICROCAP)\b",
    re.IGNORECASE,
)

# SIC code → Signal OS DD recommended detector agents
SIC_TO_DETECTORS = {
    # Biotech / pharma
    "2836": ["people_entities", "clinical_trial_referral_quality",
             "fda_approval_path_verification", "competitive_pricing"],
    "8731": ["people_entities", "clinical_trial_referral_quality"],
    # Medical devices / diagnostics
    "3841": ["people_entities", "regulatory_business_operations",
             "clinical_trial_referral_quality", "competitive_pricing"],
    "3845": ["people_entities", "regulatory_business_operations",
             "clinical_trial_referral_quality", "competitive_pricing"],
    # Aerospace / defense
    "3812": ["people_entities", "contract_pipeline_verification",
             "customer_concentration_check", "launch_cadence_verification",
             "competitive_landscape"],
    "3721": ["people_entities", "contract_pipeline_verification",
             "competitive_landscape"],
    # Software / IT
    "7370": ["people_entities", "regulatory_business_operations",
             "competitive_pricing", "customer_concentration_check"],
    "7372": ["people_entities", "regulatory_business_operations",
             "competitive_pricing", "customer_concentration_check"],
    "7371": ["people_entities", "regulatory_business_operations",
             "competitive_pricing", "customer_concentration_check"],
    # Real estate / property
    "6798": ["people_entities", "regulatory_business_operations",
             "competitive_pricing"],
    "6500": ["people_entities", "regulatory_business_operations"],
    # Utilities / energy
    "4911": ["people_entities", "regulatory_business_operations",
             "rate_regulation_check", "wildfire_liability_check"],
    "4931": ["people_entities", "regulatory_business_operations"],
    # Banks / finance
    "6020": ["people_entities", "regulatory_business_operations",
             "credit_quality_check"],
    "6770": ["people_entities", "regulatory_business_operations"],
    # Default for unknown / cross-cutting
    "_default": ["people_entities", "regulatory_business_operations",
                 "competitive_landscape"],
}


# Watch-list of known-anticipated upcoming IPOs by CIK — directly polled via
# submissions endpoint to catch filings the EDGAR full-text search misses.
# (Discovered when SpaceX's 2026-05-20 S-1 wasn't indexed by full-text search.)
WATCH_CIKS = {
    "1181412": "Space Exploration Technologies Corp (SpaceX)",
    # Add more known-imminent-IPO CIKs here as discovered
}


def fetch_filings(days_back: int = 30, forms: list[str] = None,
                  max_pages: int = 20) -> list[dict]:
    """Query SEC EDGAR full-text search for IPO-class filings, PAGINATED.

    SEC EDGAR full-text search returns max ~100 hits per page. Walks pages
    via `from` parameter until exhaustion or max_pages reached.
    """
    if forms is None:
        forms = IPO_FORMS
    end_dt = date.today()
    start_dt = end_dt - timedelta(days=days_back)
    forms_param = ",".join(forms)
    all_hits = []
    seen_acc = set()
    for page in range(max_pages):
        params = {
            "q": "",
            "forms": forms_param,
            "dateRange": "custom",
            "startdt": start_dt.isoformat(),
            "enddt": end_dt.isoformat(),
            "from": str(page * 100),
        }
        url = f"{EDGAR_FULLTEXT}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"User-Agent": "SignalOS/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
        except Exception as e:
            print(f"  Page {page} fetch error: {e}", file=sys.stderr)
            break
        hits = data.get("hits", {}).get("hits", [])
        if not hits:
            break
        new_count = 0
        for h in hits:
            acc = h.get("_id")
            if acc and acc not in seen_acc:
                seen_acc.add(acc)
                all_hits.append(h)
                new_count += 1
        if new_count == 0:
            break  # No new hits = end of pagination
    return all_hits


def fetch_watch_list_filings(days_back: int = 30) -> list[dict]:
    """Poll the WATCH_CIKS directly via submissions endpoint to catch
    filings missed by EDGAR full-text search (e.g., SpaceX's S-1).

    Returns hits in the same shape as full-text search.
    """
    cutoff = (date.today() - timedelta(days=days_back)).isoformat()
    out = []
    for cik, name in WATCH_CIKS.items():
        try:
            cik_int = int(cik)
            url = EDGAR_SUBMISSIONS.format(cik_int)
            req = urllib.request.Request(url, headers={"User-Agent": "SignalOS/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                d = json.loads(resp.read())
            recent = d.get("filings", {}).get("recent", {})
            forms_list = recent.get("form", [])
            dates_list = recent.get("filingDate", [])
            accs = recent.get("accessionNumber", [])
            for i, form in enumerate(forms_list):
                if form not in IPO_FORMS:
                    continue
                filing_date = dates_list[i] if i < len(dates_list) else ""
                if filing_date < cutoff:
                    continue
                acc = accs[i] if i < len(accs) else ""
                # Shape as full-text-search hit
                out.append({
                    "_id": acc,
                    "_source": {
                        "ciks": [cik],
                        "display_names": [f"{d.get('name','?')}  (CIK {cik})"],
                        "file_date": filing_date,
                        "forms": [form],
                        "_via_watch_list": True,
                    },
                })
        except Exception as e:
            print(f"  Watch-list fetch error for CIK {cik}: {e}", file=sys.stderr)
    return out


def fetch_company_metadata(cik: str) -> dict:
    """Pull company metadata (SIC, tickers, exchanges, primary-vs-followon).

    is_primary_ipo: True if no prior 10-K/10-Q in submission history; False if
    company is already public and the S-1 is a follow-on offering (e.g., Firefly
    2026-05-26 S-1 is a follow-on to their Aug 2025 IPO).
    """
    try:
        cik_int = int(cik.lstrip("0") or "0")
        if cik_int == 0:
            return {}
        url = EDGAR_SUBMISSIONS.format(cik_int)
        req = urllib.request.Request(url, headers={"User-Agent": "SignalOS/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            d = json.loads(resp.read())
        # Primary-IPO vs follow-on classification
        recent = d.get("filings", {}).get("recent", {})
        forms_list = recent.get("form", [])
        public_filings = {"10-K", "10-Q", "10-K/A", "10-Q/A", "8-K", "20-F", "40-F", "6-K"}
        prior_public_count = sum(1 for f in forms_list if f in public_filings)
        is_primary_ipo = prior_public_count == 0
        return {
            "name": d.get("name"),
            "sic": d.get("sic"),
            "sicDescription": d.get("sicDescription"),
            "tickers": d.get("tickers", []),
            "exchanges": d.get("exchanges", []),
            "is_primary_ipo": is_primary_ipo,
            "prior_public_filing_count": prior_public_count,
            "ipo_classification": "PRIMARY_IPO" if is_primary_ipo else f"FOLLOW_ON ({prior_public_count} prior 10-K/Q/8-K)",
        }
    except Exception as e:
        return {"_error": str(e)}


def classify_for_signalos(meta: dict) -> dict:
    """Map a company's SIC to Signal OS DD detector recommendations."""
    sic = (meta.get("sic") or "").strip()
    sic_desc = meta.get("sicDescription") or ""
    detectors = SIC_TO_DETECTORS.get(sic, SIC_TO_DETECTORS["_default"])
    return {
        "sic": sic,
        "sic_description": sic_desc,
        "suggested_signalos_detectors": detectors,
    }


def is_spac(name: str) -> bool:
    return bool(SPAC_PATTERNS.search(name or ""))


def is_fund(name: str) -> bool:
    return bool(FUND_PATTERNS.search(name or ""))


def is_shell(name: str) -> bool:
    return bool(SHELL_PATTERNS.search(name or ""))


def filter_and_dedupe(filings: list[dict]) -> tuple[list[dict], dict]:
    """Filter out SPACs, ETFs, shells. Dedupe by CIK keeping most recent filing.

    Returns (operating_companies, skipped_counts)
    """
    by_cik: dict[str, dict] = {}
    skipped = {"spac": 0, "fund": 0, "shell": 0, "no_cik": 0}
    for h in filings:
        src = h.get("_source", {})
        names = src.get("display_names") or []
        if not names:
            continue
        name = names[0]
        ciks = src.get("ciks") or []
        if not ciks:
            skipped["no_cik"] += 1
            continue
        cik = ciks[0]
        if is_spac(name):
            skipped["spac"] += 1
            continue
        if is_fund(name):
            skipped["fund"] += 1
            continue
        if is_shell(name):
            skipped["shell"] += 1
            continue
        # Keep most recent filing per CIK
        existing = by_cik.get(cik)
        filed = src.get("file_date", "")
        if existing is None or filed > existing.get("file_date", ""):
            by_cik[cik] = {
                "cik": cik,
                "company_name": name,
                "file_date": filed,
                "forms": src.get("forms", []),
                "_accession": h.get("_id"),
            }
    return list(by_cik.values()), skipped


def build_queue(days_back: int = 30) -> dict:
    """Build the Signal OS IPO DD queue.

    Combines EDGAR full-text search (paginated) + watch-list polling
    to catch filings the search index misses.

    Returns dict with:
      - generated_at, days_back
      - skipped (SPAC/fund/shell counts)
      - companies (ordered by file_date desc, enriched with metadata + suggested detectors)
    """
    print(f"Fetching SEC EDGAR S-1/F-1/DRS filings from last {days_back} days...", file=sys.stderr)
    filings = fetch_filings(days_back=days_back)
    print(f"  Full-text search: {len(filings)} raw filings", file=sys.stderr)
    watch_hits = fetch_watch_list_filings(days_back=days_back)
    print(f"  Watch-list direct poll: {len(watch_hits)} additional filings", file=sys.stderr)
    # Dedupe by accession id
    seen = {h.get("_id") for h in filings}
    for wh in watch_hits:
        if wh.get("_id") not in seen:
            filings.append(wh)
            seen.add(wh.get("_id"))
    print(f"  Combined unique: {len(filings)} filings", file=sys.stderr)

    operating, skipped = filter_and_dedupe(filings)
    print(f"  Operating companies: {len(operating)} (skipped: {skipped})", file=sys.stderr)

    # Enrich top N with SIC + suggested detectors
    operating.sort(key=lambda x: x["file_date"], reverse=True)
    enriched = []
    for i, comp in enumerate(operating):
        print(f"  Enriching {i+1}/{len(operating)}: {comp['company_name'][:60]}", file=sys.stderr)
        meta = fetch_company_metadata(comp["cik"])
        cls = classify_for_signalos(meta)
        enriched.append({
            **comp,
            "metadata": meta,
            "signalos_classification": cls,
        })
        # Rate-limit gently
        if i % 10 == 9:
            import time; time.sleep(0.5)

    return {
        "generated_at": date.today().isoformat(),
        "days_back": days_back,
        "raw_filings_count": len(filings),
        "operating_company_count": len(enriched),
        "skipped": skipped,
        "companies": enriched,
    }


def summarize_queue(queue: dict) -> str:
    """Markdown summary of the IPO queue, grouped by sector."""
    lines = ["# Signal OS IPO Pipeline Queue", ""]
    lines.append(f"**Generated**: {queue['generated_at']}  ·  **Window**: last {queue['days_back']} days")
    lines.append(f"**Raw filings**: {queue['raw_filings_count']}  ·  **Operating companies after filter**: {queue['operating_company_count']}")
    lines.append(f"**Filtered out**: {queue['skipped']}")
    lines.append("")
    lines.append("## Operating companies, by sector")
    lines.append("")
    by_sic = {}
    for c in queue["companies"]:
        sic = c["signalos_classification"]["sic"] or "unknown"
        sic_desc = c["signalos_classification"]["sic_description"] or "?"
        key = f"{sic} - {sic_desc}"
        by_sic.setdefault(key, []).append(c)
    for sector, comps in sorted(by_sic.items(), key=lambda x: -len(x[1])):
        lines.append(f"### {sector} ({len(comps)} companies)")
        lines.append("")
        lines.append("| Filed | CIK | Company | Form | Tickers | Suggested SignalOS DD |")
        lines.append("|---|---|---|---|---|---|")
        for c in comps:
            tickers = ", ".join(c["metadata"].get("tickers", [])) or "—"
            form = c["forms"][0] if c["forms"] else "?"
            dets = ", ".join(c["signalos_classification"]["suggested_signalos_detectors"][:3])
            lines.append(f"| {c['file_date']} | {c['cik']} | {c['company_name'][:50]} | {form} | {tickers} | {dets} |")
        lines.append("")
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--days", type=int, default=30)
    p.add_argument("--out", default="/Users/ajay/Desktop/ipo_pipeline_queue.json")
    p.add_argument("--md", default="/Users/ajay/Desktop/ipo_pipeline_queue.md")
    args = p.parse_args()

    queue = build_queue(days_back=args.days)
    Path(args.out).write_text(json.dumps(queue, indent=2, default=str))
    Path(args.md).write_text(summarize_queue(queue))
    print(f"\nWrote {args.out}", file=sys.stderr)
    print(f"Wrote {args.md}", file=sys.stderr)
    print(f"\nTop operating companies in queue:", file=sys.stderr)
    for c in queue["companies"][:15]:
        print(f"  {c['file_date']} | CIK {c['cik']} | {c['company_name'][:60]} | SIC {c['signalos_classification']['sic']} ({c['signalos_classification']['sic_description'][:30]})", file=sys.stderr)


if __name__ == "__main__":
    main()
