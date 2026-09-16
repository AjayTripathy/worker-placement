"""intl_dislocation_sweep — the INTERNATIONAL leg of the dislocation watch (built 2026-08-11).

THE GAP IT FILLS: dislocation_sweep watches the ~320 names we already have a verdict on, and
broken_print_radar scans the whole US tape — both are blind outside the US ledger. Meanwhile the
desk has spent months building international SHELVES it never watches: the EDINET Japan universe,
the LSE price-explorer universe (~1,599), the Euronext/Nordic shelf (~502), the KRX value
universe. A name on those shelves can fall 25% in a fortnight and nothing on the desk notices.
This is the tape watch over that stored paper.

TAPE SCREEN ONLY. It re-screens no fundamentals — the shelves already carry the cheapness work
(and would be stale here anyway). The only question asked is: did this name fall hard, and did its
OWN market fall with it?

SIGNAL = idiosyncratic drawdown vs the LOCAL index, never vs SPY. A Tokyo small-cap measured
against SPY is measuring the yen and the Nikkei, not the company (the beta-bleed lesson in its
cross-border form). Benchmarks by suffix: Nikkei 225 for .T, FTSE 100 for .L, KOSPI/KOSDAQ for
.KS/.KQ, STOXX 600 for the European suffixes with local Nordic overrides. Where no benchmark
series is available the RAW move is used and the fire says bench=UNAVAILABLE(raw) — an unbenchmarked
fire is labelled as such, never quietly presented as excess.

    DISLOC:  excess_5d <= -8%  or excess_21d <= -15%    (HIGH at <= -12% / <= -20%)

TWO GUARDS THE FIRST LIVE RUN FORCED (2026-08-11):
  - DATE-ALIGNED benchmark. Yahoo's index series carry a different holiday/missing-day grid from
    the constituent tape, so comparing close[-6] to close[-6] reads a 5-session stock window
    against a 7-session index window. The benchmark is looked up AS OF the stock's own anchor
    dates, and a bench close staler than 5 days is refused (-> raw, labelled).
  - RAW-DROP guard. A name that ROSE is not dislocated. A KOSDAQ name +7.4%/5d fired on the first
    run purely because the index was +15.9%; underperforming a ripping index is relative weakness,
    a different and much weaker claim, and it must not send the desk to re-underwrite.

DEGRADED-LOUD (the facilities_resolver doctrine, applied to the tape): Yahoo drops international
lines in waves — a sweep that priced 300 of 1,200 names and reported a quiet tape is WRONG, and the
failure is INFRASTRUCTURE, not an observation. Every run prints 'X of Y priced; Z DEGRADED' and
names the casualties. Unpriced names go through a fallback ladder (alternate suffix forms, then the
local IBKR gateway) before being counted degraded; a name the gateway quotes but Yahoo has no
history for is reported as a DATA GAP (alive, unscreenable), never as "no dislocation".

PROPOSES ONLY. Identical to the US sweep: cause-check -> discovery_state -> independent court
(v1.4) -> thesis doc -> THEN staging. Names NOT in the research ledger fire as ENQUEUE-CANDIDATEs
— the fire is a request for intake, not a position.

Emits DETFIRE|intl_dislocation|<ticker>|<SEV>|<evidence> lines; the registry's detector_scan
extractor turns them into DETECTOR_FIRE signals in desk_feed.jsonl / desk_actionable.json (the
same path dislocation_sweep uses — the sweep never writes the feed itself). Writes
data/INTL_DISLOCATION_SWEEP.json + data/intl_dislocation_state.json (new-vs-deepened dedup).

  python3 verticals/generators/intl_dislocation_sweep.py [--limit 150] [--dry-run] [--no-gw]
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DATA = HERE / "data"
OUT_JSON = DATA / "INTL_DISLOCATION_SWEEP.json"
STATE = DATA / "intl_dislocation_state.json"
LEDGER = ROOT / "desk" / "data" / "research_ledger.json"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ---------------------------------------------------------------- tunables (top, per house rule)
MIN_EXCESS_5 = -8.0          # MED gate, 5 sessions, excess vs the LOCAL index
MIN_EXCESS_21 = -15.0        # MED gate, 21 sessions
HIGH_EXCESS_5 = -12.0
HIGH_EXCESS_21 = -20.0
MOONSHOT_R21 = 15.0          # a pullback after a +15%/21d run is not cheapness
MAX_BENCH_GAP_DAYS = 5       # a benchmark close staler than this vs the stock's anchor = UNAVAILABLE
SUSPECT_R21 = -70.0          # below this, a "move" is almost always an unadjusted corporate action
SUSPECT_SESSION = -30.0      # ...and so is a SINGLE session this deep — the split/consolidation tell
QUIET_SESSIONS = 10          # re-alert only on a tier deepening inside this window
MIN_BARS = 22                # 21 sessions + today

# ---------------------------------------------------------------- SLOW-SLIDE legs (added 2026-08-13)
# WHY THEY EXIST — the SPGI miss. SPGI ground 457.38 (7/16) -> 405.24 (8/6), -11.4% peak-to-trough
# over 17 sessions with SPY flat, and NOTHING saw it. The universe gap was only half the story: the
# point-to-point legs above CANNOT see that shape either. As-of 8/6 SPGI's 21-session point-to-point
# excess was only -9.0pp (the t-21 anchor, 7/8, was itself already a local low) and its best 5d
# excess across the whole slide was -7.9pp — both comfortably inside the -15/-8 gates. Measured
# peak-anchored instead, the same tape reads -11.0pp of excess drawdown. Point-to-point return is
# ANCHOR-LUCKY; a grind needs a peak-anchored measure.
#
# Three legs, all optional (`legs=` on scan) and all OFF for the international sweep by default:
#   grind21  — excess drawdown from the 21-session HIGH (the SPGI shape)
#   63d      — point-to-point excess over ~3 months (multi-month grind no 21d window ever shows)
#   bleed52  — drawdown-from-52w-high vs the benchmark's own, and STILL WIDENING (the shape that
#              never fires on any fixed window because it never falls fast, only far)
#
# BANDS ARE CALIBRATED, NOT GUESSED (S&P 500, 5 as-of dates spanning +18.5%/-5.2% SPY 63d regimes;
# house rule = a narrow 2-15%-fire detector, not a market-regime readout):
#   grind21 <= -11pp + guards  ->  1.6-11.6% of the index fires (marginal add over 5d/21d: 0.8-4.8%)
#   63d     <= -20pp + raw <= -10%  ->  4.6-14.8%.  The raw floor is load-bearing: with only the
#           "raw must be negative" guard, -14pp fired 30% of the index on 2026-06-30 because SPY was
#           +18.5%/63d — lagging a ripping tape is relative weakness, not a dislocation, and that is
#           the beta-bleed error in its long-window form.
#   bleed52 <= -25pp gap AND >= 5pp of WIDENING over 21 sessions  ->  2.6-8.8%. Without the widening
#           test a stale loser re-fires forever; the widening is what makes it news.
GRIND_MIN_EXCESS_DD21 = -11.0   # MED: excess drawdown from the 21-session high
GRIND_HIGH_EXCESS_DD21 = -18.0
GRIND_MIN_RAW_DD21 = -8.0       # the name must actually be down off its own high, not just lag
GRIND_MIN_PEAK_AGE = 5          # the high must be >=5 sessions old — a 2-day break is the radar's job
GRIND_MAX_SESSION = -8.0        # any single session worse than this = a BREAK (broken_print_radar), not a grind
MIN_EXCESS_63 = -20.0           # MED, ~3 months point-to-point
HIGH_EXCESS_63 = -28.0
MIN_RAW_63 = -10.0              # long-window beta-bleed guard (see calibration note above)
BARS_63 = 64                    # 63 sessions + today
BLEED_GAP52 = -25.0             # MED: (name dd-from-52w-high) - (bench dd-from-its-own-52w-high)
BLEED_HIGH_GAP52 = -40.0
BLEED_WIDEN = -5.0              # ...and the gap must have widened >=5pp over the trailing 21 sessions
BLEED_HIGH_WIDEN = -8.0
BLEED_MIN_BARS = 130            # ~6 months: below this a "52-week high" is not one

LEGS_DEFAULT = ("5d", "21d")                                # what the international sweep runs
LEGS_ALL = ("5d", "21d", "grind21", "63d", "bleed52")       # what the broad-US leg runs
_TIER = {"MED": 1, "HIGH": 2}

BATCH = 150                  # yfinance names per download call
PAUSE = 0.6                  # polite gap between batches (seconds)
RETRIES = 2                  # per-batch retries inside batch_history
TIME_BUDGET_S = 480          # wall clock for the price pull; the runner kills a watch at 600s
GW_FALLBACK_CAP = 300        # most-recently-unpriced names to ask the local gateway about

# verdict first-words that mean "we decided NOT to own this" — reuse the US sweep's list
try:
    from verticals.generators.dislocation_sweep import DEAD_VERDICTS
except Exception:                                                           # pragma: no cover
    DEAD_VERDICTS = ("AVOID", "PASS", "DECLINE", "KILL", "SELL", "EXIT", "SOLD", "REJECT", "TRAP")

# ---------------------------------------------------------------- stored international universes
#   (tag, path, rows-key or None for a list/keyed-dict file, symbol field or None for dict keys)
SOURCES = [
    ("lse_universe",       ROOT / "verticals/generators/data/LSE_UNIVERSE.json", "rows", "sym"),
    ("lse_shelf",          ROOT / "verticals/generators/data/LSE_SHELF.json", "rows", "sym"),
    ("euronext_shelf",     ROOT / "verticals/generators/data/EURONEXT_SHELF.json", "rows", "sym"),
    ("euronext_universe",  ROOT / "verticals/generators/data/EURONEXT_UNIVERSE.json", "rows", "sym"),
    ("europe_shelf",       ROOT / "verticals/deep_value/global/data/europe_shortlist.json", "rows", "sym"),
    ("japan_shelf",        ROOT / "verticals/deep_value/global/data/japan_shortlist.json", None, "sym"),
    ("japan_nonpfic",      ROOT / "verticals/deep_value/global/data/japan_nonpfic_shortlist.json", "rows", "sym"),
    ("korea_shelf",        ROOT / "verticals/deep_value/global/data/korea_shortlist.json", None, "sym"),
    # px-cache files are keyed BY SYMBOL — they are the crawled screen universes (EDINET / KRX / ESEF)
    ("japan_edinet",       ROOT / "verticals/deep_value/global/data/japan_px_cache.json", None, None),
    ("krx_universe",       ROOT / "verticals/deep_value/global/data/korea_px_cache.json", None, None),
    ("europe_esef",        ROOT / "verticals/deep_value/global/data/europe_px_cache.json", None, None),
]

# ---------------------------------------------------------------- local index proxies
BENCH_BY_SUFFIX = {
    "T": "^N225",       # Nikkei 225 (TOPIX ^TOPX is not served by Yahoo)
    "L": "^FTSE",
    "KS": "^KS11",      # KOSPI
    "KQ": "^KQ11",      # KOSDAQ
    "ST": "^OMX",       # Stockholm
    "HE": "^OMXH25",    # Helsinki
    "CO": "^OMXC25",    # Copenhagen
    "OL": "^OSEAX",     # Oslo
    "PA": "^STOXX", "AS": "^STOXX", "BR": "^STOXX", "LS": "^STOXX",
    "DE": "^STOXX", "MI": "^STOXX", "MC": "^STOXX", "SW": "^STOXX",
    "VI": "^STOXX", "AT": "^STOXX", "IR": "^STOXX", "WA": "^STOXX",
}
# IB exchange/currency per suffix, for the gateway fallback leg
GW_VENUE = {
    "T": ("TSEJ", "JPY"), "L": ("LSE", "GBP"), "KS": ("KRX", "KRW"), "KQ": ("KRX", "KRW"),
    "ST": ("SFB", "SEK"), "HE": ("HEX", "EUR"), "CO": ("CPH", "DKK"), "OL": ("OSE", "NOK"),
    "PA": ("SBF", "EUR"), "AS": ("AEB", "EUR"), "BR": ("ENEXT.BE", "EUR"), "LS": ("BVL", "EUR"),
    "DE": ("IBIS", "EUR"), "MI": ("BVME", "EUR"), "MC": ("BM", "EUR"), "SW": ("EBS", "CHF"),
    "VI": ("VSE", "EUR"), "WA": ("WSE", "PLN"),
}

DOCTRINE = (" — PROPOSES ONLY: cause-check -> discovery_state -> court (v1.4) before any staging;"
            " a shallow 'no cause found' is beta, not a dislocation")


# ---------------------------------------------------------------- universe
def _suffix(sym: str) -> str:
    return sym.rsplit(".", 1)[-1].upper() if "." in sym else ""


def bench_symbol(sym: str) -> str | None:
    """The LOCAL index proxy for a symbol, or None (-> raw moves, labelled UNAVAILABLE)."""
    return BENCH_BY_SUFFIX.get(_suffix(sym))


def load_ledger() -> dict[str, str]:
    """symbol -> verdict, over both the ledger `ticker` and its `yf` alias."""
    out: dict[str, str] = {}
    try:
        for r in json.loads(LEDGER.read_text()).get("names", []):
            v = (str(r.get("verdict") or "").strip().upper().split(" ")[0] or "UNJUDGED")[:24]
            for k in (r.get("ticker"), r.get("yf")):
                if k:
                    out[str(k)] = v
    except Exception:
        pass
    return out


def load_universe(sources=None, ledger: dict[str, str] | None = None) -> dict[str, dict]:
    """symbol -> {shelf, bench, researched, verdict}; deduped, first shelf listed wins the tag.

    Names carrying a DEAD verdict (AVOID/PASS/TRAP/...) are dropped: we already decided not to own
    them, so their drawdowns are not our business (same rule as the US sweep)."""
    ledger = load_ledger() if ledger is None else ledger
    uni: dict[str, dict] = {}
    dropped_dead = 0
    for tag, path, rows_key, sym_key in (sources or SOURCES):
        try:
            d = json.loads(Path(path).read_text())
        except Exception:
            continue
        if rows_key:
            rows = d.get(rows_key) or []
            syms = [r.get(sym_key) for r in rows if isinstance(r, dict)]
        elif sym_key:
            rows = d if isinstance(d, list) else (d.get("rows") or [])
            syms = [r.get(sym_key) for r in rows if isinstance(r, dict)]
        else:                                              # dict keyed by symbol (a px cache)
            syms = list(d.keys()) if isinstance(d, dict) else []
        for s in syms:
            if not s or not isinstance(s, str) or "." not in s or s in uni:
                continue
            verdict = ledger.get(s)
            if verdict and any(verdict.startswith(x) for x in DEAD_VERDICTS):
                dropped_dead += 1
                continue
            uni[s] = {"shelf": tag, "bench": bench_symbol(s),
                      "researched": bool(verdict), "verdict": verdict or "UNRESEARCHED"}
    if dropped_dead:
        print(f"[intl_dislocation_sweep] {dropped_dead} shelf names dropped on a DEAD ledger verdict")
    return uni


# ---------------------------------------------------------------- price ladder
def alt_symbols(sym: str) -> list[str]:
    """Suffix-hardening candidates for a symbol Yahoo refused. Order = most likely first."""
    out = []
    base, _, suf = sym.rpartition(".")
    if not base:
        base, suf = sym, ""
    if suf.upper() == "KS":
        out.append(base + ".KQ")                       # KOSPI/KOSDAQ mislabel (the common KRX miss)
    elif suf.upper() == "KQ":
        out.append(base + ".KS")
    if "-" in base:
        out.append(base.replace("-", ".") + ("." + suf if suf else ""))
    if len(suf) == 1 and suf.isalpha() and suf.upper() not in BENCH_BY_SUFFIX:
        # US CLASS SHARE, the direction the intl ladder never needed: the index list says BRK.B and
        # Yahoo wants BRK-B. This is exactly what cost the first broad-US pull BRK.B and BF.B.
        out.append(sym.replace(".", "-"))
    if suf and suf.upper() != suf:
        out.append(base + "." + suf.upper())
    if base.startswith("0") and suf.upper() in ("KS", "KQ"):
        out.append(base.lstrip("0") + "." + suf.upper())
    return [x for x in dict.fromkeys(out) if x != sym]


def fetch_bars(symbols: list[str], *, batch: int = BATCH, pause: float = PAUSE,
               retries: int = RETRIES, budget_s: float = TIME_BUDGET_S,
               period: str = "3mo", label: str = "intl_dislocation_sweep",
               verbose: bool = True) -> tuple[dict, list[str]]:
    """Batched daily closes for `symbols`. Returns (bars, not_swept).

    not_swept = names the wall-clock budget cut off. They are NOT 'unpriced' (we never asked) and
    are reported separately — an un-asked name must never read as a quiet one.
    `period` is a parameter because the slow-slide legs need a year of tape, not a quarter: a
    52-week-high measure computed off a 3-month window is not a 52-week-high measure."""
    from desk.broken_print_radar import batch_history
    bars: dict[str, dict] = {}
    t0 = time.time()
    todo = list(dict.fromkeys(symbols))
    done = 0
    for k in range(0, len(todo), batch):
        if time.time() - t0 > budget_s:
            return bars, todo[k:]
        chunk = todo[k:k + batch]
        bars.update(batch_history(chunk, period=period, batch=batch, retries=retries,
                                  pause=pause, verbose=False))
        done += len(chunk)
        if verbose:
            print(f"[{label}] swept {done}/{len(todo)} — {len(bars)} priced "
                  f"({time.time() - t0:.0f}s)", flush=True)
    return bars, []


def gw_probe(symbols: list[str], verbose: bool = True,
             default_venue: tuple[str, str] | None = None) -> tuple[dict[str, dict], str]:
    """Ask the LOCAL IBKR gateway whether the still-unpriced names are alive. -> (alive, status).

    The gateway is a QUOTE source, not a history source: it cannot give us a 5d/21d move. What it
    CAN do is separate 'Yahoo dropped a live line' (infrastructure failure — loud) from 'this
    symbol is dead/misspelled' (a universe-hygiene fact). Never silently upgrades a name to priced.
    `default_venue` handles suffix-less (US) symbols — the US sweep passes ("SMART", "USD").

    The STATUS is returned, never swallowed: 'probe did not run' and 'probe ran, found nothing' are
    different facts, and reporting the second when the first happened is the degraded-as-observation
    failure this whole module is built against."""
    out: dict[str, dict] = {}
    try:
        from desk.gw_quotes import bulk_quotes
    except Exception as e:
        return out, f"NOT RUN (desk.gw_quotes unimportable: {type(e).__name__})"
    by_venue: dict[tuple, dict[str, str]] = {}                    # venue -> {ib_symbol: orig}
    for s in symbols[:GW_FALLBACK_CAP]:
        suf = _suffix(s)
        if suf in GW_VENUE:
            by_venue.setdefault(GW_VENUE[suf], {})[s.rsplit(".", 1)[0]] = s
        elif default_venue:
            by_venue.setdefault(default_venue, {})[s.replace(".", " ")] = s
    if not by_venue:
        return out, "NOT RUN (no IB venue mapping for any unpriced name)"
    probed, failed = 0, []
    for (exch, ccy), mapping in by_venue.items():
        try:
            qs = bulk_quotes(sorted(mapping), exchange=exch, currency=ccy, verbose=False)
        except Exception as e:
            failed.append(f"{exch}:{type(e).__name__}")
            if verbose:
                print(f"[intl_dislocation_sweep] gateway probe {exch} failed: {type(e).__name__}")
            continue
        probed += len(mapping)
        for ibsym, orig in mapping.items():
            q = qs.get(ibsym)
            if q:
                out[orig] = {"px": q["px"], "venue": exch}
    status = f"ran on {probed} name(s) across {len(by_venue)} venue(s)"
    if failed:
        status += f"; venue failures {', '.join(failed)}"
    return out, status


# ---------------------------------------------------------------- the screen (pure, testable)
def _moves(entry: dict | None) -> tuple[float, float, float, list[str]] | None:
    """(last, r5%, r21%, [d_now, d_5, d_21]) for one bar series, or None if too thin."""
    closes = ((entry or {}).get("close")) or []
    if len(closes) < MIN_BARS:
        return None
    last, c5, c21 = closes[-1], closes[-6], closes[-MIN_BARS]
    if not (last and c5 and c21) or c5 <= 0 or c21 <= 0:
        return None
    dates = ((entry or {}).get("dates")) or []
    anchors = [dates[-1], dates[-6], dates[-MIN_BARS]] if len(dates) == len(closes) else []
    return last, (last / c5 - 1) * 100.0, (last / c21 - 1) * 100.0, anchors


def _asof_index(entry: dict | None, d: str, max_gap_days: int = MAX_BENCH_GAP_DAYS) -> int | None:
    """Index of the last bar at or before date `d`, or None if there is none / it is too stale.

    THE one place date-alignment is implemented. Positional alignment (index close[-6] vs stock
    close[-6]) silently drifts: Yahoo's index series carry different holiday/missing-day grids from
    the constituent tape, so a 5-session window on one side can span 7 on the other and manufacture
    double-digit 'excess'. Every benchmark measure below goes through this lookup, and refuses the
    comparison (-> raw moves, labelled) when the nearest available close is more than
    `max_gap_days` stale."""
    closes = ((entry or {}).get("close")) or []
    dates = ((entry or {}).get("dates")) or []
    if len(closes) < 2 or len(dates) != len(closes):
        return None
    import bisect
    i = bisect.bisect_right(dates, d) - 1
    if i < 0 or not closes[i] or closes[i] <= 0:
        return None
    try:
        gap = (datetime.date.fromisoformat(d) - datetime.date.fromisoformat(dates[i])).days
    except Exception:
        return None
    return i if gap <= max_gap_days else None


def _asof(entry: dict | None, d: str, max_gap_days: int = MAX_BENCH_GAP_DAYS) -> float | None:
    """Close of the last bar at or before `d`, date-aligned and staleness-refused."""
    i = _asof_index(entry, d, max_gap_days)
    return None if i is None else ((entry or {}).get("close") or [])[i]


def _bench_moves(entry: dict | None, anchors: list[str],
                 max_gap_days: int = MAX_BENCH_GAP_DAYS) -> tuple[float, float] | None:
    """Benchmark 5d/21d moves DATE-ALIGNED to the stock's own anchor dates (see _asof_index)."""
    if len(anchors) != 3:
        return None
    b0, b5, b21 = (_asof(entry, a, max_gap_days) for a in anchors)
    if not (b0 and b5 and b21):
        return None
    return (b0 / b5 - 1) * 100.0, (b0 / b21 - 1) * 100.0


