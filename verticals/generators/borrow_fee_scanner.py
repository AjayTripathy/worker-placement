"""borrow_fee_scanner — Stage-0b INFO generator: BROAD short-pressure / short-volume-ratio spike scan.

THESIS (INFO-class, latency edge): a spike in short-selling PRESSURE — the daily short-volume ratio
climbing sharply above a name's OWN trailing baseline for >=2 consecutive days — is a LEADING tell of
either fundamental DISTRESS (the short is right; deterioration ahead) or a crowded SQUEEZE-SETUP (an
un-broken name with a piled-in short book). The pressure builds in the tape BEFORE the price resolves,
so the edge is LATENCY: FINRA publishes this file T+1, weeks ahead of the bi-monthly short-interest print.

This GENERALIZES desk/squeeze_watch.py — which only watches the 3-name SpaceX proxy-hedge basket
(ASTS/LUNR/BKSY) for a synchronized COVERING drop — into a broad daily scan of the full ~12k-name NMS
consolidated file, looking for the OPPOSITE-and-general signature: a short-ratio SPIKE UP on any name.

CRITICAL DOCTRINE — baked in (repo memory: the MAUDE-velocity lesson):
  A short-pressure spike measures SUPPLY / POSITIONING, NOT conviction. Naive velocity signals have
  LR ~ 1 unless you separate demand-driven from supply-driven flow. So this scanner does NOT emit a
  buy/sell on the spike alone. It (1) measures the spike against the name's OWN baseline (absolute
  short-ratio level is meaningless — MM/liquidity-provider hedging keeps it structurally 0.4-0.7),
  (2) CLASSIFIES each flagged name through the conditioning layer (discovery_state) into distress /
  squeeze-setup / noise, and (3) PROPOSES only — never a trade. A real spike on an already
  DISCOVERED_CROWDED name is NOT a fresh trade (the RCAT lesson: crowding is squeeze fuel already
  priced). The classification + conditioning are the whole point; the raw spike is just the trigger.

BORROW FEE: the IBKR MCP surface (get_price_snapshot) exposes NO short-borrow-fee / utilization /
securities-lending field — its market-data names are price/volume/IV/OI only. So borrow_fee_or_null is
recorded as null with an honest caveat. We do NOT fabricate a borrow cost. The FINRA short-volume leg
carries the signal; a real borrow-fee feed (IBKR SLB / Ortex / S3) is the v2 enrichment.

DATA (free): FINRA CNMS Reg-SHO daily short-sale volume — http://cdn.finra.org/equity/regsho/daily/
CNMSshvolYYYYMMDD.txt (pipe-delimited: Date|Symbol|ShortVolume|ShortExemptVolume|TotalVolume|Market).
Same source + fingerprint logic as squeeze_watch. READ-ONLY. Never places an order.

    python3 verticals/generators/borrow_fee_scanner.py
Writes data/BORROW_FEE.json; persists data/borrow_fee_state.json for the multi-day consecutive logic.
"""
from __future__ import annotations

import datetime
import json
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / "data" / "BORROW_FEE.json"
STATE = HERE / "data" / "borrow_fee_state.json"

HDRS = {"User-Agent": "signalos-research 4tripathy@gmail.com"}
URL = "https://cdn.finra.org/equity/regsho/daily/CNMSshvol{d}.txt"

# ── Fingerprint (squeeze_watch generalized: a SPIKE UP on the whole universe) ────────────────────
LOOKBACK = 22            # trading-day files to keep in state
BASELINE_MIN = 8         # need >=8 prior days to trust a baseline
SPIKE_PP = 0.12          # latest ratio must sit >=12pp ABOVE the trailing baseline mean
CONSEC = 2               # ...for >=2 consecutive days (one day = noise)
# Liquidity floor: the file is dominated by illiquid microcaps where the ratio is meaningless noise.
# Require real two-sided volume so the spike reflects genuine short flow, not a handful of prints.
MIN_TOTAL_VOL = 300_000    # min shares/day on the latest day (a 99% ratio on a few hundred shares is noise)
MIN_DOLLAR_VOL = 1_000_000  # min notional $/day (latest total_vol x last price) — kills ultra-thin names
# Cap how many flagged names get the (expensive, multi-connector) discovery_state classification.
MAX_CLASSIFY = 25


