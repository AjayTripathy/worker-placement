"""v3 — risk-managed AIRO-signature backtest.

Builds on v2 by adding two mechanical risk overlays:

  - Per-pair size cap: each pair is at most CAP_PCT of book (default 3%).
    Excess book sits in cash for the holding period.
  - Stop-loss on the short leg: if the name closes at >=(1+STOP_PCT) of
    entry on any trading day during the holding window, close BOTH legs
    of the pair at that close. Default STOP_PCT = 0.50 (close if name
    up 50%).

For each entry date in {2022, 2023, 2024, 2025}:
  - Read the v2 per-name results
  - Re-fetch daily price history for each in-band name
  - Detect first stop trigger; compute stopped-out pair P&L
    (sector ETF return at stop date, minus name return at stop date)
  - Aggregate as: portfolio P&L = sum(cap × pair_pnl_with_stop) +
                                  (1 - cap × n_pairs) × 0
"""
from __future__ import annotations

import json
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import pandas as pd
import yfinance as yf

HERE = Path(__file__).parent

STOP_PCT = 0.50
CAP_PCT  = 0.03


def fetch_daily(tk: str, entry: str, exit_: str) -> pd.DataFrame | None:
    try:
        h = yf.Ticker(tk).history(
            start=(pd.Timestamp(entry) - pd.Timedelta(days=10)).strftime("%Y-%m-%d"),
            end=(pd.Timestamp(exit_) + pd.Timedelta(days=10)).strftime("%Y-%m-%d"),
            auto_adjust=True,
        )
        return h if not h.empty else None
    except Exception:
        return None


def apply_stop(name_tk: str, etf_tk: str, entry: str, exit_: str,
               stop_pct: float = STOP_PCT) -> dict:
    """Return (stopped, stop_date, name_R, etf_R, pair_pnl_with_stop)."""
    nh = fetch_daily(name_tk, entry, exit_)
    eh = fetch_daily(etf_tk, entry, exit_)
    if nh is None or eh is None:
        return {"error": "no_price_data"}

    ent = pd.Timestamp(entry, tz=nh.index.tz)
    end = pd.Timestamp(exit_, tz=nh.index.tz)
    nh = nh.loc[(nh.index >= ent - pd.Timedelta(days=4)) & (nh.index <= end + pd.Timedelta(days=4))]
    eh = eh.loc[(eh.index >= ent - pd.Timedelta(days=4)) & (eh.index <= end + pd.Timedelta(days=4))]
    if nh.empty or eh.empty:
        return {"error": "empty_window"}

    # Entry prices (nearest)
    e_idx_n = nh.index.get_indexer([ent], method="nearest")[0]
    e_idx_e = eh.index.get_indexer([ent], method="nearest")[0]
    p_n_entry = float(nh.iloc[e_idx_n]["Close"])
    p_e_entry = float(eh.iloc[e_idx_e]["Close"])

    # Stop trigger: first close where p_name >= entry * (1 + stop_pct)
    trigger_threshold = p_n_entry * (1.0 + stop_pct)
    after_entry = nh.iloc[e_idx_n:]
    trigger_mask = after_entry["Close"] >= trigger_threshold
    if trigger_mask.any():
        stop_idx = trigger_mask.idxmax()  # first True
        p_n_stop = float(after_entry.loc[stop_idx]["Close"])
        # Find ETF price closest to stop_idx
        e_stop_idx = eh.index.get_indexer([stop_idx], method="nearest")[0]
        p_e_stop  = float(eh.iloc[e_stop_idx]["Close"])
        name_R = (p_n_stop / p_n_entry) - 1
        etf_R  = (p_e_stop / p_e_entry) - 1
        pair   = etf_R - name_R
        return {
            "stopped":      True,
            "stop_date":    str(stop_idx.date()),
            "name_return":  name_R,
            "etf_return":   etf_R,
            "pair_pnl":     pair,
        }

    # No stop — use exit close
    x_idx_n = nh.index.get_indexer([end], method="nearest")[0]
    x_idx_e = eh.index.get_indexer([end], method="nearest")[0]
    p_n_exit = float(nh.iloc[x_idx_n]["Close"])
    p_e_exit = float(eh.iloc[x_idx_e]["Close"])
    name_R = (p_n_exit / p_n_entry) - 1
    etf_R  = (p_e_exit / p_e_entry) - 1
    return {
        "stopped":      False,
        "stop_date":    None,
        "name_return":  name_R,
        "etf_return":   etf_R,
        "pair_pnl":     etf_R - name_R,
    }


def run_year(input_json: Path, entry_dt: str, exit_dt: str) -> dict:
    data = json.loads(input_json.read_text())
    rows = data.get("rows") if "rows" in data else data
    print(f"\n=== {entry_dt} → {exit_dt}  ({len(rows)} pairs) ===")

    risk_rows = []
    for i, r in enumerate(rows):
        tk = r["ticker"]
        etf = r.get("etf") or "IWM"
        res = apply_stop(tk, etf, entry_dt, exit_dt)
        if "error" in res:
            res = {"stopped": False, "pair_pnl": r.get("pair_pnl"), "error": res["error"]}
        risk_rows.append({
            "ticker":           tk,
            "etf":              etf,
            "sector":           r.get("sector"),
            "v2_pair_pnl":      r.get("pair_pnl"),
            **res,
        })
        if (i+1) % 10 == 0:
            print(f"  progress: {i+1}/{len(rows)}")
        time.sleep(0.05)

    return {
        "entry_dt": entry_dt,
        "exit_dt":  exit_dt,
        "rows":     risk_rows,
    }