def _bench_ret(entry: dict | None, d_from: str, d_to: str,
               max_gap_days: int = MAX_BENCH_GAP_DAYS) -> float | None:
    """Benchmark % return between two dates, both looked up AS OF (never positionally)."""
    a, b = _asof(entry, d_from, max_gap_days), _asof(entry, d_to, max_gap_days)
    return None if not (a and b) else (b / a - 1) * 100.0


def _window_move(entry: dict | None, n: int) -> tuple[float, float, list[str]] | None:
    """(last, % return over the trailing n sessions, [d_now, d_anchor]) or None if too thin."""
    closes = ((entry or {}).get("close")) or []
    dates = ((entry or {}).get("dates")) or []
    if len(closes) < n + 1 or len(dates) != len(closes):
        return None
    last, c0 = closes[-1], closes[-(n + 1)]
    if not (last and c0) or c0 <= 0:
        return None
    return last, (last / c0 - 1) * 100.0, [dates[-1], dates[-(n + 1)]]


def _drawdown(entry: dict | None, n: int) -> dict | None:
    """Peak-anchored drawdown over the trailing n sessions — the measure point-to-point misses.

    Returns {dd_pct, peak_age (sessions since the high), worst_session_pct, d_peak, d_now, last}.
    `worst_session_pct` separates a GRIND from a BREAK: a -20% single session inside the window is
    broken_print_radar's beat, already covered, and must not be re-reported here as a slow slide."""
    closes = ((entry or {}).get("close")) or []
    dates = ((entry or {}).get("dates")) or []
    if len(closes) < n + 1 or len(dates) != len(closes):
        return None
    w, wd = closes[-(n + 1):], dates[-(n + 1):]
    if any((not c) or c <= 0 for c in w):
        return None
    # LAST occurrence of the high, not the first. A name that sat at 100 for three weeks, printed
    # 100 again three sessions ago and then broke would otherwise report a 21-session-old peak and
    # sail through the "must be an old high" guard as a grind — when it is a two-day break that
    # broken_print_radar already fired on. The honest reading of "how long has this been falling"
    # is measured from the most recent time it was at its high.
    hi = max(w)
    pk = len(w) - 1 - w[::-1].index(hi)
    worst = min((w[k] / w[k - 1] - 1) * 100.0 for k in range(1, len(w)))
    return {"last": w[-1], "dd_pct": (w[-1] / w[pk] - 1) * 100.0,
            "peak_age": len(w) - 1 - pk, "worst_session_pct": worst,
            "d_peak": wd[pk], "d_now": wd[-1]}


