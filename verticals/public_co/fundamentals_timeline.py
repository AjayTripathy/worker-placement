"""Quarter-by-quarter fundamentals timeline from SEC XBRL companyfacts.

A live diligence asks not only "are the disclosures honest" but "what has the
business actually done since the prospectus." The structured-financials answer
lives in SEC's XBRL companyfacts API, which exposes every us-gaap concept the
issuer has ever tagged, per period. This module distills that firehose into a
compact per-quarter table: revenue (+ YoY growth), operating income/margin, net
income, total costs, and end-of-quarter cash -- the series an analyst scans to
separate a fundamental-deterioration story from a float/dilution/valuation one.

Discrete quarters are identified by the XBRL `frame` tag: a flow concept (income,
revenue) for calendar Q3 2025 carries frame "CY2025Q3"; a point-in-time balance
(cash) carries "CY2025Q3I". We key off frames so we get clean, non-overlapping
quarters and never double-count a 9-month YTD figure as a quarter.

Run:  python3 -m verticals.public_co.fundamentals_timeline CAI
      python3 -m verticals.public_co.fundamentals_timeline CAI --cik 0002019410
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import httpx

from . import edgar

DATA = Path(__file__).parent / "data"

# us-gaap concepts, in preference order. Issuers tag the same economic line under
# slightly different concepts; we take the first that has data.
REVENUE_CONCEPTS = [
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "RevenueFromContractWithCustomerIncludingAssessedTax",
    "Revenues",
    "RevenueFromContractWithCustomerPolicyTextBlock",
]
OP_INCOME_CONCEPTS = ["OperatingIncomeLoss"]
NET_INCOME_CONCEPTS = ["NetIncomeLoss", "ProfitLoss"]
COSTS_CONCEPTS = ["CostsAndExpenses", "BenefitsLossesAndExpenses"]
GROSS_PROFIT_CONCEPTS = ["GrossProfit"]
COST_OF_REV_CONCEPTS = [
    "CostOfRevenue", "CostOfGoodsAndServicesSold", "CostOfGoodsSold",
]
CASH_CONCEPTS = [
    "CashAndCashEquivalentsAtCarryingValue",
    "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
]

_QFRAME = re.compile(r"^CY(\d{4})Q([1-4])$")       # flow, discrete quarter
_QFRAME_I = re.compile(r"^CY(\d{4})Q([1-4])I$")    # instant, point-in-time
_YFRAME = re.compile(r"^CY(\d{4})$")               # flow, full fiscal year


def _facts_url(cik: str) -> str:
    return f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"


def fetch_companyfacts(cik: str) -> dict:
    r = httpx.get(_facts_url(cik), headers=edgar.HEADERS, timeout=60,
                  follow_redirects=True)
    r.raise_for_status()
    return r.json()


def _usd_units(facts: dict, concept: str) -> list[dict]:
    """Return the USD unit rows for a us-gaap concept, or [] if absent."""
    node = facts.get("facts", {}).get("us-gaap", {}).get(concept)
    if not node:
        return []
    units = node.get("units", {})
    return units.get("USD", []) or units.get("USD/shares", []) or []


def _first_concept(facts: dict, concepts: list[str]) -> tuple[str | None, list[dict]]:
    for c in concepts:
        rows = _usd_units(facts, c)
        if rows:
            return c, rows
    return None, []


def _quarter_flow(rows: list[dict]) -> dict[str, float]:
    """Map 'YYYYQq' -> value for discrete-quarter flow frames (CY####Q#)."""
    out: dict[str, float] = {}
    for r in rows:
        fr = r.get("frame")
        if not fr:
            continue
        m = _QFRAME.match(fr)
        if m:
            out[f"{m.group(1)}Q{m.group(2)}"] = r["val"]
    return out


def _year_flow(rows: list[dict]) -> dict[str, float]:
    """Map 'YYYY' -> value for full-year flow frames (CY####)."""
    out: dict[str, float] = {}
    for r in rows:
        fr = r.get("frame")
        if not fr:
            continue
        m = _YFRAME.match(fr)
        if m:
            out[m.group(1)] = r["val"]
    return out


def _derive_q4(qmap: dict[str, float], ymap: dict[str, float]) -> dict[str, float]:
    """Fill missing Q4 from the full-year frame: Q4 = FY - (Q1+Q2+Q3).

    XBRL frame-tags Q1/Q2/Q3 and the full year, but never an isolated Q4 (the
    10-K reports the annual figure). For any year where all three quarters and
    the annual total are present, Q4 is exactly recoverable. Mutates and returns
    qmap with derived Q4 entries added (never overwrites a tagged Q4).
    """
    for year, fy in ymap.items():
        q4k = f"{year}Q4"
        if q4k in qmap:
            continue
        parts = [qmap.get(f"{year}Q{i}") for i in (1, 2, 3)]
        if all(p is not None for p in parts):
            qmap[q4k] = round(fy - sum(parts), 2)
    return qmap


def _quarter_instant(rows: list[dict]) -> dict[str, float]:
    """Map 'YYYYQq' -> value for point-in-time instant frames (CY####Q#I)."""
    out: dict[str, float] = {}
    for r in rows:
        fr = r.get("frame")
        if not fr:
            continue
        m = _QFRAME_I.match(fr)
        if m:
            out[f"{m.group(1)}Q{m.group(2)}"] = r["val"]
    return out


def _qkey_sort(qkey: str) -> tuple[int, int]:
    y, q = qkey.split("Q")
    return int(y), int(q)


def _prior_year(qkey: str) -> str:
    y, q = qkey.split("Q")
    return f"{int(y) - 1}Q{q}"


def build_timeline(ticker: str, *, cik: str | None = None,
                   with_guidance: bool = True) -> dict:
    """Assemble the quarter-by-quarter fundamentals timeline for a ticker.

    Returns a dict with `quarters` (chronological list of per-quarter records),
    `guidance` (forward revenue guidance from earnings 8-K exhibits, if the
    corpus is on disk and `with_guidance`), plus the resolved concepts and
    coverage metadata. Also written to data/<ticker>/fundamentals_timeline.json.
    """
    cik = edgar.cik_for(ticker, override=cik)
    facts = fetch_companyfacts(cik)

    rev_c, rev_rows = _first_concept(facts, REVENUE_CONCEPTS)
    op_c, op_rows = _first_concept(facts, OP_INCOME_CONCEPTS)
    ni_c, ni_rows = _first_concept(facts, NET_INCOME_CONCEPTS)
    cost_c, cost_rows = _first_concept(facts, COSTS_CONCEPTS)
    gp_c, gp_rows = _first_concept(facts, GROSS_PROFIT_CONCEPTS)
    cor_c, cor_rows = _first_concept(facts, COST_OF_REV_CONCEPTS)
    cash_c, cash_rows = _first_concept(facts, CASH_CONCEPTS)

    rev_tagged = set(_quarter_flow(rev_rows))
    rev = _derive_q4(_quarter_flow(rev_rows), _year_flow(rev_rows))
    op = _derive_q4(_quarter_flow(op_rows), _year_flow(op_rows))
    ni = _derive_q4(_quarter_flow(ni_rows), _year_flow(ni_rows))
    cost = _derive_q4(_quarter_flow(cost_rows), _year_flow(cost_rows))
    gp = _derive_q4(_quarter_flow(gp_rows), _year_flow(gp_rows))
    cor = _derive_q4(_quarter_flow(cor_rows), _year_flow(cor_rows))
    cash = _quarter_instant(cash_rows)

    all_q = set(rev) | set(op) | set(ni) | set(cost) | set(gp) | set(cash)
    quarters = []
    for qk in sorted(all_q, key=_qkey_sort):
        r = rev.get(qk)
        o = op.get(qk)
        g = gp.get(qk)
        c_rev = cor.get(qk)
        # Derive gross profit if only cost-of-revenue is tagged.
        if g is None and r is not None and c_rev is not None:
            g = r - c_rev
        prior_r = rev.get(_prior_year(qk))
        rec = {
            "quarter": qk,
            "derived_q4": qk.endswith("Q4") and qk not in rev_tagged,
            "revenue": r,
            "revenue_yoy_pct": (round((r - prior_r) / prior_r * 100, 1)
                                if r is not None and prior_r else None),
            "gross_profit": g,
            "gross_margin_pct": (round(g / r * 100, 1)
                                 if g is not None and r else None),
            "operating_income": o,
            "operating_margin_pct": (round(o / r * 100, 1)
                                     if o is not None and r else None),
            "net_income": ni.get(qk),
            "total_costs": cost.get(qk),
            "cash_end": cash.get(qk),
        }
        quarters.append(rec)

    guidance = []
    if with_guidance:
        try:
            guidance = extract_guidance(ticker, cik=cik)
        except Exception as e:  # network/exhibit parsing is best-effort
            print(f"  guidance extraction skipped: {e}", file=sys.stderr)

    out = {
        "ticker": ticker.upper(),
        "cik": cik,
        "entity": facts.get("entityName"),
        "concepts": {
            "revenue": rev_c, "operating_income": op_c, "net_income": ni_c,
            "total_costs": cost_c, "gross_profit": gp_c,
            "cost_of_revenue": cor_c, "cash": cash_c,
        },
        "n_quarters": len(quarters),
        "quarters": quarters,
        "guidance": guidance,
    }

    out_dir = DATA / ticker.lower()
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / "fundamentals_timeline.json"
    p.write_text(json.dumps(out, indent=2))
    print(f"  wrote {p} ({len(quarters)} quarters)", file=sys.stderr)
    return out


# --------------------------------------------------------------------------- #
# Guidance from earnings-release 8-K exhibits (EX-99.1).
# --------------------------------------------------------------------------- #
# XBRL carries ACTUALS only. Forward guidance lives in the earnings press release
# attached to an Item-2.02 8-K as Exhibit 99.1 -- a separate HTML document the
# edgar.pull() primary-doc fetch does not download. We fetch the exhibit on
# demand and capture revenue-guidance ranges plus the issuer's own framing word
# (expects / reaffirms / raises / lowers), which is the disclosure-consistency
# signal: guidance held, raised, or cut between successive quarters.
_GUID_ACTION = re.compile(
    r"\b(reaffirm\w*|rais\w*|increas\w*|lower\w*|reduc\w*|cut\w*|expect\w*|"
    r"anticipat\w*|now expect\w*|update\w*)\b", re.I)
# Revenue guidance comes in two common shapes -- annual "range of $X to $Y" and
# quarterly "Revenue between $X million and $Y million" -- so match "revenue"
# followed (within a short window) by either connector. Issuers also vary on
# "to" vs "and" and on placing the $ on one or both bounds.
_GUID_RANGE = re.compile(
    r"revenue[^.$\n]{0,40}?(?:between|range of|of|in the range of)\s+"
    r"\$?\s*([\d.]+)\s*(billion|million)\s+(?:to|and)\s+"
    r"\$?\s*([\d.]+)\s*(billion|million)", re.I)
# Period the guidance applies to, searched in the text preceding the range.
_QUARTER_WORD = {"first": 1, "second": 2, "third": 3, "fourth": 4}
_PERIOD_FULLYEAR = re.compile(r"full[ -]year\s+(20\d{2})", re.I)
_PERIOD_YEAREND = re.compile(r"year ending\s+\w+\s+\d{1,2},?\s+(20\d{2})", re.I)
_PERIOD_QUARTER = re.compile(
    r"(first|second|third|fourth)\s+quarter\s+(?:of\s+)?(20\d{2})", re.I)
_PERIOD_QN = re.compile(r"\bQ([1-4])\s+(20\d{2})", re.I)
_EX99 = re.compile(r'href="([^"]*ex[\-_]?99[^"]*\.htm[l]?)"', re.I)


def _detect_period(window: str) -> tuple[str, int] | None:
    """Find the most recent period label preceding a revenue range.

    Returns (label, fiscal_year), e.g. ("FY2026", 2026) or ("Q2 2026", 2026).
    We take the LAST match in the window because the period heading ("Second
    Quarter 2026 Guidance") sits just before the revenue line.
    """
    best = None  # (position, label, year)
    for m in _PERIOD_FULLYEAR.finditer(window):
        best = max(best or (-1, "", 0), (m.start(), f"FY{m.group(1)}", int(m.group(1))))
    for m in _PERIOD_YEAREND.finditer(window):
        best = max(best or (-1, "", 0), (m.start(), f"FY{m.group(1)}", int(m.group(1))))
    for m in _PERIOD_QUARTER.finditer(window):
        q = _QUARTER_WORD[m.group(1).lower()]
        best = max(best or (-1, "", 0), (m.start(), f"Q{q} {m.group(2)}", int(m.group(2))))
    for m in _PERIOD_QN.finditer(window):
        best = max(best or (-1, "", 0),
                   (m.start(), f"Q{m.group(1)} {m.group(2)}", int(m.group(2))))
    if not best or not best[1]:
        return None
    return best[1], best[2]


def _scale(num: str, unit: str) -> float:
    return float(num) * (1e9 if unit.lower().startswith("b") else 1e6)


def recent_8k_filings(cik: str, *, limit: int = 12) -> list[dict]:
    """Most-recent 8-Ks straight from the SEC submissions API (not on-disk).

    Guidance must not depend on a pre-refreshed local corpus -- a stale backtest
    index would silently yield zero guidance (the RKLB reusability bug). Pulling
    the live submissions feed makes the extractor self-sufficient for any ticker.
    """
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    d = httpx.get(url, headers=edgar.HEADERS, timeout=30, follow_redirects=True).json()
    rec = d.get("filings", {}).get("recent", {})
    rows = [
        {"accession": a, "filing_date": fd, "primary_document": pd}
        for form, fd, a, pd in zip(
            rec.get("form", []), rec.get("filingDate", []),
            rec.get("accessionNumber", []), rec.get("primaryDocument", []))
        if form == "8-K"
    ]
    rows.sort(key=lambda r: r["filing_date"])
    return rows[-limit:]


def _strip_html(raw: str) -> str:
    import html as _html
    t = re.sub(r"<[^>]+>", " ", raw)
    return re.sub(r"\s+", " ", _html.unescape(t))


def _accession_folder_url(cik: str, accession: str) -> str:
    return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace('-', '')}/"


