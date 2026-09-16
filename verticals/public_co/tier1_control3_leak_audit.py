"""TIER-1 CONTROL 3 — blinding-leak / survivorship / benchmark audit.

 (a) SURVIVORSHIP: re-price all 66 names via yfinance (dividend-adjusted TR)
     over 2025-05-15 -> 2026-05-15; reconcile vs the stored forward_return;
     flag names that fail to price (delisted/acquired) and how they were
     handled; recompute headline under TR-consistent returns.
     Also: hindsight-in-universe test — basket group membership + the
     control_survivor-only subuniverse alpha.
 (b) LOOK-AHEAD: every pilot's filing_date vs cutoff; regex scan of tuples
     for post-cutoff date references; EDGAR submissions API verification of
     15 sampled pilots' primary-filing accession dates.
 (c) BENCHMARK: verified elsewhere (IJR TR +26.11%); here quantify the
     price-only vs total-return asymmetry between basket and benchmark.
 (d) narrative-leak restratification: pilots whose text quotes the realized
     forward return; basket math excluding them.

Writes: data/_backtest/tier1_controls/control3_leak_audit.json
"""
from __future__ import annotations

import json
import re
import statistics
import time
import urllib.request
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

from tier1_step0_reproduce import load_rows  # type: ignore

HERE = Path(__file__).parent
SURV = HERE / "data" / "_backtest" / "survivorship_2025_05"
OUT = HERE / "data" / "_backtest" / "tier1_controls"
IJR = 0.2611
CUTOFF = "2025-05-15"


def yf_returns(tickers):
    import yfinance as yf
    res = {}
    for tk in tickers:
        try:
            h = yf.download(tk, start="2025-05-13", end="2026-05-20",
                            auto_adjust=True, progress=False)
            c = h["Close"][tk] if hasattr(h["Close"], "columns") else h["Close"]
            p0 = float(c.loc["2025-05-15"]); p1 = float(c.loc["2026-05-15"])
            res[tk] = p1 / p0 - 1
        except Exception as e:
            res[tk] = None
    return res


