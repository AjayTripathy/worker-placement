"""cohort_dislocation — the COHORT-AGGREGATE leg of the dislocation watch (built 2026-08-13).

THE GAP IT FILLS (the SPGI miss, 2026-08-13). Every dislocation layer the desk owns screens ONE
NAME AT A TIME: dislocation_sweep (researched US names), intl_dislocation_sweep (foreign shelves),
broken_print_radar (single-session tape breaks). In early August 2026 the market re-rated the
financial-data vendors as a CLASS on the AI-disintermediation narrative — SPGI, MCO and MSCI each
grinding 6-12pp below SPY over 21 sessions. No single-name screen fired: each name individually sat
just under the -8%/5d and -15%/21d bars. The THEME was the signal and nothing aggregated it.

This layer asks the aggregate question: is a whole COHORT being marked down together, and if so
which member is the best-in-class name getting dragged with it? It is deliberately a THEME screen,
never a ticker screen — the output is a cohort plus one court question.

SIGNAL = the cohort's MEDIAN idiosyncratic excess vs SPY, plus BREADTH (how much of the cohort is
participating). Median not mean, because one blown-up member is not a class de-rate. Breadth,
because a median can be dragged by a minority. Both must clear:

    FIRE:  median 21d excess <= -6.0pp  AND  breadth >= 60% of members negative   (n >= 4)
           or the 63d GRIND leg: median 63d excess <= -10.0pp AND breadth >= 60%
    HIGH:  median 21d excess <= -12.0pp (or 63d <= -18.0pp)

WHY -6pp AND 60% (tuned against a recorded tape, and the tuning is reported honestly). The
single-name sweep fires at -15pp/21d; a cohort whose MEDIAN member is down 6pp is a much rarer
event than any one name down 6pp, because idiosyncratic moves cancel in a median — the point is
that the aggregate survives the cancellation. Measured on the recorded Apr-Aug 2026 tape of the
financial-data vendors (tests/golden, 70 evaluable sessions): the raw gate CLEARS on 18 of 70
sessions, which is why the raw gate alone is not the detector — after the episode dedup below
those 18 sessions become 5 events (2026-05-01, 05-05, 05-20, 07-01, 08-05), i.e. roughly 1.4 per
cohort per month, clustered into a deep uniform May selloff and the shallower summer grind. That
is the intended shape: a court-sized number of theme questions, not a daily feed. Anyone
re-tuning these numbers should re-run that measurement rather than trust this paragraph.

EPISODE DEDUP. A cohort de-rate persists for weeks, so a fresh fire is emitted only when the
cohort ENTERS a de-rate or MATERIALLY deepens (median at least DEEPEN_PP lower than the level
already reported) — a same-severity check alone let the May episode emit six fires as its median
oscillated across the HIGH boundary.

REGIME GUARD. Excess-vs-SPY already nets out a market-wide selloff, so many cohorts clearing at
once means a broad ROTATION, not twenty independent themes. When more than REGIME_SHARE of
evaluated cohorts clear, every fire that day carries a REGIME WARNING in its evidence line.

SINGLE-NAME SKEW GUARD. Every cohort also reports its EX-WORST-MEMBER median: drop the deepest
member and re-take the median. When the ex-worst median no longer clears the fire bar, the de-rate
is concentrated rather than broad — the fire still stands (it is real information) but severity is
capped at MED and the evidence line says SKEW explicitly, so the court is never told "the whole
cohort de-rated" when three of five names did. On the anchor date this fires exactly: the vendor
cohort's median is -6.7pp but its ex-worst median is only -2.1pp, because SPGI/MCO/MSCI sold off
while FDS/MORN rallied. That IS the finding, stated honestly.

COHORT MEMBERSHIP, two sources:
  1. CURATED narrative cohorts in knowledge_graph/cohorts.json (the researched names) — versioned
     data, shared with desk/class_dislocation.
  2. AUTO industry cohorts for the unresearched broad universe, from a locally cached
     yfinance-industry mapper (data/industry_map.json) filled by polite budgeted batching, with
     the Nasdaq screener's sector/industry/mcap as the free bulk fallback.
  KNOWN LIMIT, measured not assumed: the auto buckets are COARSER than the narratives that price
  them. yfinance files SPGI/MCO/FDS/MSCI/MORN together with ICE/NDAQ/TRU under "Financial Data &
  Stock Exchanges" — and on the anchor date the exchanges were RALLYING, so the auto bucket's
  median is +3pp and the de-rate is invisible. The auto leg is recall, the curated leg is
  precision; both run, and a diluted auto bucket is reported (dilution_note) rather than trusted.

  AUTO-LEG COVERAGE GATE. Because the mapper fills over days, an early auto cohort is not its
  industry — it is whichever few names the budget reached first (the first live runs produced an
  "industry:Biotechnology" of FOUR names and fired on it). Auto cohorts are therefore built and
  reported but cannot FIRE until the map covers AUTO_MIN_COVERAGE of the liquid tape. Curated
  cohorts are unaffected: their membership is explicit, not sampled.

  DUPLICATE SUPPRESSION. When an auto bucket and a curated cohort hold essentially the same names
  (Jaccard >= 0.8) only the curated one fires — the first live run handed the court the identical
  five-vendor question twice under two different cohort names.

BENCHMARK = SPY, so this layer is US-listed only. The international sweep's names are read for
context and coverage accounting but are NEVER aggregated into a SPY-benchmarked cohort (a Tokyo
line measured against SPY measures the yen — the sibling sweep's lesson, in cohort form).

RATE BUDGET. This layer is designed to REUSE, not refetch: price series live in a shared day-keyed
cache (data/cohort_px_cache.json) so a same-day re-run costs zero network, and the sweep outputs
are read for context/cross-check instead of re-derived. The only genuinely new cost is the
industry mapper's yfinance .info calls, hard-capped at --map-budget per run (default 120, ~0.35s
apart) so the map fills incrementally over days rather than in one rate-limiting burst.

DEGRADED-LOUD. Unmapped names, unpriced names and cohorts that fell under the member floor are all
COUNTED and NAMED in the summary. A cohort layer that silently dropped half its members would
report "no theme de-rate" for a theme it simply could not see.

Emits DETFIRE|cohort_dislocation|<COHORT>|<SEV>|<evidence> for the cohort plus a companion
DETFIRE|cohort_dislocation|<TICKER>|<SEV>|... for the best-in-class member, both through the
registry's detector_scan extractor. PROPOSES ONLY. Writes data/COHORT_DISLOCATION.json +
data/cohort_dislocation_state.json (new-vs-deepened dedup).

  python3 verticals/generators/cohort_dislocation.py [--map-budget 120] [--max-symbols 600] [--dry-run]
"""
from __future__ import annotations