def _classify_action(word: str) -> str:
    w = word.lower()
    if w.startswith(("reaffirm",)):
        return "reaffirmed"
    if w.startswith(("rais", "increas")):
        return "raised"
    if w.startswith(("lower", "reduc", "cut")):
        return "lowered"
    return "issued"


def extract_guidance(ticker: str, *, cik: str | None = None,
                     limit: int = 12) -> list[dict]:
    """Best-effort forward revenue-guidance extraction from earnings exhibits.

    Pulls the most recent `limit` 8-Ks live from the SEC submissions API, fetches
    each one's EX-99.1 press release, and captures every "revenue between/range of
    $X to $Y" figure with the period it applies to (full-year or a quarter).
    Returns a chronological list of {filing_date, period, fiscal_year, metric,
    low, high, action, raw, source_url}. Records nothing (rather than guessing)
    when an exhibit has no parseable range -- consistent with the framework's
    report-unverifiable-as-unverifiable rule.
    """
    cik = edgar.cik_for(ticker, override=cik)
    try:
        rows = recent_8k_filings(cik, limit=limit)
    except httpx.HTTPError as e:
        print(f"  guidance: submissions API failed ({e})", file=sys.stderr)
        return []
    out: list[dict] = []
    for r in rows:
        folder = _accession_folder_url(cik, r["accession"])
        try:
            listing = httpx.get(folder, headers=edgar.HEADERS, timeout=30,
                                follow_redirects=True).text
        except httpx.HTTPError:
            continue
        m = _EX99.search(listing)
        if not m:
            continue
        ex_url = folder + m.group(1).split("/")[-1]
        try:
            body = httpx.get(ex_url, headers=edgar.HEADERS, timeout=30,
                             follow_redirects=True).text
        except httpx.HTTPError:
            continue
        text = _strip_html(body)
        for gm in _GUID_RANGE.finditer(text):
            lo_n, lo_u, hi_n, hi_u = gm.groups()
            window = text[max(0, gm.start() - 160):gm.start()]
            period = _detect_period(window)
            if not period:
                continue  # a range with no resolvable period is not guidance
            label, fy = period
            aw = _GUID_ACTION.findall(window)
            out.append({
                "filing_date": r["filing_date"],
                "period": label,
                "fiscal_year": fy,
                "metric": "revenue",
                "low": _scale(lo_n, lo_u),
                "high": _scale(hi_n, hi_u),
                "action": _classify_action(aw[-1]) if aw else "issued",
                "raw": text[gm.start():gm.start() + 200].strip(),
                "source_url": ex_url,
            })
    out = _dedupe_and_classify(out)
    print(f"  guidance: {len(out)} revenue-guidance point(s) found", file=sys.stderr)
    return out


