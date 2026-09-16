"""us_broad_dislocation_sweep — the BROAD-US leg of the dislocation watch (built 2026-08-13).

THE GAP IT FILLS — the SPGI miss, verified on the tape:
  SPGI ground 457.38 (2026-07-16 close) -> 405.24 (2026-08-06 close), -11.4% peak-to-trough over
  17 sessions, with SPY flat and NO single session worse than -3.5%. Nothing on the desk saw it,
  and every screen had a *structural* reason to be blind:
    · broken_print_radar     only fires on SINGLE-SESSION breaks (<= -15%, or -8% on 3x volume)
    · dislocation_sweep      multi-session excess, but ONLY over the ~490-name researched universe
                             — SPGI was never researched, so it was never in scope
    · blob/value screens     a premium-multiple quality compounder never passes a cheapness screen
    · intl_dislocation_sweep gives 8,133 FOREIGN names the multi-session treatment that
                             unresearched US large-caps did not have
  So an unresearched US large-cap could bleed a fifth of its value in a month, in full view, and
  no watch on the desk would say a word. This module is that watch.

TWO GAPS, NOT ONE. Closing the universe gap alone would still have missed SPGI, and this is the
part worth remembering: as-of 2026-08-06 SPGI's 21-session POINT-TO-POINT excess vs SPY was only
-9.0pp and its deepest 5d excess over the whole slide was -7.9pp — both inside the -15/-8 gates the
other two sweeps use. The t-21 anchor (2026-07-08) happened to be a local low, so the measure never
saw the 7/16 peak at all. Point-to-point return is ANCHOR-LUCKY. Measured peak-anchored, the same
tape reads -11.0pp of excess drawdown. The METRIC was as blind as the universe.

FIVE LEGS (all the shared, date-aligned machinery in intl_dislocation_sweep — this module owns no
benchmark arithmetic of its own):
    5d       excess vs SPY <= -8pp   (HIGH -12)   — the sharp break
    21d      excess vs SPY <= -15pp  (HIGH -20)   — the classic multi-session dislocation
    grind21  excess DRAWDOWN from the 21-session high <= -11pp (HIGH -18)   <- the SPGI shape
    63d      excess vs SPY <= -20pp  (HIGH -28), raw <= -10%  — the multi-month grind
    bleed52  (dd-from-52w-high - SPY's own) <= -25pp AND still WIDENING >= 5pp/21 sessions
                                                                          -> labelled SLOW_BLEED
Bands are calibrated on the S&P 500 across five as-of dates spanning +18.5% and -5.2% SPY 63d
regimes; see the calibration block at the top of intl_dislocation_sweep. Every leg keeps the
raw-move-must-be-negative guard: underperforming a ripping tape is relative weakness, not a
dislocation, and firing on it is the beta-bleed error.

UNIVERSE = S&P 500 constituents (the weekly-cached Wikipedia list spinoff_orphans already
maintains) UNION broken_print_radar's broad US cap-ladder universe (~800 names, its own builder,
cached weekly here to stay inside the Yahoo rate budget), MINUS everything already in the
researched universe — those are dislocation_sweep's names and a double-fire is noise, not coverage.
So every fire from this module is by construction an UNRESEARCHED name: an intake proposal.

BENCHMARK = SPY for the gate. The SPDR sector ETF is resolved lazily FOR FIRES ONLY (one cached
yfinance lookup per new name, never for the whole universe) and printed as CONTEXT: a name -12pp vs
SPY but -1pp vs XLF is a sector move wearing a single name's clothes, and triage should see that
before it opens a court.

PROPOSES ONLY. Identical routing to the other two sweeps: cause-check -> discovery_state ->
independent court (v1.4) -> thesis doc -> THEN staging. Fires are ENQUEUE-CANDIDATEs.

Emits DETFIRE|us_broad_dislocation|<ticker>|<SEV>|<evidence>; the registry's detector_scan
extractor turns them into DETECTOR_FIRE signals. Writes data/US_BROAD_DISLOCATION_SWEEP.json +
data/us_broad_dislocation_state.json (new-vs-deepened dedup, keyed on tier AND leg set).

  python3 verticals/generators/us_broad_dislocation_sweep.py [--limit 200] [--dry-run]
  python3 verticals/generators/us_broad_dislocation_sweep.py --refresh-universe   # force the ladder
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DATA = HERE / "data"
OUT_JSON = DATA / "US_BROAD_DISLOCATION_SWEEP.json"
STATE = DATA / "us_broad_dislocation_state.json"
UNI_CACHE = DATA / "_us_broad_universe.json"
SECTOR_CACHE = DATA / "_us_sector_cache.json"
LEDGER = ROOT / "desk" / "data" / "research_ledger.json"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from verticals.generators import intl_dislocation_sweep as I   # noqa: E402  (shared machinery)

# ---------------------------------------------------------------- tunables (top, per house rule)
BENCH = "SPY"
HISTORY = "1y"               # bleed52 needs a real 52-week high; a 3mo window cannot supply one
LADDER_SIZE = 250            # names per cap band asked of broken_print_radar's builder
UNI_CACHE_DAYS = 7           # the cap ladder costs 8 screener calls — refresh weekly, not daily
BATCH = 60                   # yfinance names per download call (1y payload; 60 is comfortable)
PAUSE = 0.8                  # polite gap between batches; ~14 batches ≈ 20s for the whole leg
TIME_BUDGET_S = 420          # wall clock for the price pull; the runner kills a watch at 600s
MIN_UNIVERSE = 400           # below this the universe build is BROKEN — refuse, never report quiet
SECTOR_LOOKUP_CAP = 40       # sector context is per-FIRE only; cap the tail on a loud tape
EVIDENCE_BUDGET = 600        # desk.signals.make truncates evidence here — see fire_line()

# Sector -> SPDR sector ETF. CONTEXT ONLY, never the gate. Both vocabularies are here on purpose:
# the index table publishes true GICS names ("Health Care", "Information Technology") while
# yfinance publishes its own ("Healthcare", "Technology"), and the two sources feed the same map.
SECTOR_ETF = {
    # yfinance vocabulary
    "Technology": "XLK", "Financial Services": "XLF", "Healthcare": "XLV",
    "Consumer Cyclical": "XLY", "Consumer Defensive": "XLP", "Industrials": "XLI",
    "Energy": "XLE", "Utilities": "XLU", "Real Estate": "XLRE",
    "Basic Materials": "XLB", "Communication Services": "XLC",
    # GICS vocabulary (the constituent table)
    "Information Technology": "XLK", "Financials": "XLF", "Health Care": "XLV",
    "Consumer Discretionary": "XLY", "Consumer Staples": "XLP", "Materials": "XLB",
}
SECTOR_SEED_DAYS = 7         # re-seed the free index-table sector map weekly
SECTOR_INFO_BUDGET = 12      # per run: yfinance .info calls for names the free seed cannot cover
SECTOR_INFO_PAUSE = 0.4      # …paced; a 100-call burst rate-limits the whole Yahoo session
SP500_WIKI = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
SECTOR_ETFS = sorted(set(SECTOR_ETF.values()))
DETECTOR = "us_broad_dislocation"


# ---------------------------------------------------------------- universe
def yf_us(ticker: str) -> str:
    """Index/ledger ticker -> Yahoo symbol. BRK.B -> BRK-B (the class-share convention)."""
    return ticker.replace(".", "-")


def sp500(cache_only: bool = False) -> tuple[list[str], str]:
    """S&P 500 constituents + the list's asof date, off the weekly cache spinoff_orphans keeps.

    Reuses that module's fetcher rather than re-scraping: one cache, one refresh cadence, one
    place where a degraded Wikipedia fetch is refused."""
    try:
        js = json.loads((HERE / "data" / "_sp_constituents.json").read_text())
        asof, rows = js.get("asof", "?"), (js.get("indices") or {}).get("500") or []
    except Exception:
        asof, rows = "?", []
    stale = True
    try:
        stale = (datetime.date.today() - datetime.date.fromisoformat(asof)).days > 7
    except Exception:
        pass
    if rows and (cache_only or not stale):
        return sorted(rows), asof
    try:                                       # cache absent or stale -> let the owner refresh it
        from verticals.generators.spinoff_orphans import sp_constituents
        idx = sp_constituents()
        got = sorted((idx or {}).get("500") or [])
        if got:
            return got, datetime.date.today().isoformat()
    except Exception as e:
        print(f"[us_broad] S&P constituent refresh failed ({type(e).__name__}) — "
              f"falling back to the cached list asof {asof}")
    return sorted(rows), asof


def cap_ladder(refresh: bool = False, size: int = LADDER_SIZE) -> tuple[list[str], str]:
    """broken_print_radar's broad US cap-ladder universe (~800 names), cached weekly here.

    REUSES ITS BUILDER — the cap bands, the OTC/pink exclusion and the per-band pacing all live in
    _us_backfill_universe and are not re-implemented. What is added is a disk cache: the ladder
    costs 8 server-side screener calls, and this leg runs every weekday alongside two other Yahoo
    sweeps. A degraded refetch never overwrites a good cache (the sp_constituents rule)."""
    cached, asof = [], "?"
    try:
        js = json.loads(UNI_CACHE.read_text())
        cached, asof = js.get("symbols") or [], js.get("asof", "?")
        if not refresh and (datetime.date.today() - datetime.date.fromisoformat(asof)).days <= UNI_CACHE_DAYS:
            return cached, asof
    except Exception:
        pass
    try:
        from desk.broken_print_radar import _us_backfill_universe
        got = _us_backfill_universe(size=size)
    except Exception as e:
        print(f"[us_broad] cap-ladder refresh FAILED ({type(e).__name__}) — using the cached "
              f"ladder asof {asof} ({len(cached)} names)")
        return cached, asof
    if len(got) < 0.5 * len(cached):
        print(f"[us_broad] cap-ladder refetch returned {len(got)} vs {len(cached)} cached = "
              f"DEGRADED; keeping the cache asof {asof}")
        return cached, asof
    today = datetime.date.today().isoformat()
    UNI_CACHE.write_text(json.dumps({"asof": today, "source": "desk.broken_print_radar."
                                     "_us_backfill_universe (Yahoo cap-ladder screener)",
                                     "size_per_band": size, "symbols": sorted(got)}, indent=1))
    return sorted(got), today


def researched() -> set[str]:
    """Every ticker dislocation_sweep already covers, PLUS the dead-verdict names it drops.

    Both halves matter and for different reasons: a live researched name would double-fire, and a
    dead-verdict name (AVOID/PASS/TRAP) is one we decided not to own — its drawdown is not our
    business. Returned in BOTH punctuations so BRK.B and BRK-B exclude each other."""
    out: set[str] = set()
    try:
        from verticals.generators.dislocation_sweep import build_universe
        out |= set(build_universe())
    except Exception as e:
        print(f"[us_broad] WARNING: researched-universe load failed ({type(e).__name__}) — "
              f"exclusion is INCOMPLETE, expect double-fires against dislocation_sweep")
    try:
        for r in json.loads(LEDGER.read_text()).get("names", []):
            for k in (r.get("ticker"), r.get("yf")):
                if k:
                    out.add(str(k))
    except Exception:
        pass
    return {t for x in out for t in (x, x.replace(".", "-"), x.replace("-", "."))}


def load_universe(refresh_universe: bool = False) -> tuple[dict[str, dict], dict]:
    """symbol -> {shelf, bench, researched, verdict}, plus a provenance report."""
    idx, idx_asof = sp500()
    ladder, ladder_asof = cap_ladder(refresh=refresh_universe)
    known = researched()
    uni: dict[str, dict] = {}
    excluded = 0
    for shelf, rows in (("sp500", idx), ("us_tape", ladder)):
        for tk in rows:
            sym = yf_us(tk)
            if sym in uni:
                continue
            if tk in known or sym in known:
                excluded += 1
                continue
            uni[sym] = {"shelf": shelf, "bench": BENCH, "researched": False,
                        "verdict": "UNRESEARCHED"}
    rep = {"sp500": len(idx), "sp500_asof": idx_asof, "cap_ladder": len(ladder),
           "cap_ladder_asof": ladder_asof, "excluded_already_researched": excluded,
           "universe": len(uni)}
    return uni, rep


# ---------------------------------------------------------------- sector context (fires only)
def seed_sectors(cache: dict, force: bool = False) -> str:
    """Fill the sector map from the FREE index constituent table (Symbol + GICS Sector columns).

    WHY THIS EXISTS — the first live run resolved 0 of 114 sectors. yfinance's .info goes through
    Yahoo's cookie/crumb endpoint, and a burst of it straight after an 875-name history sweep
    trips YFRateLimitError for every single name. The failure was correctly LABELLED per line
    ('SECTOR CONTEXT UNAVAILABLE') but the mechanism was simply not working, which is a defect
    however honestly it is reported. The constituent table carries the sector for ~500 of the
    names outright, for one HTTP GET a week and zero Yahoo quota."""
    marker = cache.get("_seed") or {}
    try:
        fresh = (datetime.date.today()
                 - datetime.date.fromisoformat(marker.get("asof", "1970-01-01"))).days < SECTOR_SEED_DAYS
    except Exception:
        fresh = False
    if fresh and not force:
        return f"cached seed asof {marker.get('asof')} ({marker.get('n', 0)} names)"
    import re
    import urllib.request
    try:
        req = urllib.request.Request(SP500_WIKI, headers={"User-Agent": "signalos-research 4tripathy@gmail.com"})
        html = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "ignore")
        tbl = re.findall(r"<table[^>]*wikitable[^>]*>(.*?)</table>", html, re.S)[0]
    except Exception as e:
        return f"seed FAILED ({type(e).__name__}) — keeping {len(cache) - 1} cached names"
    n = 0
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", tbl, re.S):
        cells = [re.sub(r"<[^>]+>", "", c).strip()
                 for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S)]
        if len(cells) < 3 or not re.fullmatch(r"[A-Z][A-Z.\-]{0,5}", cells[0]):
            continue
        sec = cells[2]
        if sec not in SECTOR_ETF:
            continue
        cache[yf_us(cells[0])] = {"etf": SECTOR_ETF[sec], "sector": sec, "src": "index_table",
                                  "asof": datetime.date.today().isoformat()}
        n += 1
    cache["_seed"] = {"asof": datetime.date.today().isoformat(), "n": n, "source": SP500_WIKI}
    return f"seeded {n} names from the index table (free, no Yahoo quota)"


def sector_etf(symbol: str, cache: dict, budget: list[int]) -> tuple[str | None, str]:
    """(SPDR sector ETF, sector name) for ONE ticker. ('', 'UNKNOWN') if unresolved.

    Ladder: disk cache (permanent — a company's sector does not change) -> the free index-table
    seed -> a PACED, BUDGETED yfinance .info call. `budget` is a one-element list acting as a
    mutable counter across the run, so the map fills in over days instead of in one rate-limiting
    burst — the same discipline the cohort mapper uses."""
    if symbol in cache and symbol != "_seed":
        c = cache[symbol]
        return c.get("etf"), c.get("sector", "UNKNOWN")
    if budget[0] <= 0:
        return None, "UNKNOWN"
    budget[0] -= 1
    sec, err = "", ""
    try:
        import time as _t
        import yfinance as yf
        _t.sleep(SECTOR_INFO_PAUSE)
        sec = (yf.Ticker(symbol).info or {}).get("sector") or ""
    except Exception as e:
        err = type(e).__name__
        if "RateLimit" in err:                       # stop asking; the whole session is throttled
            budget[0] = 0
    if err:
        return None, "UNKNOWN"                       # NOT cached: a throttled miss is not a fact
    etf = SECTOR_ETF.get(sec)
    cache[symbol] = {"etf": etf, "sector": sec or "UNKNOWN", "src": "yfinance",
                     "asof": datetime.date.today().isoformat()}
    return etf, (sec or "UNKNOWN")


def attach_sector_context(hits: list[dict], bars: dict, cap: int = SECTOR_LOOKUP_CAP,
                          seed: bool = True) -> tuple[int, str]:
    """Annotate each fire with its excess vs its own sector ETF. CONTEXT, never a gate.

    Uses the same date-aligned lookup as the SPY leg, so the sector number is comparable to the
    headline one rather than a positionally-drifted lookalike. Returns (n_annotated, status) —
    the status is REPORTED, never swallowed: 'we could not resolve the sector' and 'we were rate
    limited out of asking' are different facts."""
    try:
        cache = json.loads(SECTOR_CACHE.read_text())
    except Exception:
        cache = {}
    # CACHE HYGIENE, and it is not cosmetic: the first live run was rate-limited and wrote 30
    # entries saying sector=UNKNOWN. Those are not facts about the companies, they are a record of
    # an outage — and once on disk they are answered from cache forever, so the outage becomes
    # permanent. An unresolved sector is dropped on load and simply re-asked later.
    stale = [k for k, v in cache.items()
             if k != "_seed" and isinstance(v, dict) and not v.get("etf")]
    for k in stale:
        cache.pop(k)
    status = seed_sectors(cache) if seed else "seed skipped"
    if stale:
        status += f"; dropped {len(stale)} unresolved-sector cache entries (re-ask, don't inherit an outage)"
    budget = [SECTOR_INFO_BUDGET]
    n = 0
    for h in hits[:cap]:
        etf, sec = sector_etf(h["ticker"], cache, budget)
        h["sector"] = sec
        h["sector_bench"] = etf or "UNAVAILABLE"
        if not etf or etf not in bars:
            continue
        e = bars.get(h["ticker"])
        m = I._moves(e)
        if not m:
            continue
        anchors = m[3]
        bm = I._bench_moves(bars.get(etf), anchors)
        if bm:
            h["sector_excess21_pct"] = round(h["r21_pct"] - bm[1], 1)
            h["sector_r21_pct"] = round(bm[1], 1)
        dd = I._drawdown(e, I.MIN_BARS - 1)
        if dd is not None:
            sdd = I._bench_drawdown(bars.get(etf), dd["d_peak"], dd["d_now"])
            if sdd is not None:
                h["sector_excess_dd21_pct"] = round(dd["dd_pct"] - sdd, 1)
        n += 1
    try:
        SECTOR_CACHE.write_text(json.dumps(cache, indent=1, sort_keys=True))
    except Exception:
        pass
    unresolved = sum(1 for h in hits[:cap] if h.get("sector_bench") == "UNAVAILABLE")
    if budget[0] == 0 and unresolved:
        status += (f"; yfinance .info budget EXHAUSTED or rate-limited — {unresolved} fire(s) "
                   f"carry no sector context this run (they resolve on later runs as the cache fills)")
    return n, status


def sector_clause(hit: dict, short: bool = False) -> str:
    """The 'is this just the sector?' sentence. Silent when we could not resolve one."""
    etf = hit.get("sector_bench")
    if not etf or etf == "UNAVAILABLE":
        return f" SECTOR CONTEXT UNAVAILABLE (sector={hit.get('sector', 'UNKNOWN')})."
    bits = []
    if hit.get("sector_excess21_pct") is not None:
        bits.append(f"{hit['sector_excess21_pct']:+.1f}pp/21d")
    if hit.get("sector_excess_dd21_pct") is not None:
        bits.append(f"{hit['sector_excess_dd21_pct']:+.1f}pp on the 21d drawdown")
    if not bits:
        return f" SECTOR CONTEXT UNAVAILABLE ({etf} had no date-aligned series)."
    if short:
        return f" SECTOR vs {etf}: {' / '.join(bits)}."
    return (f" SECTOR: vs {etf} ({hit.get('sector')}) the same move is {' / '.join(bits)}"
            f" — near zero = the sector, not the name.")


def fire_line(hit: dict) -> str:
    """The shared DETFIRE line, retagged us_broad, with the sector-context sentence spliced in
    ahead of the doctrine sentence (which stays verbatim and LAST).

    LENGTH IS A CONTRACT, not cosmetics: desk.signals.make truncates `evidence` at
    EVIDENCE_BUDGET chars, so a line that runs long silently loses its TAIL — and the tail is the
    routing sentence plus the PROPOSES-ONLY doctrine, the two parts that stop a reader treating a
    fire as a buy. Five legs plus a SUSPECT label plus sector context can overrun it. So the line
    is assembled down a ladder that sheds the least load-bearing prose first, in this order:
        sector sentence (long -> numbers-only -> gone)  ->  leg evidence (prose -> numbers -> gone)
    The routing and the doctrine are never candidates. The final hard cut exists only so the
    guarantee is STRUCTURAL and does not depend on anyone remembering to keep the prose short."""
    ladder = [(sector_clause(hit), None), (sector_clause(hit, short=True), None),
              ("", None), ("", I.leg_clause(hit, compact=True)), ("", "")]
    for sec, legs_text in ladder:
        parts = I.fire_line(hit, detector=DETECTOR, shelf_word="universe",
                            legs_text=legs_text).replace(I.DOCTRINE, sec + I.DOCTRINE).split("|", 4)
        if len(parts[4]) <= EVIDENCE_BUDGET:
            return "|".join(parts)
    tail = " …(full metrics: US_BROAD_DISLOCATION_SWEEP.json)" + I.DOCTRINE
    parts[4] = parts[4][:max(0, EVIDENCE_BUDGET - len(tail))].rstrip() + tail
    return "|".join(parts)


# ---------------------------------------------------------------- driver
def sweep(limit: int = 0, dry_run: bool = False, refresh_universe: bool = False,
          quiet_sessions: int = I.QUIET_SESSIONS,
          legs: tuple[str, ...] = I.LEGS_ALL) -> list[dict]:
    today = datetime.date.today().isoformat()
    uni, rep = load_universe(refresh_universe=refresh_universe)
    syms = sorted(uni)
    if limit:
        syms = syms[:limit]
        uni = {s: uni[s] for s in syms}
    if not limit and len(syms) < MIN_UNIVERSE:
        # The silently-dead-watch failure in its universe form: a broken constituent list would
        # make this print "0 dislocations" forever, which reads exactly like a calm tape.
        raise SystemExit(f"[us_broad] UNIVERSE BUILD FAILED: {len(syms)} names (< {MIN_UNIVERSE}) — "
                         f"{rep}. Refusing to run a screen whose quiet result would be a lie.")
    print(f"[us_broad] {today}: universe {len(syms)} "
          f"(S&P500 {rep['sp500']} asof {rep['sp500_asof']} + cap-ladder {rep['cap_ladder']} asof "
          f"{rep['cap_ladder_asof']}, minus {rep['excluded_already_researched']} already-researched) "
          f"· legs {','.join(legs)} · bench {BENCH} + {len(SECTOR_ETFS)} sector ETFs")

    bars, not_swept = I.fetch_bars(syms + [BENCH] + SECTOR_ETFS, batch=BATCH, pause=PAUSE,
                                   budget_s=TIME_BUDGET_S, period=HISTORY, label="us_broad")
    missing = [s for s in syms if len(((bars.get(s) or {}).get("close")) or []) < I.MIN_BARS
               and s not in set(not_swept)]
    alt_map = {a: s for s in missing for a in I.alt_symbols(s)}
    if alt_map:
        print(f"[us_broad] retrying {len(missing)} unpriced via {len(alt_map)} alternate forms")
        alt_bars, _ = I.fetch_bars(sorted(alt_map), budget_s=60, period=HISTORY,
                                   label="us_broad", verbose=False)
        for a, b in alt_bars.items():
            orig = alt_map[a]
            if len(b.get("close") or []) >= I.MIN_BARS and orig not in bars:
                bars[orig] = dict(b, symbol_fixed_to=a)
    still = [s for s in syms if len(((bars.get(s) or {}).get("close")) or []) < I.MIN_BARS
             and s not in set(not_swept)]
    gw_alive, gw_status = (I.gw_probe(still, default_venue=("SMART", "USD")) if still
                           else ({}, "not attempted"))

    if len((bars.get(BENCH) or {}).get("close") or []) < I.BARS_63:
        raise SystemExit(f"[us_broad] ABORT: no usable {BENCH} series — every excess would be a raw "
                         f"move wearing a benchmark's name. INFRA failure, not a quiet tape.")

    try:
        state = json.loads(STATE.read_text())
    except Exception:
        state = {}
    hits, new_state, scanned = I.scan(bars, uni, state, today, quiet_sessions=quiet_sessions,
                                      legs=legs)
    n_sector, sector_status = attach_sector_context(hits, bars)
    for h in hits:
        print(fire_line(h))

    dline, drep = I.degraded_line(syms, bars, not_swept, gw_alive, gw_status=gw_status,
                                  store="US_BROAD_DISLOCATION_SWEEP.json")
    print(dline)
    # LEG-LEVEL DEGRADATION: the slow-slide legs need more tape than the 5d/21d pair. A name with
    # 8 months of history is screened on 5d/21d/grind21/63d and NOT on bleed52 — that is a partial
    # screen, and reporting it as a full one is the degraded-as-observation failure.
    short = {"63d": 0, "bleed52": 0}
    for s in syms:
        n = len(((bars.get(s) or {}).get("close")) or [])
        if I.MIN_BARS <= n < I.BARS_63:
            short["63d"] += 1
        if I.MIN_BARS <= n < I.BLEED_MIN_BARS:
            short["bleed52"] += 1
    if any(short.values()):
        print(f"LEG COVERAGE: {short['63d']} priced names have <{I.BARS_63} bars (63d leg not "
              f"evaluated) and {short['bleed52']} have <{I.BLEED_MIN_BARS} bars (bleed52 leg not "
              f"evaluated) — screened, but on FEWER legs than the headline suggests")
    by_leg: dict[str, int] = {}
    for h in hits:
        for lg in h.get("legs") or []:
            by_leg[lg] = by_leg.get(lg, 0) + 1
    # STANDING vs NEW. "0 new/deepened" on a day when 114 names are still dislocated reads as a
    # quiet tape to anyone skimming. Both numbers, always.
    print(f"[us_broad] {today}: {scanned} screened · {len(new_state)} names STILL in dislocation "
          f"(carried) · {len(hits)} new/deepened dislocations "
          f"(by leg: {by_leg or 'none'}; shapes: "
          f"{ {s: sum(1 for h in hits if h['shape'] == s) for s in ('BREAK', 'GRIND', 'SLOW_BLEED')} }) "
          f"· sector context resolved for {n_sector}/{len(hits)} [{sector_status}]"
          f" — ALL UNRESEARCHED, PROPOSES ONLY")

    if dry_run:
        print("[us_broad] --dry-run: no state/JSON written")
        return hits
    STATE.write_text(json.dumps(new_state, indent=1))
    OUT_JSON.write_text(json.dumps({
        "asof": today, "provenance": rep, "screened": scanned, "legs": list(legs),
        "standing_dislocations": len(new_state),
        "benchmark": BENCH,
        "bench_r21_pct": round(I._moves(bars.get(BENCH))[2], 2),
        "bench_r63_pct": round(I._window_move(bars.get(BENCH), I.BARS_63 - 1)[1], 2),
        "leg_counts": by_leg, "leg_coverage_short": short,
        "sector_context": {"resolved": n_sector, "status": sector_status},
        "coverage": drep, "hits": hits}, indent=1))
    return hits


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="screen only the first N symbols")
    ap.add_argument("--dry-run", action="store_true", help="print fires; write no state/JSON")
    ap.add_argument("--refresh-universe", action="store_true",
                    help="force a cap-ladder refetch (8 screener calls) instead of the weekly cache")
    ap.add_argument("--quiet-sessions", type=int, default=I.QUIET_SESSIONS)
    ap.add_argument("--legs", default=",".join(I.LEGS_ALL),
                    help=f"comma-separated subset of {','.join(I.LEGS_ALL)}")
    a = ap.parse_args()
    sweep(limit=a.limit, dry_run=a.dry_run, refresh_universe=a.refresh_universe,
          quiet_sessions=a.quiet_sessions,
          legs=tuple(x.strip() for x in a.legs.split(",") if x.strip()))