import argparse
import datetime
import json
import statistics
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
DATA = HERE / "data"

OUT_JSON = DATA / "COHORT_DISLOCATION.json"
STATE = DATA / "cohort_dislocation_state.json"
PX_CACHE = DATA / "cohort_px_cache.json"
MAP_STORE = DATA / "industry_map.json"

# sibling sweep outputs — READ ONLY, and every one of them is optional
SWEEP_US = DATA / "DISLOCATION_SWEEP.json"
SWEEP_INTL = DATA / "INTL_DISLOCATION_SWEEP.json"
SWEEP_BROAD_CANDIDATES = ("US_BROAD_DISLOCATION_SWEEP.json", "BROAD_DISLOCATION_SWEEP.json",
                          "US_BROAD_SWEEP.json", "BROAD_SWEEP.json")

COHORT_FILE = ROOT / "knowledge_graph" / "cohorts.json"
LEDGER = ROOT / "desk" / "data" / "research_ledger.json"
CIK_MAP = ROOT / "desk" / "data" / "cik_map.json"

BENCH = "SPY"

# ------------------------------------------------------------------ gates (documented above)
FIRE_MEDIAN_21 = -6.0        # pp of excess vs SPY
FIRE_MEDIAN_63 = -10.0       # the GRIND leg — slower de-rates the 21d window flattens
HIGH_MEDIAN_21 = -12.0
HIGH_MEDIAN_63 = -18.0
FIRE_BREADTH = 0.60
MIN_MEMBERS = 4              # below this a "median" is a coin flip
AUTO_MIN_MCAP = 1e9          # auto industry cohorts: liquid members only (microcaps are not a theme)
QUIET_DAYS = 10              # new-or-deepened only, like the sibling sweeps
DEEPEN_PP = 3.0              # inside the quiet window, only a MATERIALLY deeper median re-fires
BENCH_STALE_DAYS = 5         # a benchmark close older than this cannot anchor an excess
REGIME_SHARE = 0.25          # >this share of cohorts firing at once = rotation, not a theme
AUTO_MIN_COVERAGE = 0.50     # auto industry cohorts stay PROVISIONAL until the map covers this


# ============================================================ PURE: aggregation math (offline-tested)
def excess_pct(bars: dict, bench: dict, n: int) -> float | None:
    """Idiosyncratic n-session return vs the benchmark, DATE-ALIGNED.

    The benchmark close is looked up as of the member's OWN anchor date (not by position), because
    a member with a missing session would otherwise be compared across a different window. A bench
    close staler than BENCH_STALE_DAYS relative to the anchor refuses the measurement (None) rather
    than silently producing a mis-windowed 'excess'.
    """
    closes, dates = bars.get("close") or [], bars.get("dates") or []
    if len(closes) < n + 1 or len(dates) != len(closes):
        return None
    last_i, anchor_i = len(closes) - 1, len(closes) - 1 - n
    if not closes[anchor_i] or not closes[last_i]:
        return None
    r = (closes[last_i] / closes[anchor_i] - 1) * 100
    b_last = _bench_close_asof(bench, dates[last_i])
    b_anchor = _bench_close_asof(bench, dates[anchor_i])
    if b_last is None or b_anchor is None:
        return None
    return r - (b_last / b_anchor - 1) * 100


def _bench_close_asof(bench: dict, date: str) -> float | None:
    """Benchmark close on `date`, else the most recent close within BENCH_STALE_DAYS before it."""
    bd, bc = bench.get("dates") or [], bench.get("close") or []
    if not bd or len(bd) != len(bc):
        return None
    best = None
    for d, c in zip(bd, bc):
        if d <= date and c:
            best = (d, c)
        elif d > date:
            break
    if not best:
        return None
    try:
        gap = (datetime.date.fromisoformat(date) - datetime.date.fromisoformat(best[0])).days
    except ValueError:
        return None
    return best[1] if gap <= BENCH_STALE_DAYS else None


def cohort_stats(ex21: dict[str, float], ex63: dict[str, float] | None = None) -> dict:
    """Pure aggregation over {ticker: excess_pp}. Median + breadth + the ex-worst skew guard."""
    ex63 = ex63 or {}
    st: dict = {"n": len(ex21), "n63": len(ex63)}
    if ex21:
        vals = list(ex21.values())
        worst = min(ex21, key=lambda t: ex21[t])
        rest = [v for t, v in ex21.items() if t != worst]
        st.update({
            "median21": round(statistics.median(vals), 2),
            "breadth21": round(sum(1 for v in vals if v < 0) / len(vals), 3),
            "worst_member": worst,
            "worst21": round(ex21[worst], 2),
            "ex_worst_median21": round(statistics.median(rest), 2) if rest else None,
            "best21": round(max(vals), 2),
            "dispersion21": round(max(vals) - min(vals), 2),
        })
    if ex63:
        v63 = list(ex63.values())
        st.update({"median63": round(statistics.median(v63), 2),
                   "breadth63": round(sum(1 for v in v63 if v < 0) / len(v63), 3)})
    return st


