"""insider_drift_backtest — PRE-REGISTERED validation of the insider-cluster generator's conditioned subset.

=== PRE-REGISTRATION (declared 2026-07-02, BEFORE any result was computed) ===
HYPOTHESIS (H1): clusters of >=2 DISTINCT insiders each making code-P open-market buys >= $50k within a
7-day window show POSITIVE excess drift vs the small-cap benchmark (IWM) over the following 3 months,
and the effect is CONCENTRATED in smaller names (below-median market cap of the cluster universe).
NULL (H0): excess drift ~ 0 -> the signal is fully priced; the scanner is then demoted (honestly) to pure
attention-allocation, weighted only by whether its seeds survive our trap-screen at above-random rates.
METRICS: mean + median excess return at +21/+63/+126 trading days; hit rate; N; small-vs-large split.
DECISION RULE: H1 supported iff median +63d excess > +1.5% AND hit rate > 53% AND N >= 60. Anything less =
NULL. No re-slicing after the fact; the size split is the ONLY conditioning cut examined.
CAVEATS DECLARED UP FRONT: (a) size split uses CURRENT market cap (survivor/growth-biased proxy — the
dataset lacks point-in-time mcap); (b) tickers that died/delisted drop out of yfinance -> survivorship bias
INFLATES drift, so a positive result is an UPPER bound; a null result is therefore especially credible.
===============================================================================

Data: SEC quarterly insider-transaction bulk sets (NONDERIV_TRANS + SUBMISSION TSVs), 2023Q1..latest.
Prices: yfinance daily, excess vs IWM. Run in background; ~13 zips + a few hundred price series.

  python3 verticals/generators/insider_drift_backtest.py
Writes data/INSIDER_DRIFT_BACKTEST.json. READ-ONLY.
"""
from __future__ import annotations
import json, io, csv, zipfile, datetime, statistics, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "data" / "INSIDER_DRIFT_BACKTEST.json"
RAW = HERE / "data" / "insider_bulk"
RAW.mkdir(parents=True, exist_ok=True)
URL = "https://www.sec.gov/files/structureddata/data/insider-transactions-data-sets/{}_form345.zip"
HDRS = {"User-Agent": "signalos-research 4tripathy@gmail.com"}
QUARTERS = [f"{y}q{q}" for y in (2023, 2024, 2025) for q in (1, 2, 3, 4)] + ["2026q1"]
MIN_BUY, WINDOW_D = 50_000, 7
HORIZONS = {"h21": 21, "h63": 63, "h126": 126}


def _dl(q: str) -> Path | None:
    f = RAW / f"{q}.zip"
    if f.exists() and f.stat().st_size > 1e6:
        return f
    try:
        req = urllib.request.Request(URL.format(q), headers=HDRS)
        with urllib.request.urlopen(req, timeout=300) as r:
            f.write_bytes(r.read())
        return f
    except Exception:
        return None


def _tsv(zf: zipfile.ZipFile, name: str):
    """Yield rows (generator keeps the member open during iteration — returning a reader closed it: 0-event bug)."""
    with zf.open(name) as fh:
        for row in csv.DictReader(io.TextIOWrapper(fh, "latin-1"), delimiter="\t"):
            yield row


def _d(s: str) -> datetime.date:
    """SEC bulk dates are '31-JAN-2024'."""
    return datetime.datetime.strptime(s.strip(), "%d-%b-%Y").date()


def _quarter_buys(q: str) -> list[dict]:
    f = _dl(q)
    if not f:
        return []
    try:
        zf = zipfile.ZipFile(f)
        subs = {}
        for r in _tsv(zf, "SUBMISSION.tsv"):
            subs[r["ACCESSION_NUMBER"]] = {"sym": (r.get("ISSUERTRADINGSYMBOL") or "").upper().strip(),
                                           "filed": r.get("FILING_DATE", "").strip()}
        buys = {}
        for r in _tsv(zf, "NONDERIV_TRANS.tsv"):
            if (r.get("TRANS_CODE") or "") != "P" or (r.get("TRANS_ACQUIRED_DISP_CD") or "") != "A":
                continue
            try:
                usd = float(r.get("TRANS_SHARES") or 0) * float(r.get("TRANS_PRICEPERSHARE") or 0)
            except ValueError:
                continue
            if usd < MIN_BUY:
                continue
            acc = r["ACCESSION_NUMBER"]
            sub = subs.get(acc)
            if not sub or not sub["sym"] or "." in sub["sym"] or len(sub["sym"]) > 5:
                continue
            b = buys.setdefault(acc, {"sym": sub["sym"], "filed": sub["filed"], "usd": 0.0})
            b["usd"] += usd
        # one row per FILING (accession) = one insider event; owner distinctness ~= distinct accessions
        return list(buys.values())
    except Exception:
        return []