def _worst_session(entry: dict | None, n: int) -> float | None:
    """The deepest SINGLE-session % move in the trailing n sessions.

    Cheap, and it answers two different questions: whether a fall is a grind or a break, and
    whether it is a fall at all — a lone -50% print on a mega-cap is an unadjusted split far more
    often than a tape move (first live run: MNST printed -50.6%/5d)."""
    closes = ((entry or {}).get("close")) or []
    if len(closes) < n + 1:
        return None
    w = closes[-(n + 1):]
    if any((not c) or c <= 0 for c in w):
        return None
    return min((w[k] / w[k - 1] - 1) * 100.0 for k in range(1, len(w)))


def _bench_drawdown(entry: dict | None, d_peak: str, d_now: str,
                    max_gap_days: int = MAX_BENCH_GAP_DAYS) -> float | None:
    """The benchmark's OWN drawdown from its high over the stock's [d_peak, d_now] calendar span.

    Not `bench(d_now)/bench(d_peak)`: the index's high need not fall on the stock's high. Comparing
    a peak-anchored stock drawdown to a point-to-point index return would charge the stock for the
    index's own subsequent rally and inflate every 'excess'."""
    i0 = _asof_index(entry, d_peak, max_gap_days)
    i1 = _asof_index(entry, d_now, max_gap_days)
    if i0 is None or i1 is None or i1 < i0:
        return None
    closes = (entry or {}).get("close") or []
    hi = max(closes[i0:i1 + 1])
    return None if not hi or hi <= 0 else (closes[i1] / hi - 1) * 100.0


