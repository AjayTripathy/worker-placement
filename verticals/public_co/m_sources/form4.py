"""Form 4 insider transactions — parse raw ownership.xml per filing."""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": [],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": True,
    "kind": "m_source",
    "summary": "Form 4 insider-transaction parser; raw ownership data for any US filer.",
}

import json
import re
import time
from pathlib import Path

from ..edgar import fetch_form4_xml


def parse_insider_sales(filings_index_path: Path, cik: str) -> dict:
    """Read filings_index.json, fetch ownership.xml for each Form 4, parse
    non-derivative transactions, aggregate sales (tx_code='S') by owner."""
    idx = json.loads(filings_index_path.read_text())
    form4s = [r for r in idx if r["form"] == "4"]
    cik_int = cik.lstrip("0")

    sales: list[dict] = []
    n_xml_fetched = 0
    for f4 in form4s:
        txt = fetch_form4_xml(cik_int, f4["accession"], f4.get("primary_document", ""))
        if txt is None:
            continue
        n_xml_fetched += 1
        time.sleep(0.15)

        owner_m = re.search(r"<rptOwnerName>([^<]+)</rptOwnerName>", txt)
        title_m = re.search(r"<officerTitle>([^<]+)</officerTitle>", txt)
        is_director = "<isDirector>1</isDirector>" in txt
        is_officer = "<isOfficer>1</isOfficer>" in txt
        is_10pct = "<isTenPercentOwner>1</isTenPercentOwner>" in txt

        for tx_block in re.finditer(
            r"<nonDerivativeTransaction>(.*?)</nonDerivativeTransaction>", txt, re.DOTALL
        ):
            blk = tx_block.group(1)
            d = re.search(r"<transactionDate>\s*<value>([^<]+)</value>", blk)
            code = re.search(r"<transactionCode>([^<]+)</transactionCode>", blk)
            shares = re.search(r"<transactionShares>\s*<value>([^<]+)</value>", blk)
            price = re.search(r"<transactionPricePerShare>\s*<value>([^<]+)</value>", blk)
            ad = re.search(r"<transactionAcquiredDisposedCode>\s*<value>([^<]+)</value>", blk)
            if not (owner_m and code):
                continue
            sales.append({
                "owner": owner_m.group(1),
                "officer_title": title_m.group(1) if title_m else None,
                "is_director": is_director,
                "is_officer": is_officer,
                "is_10pct": is_10pct,
                "filing_date": f4["filing_date"],
                "tx_date": d.group(1) if d else None,
                "tx_code": code.group(1).strip() if code else None,
                "shares": float(shares.group(1)) if shares else None,
                "price": float(price.group(1)) if price else None,
                "acquired_disposed": ad.group(1) if ad else None,
            })

    sales_only = [s for s in sales if s["tx_code"] == "S" and s["price"] and s["shares"]]
    for s in sales_only:
        s["proceeds_usd"] = s["shares"] * s["price"]

    by_owner: dict = {}
    for s in sales_only:
        o = s["owner"]
        by_owner.setdefault(o, {
            "total_shares_sold": 0,
            "total_proceeds": 0,
            "n_sales": 0,
            "officer_title": s.get("officer_title"),
        })
        by_owner[o]["total_shares_sold"] += s["shares"]
        by_owner[o]["total_proceeds"] += s["proceeds_usd"]
        by_owner[o]["n_sales"] += 1

    return {
        "total_form4_filings_pre_cutoff": len(form4s),
        "ownership_xml_fetched": n_xml_fetched,
        "total_transactions": len(sales),
        "sale_transactions": len(sales_only),
        "by_owner": dict(sorted(by_owner.items(), key=lambda x: -x[1]["total_proceeds"])),
        "top_sales": sorted(sales_only, key=lambda x: -x["proceeds_usd"])[:8],
    }