def build_clusters() -> list[dict]:
    events = []
    for q in QUARTERS:
        events.extend(_quarter_buys(q))
    events.sort(key=lambda e: (e["sym"], _d(e["filed"])))
    by_sym = {}
    for e in events:
        by_sym.setdefault(e["sym"], []).append(e)
    clusters = []
    for sym, evs in by_sym.items():
        i = 0
        while i < len(evs):
            d0 = _d(evs[i]["filed"])
            grp = [evs[i]]
            j = i + 1
            while j < len(evs) and (_d(evs[j]["filed"]) - d0).days <= WINDOW_D:
                grp.append(evs[j])
                j += 1
            if len(grp) >= 2:
                clusters.append({"sym": sym, "date": _d(grp[-1]["filed"]).isoformat(), "n_filings": len(grp),
                                 "total_usd": round(sum(g["usd"] for g in grp))})
                i = j
            else:
                i += 1
    return clusters


def drift(clusters: list[dict]) -> dict:
    import yfinance as yf
    syms = sorted({c["sym"] for c in clusters})
    data = {}
    for i in range(0, len(syms), 80):
        chunk = syms[i:i + 80] + (["IWM"] if i == 0 else [])
        try:
            df = yf.download(chunk, start="2022-12-01", progress=False, auto_adjust=True)["Close"]
            for s in chunk:
                try:
                    ser = df[s].dropna()
                    if len(ser) > 100:
                        data[s] = ser
                except Exception:
                    pass
        except Exception:
            pass
    bench = data.get("IWM")
    if bench is None:
        return {"error": "no benchmark series"}
    rows, dropped = [], 0
    for c in clusters:
        s = data.get(c["sym"])
        if s is None:
            dropped += 1
            continue
        d = datetime.date.fromisoformat(c["date"])
        idx = [i for i, dt in enumerate(s.index.date) if dt >= d]
        bidx = [i for i, dt in enumerate(bench.index.date) if dt >= d]
        if not idx or not bidx:
            dropped += 1
            continue
        i0, b0 = idx[0], bidx[0]
        r = dict(c)
        ok = False
        for k, h in HORIZONS.items():
            if i0 + h < len(s) and b0 + h < len(bench):
                ret = float(s.iloc[i0 + h] / s.iloc[i0] - 1) * 100
                bret = float(bench.iloc[b0 + h] / bench.iloc[b0] - 1) * 100
                r[k] = round(ret - bret, 2)
                ok = True
        if ok:
            # current-mcap size proxy (declared caveat)
            rows.append(r)
        else:
            dropped += 1
    # size split by CURRENT mcap
    caps = {}
    for i in range(0, len(syms), 40):
        for s in syms[i:i + 40]:
            if s in data:
                try:
                    caps[s] = yf.Ticker(s).fast_info.get("marketCap")
                except Exception:
                    pass
    valid_caps = sorted(v for v in caps.values() if v)
    med = valid_caps[len(valid_caps) // 2] if valid_caps else None
    for r in rows:
        c = caps.get(r["sym"])
        r["size"] = ("small" if c and med and c < med else "large" if c else "unknown")

    def stats(rs, key):
        vals = [r[key] for r in rs if key in r]
        if len(vals) < 10:
            return None
        return {"n": len(vals), "mean": round(statistics.mean(vals), 2), "median": round(statistics.median(vals), 2),
                "hit_rate_pct": round(100 * sum(1 for v in vals if v > 0) / len(vals))}
    res = {"clusters_total": len(clusters), "clusters_priced": len(rows), "dropped_no_price": dropped,
           "survivorship_note": f"{dropped} clusters dropped (dead/unpriceable tickers) — drift is an UPPER bound",
           "all": {k: stats(rows, k) for k in HORIZONS},
           "small": {k: stats([r for r in rows if r["size"] == "small"], k) for k in HORIZONS},
           "large": {k: stats([r for r in rows if r["size"] == "large"], k) for k in HORIZONS}}
    # the pre-registered decision
    m63 = (res["small"].get("h63") or {})
    supported = bool(m63 and m63["median"] > 1.5 and m63["hit_rate_pct"] > 53 and m63["n"] >= 60)
    res["preregistered_decision"] = ("H1 SUPPORTED (small-cap conditioned subset)" if supported else
                                     "NULL — no validated drift; scanner demoted to attention-allocation only")
    return res


def main():
    print("building clusters from SEC bulk sets (13 quarters)...")
    clusters = build_clusters()
    print(f"clusters found: {len(clusters)}  (pricing + drift next)")
    res = drift(clusters)
    res["asof"] = datetime.date.today().isoformat()
    OUT.write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != "survivorship_note"}, indent=1)[:1800])
    print(f"[-> {OUT.name}]")


if __name__ == "__main__":
    main()
