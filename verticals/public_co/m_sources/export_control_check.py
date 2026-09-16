"""US export-control sanctions / denied-parties / Entity List checker.

WHY THIS EXISTS

One BIS Entity List or Treasury SDN designation can cliff a company's
international revenue. Huawei (2019), SMIC (2020), and YMTC (2022) each
saw US-supplier revenue evaporate within weeks of designation. For
US-listed issuers with named Chinese / Russian / Iranian customers,
this is a non-negligible catastrophe vector — especially semis,
industrial machinery, and aerospace exporters.

DATA SOURCE

The Trade.gov Consolidated Screening List (CSL) bundles BIS Entity
List, Treasury OFAC SDN, State DDTC AECA debarred, and a handful of
others into one queryable JSON API. Free, well-documented.

  https://api.trade.gov/static/consolidated_screening_list/consolidated.csv
  Or the search API: https://api.trade.gov/v1/consolidated_screening_list/search

We use the static CSV (cached locally) to avoid auth overhead and
keep this offline-friendly during backtests.

OUTPUT

  Two query modes:

  1. query_designation(name) — is the company itself on a list?
     Returns: signal = DESIGNATED | CLEAN | UNVERIFIABLE
              Plus list of matching entries.

  2. query_customer_exposure(named_customers) — given a list of customer
     names extracted from the issuer's 10-K Item 1, return how many are
     designated.
     Returns: signal = CLEAN | EXPOSED | SEVERE_EXPOSURE | UNVERIFIABLE
              Plus list of designated customers.
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": ["36", "35", "372"],
    "issuer_features": ["export_control_exposure"],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": False,
    "kind": "detector",
    "summary": "BIS Entity List / Treasury SDN check on named foreign customers; designation is a revenue-cliff vector.",
}

import csv
from pathlib import Path
from typing import Any, Optional

import httpx

HEADERS = {"User-Agent": "Signal OS Research backtest@signalos.local"}

CACHE_DIR = Path(__file__).parent.parent / "data" / "_export_control"
CSL_CACHE = CACHE_DIR / "consolidated.csv"
OFAC_CACHE = CACHE_DIR / "ofac_sdn.csv"

# Trade.gov CSL bundles BIS Entity List + OFAC + DDTC. Less reliable mid-2026
# (server truncates body); included as best-effort.
CSL_URLS = [
    "https://api.trade.gov/static/consolidated_screening_list/consolidated.csv",
    "https://data.trade.gov/downloadable_consolidated_screening_list/v1/consolidated.csv",
]
# OFAC SDN — Treasury direct. Reliable, smaller (~5 MB).
OFAC_SDN_URL = "https://sanctionslistservice.ofac.treas.gov/api/publicationpreview/exports/sdn.csv"

# OFAC SDN.csv columns (no header row in the source; positional):
_OFAC_COLS = [
    "ent_num", "sdn_name", "sdn_type", "program", "title",
    "call_sign", "vess_type", "tonnage", "grt", "vess_flag",
    "vess_owner", "remarks",
]

_DESIGNATION_SEVERITY = {
    "CLEAN":            "PASS",
    "DESIGNATED":       "RED_FLAG_NEGATIVE",
    "EXPOSED":          "MODERATE_UNDERDELIVERY",
    "SEVERE_EXPOSURE":  "SEVERE_UNDERDELIVERY",
    "UNVERIFIABLE":     "UNVERIFIABLE",
}


def _download_file(url: str, dest: Path, min_bytes: int) -> Optional[str]:
    """Stream download to `dest`. Returns None on success, error str on failure."""
    try:
        with httpx.Client(
            headers=HEADERS,
            timeout=httpx.Timeout(connect=10, read=180, write=30, pool=10),
            follow_redirects=True,
            http2=False,
        ) as c:
            with c.stream("GET", url) as r:
                if r.status_code != 200:
                    return f"status_{r.status_code}"
                chunks = []
                for chunk in r.iter_bytes(chunk_size=65536):
                    chunks.append(chunk)
                body = b"".join(chunks)
        if not body or len(body) < min_bytes:
            return f"short body ({len(body)} bytes)"
        dest.write_bytes(body)
        return None
    except Exception as e:
        return f"{type(e).__name__}: {e}"


def refresh_local_cache() -> dict:
    """Refresh OFAC SDN (primary) and trade.gov CSL (best-effort)."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    result = {"ofac_sdn": None, "csl": None}

    err = _download_file(OFAC_SDN_URL, OFAC_CACHE, min_bytes=500_000)
    if err is None:
        result["ofac_sdn"] = {"ok": True, "path": str(OFAC_CACHE),
                              "bytes": OFAC_CACHE.stat().st_size}
    else:
        result["ofac_sdn"] = {"error": err}

    csl_err = None
    for url in CSL_URLS:
        e = _download_file(url, CSL_CACHE, min_bytes=2_000_000)
        if e is None:
            result["csl"] = {"ok": True, "path": str(CSL_CACHE),
                             "bytes": CSL_CACHE.stat().st_size, "source": url}
            csl_err = None
            break
        csl_err = e
    if result["csl"] is None:
        result["csl"] = {"error": csl_err or "all CSL sources failed",
                         "note": "BIS Entity List coverage missing; OFAC SDN-only signal."}

    return result