def evaluate(st: dict) -> dict:
    """Fire decision + severity + the skew annotation. Pure — no I/O, no thresholds hidden."""
    m21, b21 = st.get("median21"), st.get("breadth21")
    m63, b63 = st.get("median63"), st.get("breadth63")
    n, n63 = st.get("n", 0), st.get("n63", 0)
    legs = []
    if n >= MIN_MEMBERS and m21 is not None and b21 is not None \
            and m21 <= FIRE_MEDIAN_21 and b21 >= FIRE_BREADTH:
        legs.append("21d")
    if n63 >= MIN_MEMBERS and m63 is not None and b63 is not None \
            and m63 <= FIRE_MEDIAN_63 and b63 >= FIRE_BREADTH:
        legs.append("63d")
    if not legs:
        return {"fires": False, "legs": [], "severity": None, "skew": False,
                "reason": _no_fire_reason(st)}
    deep = (m21 is not None and m21 <= HIGH_MEDIAN_21) or (m63 is not None and m63 <= HIGH_MEDIAN_63)
    sev = "HIGH" if deep else "MED"
    # SKEW GUARD: if dropping the single deepest member takes the cohort back above the fire bar,
    # the de-rate is concentrated, not broad. Fire stands (it is real) but never as HIGH.
    exw = st.get("ex_worst_median21")
    skew = "21d" in legs and exw is not None and exw > FIRE_MEDIAN_21
    if skew:
        sev = "MED"
    return {"fires": True, "legs": legs, "severity": sev, "skew": skew, "reason": None}


def _no_fire_reason(st: dict) -> str:
    if st.get("n", 0) < MIN_MEMBERS:
        return f"only {st.get('n', 0)} priced members (floor {MIN_MEMBERS})"
    m21, b21 = st.get("median21"), st.get("breadth21")
    if m21 is not None and m21 > FIRE_MEDIAN_21:
        return f"median21 {m21:+.1f}pp above {FIRE_MEDIAN_21}pp"
    if b21 is not None and b21 < FIRE_BREADTH:
        return f"breadth {b21:.0%} below {FIRE_BREADTH:.0%} (median carried by a minority)"
    return "below gates"


def best_in_class(ex21: dict[str, float], meta: dict[str, dict]) -> dict | None:
    """The largest, least-levered member being DRAGGED — the name the court should look at first.

    Ranked over the members with NEGATIVE excess only (a member that rallied is not being dragged).
    Score = 0.6 * size rank + 0.4 * balance-sheet rank. Missing balance-sheet data scores NEUTRAL
    and is named in data_gaps — never treated as clean (the pull-cap-structure rule).
    """
    dragged = {t: v for t, v in ex21.items() if v < 0}
    pool = dragged or ex21
    if not pool:
        return None
    rows = []
    for t in pool:
        m = meta.get(t) or {}
        mcap = m.get("mcap") or 0
        cash, debt = m.get("cash"), m.get("debt")
        net_cash = (cash - debt) if (cash is not None and debt is not None) else None
        rows.append({"ticker": t, "excess21": round(pool[t], 2), "mcap": mcap,
                     "net_cash": net_cash, "cash": cash, "debt": debt})
    caps = sorted({r["mcap"] for r in rows})
    known_lev = [r for r in rows if r["net_cash"] is not None and r["mcap"]]
    lev_vals = sorted({(r["net_cash"] / r["mcap"]) for r in known_lev})
    for r in rows:
        r["size_rank"] = (caps.index(r["mcap"]) / max(len(caps) - 1, 1)) if len(caps) > 1 else 0.5
        if r["net_cash"] is not None and r["mcap"] and len(lev_vals) > 1:
            r["lev_rank"] = lev_vals.index(r["net_cash"] / r["mcap"]) / (len(lev_vals) - 1)
        else:
            r["lev_rank"] = 0.5          # NEUTRAL, not clean
        r["score"] = round(0.6 * r["size_rank"] + 0.4 * r["lev_rank"], 4)
    rows.sort(key=lambda r: (-r["score"], -r["mcap"]))
    top = rows[0]
    gaps = []
    if top["net_cash"] is None:
        gaps.append("leverage UNKNOWN (no cash/debt in the mapper cache) — scored NEUTRAL, not clean")
    if not top["mcap"]:
        gaps.append("market cap UNKNOWN")
    return {**top, "data_gaps": gaps, "ranked": [r["ticker"] for r in rows[:8]],
            "pool": "dragged members" if dragged else "all members (none negative)"}


def court_question(cohort: str, best: dict | None) -> str:
    name = best["ticker"] if best else "the best-in-class member"
    return (f"cohort de-rate: is {name} dislocated with its cohort or correctly repriced?")


