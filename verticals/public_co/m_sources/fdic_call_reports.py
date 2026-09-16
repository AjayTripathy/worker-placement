"""
FDIC Call Reports — quarterly bank-level financial data.

Banks file Call Reports (FFIEC 031/041) every quarter; FDIC publishes the
data via api.fdic.gov. This connector supports the fintech-vertical use
case where non-bank lenders (UPST, AFRM, etc.) originate loans on
bank-partner balance sheets. The bank's Call Report adjudicates the
cohort credit-quality of those loans indirectly.

Key fields surfaced:
  - LNCONOTH    Other consumer loans (incl. unsecured personal loans like UPST)
  - LNCONOTH_30 Past-due 30-89 days
  - LNCONOTH_90 Past-due 90+ days
  - LNCONOTH_NA Nonaccrual
  - NTLNLS      Net charge-offs, total loans (ytd)
  - NCLNLS      Nonaccrual loans, total
  - ASSET       Total assets
  - NETINC      Net income (ytd)
  - ROAQ / ROEQ Return on assets / equity (quarterly)
  - DEPDOM      Domestic deposits

API: https://api.fdic.gov/banks/{institutions,financials}
Auth: none
Cost: free
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": ["60", "61"],
    "issuer_features": ["bank_partner_origination"],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": False,
    "kind": "m_source",
    "summary": "FDIC call-report data; bank-partner credit quality adjudicates fintech originator narratives indirectly.",
}

import sys
import time

import httpx

HEADERS = {"User-Agent": "Signal OS Research backtest@signalos.local"}

BASE = "https://api.fdic.gov/banks"

# Default fields returned for credit-quality queries
DEFAULT_FIELDS = [
    "NAME", "REPDTE", "ASSET",
    "LNCONOTH", "LNCONOTH_30", "LNCONOTH_90", "LNCONOTH_NA",
    "LNCRCD",   # credit-card loans
    "LNCON",    # total consumer loans (includes cards + other)
    "NTLNLS", "NCLNLS",
    "NTLNRE", "NTLNCI",  # net charge-offs by category (RE / C&I)
    "NETINC", "ROAQ", "ROEQ",
    "DEPDOM",
]


def _get(path: str, params: dict) -> dict | None:
    url = f"{BASE}/{path}"
    try:
        with httpx.Client(headers=HEADERS, timeout=30, follow_redirects=True) as c:
            r = c.get(url, params=params)
            if r.status_code != 200:
                return {"error": f"status_{r.status_code}", "body": r.text[:300]}
            return r.json()
    except httpx.HTTPError as e:
        return {"error": f"http: {e}"}


def lookup_institution(name: str) -> dict:
    """Resolve a bank name to its FDIC CERT (and RSSD). Tries exact-phrase
    match first; falls back to a prefix wildcard on a shortened form
    (stripping ', National Association', 'Bank', etc.) for multi-word names."""
    short = name.strip()
    for suffix in [", National Association", ", N.A.", ", FSB", ", S.B.", ", S.A."]:
        if short.endswith(suffix):
            short = short[: -len(suffix)]
    if short.endswith(" Bank") and len(short.split()) > 2:
        short = short[: -len(" Bank")]

    tokens = short.split()
    multi_token_filter = " AND ".join(f"NAME:{t}*" for t in tokens)
    strategies = [
        ("exact",          f'NAME:"{short}"'),
        ("exact_orig",     f'NAME:"{name}"'),
        ("multi_token",    multi_token_filter),
        ("prefix",         f"NAME:{tokens[0]}*"),
    ]
    seen_filter = set()
    for label, filt in strategies:
        if filt in seen_filter:
            continue
        seen_filter.add(filt)
        res = _get(
            "institutions",
            {
                "filters": filt,
                "fields":  "NAME,CERT,RSSDID,STALP,CITY,ASSET,INACTIVE,DATEUPDT",
                "limit":   100,
            },
        )
        if not res or "error" in res:
            continue
        rows = [d["data"] for d in res.get("data", [])]
        # Reject pure prefix-match noise: keep rows whose NAME contains the
        # full first-token of the original query (case-insensitive).
        anchor = short.lower().split()
        if anchor:
            rows = [r for r in rows if all(tok in (r.get("NAME") or "").lower()
                                            for tok in anchor)]
        if not rows:
            continue
        rows.sort(key=lambda r: (r.get("INACTIVE", 0), -1 * (r.get("ASSET") or 0)))
        return {
            "query":    name,
            "short":    short,
            "strategy": label,
            "n_total":  res.get("meta", {}).get("total", 0),
            "matches":  rows,
        }

    return {"query": name, "short": short, "n_total": 0, "matches": []}


def query_bank_credit_history(
    *,
    bank_name: str | None = None,
    cert: int | str | None = None,
    quarters: int = 8,
    fields: list[str] | None = None,
) -> dict:
    """Pull recent Call Report data for a bank.

    Specify either bank_name (substring lookup -> CERT) or cert (direct).
    Returns the last N quarters of headline credit-quality data.

    Returns:
      {
        "bank_name":    "...",
        "cert":         58410,
        "rssd":         123456,
        "quarters_pulled": [
          {"REPDTE": "20251231", "LNCONOTH": 2563885, ...},
          ...
        ],
        "summary": {
            "latest_quarter":     "20251231",
            "latest_LNCONOTH":    2563885,
            "latest_NTLNLS":      62924,
            "latest_NCLNLS":      255596,
            "charge_off_rate_pct": 2.45,
            "nonaccrual_rate_pct": 9.97,
        }
      }
    """
    if cert is None and not bank_name:
        return {"error": "specify bank_name or cert"}

    bank_info = {}
    if cert is None:
        lookup = lookup_institution(bank_name)
        if "error" in lookup or not lookup.get("matches"):
            return {"error": "no_institution_match", "query": bank_name, "lookup": lookup}
        bank = lookup["matches"][0]
        cert = bank["CERT"]
        bank_info = {
            "bank_name": bank.get("NAME", bank_name),
            "cert":      cert,
            "rssd":      bank.get("RSSDID"),
            "state":     bank.get("STALP"),
            "city":      bank.get("CITY"),
        }

    # `fields` is additive: callers can request extra fields but DEFAULT_FIELDS
    # are always included so the summary computation has its denominators.
    field_set = list(DEFAULT_FIELDS)
    if fields:
        for f in fields:
            if f and f not in field_set and f != "NAMEFULL":  # drop the non-existent NAMEFULL
                field_set.append(f)
    params = {
        "filters":    f"CERT:{cert}",
        "fields":     ",".join(field_set),
        "sort_by":    "REPDTE",
        "sort_order": "desc",
        "limit":      max(1, min(quarters, 40)),
    }
    res = _get("financials", params)
    if not res or "error" in res:
        return {"bank": bank_info, "error": res.get("error") if res else "no response"}

    rows = [d["data"] for d in res.get("data", [])]
    summary = {}
    if rows:
        latest = rows[0]
        ln_other = latest.get("LNCONOTH") or 0
        ln_card  = latest.get("LNCRCD")   or 0
        ln_total = latest.get("LNCON")    or (ln_other + ln_card)
        nc = latest.get("NCLNLS") or 0
        nt = latest.get("NTLNLS") or 0
        # Use the broadest available denominator that the bank actually carries
        # (LNCON > LNCONOTH+LNCRCD > LNCONOTH); rates against LNCONOTH only are
        # misleading for card-heavy issuers like Capital One.
        denom = ln_total or (ln_other + ln_card) or ln_other or None
        summary = {
            "latest_quarter":         latest.get("REPDTE"),
            "latest_LNCONOTH":        ln_other,
            "latest_LNCRCD":          ln_card,
            "latest_LNCON_total":     ln_total,
            "latest_NTLNLS_ytd":      nt,
            "latest_NCLNLS":          nc,
            "consumer_loan_denom":    denom,
            "charge_off_rate_pct":    round((nt / denom * 100), 2) if denom else None,
            "nonaccrual_rate_pct":    round((nc / denom * 100), 2) if denom else None,
        }
        # Trajectory hint: latest vs 4q-prior, on the broadest denominator.
        if len(rows) >= 5:
            prior = rows[4]
            denom_old = (prior.get("LNCON") or 0) or ((prior.get("LNCONOTH") or 0) + (prior.get("LNCRCD") or 0))
            if denom and denom_old:
                summary["consumer_loans_yoy_pct"] = round((denom - denom_old) / denom_old * 100, 1)

    return {
        "bank":             bank_info,
        "cert":             cert,
        "quarters_pulled":  rows,
        "n_quarters":       len(rows),
        "summary":          summary,
    }


def query_multi_bank_originations(
    bank_names: list[str],
    *,
    quarters: int = 4,
) -> dict:
    """Pull aggregate consumer-loan + credit-card balances across a list of
    bank partners. Adjudicates "concentration" claims like UPST's '83% of
    originations through top three lending partners' — if UPST's claim is
    accurate, the named partners' Call Reports should show consumer-loan
    portfolios consistent with the claimed origination volume.

    Returns:
      {
        "banks": [{"bank_name": ..., "cert": ..., "summary": ...}, ...],
        "aggregate": {
            "total_consumer_loans_M": <sum of LNCON across all banks>,
            "weighted_charge_off_pct": <weighted by denom>,
            "weighted_nonaccrual_pct": <weighted by denom>,
        },
        "n_banks_resolved": <int>,
      }
    """
    rows = []
    total_denom = 0
    weighted_co = 0.0
    weighted_na = 0.0
    n_resolved = 0
    for name in (bank_names or []):
        r = query_bank_credit_history(bank_name=name, quarters=quarters)
        if r.get("cert"):
            n_resolved += 1
            s = r.get("summary") or {}
            denom = s.get("consumer_loan_denom") or 0
            co    = s.get("charge_off_rate_pct") or 0
            na    = s.get("nonaccrual_rate_pct") or 0
            if denom:
                total_denom += denom
                weighted_co += denom * co
                weighted_na += denom * na
        rows.append({
            "input_name": name,
            "bank_name":  (r.get("bank") or {}).get("bank_name"),
            "cert":       r.get("cert"),
            "summary":    r.get("summary"),
        })
    agg = {
        "total_consumer_loans": total_denom,
        "weighted_charge_off_pct": round(weighted_co / total_denom, 3) if total_denom else None,
        "weighted_nonaccrual_pct": round(weighted_na / total_denom, 3) if total_denom else None,
    }
    return {
        "banks":               rows,
        "aggregate":           agg,
        "n_banks_resolved":    n_resolved,
        "n_banks_requested":   len(bank_names or []),
    }


def main():
    """CLI: python3 -m verticals.public_co.m_sources.fdic_call_reports "Cross River Bank" [quarters]"""
    if len(sys.argv) < 2:
        print('usage: python3 -m verticals.public_co.m_sources.fdic_call_reports "Cross River Bank" [quarters]', file=sys.stderr)
        sys.exit(2)
    name = sys.argv[1]
    q = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    res = query_bank_credit_history(bank_name=name, quarters=q)
    import json as _j
    print(_j.dumps(res, indent=2, default=str))


if __name__ == "__main__":
    main()
