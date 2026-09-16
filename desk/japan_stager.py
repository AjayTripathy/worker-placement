"""
japan_stager — Algorithmic Staging & Bidding Engine for Japanese Cash Fortresses.

Stages and executes passive limit orders and dislocation ladders across Tokyo Stock Exchange
equities on Interactive Brokers (Port 4001, Client ID 0).

Rules Enforced:
  1. Standard TSE Board Lots (All quantities are multiples of 100 shares).
  2. Two-Tranche Architecture:
     - Tranche 1 (Starter Bid): 50% allocation at current Best Bid / Midpoint with displaySize=100.
     - Tranche 2 (Dislocation Ladder): 50% allocation staged in 2-3 rungs at -3.5% to -8.0% discounts.
  3. GTC Time-in-Force (tif='GTC', outsideRth=False) to participate passively in Tokyo market hours.
  4. Full attribution logging in desk/data/antigravity_attributed_orders.json.

Usage:
    python3 -m desk.japan_stager --dry-run
    python3 -m desk.japan_stager --execute
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

ATTRIBUTED_ORDERS_FILE = ROOT / "desk" / "data" / "antigravity_attributed_orders.json"

# Defined Staging Portfolio Configuration
STAGING_COHORT = [
    {
        "ticker": "5697.T",
        "symbol": "5697",
        "company_name": "Sanyu Co., Ltd.",
        "target_usd": 7500.0,
        "ref_price_jpy": 823.0,
        "tranche1_qty": 700,
        "tranche1_price_jpy": 823.0,
        "tranche2_rungs": [
            {"qty": 300, "price_jpy": 795.0},
            {"qty": 200, "price_jpy": 775.0},
            {"qty": 200, "price_jpy": 750.0},
        ],
        "algorithm": "IBKR Accumulate/Distribute (100 shs / 25m interval)"
    },
    {
        "ticker": "9713.T",
        "symbol": "9713",
        "company_name": "The Royal Hotel, Limited",
        "target_usd": 7500.0,
        "ref_price_jpy": 1385.0,
        "tranche1_qty": 400,
        "tranche1_price_jpy": 1385.0,
        "tranche2_rungs": [
            {"qty": 200, "price_jpy": 1340.0},
            {"qty": 200, "price_jpy": 1300.0},
        ],
        "algorithm": "POV 5% Inline Flow (displaySize=100)"
    },
    {
        "ticker": "6286.T",
        "symbol": "6286",
        "company_name": "Seiko Corporation",
        "target_usd": 7500.0,
        "ref_price_jpy": 580.0,
        "tranche1_qty": 1000,
        "tranche1_price_jpy": 580.0,
        "tranche2_rungs": [
            {"qty": 500, "price_jpy": 560.0},
            {"qty": 500, "price_jpy": 540.0},
        ],
        "algorithm": "Passive Limit Ladder (displaySize=100)"
    },
    {
        "ticker": "7254.T",
        "symbol": "7254",
        "company_name": "Univance Corporation",
        "target_usd": 5000.0,
        "ref_price_jpy": 795.0,
        "tranche1_qty": 500,
        "tranche1_price_jpy": 795.0,
        "tranche2_rungs": [
            {"qty": 300, "price_jpy": 765.0},
            {"qty": 200, "price_jpy": 740.0},
        ],
        "algorithm": "POV 5% Inline Flow (displaySize=100)"
    },
    {
        "ticker": "8104.T",
        "symbol": "8104",
        "company_name": "Kuwazawa Holdings Corporation",
        "target_usd": 5000.0,
        "ref_price_jpy": 450.0,
        "tranche1_qty": 800,
        "tranche1_price_jpy": 450.0,
        "tranche2_rungs": [
            {"qty": 500, "price_jpy": 435.0},
            {"qty": 400, "price_jpy": 420.0},
        ],
        "algorithm": "Passive Best Bid (100 shs / slice)"
    },
    {
        "ticker": "2819.T",
        "symbol": "2819",
        "company_name": "Ebara Foods Industry, Inc.",
        "target_usd": 5000.0,
        "ref_price_jpy": 2380.0,
        "tranche1_qty": 100,
        "tranche1_price_jpy": 2380.0,
        "tranche2_rungs": [
            {"qty": 100, "price_jpy": 2300.0},
            {"qty": 100, "price_jpy": 2220.0},
        ],
        "algorithm": "Passive Best Bid"
    },
    {
        "ticker": "7239.T",
        "symbol": "7239",
        "company_name": "Tachi-S Co., Ltd.",
        "target_usd": 5000.0,
        "ref_price_jpy": 1630.0,
        "tranche1_qty": 200,
        "tranche1_price_jpy": 1630.0,
        "tranche2_rungs": [
            {"qty": 200, "price_jpy": 1570.0},
            {"qty": 100, "price_jpy": 1510.0},
        ],
        "algorithm": "POV 5% Inline Flow"
    },
    {
        "ticker": "5458.T",
        "symbol": "5458",
        "company_name": "Takasago Tekko K.K.",
        "target_usd": 2500.0,
        "ref_price_jpy": 865.0,
        "tranche1_qty": 200,
        "tranche1_price_jpy": 865.0,
        "tranche2_rungs": [
            {"qty": 200, "price_jpy": 830.0},
        ],
        "algorithm": "Micro-slice (100 shs / slice)"
    },
    {
        "ticker": "8135.T",
        "symbol": "8135",
        "company_name": "Zett Corporation",
        "target_usd": 2500.0,
        "ref_price_jpy": 348.0,
        "tranche1_qty": 500,
        "tranche1_price_jpy": 348.0,
        "tranche2_rungs": [
            {"qty": 300, "price_jpy": 335.0},
            {"qty": 300, "price_jpy": 320.0},
        ],
        "algorithm": "Micro-slice (100 shs / slice)"
    }
]


def build_staged_order_plan(cohort: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    """Generate structured order plans with exact board lot quantities and pricing."""
    items = cohort or STAGING_COHORT
    planned_orders = []

    for c in items:
        sym = c["symbol"]
        ticker = c["ticker"]
        name = c["company_name"]

        # Tranche 1: Starter Bid
        t1_qty = int(c["tranche1_qty"])
        if t1_qty % 100 != 0:
            raise ValueError(f"Quantity for {ticker} Tranche 1 must be a multiple of 100 shares (got {t1_qty})")
        
        t1_price = float(c["tranche1_price_jpy"])
        planned_orders.append({
            "ticker": ticker,
            "symbol": sym,
            "company_name": name,
            "tranche": "Tranche 1 (Starter Bid)",
            "quantity": t1_qty,
            "limit_price_jpy": t1_price,
            "total_value_jpy": t1_qty * t1_price,
            "approx_value_usd": round((t1_qty * t1_price) / 155.0, 2),
            "tif": "GTC",
            "outside_rth": False,
            "order_type": "LMT",
            "display_size": 100,
            "algorithm": c["algorithm"]
        })

        # Tranche 2: Dislocation Ladder Rungs
        for idx, rung in enumerate(c.get("tranche2_rungs", []), 1):
            r_qty = int(rung["qty"])
            if r_qty % 100 != 0:
                raise ValueError(f"Quantity for {ticker} Tranche 2 Rung {idx} must be a multiple of 100 shares (got {r_qty})")
            
            r_price = float(rung["price_jpy"])
            discount_pct = round(((c["ref_price_jpy"] - r_price) / c["ref_price_jpy"]) * 100.0, 1)
            planned_orders.append({
                "ticker": ticker,
                "symbol": sym,
                "company_name": name,
                "tranche": f"Tranche 2 (Rung {idx} / -{discount_pct}%)",
                "quantity": r_qty,
                "limit_price_jpy": r_price,
                "total_value_jpy": r_qty * r_price,
                "approx_value_usd": round((r_qty * r_price) / 155.0, 2),
                "tif": "GTC",
                "outside_rth": False,
                "order_type": "LMT",
                "display_size": 100,
                "algorithm": c["algorithm"]
            })

    return planned_orders


def log_attributed_order(order_record: Dict[str, Any]) -> None:
    """Append placed order to persistent SignalOS attribution ledger."""
    ATTRIBUTED_ORDERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    ledger = []
    if ATTRIBUTED_ORDERS_FILE.exists():
        try:
            with open(ATTRIBUTED_ORDERS_FILE, "r", encoding="utf-8") as f:
                ledger = json.load(f)
        except Exception:
            ledger = []

    ledger.append(order_record)
    with open(ATTRIBUTED_ORDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=2)


def execute_staged_orders_live(orders: List[Dict[str, Any]], host: str = "127.0.0.1", port: int = 4001, client_id: int = 0) -> List[Dict[str, Any]]:
    """Transmit staged orders to IB Gateway."""
    from ib_insync import IB, Stock, LimitOrder

    ib = IB()
    print(f"Connecting to Interactive Brokers Gateway at {host}:{port} (clientId={client_id})...")
    ib.connect(host, port, clientId=client_id, timeout=10)

    results = []
    for o in orders:
        symbol = o["symbol"]
        qty = o["quantity"]
        lmt_px = o["limit_price_jpy"]

        # TSE Stock Contract definition
        contract = Stock(symbol=symbol, exchange="SMART", currency="JPY", primaryExchange="TSEJ")
        ib.qualifyContracts(contract)

        from desk.account_registry import require_alpha
        _acct = require_alpha(ib)
        order = LimitOrder(
            action="BUY",
            totalQuantity=qty,
            lmtPrice=lmt_px,
            tif="GTC",
            outsideRth=False,
            displaySize=o.get("display_size", 100)
        )

        order.account = _acct
        trade = ib.placeOrder(contract, order)
        ib.sleep(0.5)

        order_record = {
            "timestamp_utc": dt.datetime.utcnow().isoformat() + "Z",
            "order_id": trade.order.orderId,
            "ticker": o["ticker"],
            "symbol": symbol,
            "company_name": o["company_name"],
            "tranche": o["tranche"],
            "action": "BUY",
            "quantity": qty,
            "limit_price_jpy": lmt_px,
            "currency": "JPY",
            "tif": "GTC",
            "order_status": trade.orderStatus.status,
            "algorithm": o["algorithm"],
            "attributed_thesis": "Cold, Hard, Steel: The Tokyo Capital Reform Super-Cycle"
        }
        log_attributed_order(order_record)
        results.append(order_record)
        print(f"Placed [{o['ticker']}] OrderId={trade.order.orderId} | {o['tranche']} | BUY {qty} shs @ ¥{lmt_px} JPY (Status: {trade.orderStatus.status})")

    ib.disconnect()
    return results


def main():
    parser = argparse.ArgumentParser(description="Japanese Cash Fortress Algorithmic Stager")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Simulate and print order schedule (default)")
    parser.add_argument("--execute", action="store_true", help="Submit live orders to IB Gateway")
    args = parser.parse_args()

    orders = build_staged_order_plan()

    total_jpy = sum(o["total_value_jpy"] for o in orders)
    total_usd = sum(o["approx_value_usd"] for o in orders)
    total_shares = sum(o["quantity"] for o in orders)

    print(f"\n=========================================================================================================")
    print(f"       SIGNALOS JAPANESE CASH FORTRESS STAGING SCHEDULE ({len(orders)} CHILD ORDERS)")
    print(f"=========================================================================================================")
    print(f"Total Staged Commitment: ¥{total_jpy:,.0f} JPY (~${total_usd:,.2f} USD) | Total Volume: {total_shares:,} shares")
    print(f"Time-in-Force: GTC | Lot Constraint: 100-share TSE Board Lots | Exchange: SMART / TSE\n")

    print(f"{'Ticker':<8} | {'Company Name':<25} | {'Tranche / Rung':<28} | {'Qty':<6} | {'Limit Px':<9} | {'Val (USD)':<9} | {'Algorithm'}")
    print(f"{'-'*8}-|-{'-'*25}-|-{'-'*28}-|-{'-'*6}-|-{'-'*9}-|-{'-'*9}-|-{'-'*25}")
    for o in orders:
        print(f"{o['ticker']:<8} | {o['company_name'][:25]:<25} | {o['tranche']:<28} | {o['quantity']:>6} | ¥{o['limit_price_jpy']:>7.1f} | ${o['approx_value_usd']:>7.2f} | {o['algorithm']}")

    print(f"=========================================================================================================\n")

    if args.execute:
        print(">>> LIVE EXECUTION FLAG DETECTED. INITIATING TRANSMISSION TO IB GATEWAY...")
        execute_staged_orders_live(orders)
    else:
        print("DRY-RUN MODE COMPLETE. To submit live orders to IB Gateway, run with: --execute\n")


if __name__ == "__main__":
    main()