def _dd_from_high(entry: dict | None, d: str, min_bars: int = BLEED_MIN_BARS,
                  max_gap_days: int = MAX_BENCH_GAP_DAYS) -> float | None:
    """Drawdown (%) from the running high of everything on the tape up to and including `d`.

    Uses ONLY bars at or before `d`, so it is honest when evaluated 21 sessions in the past (the
    widening test) — a running high computed off the full series would leak the future into the
    'before' reading and manufacture widening out of nothing."""
    i = _asof_index(entry, d, max_gap_days)
    if i is None or i + 1 < min_bars:
        return None
    closes = (entry or {}).get("close") or []
    hi = max(closes[:i + 1])
    return None if not hi or hi <= 0 else (closes[i] / hi - 1) * 100.0


def _leg_grind21(entry: dict, bench: dict | None, out: dict) -> str | None:
    """Excess drawdown from the 21-session high — the SPGI shape. -> 'MED' | 'HIGH' | None."""
    dd = _drawdown(entry, MIN_BARS - 1)
    if dd is None:
        return None
    bdd = _bench_drawdown(bench, dd["d_peak"], dd["d_now"]) if bench else None
    exdd = dd["dd_pct"] - (bdd if bdd is not None else 0.0)
    out.update({"dd21_pct": round(dd["dd_pct"], 1), "excess_dd21_pct": round(exdd, 1),
                "bench_dd21_pct": (round(bdd, 1) if bdd is not None else None),
                "peak_age_sessions": dd["peak_age"],
                "worst_session_pct": round(dd["worst_session_pct"], 1),
                "peak_date": dd["d_peak"]})
    if dd["dd_pct"] > GRIND_MIN_RAW_DD21:                      # not actually off its own high
        return None
    if dd["peak_age"] < GRIND_MIN_PEAK_AGE:                    # 2-day break, not a grind
        return None
    if dd["worst_session_pct"] <= GRIND_MAX_SESSION:           # a BREAK — broken_print_radar's beat
        return None
    if exdd <= GRIND_HIGH_EXCESS_DD21:
        return "HIGH"
    return "MED" if exdd <= GRIND_MIN_EXCESS_DD21 else None


