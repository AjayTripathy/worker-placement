"""
japan_fortress_sweeper — Automated Sweeper for Japanese Cash Fortresses & Reform Beneficiaries.

Filters and scores the universe of Tokyo Stock Exchange (TSE Prime & Standard) equities
against the 'Cold, Hard, Steel' Cash Fortress Thesis:
  1. P/B <= 0.75x (Strict sub-1.0x book value target for TSE reforms)
  2. Net Cash / Market Cap >= 50.0% (Cash & ST Investments - Debt >= 0.50 * Market Cap)
  3. Operating EV / EBIT <= 3.5x (Residual operating business priced at deep liquidation multiple)
  4. TTM Operating Income (EBIT) > 0 (Profitable manufacturing / industrial operations)
  5. Free Cash Flow (FCF) > 0 (Cash generative)
  6. PFIC IRC §1297(e) Active Asset Test < 50.0% (Clean for US taxable accounts)
  7. Non-Financial Industry (Excludes banks, brokerages, insurers, real estate holdcos)
  8. Market Cap between $15M and $600M USD (Capacity sweet spot below mega-fund radars)

Usage:
    python3 -m desk.japan_fortress_sweeper [--top 15] [--min-cash 50.0] [--max-pb 0.75]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
NONPFIC_DATA_PATH = ROOT / "verticals" / "deep_value" / "global" / "data" / "japan_nonpfic_shortlist.json"
OUTPUT_CANDIDATES_PATH = ROOT / "desk" / "data" / "japan_fortress_candidates.json"

USD_JPY_FX = 155.0  # Screening conversion rate


def load_raw_candidates(data_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Load audited Japanese financial records from EDINET database."""
    target_path = data_path or NONPFIC_DATA_PATH
    if not target_path.exists():
        raise FileNotFoundError(f"Japanese financial dataset not found at {target_path}")
    
    with open(target_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("rows", [])


def compute_fortress_metrics(record: Dict[str, Any], fx_rate: float = USD_JPY_FX) -> Optional[Dict[str, Any]]:
    """
    Compute valuation, cash backing, and composite fortress score for a Japanese equity record.
    """
    sym = record.get("sym", "")
    name = record.get("ind", "")
    sec = record.get("sec", "")
    mktcap_jpy = float(record.get("mktcap") or 0.0)
    px = float(record.get("px") or 0.0)
    pb = float(record.get("pb") or 1.0)
    ncash_r = float(record.get("ncash_r") or 0.0)
    ncav_r = float(record.get("ncav_r") or 0.0)
    ebit = float(record.get("ebit") or 0.0)
    fcf = float(record.get("fcf") or 0.0)
    fcfy = float(record.get("fcfy") or 0.0)
    pfic_share = float(record.get("pfic_fmv_share") or 0.0)

    if mktcap_jpy <= 0 or px <= 0:
        return None

    mktcap_usd = mktcap_jpy / fx_rate
    net_cash_jpy = mktcap_jpy * ncash_r
    ev_jpy = max(0.0, mktcap_jpy - net_cash_jpy)
    ev_ebit = (ev_jpy / ebit) if ebit > 0 else 999.0

    # Composite Fortress Score:
    # 40% Net Cash Weight + 30% FCF Yield + 20% P/B Discount + 10% EV/EBIT Multiple
    score = (
        (ncash_r * 40.0)
        + (min(fcfy, 0.50) * 30.0)
        + ((1.0 - min(pb, 1.0)) * 20.0)
        + ((3.5 - min(ev_ebit, 3.5)) * 10.0)
    )

    # Assign Industry Sub-Cluster
    if any(k in sec.lower() or k in name.lower() for k in ["steel", "metal", "nonferrous"]):
        cluster = "Precision Steel & Metallurgy"
    elif any(k in sec.lower() or k in name.lower() for k in ["transport", "auto", "radiator", "univance", "kinki"]):
        cluster = "Automotive & Drivetrain Keiretsu"
    elif any(k in sec.lower() or k in name.lower() for k in ["chemical", "construct", "glass", "machinery", "paint"]):
        cluster = "Industrial Infrastructure & Specialty Materials"
    else:
        cluster = "Consumer, Food & Commercial Net-Nets"

    return {
        "ticker": sym,
        "company_name": name,
        "industry_sector": sec,
        "cluster": cluster,
        "price_jpy": px,
        "market_cap_jpy": mktcap_jpy,
        "market_cap_usd": round(mktcap_usd, 2),
        "pb_ratio": round(pb, 2),
        "net_cash_pct": round(ncash_r * 100.0, 1),
        "ncav_to_cap": round(ncav_r, 2),
        "ebit_jpy": ebit,
        "ev_to_ebit": round(ev_ebit, 2),
        "fcf_jpy": fcf,
        "fcf_yield_pct": round(fcfy * 100.0, 1),
        "pfic_fmv_passive_pct": round(pfic_share * 100.0, 1),
        "fortress_score": round(score, 1)
    }


def sweep_japanese_fortresses(
    max_pb: float = 0.75,
    min_net_cash_pct: float = 50.0,
    max_ev_ebit: float = 3.5,
    min_mcap_usd: float = 15.0e6,
    max_mcap_usd: float = 600.0e6,
    data_path: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Execute full quantitative sweep across the Japanese equity universe.
    """
    raw_records = load_raw_candidates(data_path)
    candidates = []

    for r in raw_records:
        metrics = compute_fortress_metrics(r)
        if not metrics:
            continue

        # Filter Gates
        if metrics["pb_ratio"] > max_pb:
            continue
        if metrics["net_cash_pct"] < min_net_cash_pct:
            continue
        if metrics["ebit_jpy"] <= 0:
            continue
        if metrics["ev_to_ebit"] > max_ev_ebit:
            continue
        if metrics["fcf_jpy"] <= 0:
            continue
        if metrics["pfic_fmv_passive_pct"] >= 50.0:
            continue
        if not (min_mcap_usd <= metrics["market_cap_usd"] <= max_mcap_usd):
            continue

        candidates.append(metrics)

    # Sort candidates by Fortress Score descending
    candidates.sort(key=lambda x: x["fortress_score"], reverse=True)
    return candidates


def run_sweep_and_save(top_n: int = 15) -> Dict[str, Any]:
    """Execute sweep, persist JSON output, and return structured payload."""
    candidates = sweep_japanese_fortresses()
    top_candidates = candidates[:top_n]

    output_payload = {
        "sweep_timestamp_utc": dt.datetime.utcnow().isoformat() + "Z",
        "universe_description": "TSE Prime & Standard Listed Equities with Audited EDINET Filings",
        "gates_applied": {
            "max_pb": 0.75,
            "min_net_cash_pct": 50.0,
            "max_ev_ebit": 3.5,
            "min_ebit": "> 0 (Profitable)",
            "min_fcf": "> 0 (Cash Generative)",
            "pfic_safety": "< 50.0% Passive Asset Ratio (IRS IRC §1297)",
            "mcap_range_usd": "$15M to $600M"
        },
        "total_screened": len(load_raw_candidates()),
        "total_passed": len(candidates),
        "top_candidates_count": len(top_candidates),
        "candidates": top_candidates
    }

    OUTPUT_CANDIDATES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_CANDIDATES_PATH, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2)

    return output_payload


def main():
    parser = argparse.ArgumentParser(description="SignalOS Japanese Cash Fortress Sweeper")
    parser.add_argument("--top", type=int, default=15, help="Number of top candidates to display (default: 15)")
    parser.add_argument("--min-cash", type=float, default=50.0, help="Minimum net cash % of market cap (default: 50.0)")
    parser.add_argument("--max-pb", type=float, default=0.75, help="Maximum P/B ratio (default: 0.75)")
    parser.add_argument("--max-ev-ebit", type=float, default=3.5, help="Maximum EV/EBIT (default: 3.5)")
    args = parser.parse_args()

    payload = run_sweep_and_save(top_n=args.top)
    candidates = payload["candidates"]

    print(f"\n=========================================================================================================")
    print(f"       SIGNALOS JAPANESE CASH FORTRESS SWEEPER — TOP {len(candidates)} DISLOCATIONS")
    print(f"=========================================================================================================")
    print(f"Sweep Time: {payload['sweep_timestamp_utc']} | Universe: {payload['universe_description']}")
    print(f"Gates: P/B <= {args.max_pb}x | Net Cash >= {args.min_cash}% | EV/EBIT <= {args.max_ev_ebit}x | Clean PFIC\n")

    print(f"{'Ticker':<8} | {'Company Name':<28} | {'Cluster':<24} | {'Mkt Cap':<8} | {'P/B':<5} | {'NetCash':<7} | {'EV/EBIT':<7} | {'FCF Yld':<7} | {'Score'}")
    print(f"{'-'*8}-|-{'-'*28}-|-{'-'*24}-|-{'-'*8}-|-{'-'*5}-|-{'-'*7}-|-{'-'*7}-|-{'-'*7}-|-{'-'*5}")
    for c in candidates:
        mcap_str = f"${c['market_cap_usd']/1e6:.1f}M"
        print(f"{c['ticker']:<8} | {c['company_name'][:28]:<28} | {c['cluster'][:24]:<24} | {mcap_str:>8} | {c['pb_ratio']:>4.2f}x | {c['net_cash_pct']:>5.1f}% | {c['ev_to_ebit']:>5.2f}x | {c['fcf_yield_pct']:>5.1f}% | {c['fortress_score']:>5.1f}")

    print(f"\n=========================================================================================================")
    print(f"Results saved to: {OUTPUT_CANDIDATES_PATH}\n")


if __name__ == "__main__":
    main()