def fire_line(cohort: str, st: dict, verdict: dict, best: dict | None, ctx: str = "") -> str:
    """DETFIRE|cohort_dislocation|<COHORT>|<SEV>|<evidence> — the cohort-level line."""
    m21 = st.get("median21")
    bits = [f"median 21d excess {m21:+.1f}pp vs SPY" if m21 is not None else "21d n/a",
            f"breadth {st['breadth21']:.0%} of {st['n']} members negative" if st.get("breadth21") is not None
            else f"{st.get('n', 0)} members"]
    if st.get("median63") is not None:
        bits.append(f"63d median {st['median63']:+.1f}pp ({st['breadth63']:.0%} breadth)")
    if st.get("ex_worst_median21") is not None:
        bits.append(f"ex-worst({st['worst_member']} {st['worst21']:+.1f}pp) median "
                    f"{st['ex_worst_median21']:+.1f}pp")
    ev = f"cohort de-rate [{'+'.join(verdict['legs'])} leg]: " + "; ".join(bits)
    if verdict["skew"]:
        ev += (" — SKEW: dropping the deepest member takes the cohort back above the fire bar, so "
               "this is a CONCENTRATED de-rate, not a uniform one; do not tell the court 'the whole "
               "cohort re-rated'")
    if best:
        parts = [f"{best['excess21']:+.1f}pp"]
        if best.get("mcap"):
            parts.append(f"mcap ${best['mcap']/1e9:.1f}B")
        if best.get("net_cash") is not None:
            nc = best["net_cash"]
            parts.append(f"net cash ${nc/1e9:.2f}B" if nc >= 0 else f"net DEBT ${-nc/1e9:.2f}B")
        ev += f". BEST-IN-CLASS DRAGGED: {best['ticker']} ({', '.join(parts)})"
        for g in best["data_gaps"]:
            ev += f" [{g}]"
    if ctx:
        ev += f". {ctx}"
    ev += (f". COURT QUESTION: {court_question(cohort, best)}"
           " — PROPOSES ONLY: cause-check -> discovery_state -> court (v1.4) before any staging;"
           " a cohort that fell together may be correctly repriced, and a shallow 'no cause found'"
           " is beta, not a dislocation")
    return f"DETFIRE|cohort_dislocation|{cohort}|{verdict['severity']}|{ev}"


def member_fire_line(cohort: str, verdict: dict, best: dict) -> str:
    """Companion line so the best-in-class name routes into the feed as a TICKER, not a theme."""
    return (f"DETFIRE|cohort_dislocation|{best['ticker']}|{verdict['severity']}|"
            f"best-in-class member of the de-rating cohort '{cohort}' ({best['excess21']:+.1f}pp "
            f"21d excess vs SPY; ranked #1 of {len(best['ranked'])} on size+balance-sheet). "
            f"COURT QUESTION: {court_question(cohort, best)}"
            f" — PROPOSES ONLY: the cohort fired, not this name; cause-check -> discovery_state -> "
            f"court (v1.4) before any staging")


# ============================================================ PURE: cohort assembly
def parse_curated(blob: dict) -> dict[str, list[str]]:
    """Curated narrative cohorts from knowledge_graph/cohorts.json.

    Defensive on purpose: the live file has one cohort (osb_prediction_market_exposed) sitting at
    the TOP level rather than inside "cohorts" — an editing slip that a strict reader would silently
    drop. Any top-level dict carrying "members" is accepted as a cohort.
    """
    out: dict[str, list[str]] = {}
    for name, spec in (blob.get("cohorts") or {}).items():
        if isinstance(spec, dict) and spec.get("members"):
            out[f"narrative:{name}"] = [str(t).strip().upper() for t in spec["members"]]
    for name, spec in blob.items():
        if name in ("cohorts", "_doc") or not isinstance(spec, dict):
            continue
        if spec.get("members") and f"narrative:{name}" not in out:
            out[f"narrative:{name}"] = [str(t).strip().upper() for t in spec["members"]]
    return out


def auto_cohorts(meta: dict[str, dict], min_mcap: float = AUTO_MIN_MCAP) -> dict[str, list[str]]:
    """industry:<label> cohorts over every mapped name above the liquidity floor."""
    out: dict[str, list[str]] = {}
    for t, m in meta.items():
        ind = (m.get("industry") or "").strip()
        if not ind or (m.get("mcap") or 0) < min_mcap:
            continue
        out.setdefault(f"industry:{ind}", []).append(t)
    return {k: sorted(v) for k, v in out.items() if len(v) >= MIN_MEMBERS}


def is_us_symbol(t: str) -> bool:
    """SPY-benchmarking only makes sense for US lines (the cross-benchmark guard)."""
    return bool(t) and "." not in t and "-" not in t and t.isascii() and t.isalpha() and len(t) <= 5


# ============================================================ I/O: sweep context (all optional)
def load_sweep_context() -> dict:
    """Read the sibling sweeps for universe seeds + cross-check. Every file is optional."""
    ctx: dict = {"files": {}, "seed_tickers": set(), "us_excess21": {}, "spy21_pct": None,
                 "intl_tickers": set()}
    try:
        d = json.loads(SWEEP_US.read_text())
        ctx["files"]["DISLOCATION_SWEEP.json"] = d.get("asof")
        ctx["spy21_pct"] = d.get("spy21_pct")
        for h in d.get("hits") or []:
            t = str(h.get("ticker") or "").upper()
            if t:
                ctx["seed_tickers"].add(t)
                if h.get("excess21_pct") is not None:
                    ctx["us_excess21"][t] = h["excess21_pct"]
    except Exception as e:
        ctx["files"]["DISLOCATION_SWEEP.json"] = f"ABSENT/UNREADABLE ({type(e).__name__})"
    try:
        d = json.loads(SWEEP_INTL.read_text())
        ctx["files"]["INTL_DISLOCATION_SWEEP.json"] = d.get("asof")
        for h in d.get("hits") or []:
            t = str(h.get("ticker") or "").upper()
            if t:
                ctx["intl_tickers"].add(t)     # context only — never SPY-benchmarked
    except Exception as e:
        ctx["files"]["INTL_DISLOCATION_SWEEP.json"] = f"ABSENT/UNREADABLE ({type(e).__name__})"
    for fn in SWEEP_BROAD_CANDIDATES:          # the sibling's broad-US leg, whenever it lands
        p = DATA / fn
        if not p.exists():
            continue
        try:
            d = json.loads(p.read_text())
            ctx["files"][fn] = d.get("asof")
            for h in (d.get("hits") or d.get("names") or []):
                t = str((h.get("ticker") if isinstance(h, dict) else h) or "").upper()
                if t and is_us_symbol(t):
                    ctx["seed_tickers"].add(t)
                    if isinstance(h, dict) and h.get("excess21_pct") is not None:
                        ctx["us_excess21"][t] = h["excess21_pct"]
        except Exception as e:
            ctx["files"][fn] = f"UNREADABLE ({type(e).__name__})"
        break
    else:
        ctx["files"]["us_broad_sweep"] = "NOT YET LANDED (sibling in flight) — tolerated"
    return ctx