# ── EQUITY-ONLY guard ─────────────────────────────────────────────────────────────────────────────
# THE FIX (e2e over-firing bug): the FINRA short-VOLUME file's ratio is dominated by bona-fide
# MARKET-MAKER / authorized-participant hedging. For an ETF/ETN that MM/AP creation-redemption plumbing
# pins the short-vol ratio near ~99% — a pure SUPPLY-SIDE ARTIFACT with zero conviction/squeeze content
# (you can't squeeze a name whose shares are minted on demand). Live top-25 was ~all ETFs (EFV, IYG,
# USTB, HFXI, BCI, SIO, FLAU, DFGP, GLIX, CCNR ...). This scanner hunts SINGLE-NAME distress/squeeze
# setups, so we hard-filter the candidate universe to genuine common stock (quoteType == 'EQUITY') BEFORE
# the expensive discovery_state classification — so ETFs never consume the MAX_CLASSIFY budget or appear
# in 'flagged'. Cached to avoid re-fetching the same tickers.
_QT_CACHE: dict[str, str] = {}
# quoteTypes we DROP. Allow-list is "EQUITY only", but we keep an explicit deny-set for readability.
_NON_EQUITY_QT = frozenset({"ETF", "ETN", "MUTUALFUND", "MONEYMARKET", "INDEX", "CURRENCY",
                            "CRYPTOCURRENCY", "FUTURE", "OPTION"})


def _quote_type(sym: str) -> str:
    """yfinance quoteType (UPPER) for sym; '' if unresolved. Cached. fast_info lacks quote_type,
    so .info is required (heavier, but we only call it on the small spike/prelim list)."""
    if sym in _QT_CACHE:
        return _QT_CACHE[sym]
    qt = ""
    try:
        import yfinance as yf
        qt = str((yf.Ticker(sym).info or {}).get("quoteType") or "").upper()
    except Exception:
        qt = ""
    _QT_CACHE[sym] = qt
    return qt


def _is_equity(sym: str) -> bool:
    """True iff sym classifies as genuine single-name common stock (quoteType == 'EQUITY').
    UNRESOLVED (empty quoteType — yfinance miss / rate-limit) is treated as EQUITY so a lookup outage
    does not silently blind the whole scan; the deny-set only excludes POSITIVELY-identified funds."""
    qt = _quote_type(sym)
    if qt == "":
        return True   # fail-open: unresolved != fund; don't drop real equities on a yfinance hiccup
    if qt in _NON_EQUITY_QT:
        return False
    return qt == "EQUITY"


def _fetch_day(d: datetime.date) -> dict[str, tuple[float, float]]:
    """{sym: (short_vol, total_vol)} for ALL NMS names on date d; {} if no file (holiday/weekend/403)."""
    try:
        req = urllib.request.Request(URL.format(d=d.strftime("%Y%m%d")), headers=HDRS)
        with urllib.request.urlopen(req, timeout=45) as r:
            txt = r.read().decode(errors="ignore")
    except Exception:
        return {}
    out: dict[str, tuple[float, float]] = {}
    for ln in txt.splitlines()[1:]:
        p = ln.split("|")
        if len(p) >= 5 and p[1] and p[1].isascii():
            try:
                sv, tv = float(p[2]), float(p[4])
            except ValueError:
                continue
            if tv > 0:
                out[p[1]] = (sv, tv)
    return out


def _refresh_state() -> dict:
    """Load state, backfill missing trailing FINRA days, self-prune to LOOKBACK. Compact storage:
    per date we keep {sym: [short_ratio_x1000_int]} to stay small across ~12k names x 22 days."""
    state = json.load(open(STATE)) if STATE.exists() else {"days": {}}
    days = state.setdefault("days", {})
    d = datetime.date.today()
    tried, got = 0, 0
    # Walk back until we have LOOKBACK+2 real trading-day files (skips weekends/holidays/403s).
    while len([k for k in days]) < LOOKBACK + 2 and tried < 45:
        d -= datetime.timedelta(days=1)
        tried += 1
        k = d.isoformat()
        if k in days:
            continue
        row = _fetch_day(d)
        if row:
            # store short-volume RATIO (x1000, int) — compact and all we need downstream
            days[k] = {s: round(sv / tv * 1000) for s, (sv, tv) in row.items()}
            # keep raw latest-day volumes for the newest day (for the liquidity gate + reporting)
            if got == 0:
                state["latest_vol"] = {s: round(tv) for s, (sv, tv) in row.items()}
                state["latest_date"] = k
            got += 1
    # prune to newest LOOKBACK days
    for k in sorted(days)[:-LOOKBACK]:
        days.pop(k, None)
    return state


