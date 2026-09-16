"""FDA Orange Book — patent + exclusivity ladder for marketed Rx drugs.

WHY THIS EXISTS

Loss of exclusivity (LOE) is the dominant catastrophe vector for
small-/mid-cap marketed-Rx names. A pharma with a single dominant drug
and a near-term LOE gap is structurally exposed — IPR/PGR patent
challenges and generic ANDAs accelerate the cliff.

The FDA Orange Book is the canonical reference: it lists every approved
drug product with its associated patents (expiration dates, use codes)
and exclusivity grants (expiration dates, exclusivity codes like NCE,
GAIN, ODE). Free download as pipe-delimited text files.

DATA SOURCE
  https://www.fda.gov/drugs/drug-approvals-and-databases/orange-book-data-files
  Files:
    products.txt    — every approved product, with applicant
    patent.txt      — patents per product, expiration
    exclusivity.txt — exclusivity grants per product, expiration

We accept the applicant_name as input; in practice the Orange Book
applicant names are the legal entities (e.g., "Catalyst Pharms Inc",
"Krystal Biotech Inc", "Corcept Therapeutics") and need substring
matching against ticker/CIK.

LOCAL CACHE

To avoid hammering the FDA download every call, the module looks for
a local copy at `data/_orange_book/{products,patent,exclusivity}.txt`.
Use `refresh_local_cache()` to download.

OUTPUT

  signal: NO_DRUGS | INSULATED | LOE_FAR | LOE_NEAR | LOE_IMMINENT | UNVERIFIABLE
  metrics: {n_drugs, n_drugs_with_patent_or_exclusivity, earliest_loe_date,
            months_to_loe, drugs_at_risk}

THRESHOLDS (months from cutoff to earliest patent/exclusivity expiration
on the applicant's largest product set)

  > 60 months         → INSULATED
  24-60 months        → LOE_FAR
  12-24 months        → LOE_NEAR
  < 12 months         → LOE_IMMINENT
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": ["283"],
    "issuer_features": ["marketed_drug_or_device"],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": False,
    "kind": "m_source",
    "summary": "FDA Orange Book patent/exclusivity ladder; single-drug near-LOE concentration is the catastrophe vector.",
}

from datetime import date
from pathlib import Path
from typing import Any, Optional

import httpx

HEADERS = {"User-Agent": "Signal OS Research backtest@signalos.local"}

CACHE_DIR = Path(__file__).parent.parent / "data" / "_orange_book"
PRODUCTS_FILE   = CACHE_DIR / "products.txt"
PATENT_FILE     = CACHE_DIR / "patent.txt"
EXCLUSIVITY_FILE = CACHE_DIR / "exclusivity.txt"

ORANGE_BOOK_ZIP_URL = "https://www.fda.gov/media/76860/download?attachment"

_SEVERITY_MAP = {
    "NO_DRUGS":     "PASS",  # informational — pre-market issuer
    "INSULATED":    "PASS",
    "LOE_FAR":      "PASS",
    "LOE_NEAR":     "MODERATE_UNDERDELIVERY",
    "LOE_IMMINENT": "SEVERE_UNDERDELIVERY",
    "UNVERIFIABLE": "UNVERIFIABLE",
}


def _parse_date(s: str) -> Optional[date]:
    """Orange Book dates are like 'Jan 1, 2030' or 'Aug 15, 2025'."""
    s = (s or "").strip()
    if not s or s.upper() == "N/A":
        return None
    for fmt in ("%b %d, %Y", "%Y-%m-%d", "%m/%d/%Y"):
        try:
            from datetime import datetime
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def refresh_local_cache() -> dict:
    """Download Orange Book zip and extract products/patent/exclusivity text files."""
    import io
    import zipfile

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with httpx.Client(headers=HEADERS, timeout=120, follow_redirects=True) as c:
            r = c.get(ORANGE_BOOK_ZIP_URL)
            if r.status_code != 200:
                return {"error": f"download status_{r.status_code}"}
            zf = zipfile.ZipFile(io.BytesIO(r.content))
            for member in zf.namelist():
                low = member.lower()
                if low.endswith("products.txt"):
                    (CACHE_DIR / "products.txt").write_bytes(zf.read(member))
                elif low.endswith("patent.txt"):
                    (CACHE_DIR / "patent.txt").write_bytes(zf.read(member))
                elif low.endswith("exclusivity.txt"):
                    (CACHE_DIR / "exclusivity.txt").write_bytes(zf.read(member))
        return {"ok": True, "cache_dir": str(CACHE_DIR)}
    except Exception as e:
        return {"error": str(e)}


def _read_pipe_delim(path: Path) -> list[dict]:
    if not path.exists():
        return []
    txt = path.read_text(encoding="utf-8", errors="replace")
    lines = [ln for ln in txt.splitlines() if ln.strip()]
    if not lines:
        return []
    headers = [h.strip() for h in lines[0].split("~")]
    out = []
    for ln in lines[1:]:
        parts = ln.split("~")
        row = {}
        for i, h in enumerate(headers):
            row[h] = parts[i].strip() if i < len(parts) else ""
        out.append(row)
    return out


_NOISE_TOKENS = {
    "inc", "inc.", "corp", "corp.", "ltd", "ltd.", "co", "co.", "llc",
    "lp", "plc", "pharms", "pharma", "pharmaceuticals", "pharmaceutical",
    "biotech", "biotechnology", "therapeutics", "labs", "laboratories",
    "holdings", "group", "the", "&", "and",
}


def _match_applicant(applicant_field: str, query: str) -> bool:
    """Require all meaningful (non-corporate-suffix) query tokens to appear."""
    q = (query or "").lower().strip()
    a = (applicant_field or "").lower()
    if not q or not a:
        return False
    if q in a:
        return True
    tokens = [t for t in q.replace(",", " ").split() if t not in _NOISE_TOKENS and len(t) >= 3]
    if not tokens:
        return q in a
    return all(t in a for t in tokens)


def query_orange_book(applicant_name: str, cutoff_date: str) -> dict[str, Any]:
    """Return LOE signal for an applicant.

    Args:
      applicant_name: company name (Orange Book applicant_full_name format,
                      e.g., "Catalyst Pharms Inc", "Krystal Biotech Inc").
      cutoff_date: ISO YYYY-MM-DD.
    """
    cutoff = _parse_date(cutoff_date)
    if cutoff is None:
        return {"signal": "UNVERIFIABLE", "severity": "UNVERIFIABLE",
                "direction": "neutral", "_note": f"bad cutoff {cutoff_date}"}

    if not PRODUCTS_FILE.exists():
        return {
            "signal":   "UNVERIFIABLE",
            "severity": "UNVERIFIABLE",
            "direction": "neutral",
            "_note": (
                f"Orange Book cache missing at {CACHE_DIR}. "
                "Call orange_book.refresh_local_cache() once to populate."
            ),
        }

    products = _read_pipe_delim(PRODUCTS_FILE)
    patents  = _read_pipe_delim(PATENT_FILE)
    exclusivity = _read_pipe_delim(EXCLUSIVITY_FILE)

    # Filter products to applicant
    my_products = [
        p for p in products
        if _match_applicant(p.get("Applicant_Full_Name", "") or p.get("Applicant", ""), applicant_name)
    ]
    if not my_products:
        return {
            "applicant_searched": applicant_name,
            "cutoff_date": cutoff_date,
            "signal":   "NO_DRUGS",
            "severity": _SEVERITY_MAP["NO_DRUGS"],
            "direction": "neutral",
            "_note": (
                "No Orange Book applications match this applicant. Three possibilities: "
                "(a) pre-approval clinical-stage issuer (no marketed drugs); "
                "(b) biologic-only issuer (BLAs are listed in the FDA Purple Book, "
                "not the Orange Book — gene therapy, mAbs, vaccines); "
                "(c) applicant-name string did not match Orange Book applicant field — "
                "try a shorter or longer name variant."
            ),
            "metrics": {"n_drugs": 0},
        }

    # Key by (Appl_No, Product_No)
    my_keys = {(p.get("Appl_No"), p.get("Product_No")) for p in my_products}

    earliest_expirations: list[tuple[date, str, str, str]] = []  # (date, drug, type, code/use)

    for pt in patents:
        key = (pt.get("Appl_No"), pt.get("Product_No"))
        if key not in my_keys:
            continue
        d = _parse_date(pt.get("Patent_Expire_Date_Text") or pt.get("Patent_Expire_Date") or "")
        if d is None or d <= cutoff:
            continue
        earliest_expirations.append((d, f"App{pt.get('Appl_No')}/{pt.get('Product_No')}",
                                     "patent", pt.get("Patent_No", "")))

    for ex in exclusivity:
        key = (ex.get("Appl_No"), ex.get("Product_No"))
        if key not in my_keys:
            continue
        d = _parse_date(ex.get("Exclusivity_Date") or "")
        if d is None or d <= cutoff:
            continue
        earliest_expirations.append((d, f"App{ex.get('Appl_No')}/{ex.get('Product_No')}",
                                     "exclusivity", ex.get("Exclusivity_Code", "")))

    if not earliest_expirations:
        # Drugs exist but no future patent/exclusivity → already LOE
        return {
            "applicant_searched": applicant_name,
            "cutoff_date": cutoff_date,
            "signal":   "LOE_IMMINENT",
            "severity": _SEVERITY_MAP["LOE_IMMINENT"],
            "direction": "negative",
            "_note": (
                f"{len(my_products)} approved product(s) but no remaining patent "
                "or exclusivity past cutoff — already LOE / generic-eligible."
            ),
            "metrics": {
                "n_drugs": len(my_products),
                "n_drugs_with_patent_or_exclusivity": 0,
                "earliest_loe_date": None,
                "months_to_loe": 0,
            },
        }

    earliest_expirations.sort()
    earliest_date, earliest_drug, earliest_type, earliest_code = earliest_expirations[0]
    months_to_loe = (earliest_date.year - cutoff.year) * 12 + (earliest_date.month - cutoff.month)

    if months_to_loe > 60:
        signal = "INSULATED"
    elif months_to_loe >= 24:
        signal = "LOE_FAR"
    elif months_to_loe >= 12:
        signal = "LOE_NEAR"
    else:
        signal = "LOE_IMMINENT"

    direction = "negative" if signal in ("LOE_NEAR", "LOE_IMMINENT") else "positive"

    return {
        "applicant_searched": applicant_name,
        "cutoff_date": cutoff_date,
        "signal":   signal,
        "severity": _SEVERITY_MAP[signal],
        "direction": direction,
        "metrics": {
            "n_drugs":                            len(my_products),
            "n_drugs_with_patent_or_exclusivity": len({d for _, d, _, _ in earliest_expirations}),
            "earliest_loe_date":                  str(earliest_date),
            "months_to_loe":                      months_to_loe,
            "earliest_loe_drug":                  earliest_drug,
            "earliest_loe_type":                  earliest_type,
            "earliest_loe_code":                  earliest_code,
        },
        "_note": (
            f"{len(my_products)} approved product(s); earliest LOE "
            f"{earliest_date} ({months_to_loe} months) — {earliest_type} on {earliest_drug}."
        ),
    }


if __name__ == "__main__":
    import json
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--refresh":
        print(json.dumps(refresh_local_cache(), indent=2))
        sys.exit(0)
    applicant = sys.argv[1] if len(sys.argv) > 1 else "Catalyst Pharms"
    cutoff = sys.argv[2] if len(sys.argv) > 2 else "2024-05-15"
    print(json.dumps(query_orange_book(applicant, cutoff), indent=2, default=str))