def _leg_63d(entry: dict, bench: dict | None, out: dict) -> str | None:
    """~3-month point-to-point excess: the multi-month grind no 21d window ever shows."""
    m = _window_move(entry, BARS_63 - 1)
    if m is None:
        return None
    last, r63, anchors = m
    b63 = _bench_ret(bench, anchors[1], anchors[0]) if bench else None
    ex63 = r63 - (b63 if b63 is not None else 0.0)
    out.update({"r63_pct": round(r63, 1), "excess63_pct": round(ex63, 1),
                "bench_r63_pct": (round(b63, 1) if b63 is not None else None)})
    if r63 > MIN_RAW_63:            # lagging a ripping tape is relative weakness, not a dislocation
        return None
    if ex63 <= HIGH_EXCESS_63:
        return "HIGH"
    return "MED" if ex63 <= MIN_EXCESS_63 else None


def _leg_bleed52(entry: dict, bench: dict | None, anchors: list[str], out: dict) -> str | None:
    """Drawdown-from-52w-high vs the benchmark's own — and STILL WIDENING.

    The shape that never fires on any fixed window because it never falls fast, only far. The
    widening test (gap today vs gap 21 sessions ago, both computed from bars available AT THAT
    TIME) is what keeps a stale loser from re-firing forever: only a gap that is still opening is
    news."""
    now, then = anchors[0], anchors[2]
    dd_now, dd_then = _dd_from_high(entry, now), _dd_from_high(entry, then)
    if dd_now is None or dd_then is None:
        return None
    b_now = _dd_from_high(bench, now) if bench else None
    b_then = _dd_from_high(bench, then) if bench else None
    if b_now is None or b_then is None:
        # UNLIKE the other legs, this one has no honest raw fallback: without a benchmark the "gap"
        # collapses into plain drawdown-from-high, which is true of every name in a bear market.
        out["bleed52_status"] = "NO ALIGNED BENCHMARK — leg not evaluated (raw dd-from-high is not a gap)"
        return None
    gap_now = dd_now - b_now
    gap_then = dd_then - b_then
    widen = gap_now - gap_then
    out.update({"dd52_pct": round(dd_now, 1), "bench_dd52_pct": (round(b_now, 1) if b_now is not None else None),
                "gap52_pct": round(gap_now, 1), "gap52_widened_pp": round(widen, 1)})
    if gap_now <= BLEED_HIGH_GAP52 and widen <= BLEED_HIGH_WIDEN:
        return "HIGH"
    return "MED" if (gap_now <= BLEED_GAP52 and widen <= BLEED_WIDEN) else None