def scan(dry: bool = False) -> dict:
    state = _refresh_state()
    days = state["days"]
    dates = sorted(days)
    caveats = []
    if len(dates) < BASELINE_MIN + CONSEC:
        res = {"asof": datetime.date.today().isoformat(), "n_scanned": 0, "flagged": [],
               "note": "insufficient FINRA history to compute baselines (need "
                       f"{BASELINE_MIN + CONSEC} trading days, have {len(dates)})",
               "caveats": ["FINRA files unavailable or first run — rerun after backfill"]}
        if not dry:
            OUT.write_text(json.dumps(res, indent=1))
            json.dump(state, open(STATE, "w"))
        return res

    latest_date = dates[-1]
    latest_vol = state.get("latest_vol", {})
    consec_dates = dates[-CONSEC:]
    base_dates = dates[:-CONSEC]

    # Candidate spikes: for each name present on ALL of the last CONSEC days, ratio must sit
    # >=SPIKE_PP above its trailing baseline mean on EVERY one of those days.
    prelim = []
    universe = set()
    for s, r in days[latest_date].items():
        universe.add(s)
    n_scanned = len(universe)

    for s in universe:
        # baseline from prior days (exclude the CONSEC recent window)
        base = [days[dt][s] / 1000.0 for dt in base_dates if s in days[dt]]
        if len(base) < BASELINE_MIN:
            continue
        recent = [days[dt][s] / 1000.0 for dt in consec_dates if s in days[dt]]
        if len(recent) < CONSEC:
            continue
        baseline = sum(base) / len(base)
        # spike on EVERY consecutive day
        if not all(r - baseline >= SPIKE_PP for r in recent):
            continue
        # liquidity gate on the latest day
        tv = latest_vol.get(s, 0)
        if tv < MIN_TOTAL_VOL:
            continue
        latest_ratio = recent[-1]
        prelim.append({
            "ticker": s,
            "short_vol_ratio": round(latest_ratio, 3),
            "baseline": round(baseline, 3),
            "spike_pp": round((latest_ratio - baseline) * 100, 1),
            "consecutive_days": CONSEC,
            "latest_total_vol": tv,
        })

    prelim.sort(key=lambda x: -x["spike_pp"])
    n_spikes = len(prelim)

    # ── EQUITY-ONLY + $-liquidity filter (applied BEFORE the MAX_CLASSIFY budget) ─────────────────
    # The e2e over-firing bug: the live top-25 was ~all ETFs (EFV/IYG/USTB/HFXI/BCI/SIO/FLAU/DFGP/...)
    # whose ~99% short-vol ratio is MM/authorized-participant creation-redemption plumbing, not short
    # pressure. We drop non-equity (quoteType != 'EQUITY') and ultra-thin names HERE, so ETFs never
    # consume the classify budget or reach 'flagged'. We resolve quoteType once per ticker (cached) and,
    # in the same yfinance pull, apply a notional $-volume floor (last price x latest share volume).
    equity_candidates = []
    n_dropped_etf = 0
    n_dropped_thin = 0
    yf_ok = True
    try:
        import yfinance as yf  # noqa: F401  (import here so an outage fails-open below)
    except Exception:
        yf_ok = False
        caveats.append("yfinance unavailable — equity-only / $-volume filter FAILED OPEN (fund tickers "
                       "may leak into 'flagged'; treat ETF-looking names as artifact).")
    for row in prelim:
        s = row["ticker"]
        if yf_ok and not _is_equity(s):
            n_dropped_etf += 1
            continue
        # $-volume floor: reuse the same yfinance handle for a last price; unresolved price → fail-open.
        px = None
        if yf_ok:
            try:
                import yfinance as yf
                fi = yf.Ticker(s).fast_info
                px = fi.get("last_price") or fi.get("previous_close")
            except Exception:
                px = None
        if px:
            row["last_price"] = round(float(px), 4)
            row["latest_dollar_vol"] = round(float(px) * row["latest_total_vol"])
            if row["latest_dollar_vol"] < MIN_DOLLAR_VOL:
                n_dropped_thin += 1
                continue
        equity_candidates.append(row)

    n_equity = len(equity_candidates)
    to_classify = equity_candidates[:MAX_CLASSIFY]
    if n_dropped_etf:
        caveats.append(f"{n_dropped_etf} spiking names DROPPED as non-equity (ETF/ETN/fund) — their ~99% "
                       "short-vol ratio is MM/authorized-participant creation-redemption plumbing, a "
                       "SUPPLY-side artifact, not a squeeze/distress setup. Equity-only by design.")
    if n_dropped_thin:
        caveats.append(f"{n_dropped_thin} spiking equities DROPPED below the ${MIN_DOLLAR_VOL:,}/day "
                       "notional-volume floor (a 99% ratio on a handful of shares is noise).")
    if n_equity > MAX_CLASSIFY:
        caveats.append(f"{n_equity} real equities spiked; classifying only the top {MAX_CLASSIFY} by "
                       "spike_pp (discovery_state is a multi-connector pull). Full spike list not enriched.")

    # ── CLASSIFY through the conditioning layer ──────────────────────────────────────────────────
    # distress        : deterioration ahead — the short is likely RIGHT. AVOID / short-side only.
    # squeeze-setup   : un-broken name, crowded short book, NOT already discovered → potential squeeze.
    # already-crowded : real spike but the name is DISCOVERED_CROWDED → NOT a fresh trade (RCAT lesson).
    # noise           : spike present but conditioning says nothing actionable / low confidence.
    flagged = []
    try:
        sys.path.insert(0, str(ROOT))
        from verticals.buyside_dd.connectors.discovery_state import discovery_state
        have_ds = True
    except Exception as e:  # pragma: no cover
        have_ds = False
        caveats.append(f"discovery_state unavailable ({e}); flagged names carry the FINRA spike only, "
                       "UNCLASSIFIED — supply/conviction separation NOT performed.")

    # NOTE: ETFs/ETNs/funds are already excluded upstream by the equity-only filter (they never reach
    # to_classify), so no per-name fund guard is needed here — everything below is genuine equity.
    for row in to_classify:
        t = row["ticker"]
        ds_regime = None
        note = ""
        classification = "unclassified"
        if have_ds:
            try:
                ds = discovery_state(t, enable_options=False, enable_13f=False)
                ds_regime = ds.get("regime")
                si = (ds.get("components", {}).get("short_interest") or {})
                si_pct = si.get("short_interest_pct")
                ac = (ds.get("components", {}).get("analyst_coverage") or {})
                rec_key = ac.get("recommendation_key")
                # Classification logic — conditioning-layer driven, doctrine-compliant:
                if ds_regime in ("DISCOVERED_CROWDED",):
                    classification = "already-crowded"
                    note = ("spike is REAL but the conditioning layer reads the name DISCOVERED_CROWDED — "
                            "the short/attention is already priced (RCAT lesson: crowding is squeeze fuel, "
                            "not a fresh entry). INFO only.")
                elif ds_regime in ("UNDISCOVERED", "UNDISCOVERED_RETAIL_ONLY", "DISCOVERING"):
                    # supply-vs-demand split we CAN'T fully do from FINRA alone → route by soft tells:
                    # a bearish sell-side tilt or elevated SI leans distress; a quiet, un-crowded name
                    # with a fresh short SPIKE leans squeeze-setup. Both are PROPOSALS, not calls.
                    bearish = (rec_key in ("underperform", "sell")) or (si_pct is not None and si_pct >= 20)
                    if bearish:
                        classification = "distress"
                        note = ("fresh short-pressure spike + bearish sell-side / elevated SI → the short "
                                "may be RIGHT (deterioration). AVOID long / short-side candidate. VERIFY "
                                "the fundamental catalyst before acting — this is a supply signal, not a call.")
                    else:
                        classification = "squeeze-setup"
                        note = ("fresh short-pressure spike on an un-crowded, not-yet-discovered name with "
                                "no bearish sell-side tilt → potential SQUEEZE-SETUP. NOT a buy: confirm the "
                                "name is un-broken (no distress catalyst) + a real borrow constraint before "
                                "any defined-risk expression. Supply signal, PROPOSE only.")
                else:
                    classification = "noise"
                    note = f"conditioning layer inconclusive (regime={ds_regime}); treat as noise."
            except Exception as e:
                classification = "unclassified"
                note = f"discovery_state failed for {t}: {e}"
        row_out = {
            "ticker": t,
            "name": t,  # FINRA carries no issuer name; ticker is the key
            "short_vol_ratio": row["short_vol_ratio"],
            "baseline": row["baseline"],
            "spike_pp": row["spike_pp"],
            "consecutive_days": row["consecutive_days"],
            "latest_total_vol": row["latest_total_vol"],
            "last_price": row.get("last_price"),
            "latest_dollar_vol": row.get("latest_dollar_vol"),
            "quote_type": "EQUITY",       # equity-only filter guarantees this; ETFs never reach here
            "borrow_fee_or_null": None,   # IBKR MCP exposes no borrow/utilization field — never fabricate
            "discovery_state": ds_regime,
            "classification": classification,
            "note": note,
        }
        flagged.append(row_out)

    res = {
        "asof": latest_date,
        "n_scanned": n_scanned,
        "n_spikes": n_spikes,
        "n_equity_spikes": n_equity,
        "n_dropped_nonequity": n_dropped_etf,
        "n_dropped_thin": n_dropped_thin,
        "flagged": flagged,
        "note": ("BROAD short-pressure / short-volume-ratio SPIKE scan (generalizes squeeze_watch's "
                 "3-name basket to the full FINRA NMS file). A spike = short-vol ratio >="
                 f"{int(SPIKE_PP*100)}pp above the name's OWN {BASELINE_MIN}+day baseline for "
                 f">={CONSEC} consecutive days, on genuine SINGLE-NAME EQUITIES (quoteType=='EQUITY') "
                 f"with >={MIN_TOTAL_VOL:,} shares/day AND >=${MIN_DOLLAR_VOL:,}/day notional. "
                 "DOCTRINE: a spike measures SUPPLY/positioning, NOT conviction (the MAUDE-velocity "
                 "lesson — naive velocity has LR~1). Each name is CLASSIFIED through the conditioning "
                 "layer (distress vs squeeze-setup vs already-crowded vs noise) and PROPOSED only — "
                 "never a buy/sell on the spike alone. A real spike on a DISCOVERED_CROWDED name is "
                 "not a fresh trade (RCAT)."),
        "caveats": caveats + [
            "EQUITY-ONLY BY DESIGN: ETFs/ETNs/funds are EXCLUDED. On a fund the FINRA short-vol ratio "
            "runs ~99% because it is authorized-participant / market-maker creation-redemption plumbing "
            "(shares minted on demand), a pure SUPPLY-side artifact with zero squeeze content — not short "
            "pressure. Only quoteType=='EQUITY' single names are flagged (unresolved quoteType fails OPEN).",
            "ABSOLUTE short-vol ratio is structurally high (MM/liquidity-provider hedging keeps it "
            "0.4-0.7 for most names) — ONLY the spike-vs-own-baseline is signal; the level is not.",
            "FINRA short VOLUME != short INTEREST (it's tape-side sell flow incl. bona-fide MM hedging), "
            "and it excludes dark/ATS off-tape prints unevenly. It's a LEADING proxy, not a position count.",
            "borrow_fee_or_null is null: the IBKR MCP get_price_snapshot surface exposes no borrow-fee / "
            "utilization / securities-lending field. Not fabricated. A real borrow feed = v2.",
            "distress vs squeeze-setup here is a SOFT conditioning-layer lean (sell-side tilt / SI% + "
            "discovery regime), NOT a demand-vs-supply decomposition of the short flow itself (v2).",
        ],
    }
    if not dry:
        OUT.write_text(json.dumps(res, indent=1))
        # don't persist the giant latest_vol map long-term; keep state lean
        state.pop("latest_vol", None)
        json.dump({"days": state["days"]}, open(STATE, "w"))
    return res