# ============================================================ I/O: the cached industry mapper
def load_map() -> dict:
    try:
        return json.loads(MAP_STORE.read_text()).get("names") or {}
    except Exception:
        return {}


def save_map(m: dict) -> None:
    MAP_STORE.write_text(json.dumps(
        {"_doc": "cached ticker -> {sector, industry, mcap, cash, debt} for cohort_dislocation. "
                 "Industry is near-static so rows never expire; mcap/cash/debt refresh on re-map. "
                 "Filled incrementally under --map-budget to stay inside the yfinance rate budget.",
         "asof": datetime.date.today().isoformat(), "names": m}, indent=1))


def screener_meta() -> dict[str, dict]:
    """One free Nasdaq-screener call: the whole US tape's sector/industry/mcap.

    Used as the BULK fallback layer. Its industry labels are a different (coarser, and differently
    cut) taxonomy from yfinance's — it files SPGI under 'Finance: Consumer Services' with the
    consumer lenders and FDS under 'Computer Software', which is precisely why it cannot carry the
    auto cohorts on its own. It is excellent for mcap and for a sector floor.
    """
    try:
        sys.path.insert(0, str(ROOT / "verticals" / "deep_value"))
        from universe import _get, NASDAQ_URL, NASDAQ_HDRS
        rows = _get(NASDAQ_URL, NASDAQ_HDRS)["data"]["rows"]
    except Exception as e:
        print(f"[cohort_dislocation] Nasdaq screener unavailable ({type(e).__name__}) — "
              f"mcap/sector fallback degraded; mapper cache carries the run")
        return {}
    out = {}
    for r in rows:
        t = str(r.get("symbol") or "").strip().upper()
        if not is_us_symbol(t):
            continue
        try:
            mc = float(str(r.get("marketCap", "")).replace("$", "").replace(",", "") or 0)
        except ValueError:
            mc = 0.0
        out[t] = {"screener_sector": r.get("sector"), "screener_industry": r.get("industry"),
                  "mcap": mc}
    return out


MAP_RETRY_DAYS = 30


def _needs_map(t: str, cache: dict, today: str) -> bool:
    """Unmapped, or a NEGATIVE cache entry old enough to be worth one retry.

    Negative caching matters: the priority list carries ledger names that are foreign lines with
    US-shaped symbols (EMAAR, POLI, CBKD). Without it every run spent budget re-asking Yahoo about
    the same names it had already refused, so the map crawled forward far slower than the budget
    implied.
    """
    row = cache.get(t)
    if row is None:
        return True
    if row.get("industry"):
        return False
    try:
        age = (datetime.date.fromisoformat(today)
               - datetime.date.fromisoformat(row.get("failed") or today)).days
    except ValueError:
        return False
    return age >= MAP_RETRY_DAYS


def map_names(tickers: list[str], cache: dict, budget: int, sleep: float = 0.35,
              today: str | None = None) -> dict:
    """Fill industry/mcap/cash/debt for up to `budget` unmapped names. Polite and bounded."""
    today = today or datetime.date.today().isoformat()
    todo = [t for t in tickers if _needs_map(t, cache, today)][:max(budget, 0)]
    if not todo:
        return {"attempted": 0, "mapped": 0, "failed": []}
    import yfinance as yf
    mapped, failed = 0, []
    for i, t in enumerate(todo):
        try:
            info = yf.Ticker(t).info or {}
            ind = info.get("industry")
        except Exception:
            ind, info = None, {}
        if ind:
            cache[t] = {"sector": info.get("sector"), "industry": ind,
                        "mcap": info.get("marketCap"), "cash": info.get("totalCash"),
                        "debt": info.get("totalDebt"), "src": "yfinance.info", "asof": today}
            mapped += 1
        else:
            failed.append(t)
            cache[t] = {"industry": None, "src": "yfinance.info", "failed": today,
                        "note": f"no industry from yfinance — retried after {MAP_RETRY_DAYS}d"}
        if i < len(todo) - 1:
            time.sleep(sleep)
    return {"attempted": len(todo), "mapped": mapped, "failed": failed}


# ============================================================ I/O: the shared price-series cache
def load_px_cache() -> dict:
    try:
        return json.loads(PX_CACHE.read_text())
    except Exception:
        return {}