def shape_of(legs: list[str]) -> str:
    """BREAK / GRIND / SLOW_BLEED — what KIND of fall this is, so triage knows what it is reading."""
    if {"5d", "21d"} & set(legs):
        return "BREAK"
    if {"grind21", "63d"} & set(legs):
        return "GRIND"
    return "SLOW_BLEED"


def scan(bars: dict, uni: dict, state: dict, today: str, *,
         min_excess5: float = MIN_EXCESS_5, min_excess21: float = MIN_EXCESS_21,
         quiet_sessions: int = QUIET_SESSIONS,
         legs: tuple[str, ...] = LEGS_DEFAULT) -> tuple[list[dict], dict, int]:
    """Pure screen: (hits, new_state, n_scanned). `bars` = {sym: {close, dates}} incl benchmarks.

    `legs` selects which windows are armed. The international sweep runs LEGS_DEFAULT (5d/21d
    point-to-point, unchanged); the broad-US leg runs LEGS_ALL, adding the three slow-slide legs
    calibrated at the top of this module. Severity is the deepest tier any armed leg reaches, and
    every firing leg is named in the hit so triage never has to guess which window saw it."""
    state = dict(state)
    hits, scanned = [], 0
    for sym in sorted(uni):
        meta = uni[sym]
        entry = bars.get(sym)
        m = _moves(entry)
        if m is None:
            continue
        scanned += 1
        last, r5, r21, anchors = m
        bsym = meta.get("bench")
        bench = bars.get(bsym) if bsym else None
        bm = _bench_moves(bench, anchors) if bsym else None
        b5, b21 = bm if bm else (0.0, 0.0)
        bench_label = bsym if bm else "UNAVAILABLE(raw)"
        ex5, ex21 = r5 - b5, r21 - b21
        if r21 > MOONSHOT_R21:
            continue
        extra: dict = {}
        fired: dict[str, str] = {}
        # RAW-DROP GUARD: a name that ROSE is not dislocated. Underperforming a ripping index is
        # relative weakness — a different and much weaker claim — and firing it as a "dislocation"
        # sends the desk to re-underwrite a name whose tape never broke (first live run: a KOSDAQ
        # name +7.4%/5d fired purely because the index was +15.9%).
        if "5d" in legs and r5 <= 0:
            if ex5 <= HIGH_EXCESS_5:
                fired["5d"] = "HIGH"
            elif ex5 <= min_excess5:
                fired["5d"] = "MED"
        if "21d" in legs and r21 <= 0:
            if ex21 <= HIGH_EXCESS_21:
                fired["21d"] = "HIGH"
            elif ex21 <= min_excess21:
                fired["21d"] = "MED"
        if "grind21" in legs and (t := _leg_grind21(entry, bench, extra)):
            fired["grind21"] = t
        if "63d" in legs and (t := _leg_63d(entry, bench, extra)):
            fired["63d"] = t
        if "bleed52" in legs and (t := _leg_bleed52(entry, bench, anchors, extra)):
            fired["bleed52"] = t
        sev = max(fired.values(), key=lambda s: _TIER[s]) if fired else None
        prior = state.get(sym, {})
        if sev is None:
            state.pop(sym, None)                                  # recovered — re-arm
            continue
        leg_names = sorted(fired)
        # Repeat suppression: same tier AND no NEW leg. A name that was grinding and now also
        # breaks on 5d is new information even at the same severity, so a widened leg set re-fires.
        if prior and prior.get("sev") == sev and not (set(leg_names) - set(prior.get("legs") or [])):
            try:
                age = (datetime.date.fromisoformat(today)
                       - datetime.date.fromisoformat(prior.get("fired", today))).days
                if age < quiet_sessions * 1.5:                    # calendar-day approximation
                    continue
            except Exception:
                pass
        state[sym] = {"sev": sev, "fired": today, "legs": leg_names,
                      "ex5": round(ex5, 1), "ex21": round(ex21, 1)}
        # CORPORATE-ACTION TELL, two forms. The -70%/21d form catches consolidation stubs on thin
        # foreign lines; the single-session form catches the US one the first live run surfaced —
        # MNST printed -50.6%/5d, and a mega-cap does not halve in a session, an unadjusted split
        # does. Both LABEL the fire (verify the CA history), neither suppresses it.
        worst21 = _worst_session(entry, MIN_BARS - 1)
        hits.append({"ticker": sym, "severity": sev, "px": round(last, 4),
                     "worst_session_21d_pct": (round(worst21, 1) if worst21 is not None else None),
                     "suspect_corporate_action": bool(
                         r21 <= SUSPECT_R21
                         or (worst21 is not None and worst21 <= SUSPECT_SESSION)),
                     "r5_pct": round(r5, 1), "r21_pct": round(r21, 1),
                     "excess5_pct": round(ex5, 1), "excess21_pct": round(ex21, 1),
                     "benchmark": bench_label, "bench_r5_pct": round(b5, 1),
                     "bench_r21_pct": round(b21, 1), "shelf": meta.get("shelf"),
                     "legs": leg_names, "leg_tiers": fired, "shape": shape_of(leg_names),
                     **extra,
                     "researched": bool(meta.get("researched")),
                     "verdict": meta.get("verdict", "UNRESEARCHED"), "fired": today})
    return hits, state, scanned


