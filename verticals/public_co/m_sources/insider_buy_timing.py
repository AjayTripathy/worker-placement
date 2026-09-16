"""Insider-buy timing classifier — separate Form 4 code-P transactions by
their proximity to 8-K disclosures.

THE SIGNAL
A code-P open-market PURCHASE by a C-suite officer or director carries
different information value depending on WHEN it happened:

  POST_BAD_NEWS_BUY: 0-30 days AFTER a bad-news 8-K (Item 4.02 non-reliance,
    NT filing, Item 3.01 delisting, Item 2.04 acceleration, Item 5.02
    abrupt exec departure). Highest conviction — insider buying after
    bad news is public is the strongest "I think this is overdone"
    signal because the info asymmetry is minimized.

  POST_EARNINGS_BUY: 0-15 days after a Item 2.02 earnings 8-K when stock
    is down. Indicates earnings-overreaction conviction.

  PRE_GOOD_NEWS_BUY: 0-30 days BEFORE a positive 8-K (Item 1.01 major
    contract, Item 8.01 favorable settlement, Item 2.02 beat). Potential
    insider-trading red flag if the buy was material and the news was
    foreseeable.

  QUIET_PERIOD_BUY: no bad news in 90 days prior, no good news 30 days
    after. Modest positive but lower conviction.

  LOCKUP_EXPIRY_BUY: within 30 days of an IPO/lockup expiry. Possibly
    pre-arranged or routine.

OUTPUT FIELDS

  P_transactions: list of code-P transactions with assigned timing class
  P_count_post_bad_news: int — highest-conviction positive count
  P_dollar_post_bad_news: float
  P_count_pre_good_news: int — red-flag count
  signal: STRONG_POST_DISTRESS_BUY | MIXED | NO_INSIDER_BUYS | POTENTIAL_INSIDER_TRADING

LIMITATIONS
- "Bad news 8-K" classification is heuristic based on item codes. Some
  earnings releases (Item 2.02) include bad guidance cuts that aren't
  detected without text parsing.
- Form 4 fetch is rate-limited; this module is best run on small samples.
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": [],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": True,
    "kind": "detector",
    "summary": "Classifies code-P insider buys by proximity to bad-news 8-Ks; post-bad-news buys are the conviction class.",
}

import re
import time
from datetime import date, timedelta
from typing import Any, Optional

from .. import edgar
from ..edgar import fetch_form4_xml


# 8-K item codes that strongly signal bad news
HARD_BAD_NEWS_ITEMS = {
    "4.02",  # non-reliance / restatement
    "3.01",  # notice of delisting
    "2.04",  # triggering events accelerating direct financial obligation
    "5.04",  # temporary suspension of trading
}

# Item codes that often signal bad news (judgment required)
SOFT_BAD_NEWS_ITEMS = {
    "2.05",  # costs associated with exit/disposal
    "2.06",  # material impairments
    "4.01",  # auditor change
    "5.02",  # executive departures — often (but not always) bad
}

# Item codes that often signal good news
POSITIVE_NEWS_ITEMS = {
    "1.01",  # entry into material agreement (new contract)
    "1.02",  # termination of material agreement (depends)
    "8.01",  # other (often positive announcements)
    "2.01",  # acquisition completion (positive for acquirer's stock if accretive)
}


def _parse_date(s: str) -> Optional[date]:
    try:
        return date.fromisoformat(s[:10])
    except (ValueError, TypeError):
        return None


def _extract_8k_items(primary_doc: str, accession: str, cik_int: str) -> list[str]:
    """Best-effort: fetch the 8-K cover page and extract Item codes mentioned.
    Returns empty list if fetch fails. The 8-K cover lists items as
    'Item 2.02' / 'Item 5.02 Departure of Directors...' etc.
    """
    try:
        text = edgar.fetch_filing_clean(cik_int, accession, primary_doc)
    except Exception:
        return []
    if not text:
        return []
    items = set()
    for m in re.finditer(r"Item\s+(\d+\.\d+)", text):
        items.add(m.group(1))
    return sorted(items)


def _classify_8k(items: set[str]) -> str:
    """Return 'HARD_BAD' | 'SOFT_BAD' | 'POSITIVE' | 'NEUTRAL'."""
    if items & HARD_BAD_NEWS_ITEMS:
        return "HARD_BAD"
    if items & SOFT_BAD_NEWS_ITEMS:
        return "SOFT_BAD"
    if items & POSITIVE_NEWS_ITEMS:
        return "POSITIVE"
    return "NEUTRAL"


def _parse_form4_p_transactions(cik: str, accession: str, primary_doc: str) -> list[dict]:
    """Return list of code-P transactions from a single Form 4."""
    cik_int = cik.lstrip("0")
    txt = fetch_form4_xml(cik_int, accession, primary_doc)
    if not txt:
        return []

    owner_m = re.search(r"<rptOwnerName>([^<]+)</rptOwnerName>", txt)
    title_m = re.search(r"<officerTitle>([^<]+)</officerTitle>", txt)
    is_director = "<isDirector>1</isDirector>" in txt
    is_officer = "<isOfficer>1</isOfficer>" in txt
    is_10pct = "<isTenPercentOwner>1</isTenPercentOwner>" in txt

    out = []
    for tx_block in re.finditer(
        r"<nonDerivativeTransaction>(.*?)</nonDerivativeTransaction>", txt, re.DOTALL
    ):
        blk = tx_block.group(1)
        code_m = re.search(r"<transactionCode>([^<]+)</transactionCode>", blk)
        if not code_m or code_m.group(1).strip() != "P":
            continue
        d_m = re.search(r"<transactionDate>\s*<value>([^<]+)</value>", blk)
        sh_m = re.search(r"<transactionShares>\s*<value>([^<]+)</value>", blk)
        pr_m = re.search(r"<transactionPricePerShare>\s*<value>([^<]+)</value>", blk)
        if not (owner_m and d_m and sh_m and pr_m):
            continue
        shares = float(sh_m.group(1))
        price = float(pr_m.group(1))
        out.append({
            "owner": owner_m.group(1),
            "officer_title": title_m.group(1) if title_m else None,
            "is_director": is_director,
            "is_officer": is_officer,
            "is_10pct": is_10pct,
            "tx_date": d_m.group(1),
            "shares": shares,
            "price": price,
            "dollars": shares * price,
        })
    return out


def query_insider_buy_timing(
    cik: str,
    cutoff_date: str,
    lookback_days: int = 540,
    classify_8k_text: bool = False,
) -> dict[str, Any]:
    """Pull Form 4 code-P transactions in the window, classify each by its
    timing relative to surrounding 8-K disclosures.

    Args:
      cik: 10-digit padded CIK
      cutoff_date: ISO YYYY-MM-DD
      lookback_days: how far back to look for transactions and 8-Ks
      classify_8k_text: if True, fetch each 8-K's primary document and parse
        Item codes (slower; rate-limited). If False (default), uses
        primary_doc_description heuristic only.
    """
    cutoff = _parse_date(cutoff_date)
    if cutoff is None:
        return {"signal": "ERROR", "_note": f"bad cutoff_date={cutoff_date!r}"}

    window_start = cutoff - timedelta(days=lookback_days)

    try:
        _, filings = edgar.list_filings(cik)
    except Exception as e:
        return {"signal": "ERROR", "_note": f"list_filings failed: {e}"}

    # Index 8-Ks in the window, classified by item codes
    eight_ks = []
    for f in filings:
        if f.get("form") != "8-K":
            continue
        fd = _parse_date(f.get("filing_date") or "")
        if not fd or fd > cutoff or fd < window_start - timedelta(days=120):
            continue
        # Use primary_doc_description as a quick item-code hint (no fetch)
        desc = (f.get("primary_doc_description") or "").lower()
        items: set[str] = set()
        for m in re.finditer(r"item\s+(\d+\.\d+)", desc):
            items.add(m.group(1))
        if classify_8k_text and not items:
            text_items = _extract_8k_items(f.get("primary_document", ""), f["accession"], cik.lstrip("0"))
            items = set(text_items)
            time.sleep(0.15)
        category = _classify_8k(items)
        eight_ks.append({
            "filing_date": fd,
            "accession": f["accession"],
            "items": sorted(items),
            "category": category,
        })

    # Pull Form 4s in the window
    form4s_in_window = []
    for f in filings:
        if f.get("form") != "4":
            continue
        fd = _parse_date(f.get("filing_date") or "")
        if not fd or fd > cutoff or fd < window_start:
            continue
        form4s_in_window.append(f)

    # Parse each Form 4 for P transactions
    p_transactions: list[dict] = []
    for f in form4s_in_window:
        try:
            p_txs = _parse_form4_p_transactions(cik, f["accession"], f.get("primary_document", ""))
        except Exception:
            continue
        for tx in p_txs:
            tx["form4_accession"] = f["accession"]
            tx["form4_filing_date"] = f["filing_date"]
            p_transactions.append(tx)
        time.sleep(0.15)

    # Classify each P transaction by its 8-K neighborhood
    for tx in p_transactions:
        tx_date = _parse_date(tx["tx_date"])
        if not tx_date:
            tx["timing_class"] = "UNDATED"
            continue

        bad_before = None  # most recent bad-news 8-K within 30 days BEFORE tx
        good_after = None  # earliest good-news 8-K within 30 days AFTER tx
        for ek in eight_ks:
            delta = (tx_date - ek["filing_date"]).days
            if 0 < delta <= 30:
                if ek["category"] in ("HARD_BAD", "SOFT_BAD"):
                    if bad_before is None or ek["filing_date"] > bad_before["filing_date"]:
                        bad_before = ek
            elif -30 <= delta < 0:
                if ek["category"] == "POSITIVE":
                    if good_after is None or ek["filing_date"] < good_after["filing_date"]:
                        good_after = ek

        if bad_before:
            tx["timing_class"] = "POST_BAD_NEWS_BUY"
            tx["nearby_8k"] = {"category": bad_before["category"],
                               "items": bad_before["items"],
                               "filing_date": str(bad_before["filing_date"]),
                               "days_after_8k": (tx_date - bad_before["filing_date"]).days}
        elif good_after:
            tx["timing_class"] = "PRE_GOOD_NEWS_BUY"
            tx["nearby_8k"] = {"category": good_after["category"],
                               "items": good_after["items"],
                               "filing_date": str(good_after["filing_date"]),
                               "days_before_8k": (good_after["filing_date"] - tx_date).days}
        else:
            tx["timing_class"] = "QUIET_PERIOD_BUY"

    # Aggregate
    count = {"POST_BAD_NEWS_BUY": 0, "PRE_GOOD_NEWS_BUY": 0,
             "QUIET_PERIOD_BUY": 0, "UNDATED": 0}
    dollars = {"POST_BAD_NEWS_BUY": 0.0, "PRE_GOOD_NEWS_BUY": 0.0,
               "QUIET_PERIOD_BUY": 0.0, "UNDATED": 0.0}
    for tx in p_transactions:
        c = tx.get("timing_class", "UNDATED")
        count[c] = count.get(c, 0) + 1
        dollars[c] = dollars.get(c, 0.0) + tx.get("dollars", 0.0)

    # Signal classification
    n_total = len(p_transactions)
    n_post_bad = count["POST_BAD_NEWS_BUY"]
    n_pre_good = count["PRE_GOOD_NEWS_BUY"]
    if n_total == 0:
        signal = "NO_INSIDER_BUYS"
    elif n_post_bad >= 2 and dollars["POST_BAD_NEWS_BUY"] >= 100_000:
        signal = "STRONG_POST_DISTRESS_BUY"
    elif n_pre_good >= 1 and dollars["PRE_GOOD_NEWS_BUY"] >= 250_000:
        signal = "POTENTIAL_INSIDER_TRADING"
    elif n_post_bad >= 1:
        signal = "MODERATE_POST_DISTRESS_BUY"
    else:
        signal = "QUIET_PERIOD_BUYS_ONLY"

    return {
        "cik": cik,
        "cutoff_date": cutoff_date,
        "lookback_days": lookback_days,
        "n_form4_filings": len(form4s_in_window),
        "n_8ks_indexed": len(eight_ks),
        "n_P_transactions": n_total,
        "timing_class_counts": count,
        "timing_class_dollars": {k: round(v, 0) for k, v in dollars.items()},
        "p_transactions": p_transactions,
        "signal": signal,
    }


if __name__ == "__main__":
    import json
    # ABG — known to have CEO post-Q4-print code-P buying
    print("ABG (Asbury Auto):")
    r = query_insider_buy_timing("0001144980", "2026-05-26", lookback_days=400)
    # Compact print
    print(json.dumps({k: v for k, v in r.items() if k != "p_transactions"}, indent=2))
    print(f"\np_transactions ({len(r.get('p_transactions',[]))}):")
    for tx in r.get("p_transactions", [])[:10]:
        print(f"  {tx['tx_date']}  {tx['owner']:30}  {tx['timing_class']:20}  ${tx['dollars']:,.0f}")