def fetch_series(symbols: list[str], cache: dict, today: str, max_symbols: int) -> tuple[dict, list]:
    """Day-keyed reuse: anything already fetched TODAY costs nothing. Chunked batch download."""
    need = [s for s in symbols if (cache.get(s) or {}).get("fetched") != today][:max_symbols]
    if need:
        import yfinance as yf
        for i in range(0, len(need), 80):
            chunk = need[i:i + 80]
            try:
                px = yf.download(chunk, period="9mo", progress=False, auto_adjust=True)["Close"]
            except Exception as e:
                print(f"[cohort_dislocation] price chunk failed ({type(e).__name__}) — "
                      f"{len(chunk)} names fall back to any cached series")
                continue
            for s in chunk:
                try:
                    ser = (px[s] if hasattr(px, "columns") and s in px.columns else px).dropna()
                except Exception:
                    continue
                if len(ser) >= 22:
                    cache[s] = {"dates": [d.date().isoformat() for d in ser.index],
                                "close": [round(float(v), 4) for v in ser],
                                "fetched": today}
    unpriced = [s for s in symbols if s not in cache]
    return cache, unpriced


# ============================================================ the scan
def scan(cohorts: dict[str, list[str]], bars: dict, meta: dict[str, dict], today: str,
         state: dict | None = None) -> tuple[list[dict], dict, dict]:
    """Pure over its inputs: cohorts + bars + meta -> (fires, new_state, coverage)."""
    state = dict(state or {})
    bench = bars.get(BENCH)
    if not bench:
        raise RuntimeError(f"{BENCH} series missing — every excess in this layer is measured "
                           f"against it; refusing to scan (a cohort layer without its benchmark "
                           f"reports beta as a theme)")
    fires, evaluated, skipped = [], [], []
    for cohort, members in sorted(cohorts.items()):
        us = [t for t in members if is_us_symbol(t)]
        dropped_intl = [t for t in members if t not in us]
        ex21, ex63, unpriced = {}, {}, []
        for t in us:
            b = bars.get(t)
            if not b:
                unpriced.append(t)
                continue
            e21 = excess_pct(b, bench, 21)
            if e21 is None:
                unpriced.append(t)
                continue
            ex21[t] = e21
            e63 = excess_pct(b, bench, 63)
            if e63 is not None:
                ex63[t] = e63
        st = cohort_stats(ex21, ex63)
        st.update({"cohort": cohort, "members_total": len(members), "unpriced": sorted(unpriced),
                   "dropped_non_us": sorted(dropped_intl)})
        verdict = evaluate(st)
        row = {**st, **{f"verdict_{k}": v for k, v in verdict.items()},
               "members_by_excess21": sorted(((t, round(v, 2)) for t, v in ex21.items()),
                                             key=lambda x: x[1])}
        if st["n"] < MIN_MEMBERS:
            skipped.append({"cohort": cohort, "n": st["n"], "reason": verdict["reason"]})
            continue
        evaluated.append(row)
        if not verdict["fires"]:
            # COOLING-OFF, not an instant re-arm. A cohort de-rate oscillates around the bar for
            # weeks; popping the state on the first quiet session re-armed the detector mid-episode
            # and fragmented the recorded May selloff into five "new" fires. The cohort must sit
            # BELOW the gate for QUIET_DAYS before it can fire as a new episode.
            prior = state.get(cohort)
            if prior:
                cs = prior.get("clear_since")
                if not cs:
                    prior["clear_since"] = today
                else:
                    try:
                        cleared = (datetime.date.fromisoformat(today)
                                   - datetime.date.fromisoformat(cs)).days
                    except ValueError:
                        cleared = 999
                    if cleared >= QUIET_DAYS:
                        state.pop(cohort, None)
            continue
        # EPISODE DEDUP. A cohort de-rate is a multi-week episode, not a daily event: gating only
        # on "same severity" let the recorded May 2026 vendor selloff emit SIX fires as the median
        # oscillated across the HIGH boundary. Inside the quiet window a repeat fires ONLY if the
        # median deepened materially (DEEPEN_PP) past the level already reported.
        prior = state.get(cohort)
        if prior:
            try:
                age = (datetime.date.fromisoformat(today)
                       - datetime.date.fromisoformat(prior.get("fired", today))).days
            except ValueError:
                age = 999
            pm, cm = prior.get("median21"), st.get("median21")
            deepened = (pm is not None and cm is not None and cm <= pm - DEEPEN_PP)
            if age < QUIET_DAYS * 1.5 and not deepened:
                row["suppressed_repeat"] = True
                continue
        best = best_in_class(ex21, meta)
        state[cohort] = {"severity": verdict["severity"], "fired": today,
                         "median21": st.get("median21"), "clear_since": None}
        fires.append({**row, "best_in_class": best, "severity": verdict["severity"],
                      "legs": verdict["legs"], "skew": verdict["skew"],
                      "court_question": court_question(cohort, best), "fired": today})
    # DUPLICATE-COHORT SUPPRESSION (caught by the first live run). An auto industry bucket can hold
    # essentially the same names as a curated narrative cohort — on 2026-08-13 both fired on the
    # identical five vendors, handing the court the same question twice under two names. The
    # CURATED cohort wins: it is the precise, tape-audited one. The auto twin keeps its state entry
    # (it did clear the gate, so it must not re-fire tomorrow) but emits nothing.
    narrative_sets = {f["cohort"]: {t for t, _ in f["members_by_excess21"]}
                      for f in fires if f["cohort"].startswith("narrative:")}
    kept = []
    for f in fires:
        s = {t for t, _ in f["members_by_excess21"]}
        dup = next((n for n, ns in narrative_sets.items()
                    if s and n != f["cohort"] and len(s & ns) / len(s | ns) >= 0.8), None)
        if f["cohort"].startswith("industry:") and dup:
            f["suppressed_duplicate_of"] = dup
            for row in evaluated:
                if row["cohort"] == f["cohort"]:
                    row["suppressed_duplicate_of"] = dup
            continue
        kept.append(f)
    fires = kept

    # REGIME GUARD (the beta-bleed doctrine in cohort form). Excess-vs-SPY already nets out a
    # market-wide selloff, so many cohorts clearing the bar at once is not a market drop — it is a
    # broad ROTATION out of a whole side of the tape. Either way it is not "this theme de-rated",
    # and the court must not be handed twenty independent-looking theme questions on one factor day.
    clearing = sum(1 for r in evaluated
                   if r.get("verdict_fires") and not r.get("suppressed_duplicate_of"))
    share = (clearing / len(evaluated)) if evaluated else 0.0
    regime = len(evaluated) >= 8 and share > REGIME_SHARE
    for f in fires:
        f["regime_share"] = round(share, 3)
        f["regime_warning"] = regime
    coverage = {"cohorts_evaluated": len(evaluated), "cohorts_below_member_floor": skipped,
                "evaluated": evaluated, "gate_clearing": clearing,
                "gate_clearing_share": round(share, 3), "regime_warning": regime}
    return fires, state, coverage