def leg_clause(hit: dict, compact: bool = False) -> str:
    """The evidence sentence for the slow-slide legs — only the legs that actually fired.

    A SLOW_BLEED hit's 5d/21d numbers are near zero by construction; printing only those would make
    the fire look like nothing happened. This says which window saw it and what it saw.
    `compact` keeps the NUMBERS and drops the prose, for the length-budget ladder in the broad-US
    fire line (see us_broad_dislocation_sweep.fire_line)."""
    legs = hit.get("legs") or []
    if compact:
        b = []
        if "grind21" in legs:
            b.append(f"dd21 {hit.get('excess_dd21_pct'):+.1f}pp (peak {hit.get('peak_date')})")
        if "63d" in legs:
            b.append(f"63d {hit.get('excess63_pct'):+.1f}pp")
        if "bleed52" in legs:
            b.append(f"gap52 {hit.get('gap52_pct'):+.1f}pp widening {hit.get('gap52_widened_pp'):+.1f}pp")
        return (" " + hit.get("shape", "") + ": " + " / ".join(b) + ".") if b else ""
    bits = []
    raw = " [RAW — no aligned benchmark, not excess]"
    if "grind21" in legs:
        bits.append(f"{hit.get('dd21_pct'):+.1f}% off its {hit.get('peak_age_sessions')}-session-old "
                    f"high ({hit.get('peak_date')}) = {hit.get('excess_dd21_pct'):+.1f}pp excess, "
                    f"worst session {hit.get('worst_session_pct'):+.1f}%"
                    + (raw if hit.get("bench_dd21_pct") is None else ""))
    if "63d" in legs:
        bits.append(f"63d {hit.get('r63_pct'):+.1f}% = {hit.get('excess63_pct'):+.1f}pp excess"
                    + (raw if hit.get("bench_r63_pct") is None else ""))
    if "bleed52" in legs:
        bits.append(f"{hit.get('dd52_pct'):+.1f}% off the 52w high vs the benchmark's "
                    f"{hit.get('bench_dd52_pct')}% = {hit.get('gap52_pct'):+.1f}pp gap, still "
                    f"WIDENING {hit.get('gap52_widened_pp'):+.1f}pp/21 sessions")
    return (" " + hit.get("shape", "") + ": " + "; ".join(bits) + ".") if bits else ""


def fire_line(hit: dict, detector: str = "intl_dislocation", shelf_word: str = "shelf",
              legs_text: str | None = None) -> str:
    """The DETFIRE line — same shape as dislocation_sweep, with the intake routing on top.

    `detector` is the tag the detector_scan extractor keys on; the broad-US leg passes
    'us_broad_dislocation' so its fires are attributable to the leg that found them.
    `legs_text` overrides the leg-evidence clause (the length-budget ladder uses it)."""
    if hit["researched"]:
        who = f"{hit['verdict']} (ledger; {shelf_word} {hit['shelf']})"
        route = " RESEARCHED -> re-underwrite against the standing verdict;"
    else:
        who = f"UNRESEARCHED ({hit['shelf']} {shelf_word})"
        route = " ENQUEUE-CANDIDATE: not in the research ledger — propose intake (court queue), not a position;"
    if hit.get("suspect_corporate_action"):
        # the ADIG thin-print rule in its corporate-action form: a -99%/21d "fall" on a foreign line
        # is a consolidation / delisting stub / unadjusted split far more often than a real break
        ws = hit.get("worst_session_21d_pct")
        what = (f"a single session of {ws:+.0f}%" if ws is not None and ws <= SUSPECT_SESSION
                else f"a {hit['r21_pct']:+.0f}%/21d line")
        route = (f" SUSPECT — {what} is usually an unadjusted CORPORATE "
                 f"ACTION (split, consolidation, delisting stub), not a tape move: verify the "
                 f"split/CA history before treating this as a dislocation;" + route)
    return (f"DETFIRE|{detector}|{hit['ticker']}|{hit['severity']}|{who} fell "
            f"{hit['r5_pct']:+.1f}%/5d {hit['r21_pct']:+.1f}%/21d = "
            f"{hit['excess5_pct']:+.1f}/{hit['excess21_pct']:+.1f}pp vs {hit['benchmark']} "
            f"@ {hit['px']:.2f}."
            f"{leg_clause(hit) if legs_text is None else legs_text}{route}{DOCTRINE}")