def _load_csl_entries() -> list[dict]:
    if not CSL_CACHE.exists():
        return []
    with CSL_CACHE.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def _load_ofac_entries() -> list[dict]:
    if not OFAC_CACHE.exists():
        return []
    rows = []
    with OFAC_CACHE.open(newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        for parts in reader:
            row = {}
            for i, col in enumerate(_OFAC_COLS):
                row[col] = parts[i].strip().strip('"') if i < len(parts) else ""
            # Normalize to common schema used by query_designation.
            rows.append({
                "name":     row["sdn_name"],
                "alt_names": "",
                "source":   f"OFAC SDN ({row['sdn_type']})",
                "type":     row["sdn_type"],
                "country":  "",
                "programs": row["program"],
                "federal_register_notice": "",
            })
    return rows


def _load_entries() -> list[dict]:
    return _load_csl_entries() + _load_ofac_entries()


def _any_cache_present() -> bool:
    return CSL_CACHE.exists() or OFAC_CACHE.exists()


_NOISE_TOKENS = {
    # US/UK corporate forms
    "inc", "inc.", "incorporated", "corp", "corp.", "corporation",
    "ltd", "ltd.", "limited", "co", "co.", "company", "companies",
    "llc", "lp", "plc",
    # Continental Europe forms
    "ag", "sa", "se", "nv", "bv", "spa", "gmbh", "kg", "kgaa", "oy", "oyj",
    # Russian / CIS / Chinese / Asian forms
    "public", "joint", "stock", "private", "open", "closed",
    "liability", "state", "federal", "national", "international",
    "pjsc", "oao", "ojsc", "ooo", "zao", "pao",
    "pte", "sdn", "bhd", "spv", "jsc", "llp",
    # Generic
    "the", "&", "and", "of", "for", "group", "holdings", "holding",
}


def _normalize(s: str) -> str:
    s = (s or "").lower()
    for ch in ",.;:()[]\"'":
        s = s.replace(ch, " ")
    return " ".join(s.split())


def _meaningful_tokens(s: str) -> list[str]:
    return [t for t in _normalize(s).split() if t not in _NOISE_TOKENS and len(t) >= 3]


_MIN_OVERLAP_FRACTION = 0.4  # of entry's meaningful tokens must overlap query


def _match_name(entry_name: str, query: str) -> bool:
    """Token-set match.

    Match iff:
      1. every meaningful query token appears in entry, AND
      2. for single-token queries: the query token is the entry's first
         meaningful token (entity brand-name position), AND
      3. for multi-token queries: query tokens cover ≥ 40% of entry's
         meaningful tokens.

    Brand-name position rule avoids 'Apple Inc' matching 'Oriental Apple
    Company' (apple at position 1, not 0). Keeps 'Sberbank' → 'PJSC
    Sberbank of Russia' (after noise strip: 'sberbank' is at position 0).
    """
    q_tokens = _meaningful_tokens(query)
    e_tokens = _meaningful_tokens(entry_name)
    if not q_tokens or not e_tokens:
        return False
    e_set = set(e_tokens)
    if not all(t in e_set for t in q_tokens):
        return False
    if len(q_tokens) == 1:
        return e_tokens[0] == q_tokens[0]
    overlap = sum(1 for t in q_tokens if t in e_set)
    return (overlap / len(e_tokens)) >= _MIN_OVERLAP_FRACTION


def query_designation(name: str) -> dict[str, Any]:
    """Is `name` on any US export-control list?"""
    if not _any_cache_present():
        return {
            "signal":   "UNVERIFIABLE",
            "severity": _DESIGNATION_SEVERITY["UNVERIFIABLE"],
            "direction": "neutral",
            "_note": (
                f"No export-control caches at {CACHE_DIR}. "
                "Call export_control_check.refresh_local_cache() once to populate."
            ),
        }

    entries = _load_entries()
    matches = []
    for e in entries:
        primary = e.get("name") or e.get("entity_name") or ""
        aliases = (e.get("alt_names") or "").split(";")
        candidates = [primary] + [a.strip() for a in aliases if a.strip()]
        for cand in candidates:
            if _match_name(cand, name):
                matches.append({
                    "matched_name":  cand,
                    "source":        e.get("source"),
                    "type":          e.get("type"),
                    "country":       e.get("country") or e.get("countries"),
                    "programs":      e.get("programs"),
                    "federal_register_notice": e.get("federal_register_notice"),
                })
                break

    if matches:
        return {
            "name_searched": name,
            "signal":   "DESIGNATED",
            "severity": _DESIGNATION_SEVERITY["DESIGNATED"],
            "direction": "negative",
            "n_matches": len(matches),
            "matches":  matches[:5],
            "_note": (
                f"{len(matches)} designation(s) match '{name}': "
                + ", ".join(f"{m['source']}/{m['matched_name']}" for m in matches[:3])
            ),
        }

    return {
        "name_searched": name,
        "signal":   "CLEAN",
        "severity": _DESIGNATION_SEVERITY["CLEAN"],
        "direction": "positive",
        "n_matches": 0,
        "_note": "No US export-control designations match this name.",
    }


def query_customer_exposure(
    named_customers: list[str],
    cutoff_date: Optional[str] = None,
) -> dict[str, Any]:
    """Score export-control exposure of an issuer's named customers/distributors.

    Args:
      named_customers: list of company names from 10-K Item 1 / customer table.
      cutoff_date: informational only (CSL is a current snapshot).
    """
    if not _any_cache_present():
        return {
            "signal":   "UNVERIFIABLE",
            "severity": _DESIGNATION_SEVERITY["UNVERIFIABLE"],
            "direction": "neutral",
            "_note": "CSL cache missing; refresh first.",
        }

    if not named_customers:
        return {
            "signal":   "UNVERIFIABLE",
            "severity": _DESIGNATION_SEVERITY["UNVERIFIABLE"],
            "direction": "neutral",
            "_note": "No customers provided.",
        }

    designated = []
    for cust in named_customers:
        d = query_designation(cust)
        if d.get("signal") == "DESIGNATED":
            designated.append({
                "customer": cust,
                "matches":  d.get("matches", [])[:2],
            })

    n_total = len(named_customers)
    n_des = len(designated)
    pct = 100.0 * n_des / n_total if n_total else 0.0

    if n_des == 0:
        signal = "CLEAN"
    elif n_des == 1 or pct < 15:
        signal = "EXPOSED"
    else:
        signal = "SEVERE_EXPOSURE"

    direction = (
        "positive" if signal == "CLEAN"
        else "negative"
    )

    return {
        "cutoff_date": cutoff_date,
        "signal":   signal,
        "severity": _DESIGNATION_SEVERITY[signal],
        "direction": direction,
        "n_customers_checked":  n_total,
        "n_designated":         n_des,
        "pct_designated":       round(pct, 1),
        "designated_customers": designated,
        "_note": (
            f"{n_des}/{n_total} named customer(s) designated on US export-control lists."
            if n_des else
            f"All {n_total} named customers clean."
        ),
    }


if __name__ == "__main__":
    import json
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--refresh":
        print(json.dumps(refresh_local_cache(), indent=2))
        sys.exit(0)
    name = sys.argv[1] if len(sys.argv) > 1 else "Huawei Technologies"
    print(json.dumps(query_designation(name), indent=2, default=str))