def _dedupe_and_classify(points: list[dict]) -> list[dict]:
    """Drop duplicate ranges restated within one release; classify the action by
    comparing each guide's midpoint to the prior guide for the SAME period
    (raised / lowered / reaffirmed), which is more robust than the framing word.
    The first guide for a period stays `issued`.
    """
    seen = set()
    uniq = []
    for p in sorted(points, key=lambda x: (x["filing_date"], x["period"])):
        key = (p["filing_date"], p["period"], p["low"], p["high"])
        if key in seen:
            continue
        seen.add(key)
        uniq.append(p)
    prior_mid: dict[str, float] = {}
    for p in uniq:
        per = p["period"]
        mid = (p["low"] + p["high"]) / 2
        if per not in prior_mid:
            p["action"] = "issued"
        elif mid > prior_mid[per] * 1.005:
            p["action"] = "raised"
        elif mid < prior_mid[per] * 0.995:
            p["action"] = "lowered"
        else:
            p["action"] = "reaffirmed"
        prior_mid[per] = mid
    return uniq


def _fmt_m(v: float | None) -> str:
    return f"{v / 1e6:,.1f}" if v is not None else "--"


def _print_table(tl: dict) -> None:
    hdr = f"{'Quarter':<8} {'Rev($M)':>9} {'YoY%':>7} {'OpMgn%':>8} {'NetInc($M)':>11} {'Cash($M)':>10}"
    print(hdr)
    print("-" * len(hdr))
    for q in tl["quarters"]:
        print(f"{q['quarter']:<8} {_fmt_m(q['revenue']):>9} "
              f"{(str(q['revenue_yoy_pct']) if q['revenue_yoy_pct'] is not None else '--'):>7} "
              f"{(str(q['operating_margin_pct']) if q['operating_margin_pct'] is not None else '--'):>8} "
              f"{_fmt_m(q['net_income']):>11} {_fmt_m(q['cash_end']):>10}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Build a quarterly fundamentals timeline from SEC XBRL.")
    ap.add_argument("ticker")
    ap.add_argument("--cik", default=None, help="10-digit CIK override.")
    ap.add_argument("--no-guidance", action="store_true",
                    help="Skip earnings-8-K guidance extraction (XBRL actuals only).")
    args = ap.parse_args()
    tl = build_timeline(args.ticker, cik=args.cik, with_guidance=not args.no_guidance)
    print(f"\n{tl['entity']} ({tl['ticker']}) -- concepts: "
          f"rev={tl['concepts']['revenue']}", file=sys.stderr)
    _print_table(tl)
    if tl.get("guidance"):
        print("\nForward revenue guidance (from earnings 8-K EX-99.1):")
        for g in tl["guidance"]:
            print(f"  {g['filing_date']}  {g['period']:<9} {g['action']:<10} "
                  f"${g['low']/1e6:,.0f}M - ${g['high']/1e6:,.0f}M")


if __name__ == "__main__":
    main()