def degraded_line(requested: list[str], bars: dict, not_swept: list[str],
                  gw_alive: dict, name_cap: int = 40, gw_status: str = "",
                  store: str = "INTL_DISLOCATION_SWEEP.json") -> tuple[str, dict]:
    """'X of Y priced; Z DEGRADED (listed)' — the loud line. Never let an unpriced name pass quiet."""
    priced = [s for s in requested if len(((bars.get(s) or {}).get("close")) or []) >= MIN_BARS]
    thin = [s for s in requested if s in bars and s not in set(priced)]
    ns = set(not_swept)
    unpriced = [s for s in requested if s not in bars and s not in ns]
    deg = unpriced + thin + list(not_swept)
    rep = {"requested": len(requested), "priced": len(priced), "degraded": len(deg),
           "unpriced_no_data": len(unpriced), "thin_history": len(thin),
           "not_swept_time_budget": len(not_swept), "gw_probe": gw_status or "not attempted",
           "gw_alive_no_history": sorted(gw_alive), "degraded_names": sorted(deg)}
    shown = sorted(deg)[:name_cap]
    more = f" +{len(deg) - len(shown)} more ({store}:degraded_names)" if len(deg) > len(shown) else ""
    if gw_alive:
        gw = (f" | {len(gw_alive)} of them QUOTE LIVE at the IBKR gateway = a Yahoo history gap "
              f"(INFRA failure, not an observation)")
    elif deg:
        gw = f" | gateway liveness probe: {gw_status or 'not attempted'} — 0 alive"
    else:
        gw = ""
    line = (f"DEGRADED-LOUD: {len(priced)} of {len(requested)} priced; {len(deg)} DEGRADED "
            f"({len(unpriced)} no-data, {len(thin)} thin-history, {len(not_swept)} not-swept-time-budget)"
            f"{gw} — {', '.join(shown)}{more}")
    return line, rep


# ---------------------------------------------------------------- driver
def sweep(limit: int = 0, dry_run: bool = False, use_gw: bool = True,
          min_excess5: float = MIN_EXCESS_5, min_excess21: float = MIN_EXCESS_21,
          quiet_sessions: int = QUIET_SESSIONS) -> list[dict]:
    today = datetime.date.today().isoformat()
    uni = load_universe()
    syms = sorted(uni)
    if limit:
        # ROUND-ROBIN across shelves, not the first N alphabetically: the union sorts into long
        # single-venue runs (the first 150 names are all KRX 000xxx), so a truncated alphabetical
        # sweep is a one-country sample dressed up as an international one.
        by_shelf: dict[str, list[str]] = {}
        for s in syms:
            by_shelf.setdefault(uni[s]["shelf"], []).append(s)
        order, queues = [], list(by_shelf.values())
        for i in range(max(len(q) for q in queues)):
            for q in queues:
                if i < len(q):
                    order.append(q[i])
        syms = order[:limit]
        uni = {s: uni[s] for s in syms}
    benches = sorted({b for b in (uni[s]["bench"] for s in syms) if b})
    print(f"[intl_dislocation_sweep] {today}: universe {len(syms)} across "
          f"{len({uni[s]['shelf'] for s in syms})} shelves · {len(benches)} local benchmarks")

    bars, not_swept = fetch_bars(syms + benches)
    # --- fallback ladder: alternate suffix forms for anything Yahoo refused
    missing = [s for s in syms if len(((bars.get(s) or {}).get("close")) or []) < MIN_BARS
               and s not in set(not_swept)]
    alt_map = {a: s for s in missing for a in alt_symbols(s)}
    if alt_map:
        print(f"[intl_dislocation_sweep] retrying {len(missing)} unpriced via "
              f"{len(alt_map)} alternate suffix forms")
        alt_bars, _ = fetch_bars(sorted(alt_map), budget_s=60, verbose=False)
        for a, b in alt_bars.items():
            orig = alt_map[a]
            if len((b.get("close") or [])) >= MIN_BARS and orig not in bars:
                bars[orig] = b
                bars[orig]["symbol_fixed_to"] = a
    still = [s for s in syms if len(((bars.get(s) or {}).get("close")) or []) < MIN_BARS
             and s not in set(not_swept)]
    gw_alive, gw_status = gw_probe(still) if (use_gw and still) else ({}, "not attempted")

    state = {}
    try:
        state = json.loads(STATE.read_text())
    except Exception:
        pass
    hits, new_state, scanned = scan(bars, uni, state, today, min_excess5=min_excess5,
                                    min_excess21=min_excess21, quiet_sessions=quiet_sessions)
    for h in hits:
        print(fire_line(h))
    dline, drep = degraded_line(syms, bars, not_swept, gw_alive, gw_status=gw_status)
    print(dline)
    bench_dead = [b for b in benches if len(((bars.get(b) or {}).get("close")) or []) < MIN_BARS]
    if bench_dead:
        print(f"BENCHMARKS DEGRADED: {', '.join(bench_dead)} — those names screened on RAW moves "
              f"(labelled UNAVAILABLE(raw) in the fire line)")
    print(f"[intl_dislocation_sweep] {today}: {scanned} screened · {len(hits)} new/deepened "
          f"dislocations ({sum(1 for h in hits if not h['researched'])} unresearched) "
          f"— PROPOSES ONLY")

    if dry_run:
        print("[intl_dislocation_sweep] --dry-run: no state/JSON written")
        return hits
    STATE.write_text(json.dumps(new_state, indent=1))
    OUT_JSON.write_text(json.dumps({
        "asof": today, "universe": len(syms), "screened": scanned,
        "shelves": sorted({uni[s]["shelf"] for s in syms}),
        "benchmarks": {b: (round(m[2], 2) if (m := _moves(bars.get(b))) else None) for b in benches},
        "coverage": drep, "hits": hits}, indent=1))
    return hits


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="screen only the first N symbols")
    ap.add_argument("--dry-run", action="store_true", help="print fires; write no state/JSON")
    ap.add_argument("--no-gw", action="store_true", help="skip the IBKR-gateway liveness probe")
    ap.add_argument("--min-excess5", type=float, default=MIN_EXCESS_5)
    ap.add_argument("--min-excess21", type=float, default=MIN_EXCESS_21)
    ap.add_argument("--quiet-sessions", type=int, default=QUIET_SESSIONS)
    a = ap.parse_args()
    sweep(limit=a.limit, dry_run=a.dry_run, use_gw=not a.no_gw,
          min_excess5=a.min_excess5, min_excess21=a.min_excess21,
          quiet_sessions=a.quiet_sessions)