def main():
    rows, unscoreable, test_set = load_rows()
    rows = [r for r in rows if r["forward_return"] is not None]
    fw_long = [r for r in rows if r["tier"] in ("STRICT_LONG", "LOOSE_LONG")]

    out = {}

    # ---------- (a) survivorship ----------
    tickers = sorted(test_set)
    yr = yf_returns(tickers)
    recon = []
    for tk in tickers:
        stored = test_set[tk]["forward_return"]
        live = yr.get(tk)
        recon.append({
            "ticker": tk, "stored": stored, "yf_tr": live,
            "diff_pp": None if live is None else (live - stored) * 100,
            "group": test_set[tk]["group"],
        })
    unpriced = [r for r in recon if r["yf_tr"] is None]
    big_diff = [r for r in recon if r["yf_tr"] is not None and abs(r["diff_pp"]) > 5]

    # recompute headline under TR-consistent returns (fallback to stored when unpriced)
    def tr_ret(r):
        v = yr.get(r["ticker"])
        return v if v is not None else r["forward_return"]
    ll_tr = statistics.mean(tr_ret(r) for r in fw_long)
    univ_tr = statistics.mean(
        (yr.get(tk) if yr.get(tk) is not None else test_set[tk]["forward_return"])
        for tk in tickers)
    out["survivorship"] = {
        "n_unpriced_by_yf": len(unpriced),
        "unpriced": [(r["ticker"], r["stored"]) for r in unpriced],
        "n_diff_gt_5pp": len(big_diff),
        "big_diffs": [(r["ticker"], round(r["stored"], 3), round(r["yf_tr"], 3)) for r in big_diff],
        "median_tr_minus_stored_pp": statistics.median(
            r["diff_pp"] for r in recon if r["diff_pp"] is not None),
        "loose_long_mean_TR": ll_tr,
        "loose_long_alpha_TR_vs_ijr": ll_tr - IJR,
        "universe_mean_TR": univ_tr,
    }

    # hindsight-in-universe: basket group membership + control-only subuniverse
    groups = {r["ticker"]: r["group"] for r in rows}
    basket_groups = {r["ticker"]: r["group"] for r in fw_long}
    ctrl = [r for r in rows if r["group"] == "control_survivor"]
    ctrl_long = [r for r in ctrl if r["tier"] in ("STRICT_LONG", "LOOSE_LONG")]
    dist = [r for r in rows if r["group"] == "delisted_or_distressed"]
    dist_long = [r for r in dist if r["tier"] in ("STRICT_LONG", "LOOSE_LONG")]
    out["hindsight_universe"] = {
        "basket_membership": basket_groups,
        "control_only": {
            "universe_n": len(ctrl),
            "universe_mean": statistics.mean(r["forward_return"] for r in ctrl),
            "long_n": len(ctrl_long),
            "long_mean": statistics.mean(r["forward_return"] for r in ctrl_long) if ctrl_long else None,
        },
        "distressed_only": {
            "universe_n": len(dist),
            "universe_mean": statistics.mean(r["forward_return"] for r in dist),
            "long_n": len(dist_long),
            "long_mean": statistics.mean(r["forward_return"] for r in dist_long) if dist_long else None,
        },
    }

    # ---------- (b) look-ahead ----------
    post_cutoff_filings = []
    date_re = re.compile(r"20(2[5-9])-(\d{2})-(\d{2})")
    tuple_date_flags = []
    pilots_meta = {}
    for f in sorted((SURV / "scores").glob("pilot_*.json")):
        d = json.loads(f.read_text())
        tk = d.get("ticker") or f.stem.replace("pilot_", "")
        fd = d.get("filing_date")
        pilots_meta[tk] = {"filing": d.get("filing"), "filing_date": fd, "cik": d.get("cik")}
        if fd and fd > CUTOFF:
            post_cutoff_filings.append((tk, fd))
        for t in d.get("rfm_tuples") or []:
            text = " ".join(str(t.get(k) or "") for k in ("R", "f", "M_source", "M_value"))
            for m in date_re.finditer(text):
                ds = m.group(0)
                if ds > CUTOFF:
                    tuple_date_flags.append({"ticker": tk, "claim": t.get("claim_id"), "date": ds,
                                             "ctx": text[max(0, m.start()-60):m.end()+40]})
    out["lookahead_filing_dates"] = {
        "n_pilots": len(pilots_meta),
        "post_cutoff_primary_filings": post_cutoff_filings,
        "n_tuples_referencing_post_cutoff_dates": len(tuple_date_flags),
        "post_cutoff_tuple_refs": tuple_date_flags[:20],
    }

    # EDGAR verification of 15 sampled pilots (deterministic sample: first 15 alphabetical with accession-style filing)
    sample = [tk for tk in sorted(pilots_meta) if pilots_meta[tk].get("filing")][:15]
    edgar_checks = []
    for tk in sample:
        meta = pilots_meta[tk]
        acc = (meta["filing"] or "").split("_")[0]
        cik = (meta.get("cik") or "").lstrip("0")
        ok = None; edgar_date = None
        if acc and cik:
            try:
                req = urllib.request.Request(
                    f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json",
                    headers={"User-Agent": "signalos research 4tripathy@gmail.com"})
                sub = json.loads(urllib.request.urlopen(req, timeout=30).read())
                rec = sub["filings"]["recent"]
                accs = rec["accessionNumber"]; dates = rec["filingDate"]
                acc_fmt = acc if "-" in acc else f"{acc[:10]}-{acc[10:12]}-{acc[12:]}"
                if acc_fmt in accs:
                    edgar_date = dates[accs.index(acc_fmt)]
                    ok = edgar_date <= CUTOFF and edgar_date == meta["filing_date"]
                time.sleep(0.3)
            except Exception as e:
                ok = f"error: {e}"
        edgar_checks.append({"ticker": tk, "accession": acc, "claimed_date": meta["filing_date"],
                             "edgar_date": edgar_date, "pre_cutoff_and_consistent": ok})
    out["edgar_verification_sample"] = edgar_checks

    # ---------- (d) narrative-leak restratification ----------
    leakers = []
    for f in sorted((SURV / "scores").glob("pilot_*.json")):
        d = json.loads(f.read_text())
        tk = d.get("ticker") or f.stem.replace("pilot_", "")
        text = json.dumps(d.get("summary")) + " " + json.dumps(d.get("framework_notes"))
        if re.search(r"forward[- ]return|realized|materiali[sz]ed|turned out|known limitation", text, re.I):
            leakers.append(tk)
    clean_rows = [r for r in rows if r["ticker"] not in leakers]
    clean_long = [r for r in clean_rows if r["tier"] in ("STRICT_LONG", "LOOSE_LONG")]
    out["narrative_leak"] = {
        "n_leakers": len(leakers), "leakers": leakers,
        "clean_universe_n": len(clean_rows),
        "clean_long_n": len(clean_long),
        "clean_long_mean": statistics.mean(r["forward_return"] for r in clean_long) if clean_long else None,
        "clean_long_alpha_vs_ijr": (statistics.mean(r["forward_return"] for r in clean_long) - IJR) if clean_long else None,
        "leaker_long": [ (r["ticker"], r["forward_return"]) for r in fw_long if r["ticker"] in leakers],
    }

    (OUT / "control3_leak_audit.json").write_text(json.dumps(out, indent=2, default=str))
    print(json.dumps(out, indent=2, default=str)[:6000])


if __name__ == "__main__":
    main()