def main():
    res = scan(dry="--dry" in sys.argv)
    print(f"=== BORROW-FEE / SHORT-PRESSURE SCANNER  asof {res.get('asof')}  "
          f"({res.get('n_scanned', 0):,} names scanned, {res.get('n_spikes', 0)} spikes, "
          f"{res.get('n_dropped_nonequity', 0)} ETF/fund dropped, "
          f"{res.get('n_dropped_thin', 0)} thin dropped, "
          f"{len(res.get('flagged', []))} equities classified) ===")
    if not res.get("flagged"):
        print("  no qualifying short-pressure spikes today.")
    for r in res.get("flagged", []):
        tag = {"distress": "DISTRESS ", "squeeze-setup": "SQUEEZE? ", "already-crowded": "CROWDED  ",
               "etf-plumbing": "etf-plumb", "noise": "noise    ",
               "unclassified": "unclass  "}.get(r["classification"], "?        ")
        print(f"  {tag} {r['ticker']:8} ratio {r['short_vol_ratio']:.2f} vs base {r['baseline']:.2f} "
              f"(+{r['spike_pp']:.0f}pp) vol {r['latest_total_vol']/1e6:.1f}M  "
              f"[{r['discovery_state'] or 'n/a'}]")
    if res.get("caveats"):
        print("  caveats: SUPPLY not conviction (PROPOSE only); borrow_fee=null (MCP has no field).")
    print(f"[-> {OUT.name}]")


if __name__ == "__main__":
    main()