# ============================================================ run
def run(map_budget: int, max_symbols: int, dry_run: bool, min_mcap: float) -> list[dict]:
    today = datetime.date.today().isoformat()
    ctx = load_sweep_context()
    print(f"[cohort_dislocation] sweep context: "
          + "; ".join(f"{k}={v}" for k, v in ctx["files"].items()))

    curated_blob = {}
    try:
        curated_blob = json.loads(COHORT_FILE.read_text())
    except Exception as e:
        print(f"[cohort_dislocation] cohorts.json unreadable ({type(e).__name__}) — "
              f"curated leg DISABLED this run (auto leg still runs)")
    curated = parse_curated(curated_blob)

    scr = screener_meta()
    cache = load_map()

    # MAPPING PRIORITY: names we can actually act on first — curated members, then the sweeps'
    # own hits, then the ledger, then the largest unmapped caps. The budget is small on purpose,
    # so what it spends on matters more than how much it spends.
    prio: list[str] = []
    for members in curated.values():
        prio += [t for t in members if is_us_symbol(t)]
    prio += sorted(t for t in ctx["seed_tickers"] if is_us_symbol(t))
    try:
        prio += [str(r.get("ticker") or "").upper()
                 for r in json.loads(LEDGER.read_text()).get("names", [])
                 if is_us_symbol(str(r.get("ticker") or "").upper())]
    except Exception:
        pass
    prio += [t for t, m in sorted(scr.items(), key=lambda kv: -(kv[1].get("mcap") or 0))
             if (m.get("mcap") or 0) >= min_mcap]
    seen: set[str] = set()
    prio = [t for t in prio if not (t in seen or seen.add(t))]

    mstat = map_names(prio, cache, map_budget, today=today)
    if mstat["attempted"]:
        save_map(cache)
    mapped_ok = sum(1 for r in cache.values() if r.get("industry"))
    print(f"[cohort_dislocation] industry map: {mapped_ok} mapped / {len(cache)} probed "
          f"(+{mstat['mapped']} this run of {mstat['attempted']} attempted, "
          f"{len(mstat['failed'])} refused)")

    # meta merges the mapper (industry, cash/debt) over the screener (mcap floor)
    meta: dict[str, dict] = {}
    for t, m in scr.items():
        meta[t] = {"mcap": m.get("mcap"), "sector": m.get("screener_sector"),
                   "industry": None, "src": "screener"}
    for t, m in cache.items():
        row = meta.setdefault(t, {})
        row.update({"industry": m.get("industry"), "sector": m.get("sector") or row.get("sector"),
                    "cash": m.get("cash"), "debt": m.get("debt"), "src": "yfinance.info"})
        if m.get("mcap"):
            row["mcap"] = m["mcap"]

    # AUTO-LEG COVERAGE GATE (the "industry:Biotechnology, n=4" artifact from the first live runs).
    # The mapper fills over days, so early on an auto cohort is not the industry — it is whichever
    # handful of that industry's names the budget happened to reach first, and a median over them is
    # a median over an arbitrary sample. Auto cohorts therefore only FIRE once the map covers
    # AUTO_MIN_COVERAGE of the liquid tape; until then they are built, reported and counted, but
    # cannot emit. Curated cohorts are unaffected — their membership is explicit, not sampled.
    liquid = [t for t, m in meta.items() if (m.get("mcap") or 0) >= min_mcap]
    mapped_liquid = [t for t in liquid if meta[t].get("industry")]
    auto_coverage = (len(mapped_liquid) / len(liquid)) if liquid else 0.0
    auto = auto_cohorts(meta, min_mcap)
    auto_provisional = auto_coverage < AUTO_MIN_COVERAGE
    cohorts = {**curated, **({} if auto_provisional else auto)}
    members_needed = sorted({t for v in cohorts.values() for t in v if is_us_symbol(t)} | {BENCH})

    # DEGRADED-LOUD on mapping: curated members with no industry row are fine (membership is
    # explicit) but auto-cohort candidates without one are INVISIBLE to this layer — count them.
    unmapped_liquid = [t for t, m in meta.items()
                       if not m.get("industry") and (m.get("mcap") or 0) >= min_mcap]

    px = load_px_cache()
    px, unpriced = fetch_series(members_needed, px, today, max_symbols)
    try:
        PX_CACHE.write_text(json.dumps(px))
    except Exception as e:
        print(f"[cohort_dislocation] px cache write failed ({type(e).__name__}) — "
              f"next run will refetch")

    try:
        state = json.loads(STATE.read_text())
    except Exception:
        state = {}

    fires, new_state, coverage = scan(cohorts, px, meta, today, state)

    regime_ctx = ("REGIME WARNING: {:.0%} of evaluated cohorts cleared the bar on this tape — that "
                  "is a broad rotation, not a single-theme de-rate; treat every fire today as "
                  "factor-driven until a cohort-specific cause is dated"
                  .format(coverage["gate_clearing_share"])) if coverage["regime_warning"] else ""
    for f in fires:
        print(fire_line(f["cohort"], f, {"legs": f["legs"], "severity": f["severity"],
                                         "skew": f["skew"]}, f["best_in_class"], regime_ctx))
        if f["best_in_class"]:
            print(member_fire_line(f["cohort"], {"severity": f["severity"]}, f["best_in_class"]))

    # DILUTION DIAGNOSTIC: an auto industry bucket that holds a firing curated cohort but does not
    # itself fire is a coarseness failure, not a quiet tape. Say so — this is exactly how the
    # data-vendor de-rate hides behind the rallying exchanges.
    dilution = []
    fired_names = {t for f in fires for t, _ in f["members_by_excess21"]}
    for row in coverage["evaluated"]:
        if row["cohort"].startswith("industry:") and not row["verdict_fires"]:
            overlap = fired_names & {t for t, _ in row["members_by_excess21"]}
            if len(overlap) >= 2:
                dilution.append({"industry_cohort": row["cohort"], "median21": row.get("median21"),
                                 "overlap_with_firing_cohorts": sorted(overlap),
                                 "note": "auto bucket is COARSER than the narrative pricing it — "
                                         "the de-rate is inside this bucket but averaged away"})

    out = {"asof": today, "gates": {"fire_median21_pp": FIRE_MEDIAN_21,
                                    "fire_median63_pp": FIRE_MEDIAN_63,
                                    "fire_breadth": FIRE_BREADTH, "min_members": MIN_MEMBERS,
                                    "high_median21_pp": HIGH_MEDIAN_21, "benchmark": BENCH},
           "sweep_context": {k: v for k, v in ctx["files"].items()},
           "cohorts_total": len(cohorts), "curated": len(curated),
           "auto_industry": len(cohorts) - len(curated),
           "auto_leg": {"provisional": auto_provisional,
                        "coverage": round(auto_coverage, 3),
                        "coverage_gate": AUTO_MIN_COVERAGE,
                        "cohorts_built_but_withheld": sorted(auto) if auto_provisional else [],
                        "note": "auto industry cohorts cannot fire until the mapper covers "
                                f"{AUTO_MIN_COVERAGE:.0%} of the liquid tape — before that a "
                                "cohort is an arbitrary sample of its industry, not the industry"},
           "coverage": {"members_needed": len(members_needed),
                        "priced": len(members_needed) - len(unpriced),
                        "unpriced": sorted(unpriced)[:80],
                        "unpriced_n": len(unpriced),
                        "industry_mapped": mapped_ok,
                        "industry_probed_incl_negative_cache": len(cache),
                        "unmapped_liquid_n": len(unmapped_liquid),
                        "unmapped_liquid_sample": sorted(unmapped_liquid)[:40],
                        "map_budget_used": mstat["attempted"], "map_failed": mstat["failed"][:20],
                        "intl_names_seen_not_aggregated": len(ctx["intl_tickers"])},
           "cohorts_evaluated": coverage["cohorts_evaluated"],
           "below_member_floor": coverage["cohorts_below_member_floor"][:40],
           "dilution_diagnostics": dilution,
           "fires": fires,
           "evaluated": sorted(coverage["evaluated"], key=lambda r: (r.get("median21") or 0))[:60]}
    if not dry_run:
        OUT_JSON.write_text(json.dumps(out, indent=1))
        STATE.write_text(json.dumps(new_state, indent=1))

    if auto_provisional:
        print(f"AUTO LEG PROVISIONAL: industry map covers {auto_coverage:.1%} of the "
              f"{len(liquid)} liquid names (gate {AUTO_MIN_COVERAGE:.0%}) — {len(auto)} auto "
              f"cohorts built but WITHHELD from firing (a 4-name 'industry' is an arbitrary "
              f"sample, not a theme). Curated cohorts fire normally.")
    print(f"[cohort_dislocation] {today}: {len(cohorts)} cohorts "
          f"({len(curated)} curated + {len(cohorts) - len(curated)} auto-industry), "
          f"{coverage['cohorts_evaluated']} evaluated, {len(fires)} FIRED")
    if unpriced:
        print(f"DEGRADED-LOUD: {len(members_needed) - len(unpriced)} of {len(members_needed)} "
              f"cohort members priced; {len(unpriced)} DEGRADED — "
              f"{', '.join(sorted(unpriced)[:25])}{' ...' if len(unpriced) > 25 else ''}")
    if unmapped_liquid:
        print(f"DEGRADED-LOUD: {len(unmapped_liquid)} liquid names (>= ${min_mcap/1e9:.1f}B) have NO "
              f"industry row and are invisible to the auto leg — the map fills "
              f"{map_budget}/run; {len(unmapped_liquid)//max(map_budget,1)+1} more runs to close")
    for d in dilution:
        print(f"DILUTION: {d['industry_cohort']} median {d['median21']:+.1f}pp does NOT fire but "
              f"contains {d['overlap_with_firing_cohorts']} from a firing cohort — coarse bucket")
    return fires


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--map-budget", type=int, default=120,
                    help="max NEW yfinance .info lookups this run (rate budget)")
    ap.add_argument("--max-symbols", type=int, default=600, help="max price series to fetch")
    ap.add_argument("--min-mcap", type=float, default=AUTO_MIN_MCAP)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    run(a.map_budget, a.max_symbols, a.dry_run, a.min_mcap)