def summarize(years: list[dict], cap_pct: float = CAP_PCT, stop_pct: float = STOP_PCT):
    import statistics
    print()
    print("=" * 96)
    print(f"v3 RISK-MANAGED SUMMARY  (cap={cap_pct*100:.0f}% per pair, stop={stop_pct*100:.0f}% on short)")
    print("=" * 96)

    for y in years:
        rows = y["rows"]
        if not rows: continue
        v2_pnls = [r["v2_pair_pnl"] for r in rows if r.get("v2_pair_pnl") is not None]
        v3_pnls = [r["pair_pnl"]    for r in rows if r.get("pair_pnl")    is not None]
        n_stopped = sum(1 for r in rows if r.get("stopped"))

        # Portfolio P&L = mean if equal-weight; with cap, scale by N×cap
        n = len(v3_pnls)
        deployed = min(1.0, n * cap_pct)
        port_v2 = statistics.mean(v2_pnls) if v2_pnls else 0
        port_v3 = statistics.mean(v3_pnls) if v3_pnls else 0
        port_v3_capped = port_v3 * deployed  # since rest is cash@0

        print(f"\n--- {y['entry_dt']} → {y['exit_dt']} ---")
        print(f"  n={n}   stopped: {n_stopped}/{n}")
        print(f"  v2 (no risk mgmt):    mean={port_v2*100:+7.2f}%  median={statistics.median(v2_pnls)*100:+7.2f}%")
        print(f"  v3 (stop @ {stop_pct*100:.0f}%):       mean={port_v3*100:+7.2f}%  median={statistics.median(v3_pnls)*100:+7.2f}%")
        print(f"  v3 portfolio ({cap_pct*100:.0f}% cap × {n} = {deployed*100:.0f}% deployed): {port_v3_capped*100:+7.2f}%")
        # Show stopped names + their impact
        if n_stopped > 0:
            print(f"  Names stopped out:")
            for r in [x for x in rows if x.get("stopped")]:
                print(f"    {r['ticker']:5s}/{r['etf']:5s} stop on {r['stop_date']}  "
                      f"name@stop={r['name_return']*100:+6.1f}%  etf@stop={r['etf_return']*100:+6.1f}%  "
                      f"pair={r['pair_pnl']*100:+6.1f}%  (v2 was {r['v2_pair_pnl']*100:+6.1f}%)")


def main():
    years = []
    for ent_yr, ent_dt in [("2022_05_15","2022-05-15"),
                           ("2023_05_15","2023-05-15"),
                           ("2024_05_15","2024-05-15")]:
        input_path = HERE / f"multi_year_{ent_yr}.json"
        if not input_path.exists():
            print(f"  missing {input_path}"); continue
        exit_dt = (pd.Timestamp(ent_dt) + pd.Timedelta(days=365)).strftime("%Y-%m-%d")
        y = run_year(input_path, ent_dt, exit_dt)
        years.append(y)
        (HERE / f"risk_managed_{ent_yr}.json").write_text(json.dumps(y, indent=2, default=str))

    # 2025 case: build from airo_signature_returns.json with sector mapping
    sig_path = HERE / "airo_signature_returns.json"
    if sig_path.exists():
        from_v1 = json.loads(sig_path.read_text())
        in_band = [x for x in from_v1 if x.get("mcap_entry") is not None
                                       and 100e6 <= (x["mcap_entry"] or 0) < 500e6
                                       and x.get("return") is not None]
        # Apply same sector mapping as v1 (manual)
        V1_MAP = {
            "LBUY":"MJ","VIVK":"XLE","GNPX":"XBI","CDIX":"IWM","WKHS":"DRIV",
            "WHEN":"ICLN","LVO":"XLC","HDSN":"XLI","GLTK":"IWM","PESI":"XLI",
            "CWCO":"XLU","BLNK":"DRIV","ALMU":"SMH","GLSI":"XBI","IMMX":"XBI",
        }
        synth = []
        for x in in_band:
            tk = x["ticker"]
            etf = V1_MAP.get(tk, "IWM")
            synth.append({
                "ticker":      tk,
                "etf":         etf,
                "sector":      None,
                "pair_pnl":    None,
                "v2_pair_pnl": None,  # will compute below if needed
            })
        # Synthesize v2_pair_pnl by re-fetching ETF return
        for x in synth:
            res = apply_stop(x["ticker"], x["etf"], "2025-05-15", "2026-05-15", stop_pct=99.0)
            if "error" not in res:
                x["v2_pair_pnl"] = res["pair_pnl"]
        y2025 = run_year_synth(synth, "2025-05-15", "2026-05-15")
        years.append(y2025)
        (HERE / "risk_managed_2025_05_15.json").write_text(json.dumps(y2025, indent=2, default=str))

    summarize(years)
    (HERE / "risk_managed_all.json").write_text(json.dumps(years, indent=2, default=str))


def run_year_synth(synth_rows: list[dict], entry_dt: str, exit_dt: str) -> dict:
    print(f"\n=== {entry_dt} → {exit_dt}  (synth from v1 data, {len(synth_rows)} pairs) ===")
    out = []
    for i, r in enumerate(synth_rows):
        res = apply_stop(r["ticker"], r["etf"], entry_dt, exit_dt)
        if "error" in res:
            res = {"stopped": False, "pair_pnl": r.get("v2_pair_pnl"), "error": res["error"]}
        out.append({**r, **res})
        time.sleep(0.05)
    return {"entry_dt": entry_dt, "exit_dt": exit_dt, "rows": out}


if __name__ == "__main__":
    main()
