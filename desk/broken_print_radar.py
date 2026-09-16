"""broken_print_radar — the systematized version of what the desk already does well by hand:
re-underwrite a QUALITY name the day after a violent single-session break.

THE GAP IT FILLS: every one of VRLA, KALMAR, DGE.L and BOBS entered through this door — a name
we either knew or could learn in a day fell 15-40% in ONE session, and the question was whether
the balance sheet and the franchise survived the news that broke the price. But nothing WATCHED
that door: dislocation_sweep only sees the ~320 names we already have a verdict on (a fresh
break at an un-researched name is invisible to it), band_watch only fires on ledger names with
an explicit band, and december_dislocation is seasonal and slow-clock. This scans the whole
US tape every day for the single-day break itself.

WHAT IT IS AND IS NOT
  - It is a TRIAGE SHEET. It computes metrics and emits no verdict, no severity-as-view, no
    "cheap". Severity is a routing priority (how big the break, how big the company), nothing more.
  - A -20% day is a QUESTION, not an entry. The pipeline is unchanged: cause-check (what actually
    broke?) -> discovery_state (is it already crowded/degraded?) -> independent court (v1.4) ->
    thesis doc -> THEN staging. Most single-day breaks are correctly priced; the whole point of
    the metrics below is to spend the re-underwriting hour on the few that might not be.
  - "Balance-sheet-intact" is a LEVERAGE READING (net debt / trailing EBITDA), not a solvency
    opinion. It exists because the desk's own history says the survivable breaks are the ones
    where the capital structure was never the question.

SOURCE (documented per the house rule that a screen names its tape):
  Yahoo Finance's equity screener via yfinance.screen() + EquityQuery — percentchange, intraday
  market cap and region are server-side filters, so one call returns the whole US tape's losers
  rather than us downloading a universe. Per-name enrichment (leverage, earnings dates, short
  interest) is yfinance Ticker.info / get_earnings_dates().
  KNOWN LIMIT — the screener is a LAST-SESSION SNAPSHOT with no history parameter: you cannot ask
  it for a past day. So the merged store IS the history (the ARK-rebalance lesson: the persisted
  file is the time series). Miss a day and that day is gone.
  KNOWN LIMIT — OTC/pink ADR lines routinely print "-17%" on 100 shares of stale quote. They are
  EXCLUDED by default (--include-otc to see them) and the excluded count is always reported.

STORE: desk/data/BROKEN_PRINTS.json, keyed sessions[date][ticker], MERGE-ONLY. Never clobbers a
prior date or a prior ticker (the house's recurring overwrite-clobber bug class); an unparseable
existing store is backed up, never overwritten.

EMAIL: routed through desk.mailer (the house legibility standard) and sent ONLY when the session
has hits that are new since the last run — a re-run on the same tape is silent.

    python3 -m desk.broken_print_radar [--min-drop -15] [--min-mktcap 250e6] [--max-enrich 25]
                                       [--include-otc] [--no-email] [--dry]

================================================================================
v2 (2026-08-11) — INTERNATIONAL COVERAGE + THE SESSION-WINDOW FIX
================================================================================
WHY v2 EXISTS — the ONON miss, stated plainly. On 2026-08-11 ONON (NYSE) printed
pre-market and broke ~-14% into the open (settling near -20%). No radar line surfaced it
and the principal caught it by hand. The root cause was NOT the universe and NOT the
screener: it was the CLOCK. v1 was registered at "daily" cadence, so the hourly `desk run`
heartbeat executed it exactly ONCE per calendar day — in practice ~00:30-01:35 PT, where it
correctly reports the PREVIOUS settled session. A break that happens during US regular
trading hours is therefore structurally invisible until the next small-hours run, ~24h
later. Secondary contributor: the -15% bar meant a name sitting at -14% intraday would not
have cleared even if the radar HAD been looking. Both are fixed here:
  - SESSION WINDOWS (legs_due / us_session_phase): the radar now knows what time it is and
    which tape is settled. An INTRADAY US leg runs through RTH at a lower provisional bar;
    the settled leg still runs post-close. --auto-window makes it cron-safe to call hourly.
  - INTERNATIONAL LEGS off the stored shelves (EDINET Japan, LSE, Euronext, KRX), each
    scanned after ITS OWN market closes, not after New York's.

REACTION DETECTION (the PSN / CHRW / SESG class). Outside the US we usually do NOT have a
trustworthy next-earnings date, so "was this a print?" cannot gate detection. The fallback
is the tape itself: a single-day move of >=8% ON >=3x the 20-day average volume is flagged
as a candidate print-break REGARDLESS of any known calendar. Volume is what separates a
repricing from a drift; without it an 8% bar would fire on every thin line in Helsinki.
The strict -15% bar still fires on its own, volume or not (a break that big is a question
even on quiet turnover).

DEGRADED-LOUD. Yahoo's international coverage fails in waves ("possibly delisted; no price
data found") and a silent shrink of the universe is indistinguishable from a quiet tape.
Every intl sweep reports how many symbols were requested, how many priced, and NAMES the
unpriced ones. A sweep that prices under half its universe says so in the summary line.

    python3 -m desk.broken_print_radar --leg intl [--shelves EDINET_JP,LSE]
    python3 -m desk.broken_print_radar --auto-window          # cron-safe, self-gating
    python3 -m desk.broken_print_radar --backfill 5           # sweep 5 sessions of history
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(__file__).resolve().parent / "data"
OUT_JSON = DATA / "BROKEN_PRINTS.json"
STATE_JSON = DATA / "broken_print_radar_state.json"
CRONTAB_PATCH = DATA / "CRONTAB_PATCH_NEEDED.txt"
LEDGER = DATA / "research_ledger.json"
POSCACHE = ROOT / "desk" / "ui" / "data" / "positions_cache.json"

SCHEMA = "broken_prints/v2"

# primary US listing venues; everything else (PNK/OTC bulletin lines) is quote-stale noise
US_PRIMARY = {"NMS", "NGM", "NCM", "NYQ", "ASE", "PCX", "BTS", "NYS", "NGS", "AMX"}


# ================================================================ v2: SHELVES
# The international universe is NOT screened live off a vendor — it is the desk's OWN stored
# shelves, so every intl fire can be traced to the file that put the name in scope. Each shelf
# names its files in priority order: the researched shortlist first (those names matter most
# and get scanned even when a per-shelf cap bites), the broad universe/price-cache after.
SHELVES = {
    "EDINET_JP": {
        "label": "EDINET Japan", "market": "JP", "suffix": ".T", "ccy": "JPY",
        "files": ["verticals/deep_value/global/data/japan_shortlist.json",
                  "verticals/deep_value/global/data/japan_nonpfic_shortlist.json",
                  "verticals/deep_value/global/data/japan_px_cache.json"],
        # TDnet 決算短信 land ~15:00 JST, i.e. AT or AFTER the close: the reaction is the NEXT
        # session's open. Window = session + prior session, same as a US after-close print.
        "print_channel": "TDnet, typically 15:00 JST at/after the close — reaction lands next session",
    },
    "LSE": {
        "label": "LSE", "market": "GB", "suffix": ".L",
        "files": ["verticals/generators/data/LSE_SHELF.json",
                  "verticals/generators/data/LSE_UNIVERSE.json"],
        "print_channel": "RNS, typically 07:00 London PRE-open — reaction lands the SAME session",
    },
    "EURONEXT": {
        "label": "Euronext", "market": "EU", "suffix": None,
        "files": ["verticals/generators/data/EURONEXT_SHELF.json"],
        "print_channel": "press release pre-open or after 17:30 CET — reaction same session or next",
    },
    "KRX": {
        "label": "KRX", "market": "KR", "suffix": ".KS", "ccy": "KRW",
        "files": ["verticals/deep_value/global/data/korea_shortlist.json",
                  "verticals/deep_value/global/data/korea_px_cache.json"],
        "print_channel": "DART/KIND filing, often after the 15:30 KST close — reaction next session",
    },
}

# Euronext + Nordic venue -> Yahoo suffix. Only used when a shelf row carries a venue but the
# symbol arrives bare; a symbol that already has a suffix is NEVER rewritten.
VENUE_SUFFIX = {"PAR": ".PA", "AMS": ".AS", "BRU": ".BR", "LIS": ".LS", "STO": ".ST",
                "HEL": ".HE", "CPH": ".CO", "OSL": ".OL", "MIL": ".MI", "MAD": ".MC",
                "ETR": ".DE", "FRA": ".F", "SWX": ".SW", "VIE": ".VI", "DUB": ".IR",
                "WSE": ".WA", "LON": ".L"}

# Markets grouped into the two non-US scan legs, each gated on ITS OWN close.
LEG_SHELVES = {"asia": ["EDINET_JP", "KRX"], "europe": ["LSE", "EURONEXT"]}

# REACTION-DETECTION thresholds. Deliberately a pair, not a score: an 8% day is only a
# candidate print-break when the TURNOVER says the market re-priced rather than drifted.
REACT_MOVE = -8.0        # single-session % change
REACT_VOLX = 3.0         # x 20-session average volume
REACT_LOOKBACK = 20      # sessions in the volume average
INTRADAY_MIN_DROP = -12.0   # provisional RTH bar: catch a name on its way through -15%


# ---------------------------------------------------------------- v2: symbols

def yahoo_symbol(raw, shelf_key: str, venue: str | None = None) -> str | None:
    """Suffix-hardening. Shelf files disagree about whether a symbol carries its venue: EDINET
    rows are bare 4-digit codes in some files and '7122.T' in others, KRX rows are 6-digit codes
    that split .KS/.KQ, LSE rows are TIDMs. A bare code sent to Yahoo returns 'possibly delisted'
    and looks exactly like a real delisting — hence this is a guard, not a convenience.
    Returns None for anything that cannot be made into a plausible symbol (never a guess)."""
    if raw is None:
        return None
    s = str(raw).strip().upper().replace(" ", "")
    if not s:
        return None
    sh = SHELVES.get(shelf_key) or {}
    if "." in s:
        head, _, tail = s.rpartition(".")
        # already suffixed and the suffix looks like a venue code -> trust it verbatim
        if head and tail.isalpha() and 1 <= len(tail) <= 3:
            return s
        # a trailing dot or a numeric tail is malformed, not a suffix
        s = s.rstrip(".")
        if "." in s:
            return s
    if venue:
        v = VENUE_SUFFIX.get(str(venue).strip().upper())
        if v:
            return s + v
    mkt = sh.get("market")
    if mkt == "JP":
        # TSE codes are 4 chars, digits or a digit+letter (e.g. 135A); anything else is not a code
        return s + ".T" if (len(s) == 4 and s[0].isdigit()) else None
    if mkt == "KR":
        return s + ".KS" if (len(s) == 6 and s.isdigit()) else None
    if mkt == "GB":
        return s + ".L" if s.isalnum() else None
    return None      # Euronext with no suffix and no venue: UNRESOLVED, never a guess


def _clean_name(v) -> str | None:
    """Shelf and filing names arrive HTML-escaped from their source scrapers ('YAGI &amp; CO.').
    Unescape once here so the escape never reaches a fire line or an email."""
    if not v:
        return None
    import html
    return html.unescape(str(v)).strip() or None


def _iter_shelf_rows(obj):
    """Shelf files are three shapes: {'rows': [...]}, a bare [...], or a {sym: {...}} price
    cache. Yield (symbol-ish, row-dict) from any of them without assuming which."""
    if isinstance(obj, dict):
        rows = obj.get("rows")
        if isinstance(rows, list):
            for r in rows:
                if isinstance(r, dict):
                    yield (r.get("sym") or r.get("ticker") or r.get("tidm") or r.get("symbol")), r
            return
        for k, v in obj.items():
            if k in ("meta", "schema", "updated") or not isinstance(v, dict):
                continue
            yield k, v
        return
    if isinstance(obj, list):
        for r in obj:
            if isinstance(r, dict):
                yield (r.get("sym") or r.get("ticker") or r.get("tidm") or r.get("symbol")), r
            elif isinstance(r, str):
                yield r, {}


def load_shelf(shelf_key: str, cap: int | None = None) -> tuple[list[str], dict, list[str]]:
    """(symbols, sym -> {name, shelf, file}, unresolved-raw-symbols). File order IS priority
    order — the researched shortlist is read first so a --cap truncates the broad universe,
    never the names we already care about."""
    sh = SHELVES.get(shelf_key)
    if not sh:
        return [], {}, []
    syms, meta, unresolved = [], {}, []
    for rel in sh["files"]:
        p = ROOT / rel
        if not p.exists():
            continue
        try:
            obj = json.loads(p.read_text())
        except Exception:
            continue
        for raw, row in _iter_shelf_rows(obj):
            y = yahoo_symbol(raw, shelf_key, row.get("venue"))
            if not y:
                if raw:
                    unresolved.append(str(raw))
                continue
            if y in meta:
                continue
            # a price cache row that never priced is a dead line, not a universe member
            if "px" in row and row.get("px") in (None, 0):
                continue
            # Carry the shelf's OWN fundamentals forward. Yahoo rate-limits hard right after a
            # bulk history sweep, and a blank row is the worst possible output — these files are
            # audited-filing derived and already on disk, so a rate-limited enrichment degrades
            # to filing data rather than to nothing.
            meta[y] = {"name": _clean_name(row.get("ind") or row.get("name") or row.get("shortName")),
                       "shelf": shelf_key, "shelf_label": sh["label"], "file": rel,
                       "sector": row.get("sec") or row.get("sector"),
                       "market": sh["market"],
                       # UNITS ARE NOT DECORATION. The Japan/Korea caches carry market cap in
                       # JPY/KRW and the shelves carry cash and debt in the FILING currency;
                       # printing either behind a '$' is a 100x-scale lie. USD is kept separate
                       # from local, and local always travels with its currency code.
                       "shelf_mcap_usd": row.get("mcap_usd"),
                       "shelf_mcap_local": row.get("mktcap") or row.get("mcap"),
                       "shelf_ccy": row.get("ccy") or sh.get("ccy"),
                       "shelf_cash": row.get("cash"), "shelf_debt": row.get("debt"),
                       "shelf_ebit": row.get("ebit")}
            syms.append(y)
            if cap and len(syms) >= cap:
                break
        if cap and len(syms) >= cap:
            break
    _apply_filing_facts(shelf_key, meta)
    return syms, meta, unresolved


# Offline regulator-filing stores the desk already holds. Japan and Korea have no usable Yahoo
# name or capital structure for most of their shelf, and these files answer both — from the
# FILING, which is a better authority than the vendor field it replaces, and cannot be
# rate-limited. (file, key-field, name-fields, source label)
FILING_STORES = {
    "EDINET_JP": ("verticals/deep_value/global/data/edinet_store.json", "sec_code",
                  ("name_en", "name_ja"), "EDINET"),
    "KRX": ("verticals/deep_value/global/data/dart_store.json", "stock_code",
            ("name",), "DART"),
}
_FILING_CACHE: dict[str, dict] = {}


def _bare_code(sym: str) -> str:
    return sym.rsplit(".", 1)[0]


def _filing_facts(shelf_key: str) -> dict:
    """{bare exchange code -> facts}, loaded once per process."""
    if shelf_key in _FILING_CACHE:
        return _FILING_CACHE[shelf_key]
    spec = FILING_STORES.get(shelf_key)
    out: dict[str, dict] = {}
    if spec:
        rel, keyfield, namefields, label = spec
        try:
            for rec in json.loads((ROOT / rel).read_text()).values():
                code = str(rec.get(keyfield) or "").strip()
                # EDINET pads the 4-digit TSE code with a trailing zero (71220 -> 7122)
                if shelf_key == "EDINET_JP" and len(code) == 5 and code.endswith("0"):
                    code = code[:4]
                if not code:
                    continue
                name = next((rec.get(f) for f in namefields if rec.get(f)), None)
                out[code] = {"name": _clean_name(name),
                             "cash": rec.get("CashAndCashEquivalentsAtCarryingValue"),
                             "debt": rec.get("DebtLongtermAndShorttermCombinedAmount"),
                             "ebit": rec.get("OperatingIncomeLoss"),
                             "period_end": rec.get("period_end"), "source": label}
        except Exception:
            out = {}
    _FILING_CACHE[shelf_key] = out
    return out


def _apply_filing_facts(shelf_key: str, meta: dict):
    facts = _filing_facts(shelf_key)
    if not facts:
        return
    for sym, m in meta.items():
        f = facts.get(_bare_code(sym))
        if not f:
            continue
        m["name"] = m.get("name") or f.get("name")
        for a, b in (("shelf_cash", "cash"), ("shelf_debt", "debt"), ("shelf_ebit", "ebit")):
            if m.get(a) is None:
                m[a] = f.get(b)
        m["shelf_asof"] = f.get("period_end")
        m["shelf_facts_source"] = f.get("source")


# ---------------------------------------------------------------- v2: session windows

def us_session_phase(dt_et: datetime.datetime) -> str:
    """PRE / RTH / POST / CLOSED for a New York wall-clock datetime. Weekends are CLOSED;
    holidays are not modelled (a holiday simply produces an empty tape, which the screener's
    own session-date logic already reports honestly)."""
    if dt_et.weekday() >= 5:
        return "CLOSED"
    m = dt_et.hour * 60 + dt_et.minute
    if m < 4 * 60:
        return "CLOSED"
    if m < 9 * 60 + 30:
        return "PRE"
    if m < 16 * 60:
        return "RTH"
    if m < 20 * 60:
        return "POST"
    return "CLOSED"


def legs_due(dt_et: datetime.datetime) -> list[str]:
    """WHICH TAPES ARE WORTH LOOKING AT RIGHT NOW — the fix for the ONON miss.

    us_intraday  09:45-16:00 ET   the break is happening; provisional, can deepen or recover
    us_settled   16:15-23:59 ET and 00:00-09:30 ET   the completed session
    europe       12:00-14:00 ET   LSE closes 16:30 London, Euronext 17:30 CET = ~11:30 ET
    asia         03:00-05:00 ET   TSE closes 15:00 JST, KRX 15:30 KST = ~02:30 ET

    Note what this does NOT do: it never claims a leg is due on a weekend, and the intraday
    leg is explicitly labelled provisional everywhere downstream. Returned order is scan order.
    """
    if dt_et.weekday() >= 5:
        return []
    m = dt_et.hour * 60 + dt_et.minute
    due = []
    if 3 * 60 <= m < 5 * 60:
        due.append("asia")
    if 12 * 60 <= m < 14 * 60:
        due.append("europe")
    if 9 * 60 + 45 <= m < 16 * 60:
        due.append("us_intraday")
    elif m >= 16 * 60 + 15 or m < 9 * 60 + 30:
        due.append("us_settled")
    return due


def _now_et() -> datetime.datetime:
    """New York wall clock. zoneinfo where available; otherwise the machine's own clock with a
    fixed PT->ET shift, because this desk runs on PT and a wrong-by-3-hours window is exactly
    the bug this function exists to kill."""
    try:
        from zoneinfo import ZoneInfo
        return datetime.datetime.now(ZoneInfo("America/New_York")).replace(tzinfo=None)
    except Exception:
        return datetime.datetime.now() + datetime.timedelta(hours=3)


def _load_state() -> dict:
    try:
        return json.loads(STATE_JSON.read_text())
    except Exception:
        return {}


def _mark_leg(leg: str, key: str):
    st = _load_state()
    st.setdefault("legs", {})[leg] = {"key": key, "at": datetime.datetime.now().isoformat(timespec="seconds")}
    tmp = STATE_JSON.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, indent=1))
    os.replace(tmp, STATE_JSON)


def _leg_already_ran(leg: str, key: str) -> bool:
    return ((_load_state().get("legs") or {}).get(leg) or {}).get("key") == key


def _window_key(leg: str, dt_et: datetime.datetime) -> str:
    """Once-per-window guard key. The intraday leg re-runs each hour (the tape moves); the
    settled/europe/asia legs run once per session.

    The settled key is the SESSION IT REPORTS, not the wall date: before the open that is
    yesterday, after the close it is today. Keying on the wall date instead is how v1's
    overnight run and a post-close run collapse into one job and the post-close one never
    happens — the settled record then always lags a full day."""
    if leg == "us_intraday":
        return f"{dt_et.date().isoformat()}T{dt_et.hour:02d}"
    if leg == "us_settled":
        d = dt_et.date() if dt_et.hour >= 16 else dt_et.date() - datetime.timedelta(days=1)
        return d.isoformat()
    return dt_et.date().isoformat()


# ---------------------------------------------------------------- v2: reaction detection

def _avg(xs) -> float | None:
    xs = [x for x in xs if x is not None]
    return (sum(xs) / len(xs)) if xs else None


def reaction_scan(bars: dict, idx: int = -1, min_move: float = REACT_MOVE,
                  min_volx: float = REACT_VOLX, hard_drop: float = -15.0,
                  lookback: int = REACT_LOOKBACK) -> list[dict]:
    """PURE. bars = {sym: {'dates': [...], 'close': [...], 'volume': [...]}} -> candidate rows.

    Two independent triggers, deliberately a UNION and not a blend:
      REACTION  move <= min_move AND volume >= min_volx x the trailing average. This is the
                class v1 could not see at all — a name with no known print date that the tape
                says was re-priced. PSN, CHRW and SESG were all this.
      HARD      move <= hard_drop on any turnover. A break that big is a question even thin.
    A symbol without enough history for the volume average can still fire on HARD; it is
    labelled volume-unconfirmed rather than dropped, because DATA MISSING is not DATA CLEAN.
    """
    out = []
    for sym, b in sorted(bars.items()):
        c, v, d = b.get("close") or [], b.get("volume") or [], b.get("dates") or []
        n = len(c)
        i = idx if idx >= 0 else n + idx
        if n < 2 or i < 1 or i >= n:
            continue
        prev, last = c[i - 1], c[i]
        if not prev or not last or prev <= 0:
            continue
        move = (last / prev - 1) * 100.0
        window = v[max(0, i - lookback):i]
        adv = _avg(window)
        volx = round(v[i] / adv, 1) if (adv and v[i] is not None and adv > 0) else None
        hard = move <= hard_drop
        react = (move <= min_move) and (volx is not None and volx >= min_volx)
        if not (hard or react):
            continue
        out.append({
            "ticker": sym,
            "session": d[i] if i < len(d) else None,
            "prev_close": round(float(prev), 4),
            "price": round(float(last), 4),
            "drop_pct": round(move, 2),
            "volume": int(v[i]) if v[i] is not None else None,
            "adv_lookback": int(adv) if adv else None,
            "vol_x_adv": volx,
            "trigger": "HARD+REACTION" if (hard and react) else ("HARD" if hard else "REACTION"),
            "volume_confirmed": bool(volx is not None and volx >= min_volx),
        })
    out.sort(key=lambda r: r["drop_pct"])
    return out


def degraded_summary(requested: list[str], bars: dict, name_cap: int = 30) -> dict:
    """DEGRADED-LOUD. Yahoo drops international lines in waves; a sweep that silently priced
    300 of 1,200 names reports 'quiet tape' and is wrong. Names the casualties."""
    priced = [s for s in requested if (bars.get(s) or {}).get("close")]
    unpriced = [s for s in requested if s not in set(priced)]
    n_req = len(requested)
    return {"requested": n_req, "priced": len(priced), "unpriced": len(unpriced),
            "priced_pct": round(100.0 * len(priced) / n_req, 1) if n_req else 0.0,
            "unpriced_names": unpriced[:name_cap],
            "unpriced_truncated": max(0, len(unpriced) - name_cap),
            "degraded": bool(n_req and len(priced) / n_req < 0.5)}


# ---------------------------------------------------------------- v2: batched history

def batch_history(symbols: list[str], period: str = "3mo", batch: int = 40,
                  retries: int = 3, pause: float = 1.2, verbose: bool = True) -> dict:
    """Polite batched daily history -> {sym: {dates, close, volume}}.

    auto_adjust=True ON PURPOSE: a raw close series prints an ex-dividend day as a -9% "break".
    Adjusted closes remove that false positive at the cost of hiding a genuine special-dividend
    collapse, which is the right trade for a break detector.
    Retry is per BATCH with backoff — Yahoo's international failures are bursty and a whole
    batch commonly comes back empty on the first ask and fine on the second."""
    import yfinance as yf
    out: dict[str, dict] = {}
    syms = [s for s in dict.fromkeys(symbols) if s]
    for k in range(0, len(syms), batch):
        chunk = syms[k:k + batch]
        df = None
        for attempt in range(retries):
            try:
                df = yf.download(chunk, period=period, interval="1d", group_by="ticker",
                                 auto_adjust=True, progress=False, threads=True,
                                 timeout=30)
                if df is not None and len(df):
                    break
            except Exception as ex:
                if verbose and attempt == retries - 1:
                    print(f"  [batch {k//batch+1}] {type(ex).__name__}: {str(ex)[:90]}")
            time.sleep(pause * (attempt + 1))
        if df is None or not len(df):
            time.sleep(pause)
            continue
        multi = getattr(df.columns, "nlevels", 1) > 1
        for s in chunk:
            try:
                if multi:
                    if s not in df.columns.get_level_values(0):
                        continue
                    sub = df[s]
                else:
                    if len(chunk) != 1:
                        continue
                    sub = df
            except Exception:
                continue
            try:
                sub = sub.dropna(subset=["Close"])
                if not len(sub):
                    continue
                out[s] = {"dates": [d.date().isoformat() for d in sub.index.to_pydatetime()],
                          "close": [float(x) for x in sub["Close"].tolist()],
                          "volume": [float(x) if x == x else None for x in sub["Volume"].tolist()]}
            except Exception:
                continue
        time.sleep(pause)
        if verbose:
            print(f"  priced {len(out)}/{min(k+batch, len(syms))} of {len(syms)}…", flush=True)
    return out


# ---------------------------------------------------------------- tape

def screen_losers(min_drop: float, min_mktcap: float, region: str, size: int) -> list[dict]:
    """One server-side screener call -> the whole region's single-day losers."""
    import yfinance as yf
    from yfinance import EquityQuery
    q = EquityQuery("and", [
        EquityQuery("lt", ["percentchange", min_drop]),
        EquityQuery("gte", ["intradaymarketcap", min_mktcap]),
        EquityQuery("eq", ["region", region]),
    ])
    res = yf.screen(q, size=size, sortField="percentchange", sortAsc=True)
    return list(res.get("quotes") or [])


def _session_date(quotes: list[dict]) -> str | None:
    """The tape date the screener is reporting (max regularMarketTime). None when the screener
    returned nothing at all — we do NOT stamp today's calendar date on an unknown session (that
    is how a weekend gets written into the store as a trading day)."""
    ts = [q.get("regularMarketTime") for q in quotes if q.get("regularMarketTime")]
    if not ts:
        return None
    return datetime.datetime.fromtimestamp(max(ts)).date().isoformat()


def _prev_session(d: datetime.date) -> datetime.date:
    """Previous trading day, calendar-approximate (weekends only; holidays widen the window
    harmlessly — a stale earnings match is labelled with its actual date so the reader judges)."""
    step = {0: 3, 6: 2, 5: 1}.get(d.weekday(), 1)
    return d - datetime.timedelta(days=step)


# ---------------------------------------------------------------- enrichment

def _leverage(info: dict) -> dict:
    """Net debt / trailing EBITDA + a plain-language leverage reading. Honest nulls: an unknown
    capital structure is UNKNOWN, never 0 (the DATA-MISSING-never-zero rule)."""
    sector = info.get("sector") or ""
    debt, cash, ebitda = info.get("totalDebt"), info.get("totalCash"), info.get("ebitda")
    out = {"total_debt": debt, "total_cash": cash, "ebitda_ttm": ebitda,
           "net_debt": None, "net_debt_ebitda": None, "leverage_read": "UNKNOWN",
           "balance_sheet_intact": None, "cash_burn": None, "runway_years_crude": None}
    if sector == "Financial Services":
        out["leverage_read"] = "NA_FINANCIAL"   # debt is raw material for a bank/insurer
        return out
    if debt is None or cash is None:
        return out
    nd = float(debt) - float(cash)
    out["net_debt"] = nd
    if nd <= 0:
        # NET CASH answers the LEVERAGE question only. A cash-burning net-cash name is safe from
        # its creditors and not from its own runway — say both, never let "no debt" read as "fine".
        out["leverage_read"] = "NET_CASH"
        out["balance_sheet_intact"] = True
        out["cash_burn"] = bool(ebitda is not None and float(ebitda) < 0)
        if out["cash_burn"]:
            out["leverage_read"] = "NET_CASH_BURNING"
            out["runway_years_crude"] = round(float(cash) / abs(float(ebitda)), 1)
        return out
    if not ebitda or float(ebitda) <= 0:
        out["leverage_read"] = "NET_DEBT_NEG_EBITDA"   # unmeasurable, NOT clean
        return out
    x = nd / float(ebitda)
    out["net_debt_ebitda"] = round(x, 2)
    if x > 10:
        # near-zero EBITDA makes the ratio arithmetic, not information (CERS: $21M of net debt
        # over a rounding-error EBITDA prints 311x). Say so rather than shouting "HIGH".
        out["leverage_read"] = "RATIO_NOT_MEANINGFUL"
        return out
    out["leverage_read"] = "LOW" if x <= 2.5 else ("MODERATE" if x <= 4 else "HIGH")
    out["balance_sheet_intact"] = bool(x <= 2.5)
    return out


def _earnings_context(tk, quote: dict, session: datetime.date) -> dict:
    """Was the break an EARNINGS reaction or a NEWS day? Window = the session itself plus the
    previous trading day (an after-close print drops the stock the next morning)."""
    start = _prev_session(session)
    dates: list[datetime.date] = []
    try:
        ed = tk.get_earnings_dates(limit=12)
        if ed is not None and len(ed):
            dates = [d.date() for d in ed.index.to_pydatetime()]
    except Exception:
        pass
    for k in ("earningsTimestamp", "earningsTimestampStart", "earningsTimestampEnd"):
        if quote.get(k):
            try:
                dates.append(datetime.datetime.fromtimestamp(quote[k]).date())
            except Exception:
                pass
    if not dates:
        return {"drop_type": "UNKNOWN", "earnings_date": None, "days_from_earnings": None,
                "earnings_date_estimated": bool(quote.get("isEarningsDateEstimate"))}
    inwin = [d for d in dates if start <= d <= session]
    past = [d for d in dates if d <= session]
    nearest = max(past) if past else min(dates)
    return {"drop_type": "EARNINGS" if inwin else "NEWS",
            "earnings_date": (max(inwin) if inwin else nearest).isoformat(),
            "days_from_earnings": (session - nearest).days if past else None,
            "earnings_date_estimated": bool(quote.get("isEarningsDateEstimate"))}


def _known(ticker: str) -> dict:
    """Do we already have a view or a position? A break at a name we own is a re-underwrite."""
    out = {"held": False, "held_qty": None, "ledger_verdict": None}
    try:
        for p in json.loads(POSCACHE.read_text()).get("positions", []):
            if p.get("symbol") == ticker and p.get("sec_type") == "STK":
                out["held"] = True
                out["held_qty"] = p.get("qty")
                out["avg_cost"] = p.get("avg_cost")
    except Exception:
        pass
    try:
        for n in json.loads(LEDGER.read_text()).get("names", []):
            if n.get("ticker") == ticker:
                out["ledger_verdict"] = (str(n.get("verdict") or "").strip() or None)
                break
    except Exception:
        pass
    return out


def triage(quote: dict, session: datetime.date, enrich: bool) -> dict:
    """TRIAGE METRICS ONLY — no verdicts. Every field is a measurement or an honest null."""
    import yfinance as yf
    sym = quote.get("symbol")
    px = quote.get("regularMarketPrice")
    drop = quote.get("regularMarketChangePercent")
    vol, adv = quote.get("regularMarketVolume"), quote.get("averageDailyVolume3Month")
    hi52, lo52 = quote.get("fiftyTwoWeekHigh"), quote.get("fiftyTwoWeekLow")
    row = {
        "ticker": sym,
        "name": quote.get("shortName") or quote.get("displayName"),
        "exchange": quote.get("fullExchangeName"),
        "price": px,
        "prev_close": round(px / (1 + drop / 100), 4) if (px and drop is not None and drop > -100) else None,
        "drop_pct": round(drop, 2) if drop is not None else None,
        "market_cap": quote.get("marketCap"),
        "volume": vol,
        "adv_3m": adv,
        "vol_x_adv": round(vol / adv, 1) if (vol and adv) else None,
        "pct_below_52w_high": round((px / hi52 - 1) * 100, 1) if (px and hi52) else None,
        "pct_above_52w_low": round((px / lo52 - 1) * 100, 1) if (px and lo52) else None,
        "chg_52w_pct": round(quote.get("fiftyTwoWeekChangePercent"), 1) if quote.get("fiftyTwoWeekChangePercent") is not None else None,
        "sector": None, "industry": None,
        "short_pct_float": None, "short_days_to_cover": None, "shares_short": None,
    }
    row.update({"drop_type": "UNKNOWN", "earnings_date": None, "days_from_earnings": None,
                "earnings_date_estimated": None, "leverage_read": "UNKNOWN",
                "balance_sheet_intact": None, "net_debt": None, "net_debt_ebitda": None,
                "ebitda_ttm": None, "total_debt": None, "total_cash": None,
                "cash_burn": None, "runway_years_crude": None,
                "enriched": False, "enrich_error": None})
    if enrich:
        try:
            tk = yf.Ticker(sym)
            info = tk.info or {}
            row["sector"], row["industry"] = info.get("sector"), info.get("industry")
            row.update(_leverage(info))
            row.update(_earnings_context(tk, quote, session))
            sp = info.get("shortPercentOfFloat")
            row["short_pct_float"] = round(sp * 100, 2) if sp is not None else None
            row["short_days_to_cover"] = info.get("shortRatio")
            row["shares_short"] = info.get("sharesShort")
            row["enriched"] = True
        except Exception as ex:
            row["enrich_error"] = str(ex)[:180]
    row.update(_known(sym))
    row["leg"] = "US"
    row["shelf"] = "US_TAPE"
    row["shelf_label"] = "US tape"
    row["ledger_status"] = _ledger_status(row)
    # SEVERITY = ROUTING PRIORITY ONLY (magnitude x size x do-we-own-it), explicitly NOT a view and
    # deliberately NOT a function of the balance sheet — the moment severity encodes quality it stops
    # being routing and starts being a verdict. HIGH pushes, so the bar is set where a HIGH stays rare
    # on a normal tape (Jul-31, the heaviest print day of the quarter, produced 9).
    d = row["drop_pct"] or 0
    mc = row["market_cap"] or 0
    row["severity"] = "HIGH" if (d <= -25 or (d <= -20 and mc >= 2e9) or row.get("held")) else "MED"
    return row


# ---------------------------------------------------------------- store (MERGE-ONLY)

def _load_store() -> dict:
    if not OUT_JSON.exists():
        return {"schema": SCHEMA, "sessions": {}}
    try:
        s = json.loads(OUT_JSON.read_text())
        s.setdefault("sessions", {})
        return s
    except Exception as ex:
        bak = OUT_JSON.with_suffix(f".corrupt.{int(time.time())}.json")
        OUT_JSON.replace(bak)
        print(f"[broken_print_radar] existing store unparseable ({ex}); backed up -> {bak.name}")
        return {"schema": SCHEMA, "sessions": {}}


def merge_store(session: str, rows: list[dict], params: dict) -> tuple[dict, list[str]]:
    """Merge by date+ticker. Never drops a prior session or a prior ticker; returns the store and
    the list of tickers that are NEW for this session (the email trigger)."""
    store = _load_store()
    now = datetime.datetime.now().isoformat(timespec="seconds")
    sess = store["sessions"].setdefault(session, {"scanned_at": now, "params": params, "hits": {}})
    sess["params"] = params
    sess["last_scanned_at"] = now
    if isinstance(sess.get("hits"), list):   # tolerate any hand-edited/legacy list shape
        sess["hits"] = {h.get("ticker"): h for h in sess["hits"] if isinstance(h, dict)}
    new = []
    for r in rows:
        t = r["ticker"]
        prior = sess["hits"].get(t)
        if prior is None:
            r["first_seen"] = now
            new.append(t)
        else:
            r["first_seen"] = prior.get("first_seen", now)
        r["last_updated"] = now
        sess["hits"][t] = r
    store["schema"] = SCHEMA
    store["updated"] = now
    tmp = OUT_JSON.with_suffix(".tmp")
    tmp.write_text(json.dumps(store, indent=1, default=str))
    os.replace(tmp, OUT_JSON)
    return store, new


# ---------------------------------------------------------------- output

CCY_SYMBOL = {"USD": "$", "JPY": "¥", "KRW": "₩", "GBP": "£", "GBp": "£", "EUR": "€",
              "SEK": "SEK ", "NOK": "NOK ", "DKK": "DKK ", "CHF": "CHF ", "PLN": "PLN "}


def _fmt_cap(v, ccy: str = "USD") -> str:
    """Money always carries its unit. A JPY balance sheet rendered behind a '$' is off by ~150x
    and reads as a perfectly plausible number, which is exactly what makes it dangerous."""
    if not v:
        return "market cap unknown"
    sym = CCY_SYMBOL.get(ccy or "USD", (ccy or "") + " ")
    return f"{sym}{v/1e9:.1f}B" if abs(v) >= 1e9 else f"{sym}{v/1e6:.0f}M"


def _cap_str(r: dict) -> str:
    """The row's size, in whichever unit we actually know it in — USD where the shelf converted,
    local currency (named) where it did not."""
    if r.get("market_cap"):
        return _fmt_cap(r["market_cap"])
    if r.get("market_cap_local"):
        return _fmt_cap(r["market_cap_local"], r.get("market_cap_ccy") or "")
    return "market cap unknown"


def _leverage_phrase(r: dict) -> str:
    lr = r.get("leverage_read")
    # WHICH LINE DID WE DIVIDE BY. The US leg has EBITDA; the international shelves carry
    # operating income. Printing EBIT in an "x EBITDA" slot understates leverage by all of D&A,
    # so the metric names itself and the source is stated where it is not the vendor.
    met = r.get("leverage_metric") or "trailing EBITDA"
    src = f", per the {r['leverage_basis']}" if r.get("leverage_basis") and r.get("leverage_basis") != "yfinance" else ""
    cc = r.get("fin_ccy") or "USD"
    if lr == "NET_CASH":
        return f"net cash of {_fmt_cap(abs(r['net_debt']), cc)} — no leverage constraint{src}"
    if lr == "NET_CASH_BURNING":
        return (f"net cash of {_fmt_cap(abs(r['net_debt']), cc)} — no leverage constraint, but {met} is "
                f"negative, so roughly {r['runway_years_crude']} years of cash at the current burn "
                f"(crude: operating burn only, ignores capex and working capital). The question here is "
                f"runway, not creditors{src}")
    if lr in ("LOW", "MODERATE", "HIGH"):
        return (f"net debt {_fmt_cap(r['net_debt'], cc)} = {r['net_debt_ebitda']}x {met} "
                f"({lr.lower()} leverage){src}")
    if lr == "RATIO_NOT_MEANINGFUL":
        return (f"net debt {_fmt_cap(r['net_debt'], cc)} but {met} is near zero "
                f"({r['net_debt_ebitda']}x) — the ratio carries no information; read the cash runway instead{src}")
    if lr == "NET_DEBT_NEG_EBITDA":
        return f"net debt {_fmt_cap(r['net_debt'], cc)} against NEGATIVE {met} — leverage unmeasurable, not clean{src}"
    if lr == "NA_FINANCIAL":
        return "a financial — net-debt/EBITDA does not apply; leverage must be read off capital ratios"
    return "capital structure not retrieved (DATA MISSING, not clean)"


def _hit_lines(r: dict) -> list[str]:
    L = []
    when = ("on its earnings print" if r["drop_type"] == "EARNINGS" else
            "on news, NOT an earnings day" if r["drop_type"] == "NEWS" else
            # INTERNATIONAL: no trustworthy earnings calendar, so the TAPE classifies the event.
            "on a volume-confirmed repricing (no earnings calendar available for this market — "
            "the turnover, not a date, is what says the market re-priced)"
            if r["drop_type"] == "REACTION" else
            "on a move the turnover does NOT confirm — treat the cause as unestablished"
            if r["drop_type"] == "UNCONFIRMED_TURNOVER" else "on an unclassified event")
    ed = f" (last reported {r['earnings_date']})" if r.get("earnings_date") else ""
    L.append(f"Fell {r['drop_pct']:+.1f}% to ${r['price']:,.2f} from ${r['prev_close']:,.2f}, {when}{ed}.")
    L.append(f"Size: {_fmt_cap(r['market_cap'])}" + (f" · {r['sector']} / {r['industry']}" if r.get("sector") else ""))
    if r.get("vol_x_adv"):
        L.append(f"Volume {r['volume']:,} shares = {r['vol_x_adv']}x its 3-month average — "
                 f"{'a real repricing on real turnover' if r['vol_x_adv'] >= 3 else 'thin relative to the move'}.")
    L.append(f"Balance sheet: {_leverage_phrase(r)}.")
    if r.get("pct_below_52w_high") is not None:
        L.append(f"Context: {abs(r['pct_below_52w_high']):.0f}% below the 52-week high, "
                 f"{r['pct_above_52w_low']:+.0f}% off the low; the stock is {r['chg_52w_pct']:+.0f}% over 12 months."
                 if r.get("chg_52w_pct") is not None else
                 f"Context: {abs(r['pct_below_52w_high']):.0f}% below the 52-week high.")
    if r.get("short_pct_float") is not None:
        L.append(f"Short interest {r['short_pct_float']:.1f}% of float, {r['short_days_to_cover']} days to cover "
                 f"(exchange data, updated roughly twice a month — stale by construction).")
    if r.get("held"):
        L.append(f"WE OWN THIS: {r['held_qty']:,.0f} shares at ${r.get('avg_cost', 0):,.2f} average cost — "
                 f"a break in a held name is a re-underwrite, not a shopping idea.")
    if r.get("ledger_verdict"):
        L.append(f"Our standing record: {r['ledger_verdict'][:200]}")
    return L


def _print_summary(session: str, rows: list[dict], stats: dict):
    intact = [r for r in rows if r.get("balance_sheet_intact")]
    burn = [r for r in intact if r.get("cash_burn")]
    print(f"\n[broken_print_radar] session {session} — {len(rows)} hits at "
          f"{stats['min_drop']}% / {_fmt_cap(stats['min_mktcap'])}+ "
          f"({len(intact)} balance-sheet-intact, {len(burn)} of those burning cash) · screener returned {stats['raw']}, "
          f"excluded {stats['excluded_otc']} OTC/pink + {stats['excluded_other']} non-equity/venue")
    if stats.get("session_complete") is False:
        print(f"  PROVISIONAL — the market is still open ({stats.get('market_state')}); these moves "
              f"can deepen or recover by the close. Re-run after the bell for the settled tape.")
    if not rows:
        print("  no single-day breaks cleared the bar — quiet tape\n")
        return
    unenriched = [r["ticker"] for r in rows if not r.get("enriched")]
    if unenriched:
        print(f"  NOT ENRICHED (past the --max-enrich cap, metrics blank not clean): {', '.join(unenriched)}")
    hdr = f"  {'TICKER':<8}{'DROP':>8}{'CAP':>9}{'VOL/ADV':>9}{'ND/EBITDA':>11}  {'TYPE':<9}{'52W-HI':>8}  NAME"
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    for r in rows:
        nd = {"NET_CASH": "net cash", "NET_CASH_BURNING": "cash/burn", "NA_FINANCIAL": "n/a-fin",
              "NET_DEBT_NEG_EBITDA": "neg-EBITDA",
              "RATIO_NOT_MEANINGFUL": "~0-EBITDA"}.get(r.get("leverage_read")) or (
              f"{r['net_debt_ebitda']:.1f}x" if r.get("net_debt_ebitda") is not None else "?")
        print(f"  {r['ticker']:<8}{r['drop_pct']:>7.1f}%{_fmt_cap(r['market_cap']):>9}"
              f"{(str(r['vol_x_adv'])+'x' if r.get('vol_x_adv') else '?'):>9}{nd:>11}  "
              f"{r['drop_type']:<9}{(str(round(r['pct_below_52w_high']))+'%' if r.get('pct_below_52w_high') is not None else '?'):>8}  "
              f"{(r['name'] or '')[:34]}{' [HELD]' if r.get('held') else ''}")
    print("\n  TRIAGE ONLY — no verdicts here. Each line is a question: what broke, is it already"
          "\n  crowded (discovery_state), and does the court clear it? A -20% day is usually correct.\n")
    for r in rows:
        print(f"DETFIRE|broken_print|{r['ticker']}|{r['severity']}|{r['name']} fell {r['drop_pct']:+.1f}% in one "
              f"session ({r['drop_type'].lower()}) at {_fmt_cap(r['market_cap'])}, "
              f"{r.get('vol_x_adv') or '?'}x ADV, {_leverage_phrase(r)}"
              f"{' — HELD' if r.get('held') else ''} — TRIAGE ONLY: cause-check -> discovery_state -> "
              f"court (v1.4) before any staging")


def _email(session: str, rows: list[dict], new: list[str], stats: dict, leg_label: str = "US") -> bool:
    from desk.mailer import send
    d = datetime.date.fromisoformat(session)
    intact = [r for r in rows if r.get("balance_sheet_intact")]
    held = [r for r in rows if r.get("held")]
    prov = stats.get("session_complete") is False
    subject = (("PROVISIONAL " if prov else "") +
               f"BROKEN PRINTS {leg_label} {d:%b}-{d.day}: {len(rows)} hit{'s' if len(rows) != 1 else ''}, "
               f"{len(intact)} balance-sheet-intact" + (f", {len(held)} HELD" if held else ""))
    unres = [r["ticker"] for r in rows if r.get("ledger_status") == "UNRESEARCHED"]
    pricing = stats.get("pricing") or {}
    sections = [("What happened",
                 [f"{len(rows)} {leg_label} names fell "
                  f"{abs(stats['min_drop'])}% or more (or 8%+ on 3x normal volume) in the {session} session.",
                  (f"{len(unres)} of them are UNRESEARCHED — no ledger verdict, no position: "
                   f"{', '.join(unres[:12])}." if unres else ""),
                  (f"PRICING WAS DEGRADED: only {pricing.get('priced')} of {pricing.get('requested')} "
                   f"shelf symbols returned data ({pricing.get('priced_pct')}%). A quiet result here "
                   f"means UNKNOWN, not clean." if pricing.get("degraded") else ""),
                  ("The market is still open, so these are intraday moves that can deepen or recover "
                   "by the close — provisional, not the settled tape." if prov else ""),
                  f"{len(intact)} of them carry net cash or under 2.5x net-debt/EBITDA — "
                  f"{sum(1 for r in intact if r.get('cash_burn'))} of those {len(intact)} are burning cash at the "
                  f"EBITDA line, where the question is runway rather than creditors.",
                  (f"New since the last scan: {', '.join(new)}." if new else "No new names since the last scan.")])]
    for r in sorted(rows, key=lambda x: x["drop_pct"] or 0):
        sections.append((f"{r['ticker']} {r['drop_pct']:+.1f}% — {r['name']}", _hit_lines(r)))
    if held:
        sections.append(("Live stakes in the names above",
                         [f"{r['ticker']}: {r['held_qty']:,.0f} shares at ${r.get('avg_cost', 0):,.2f} "
                          f"(from the live position cache)" for r in held]))
    sections.append(("Full sheet", [f"desk/data/BROKEN_PRINTS.json — session {session}"]))
    return send(subject, sections,
                footer=("These are triage metrics, not verdicts. Every name here is a question — what "
                        "actually broke, is the fall already crowded, and does the court clear it — and "
                        "most single-day breaks turn out to be correctly priced. Nothing is staged off "
                        "this list."))


# ================================================================ v2: international leg

def _ledger_status(r: dict) -> str:
    """UNRESEARCHED vs our standing record — the whole point of pointing a break radar at a
    shelf we have never courted. A name with no verdict and no position is the interesting one."""
    if r.get("held"):
        return "HELD"
    v = r.get("ledger_verdict")
    return f"LEDGER:{v[:40]}" if v else "UNRESEARCHED"


def _shelf_leverage(meta: dict) -> dict:
    """Leverage off the SHELF's filing data. Deliberately labelled EBIT, not EBITDA: the shelves
    carry operating income, and quietly printing it in an 'x EBITDA' slot would overstate
    leverage by whatever D&A happens to be. Say which line you divided by."""
    cash, debt, ebit = meta.get("shelf_cash"), meta.get("shelf_debt"), meta.get("shelf_ebit")
    out = {"leverage_metric": "trailing EBIT (shelf filing data — EBITDA not reported)",
           "leverage_basis": f"{meta.get('shelf')} filing"
                             + (f" as of {meta['shelf_asof']}" if meta.get("shelf_asof") else "")}
    if debt is None or cash is None:
        return {}
    nd = float(debt) - float(cash)
    out.update({"total_debt": debt, "total_cash": cash, "net_debt": nd})
    if nd <= 0:
        out["leverage_read"] = "NET_CASH"
        out["balance_sheet_intact"] = True
        out["cash_burn"] = bool(ebit is not None and float(ebit) < 0)
        if out["cash_burn"]:
            out["leverage_read"] = "NET_CASH_BURNING"
            out["runway_years_crude"] = round(float(cash) / abs(float(ebit)), 1)
        return out
    if not ebit or float(ebit) <= 0:
        out["leverage_read"] = "NET_DEBT_NEG_EBITDA"
        return out
    x = nd / float(ebit)
    out["net_debt_ebitda"] = round(x, 2)
    if x > 10:
        out["leverage_read"] = "RATIO_NOT_MEANINGFUL"
        return out
    out["leverage_read"] = "LOW" if x <= 2.5 else ("MODERATE" if x <= 4 else "HIGH")
    out["balance_sheet_intact"] = bool(x <= 2.5)
    return out


def _intl_enrich(row: dict, meta: dict, session: datetime.date, enrich: bool) -> dict:
    """Same triage vocabulary as the US leg so the two read as one sheet. Enrichment is
    best-effort: outside the US, capital structure and earnings dates are frequently absent
    from Yahoo, and absent stays UNKNOWN."""
    import yfinance as yf
    sym = row["ticker"]
    row.update({"name": meta.get("name") or sym, "shelf": meta.get("shelf"),
                "shelf_label": meta.get("shelf_label"), "shelf_file": meta.get("file"),
                "market": meta.get("market"), "leg": "INTL",
                "exchange": meta.get("shelf_label"), "sector": meta.get("sector"),
                "industry": None, "market_cap": None,
                "print_channel": (SHELVES.get(meta.get("shelf")) or {}).get("print_channel"),
                "drop_type": "REACTION" if row.get("volume_confirmed") else "UNCONFIRMED_TURNOVER",
                "earnings_date": None, "days_from_earnings": None, "earnings_date_estimated": None,
                "leverage_read": "UNKNOWN", "balance_sheet_intact": None, "net_debt": None,
                "net_debt_ebitda": None, "ebitda_ttm": None, "total_debt": None,
                "total_cash": None, "cash_burn": None, "runway_years_crude": None,
                "pct_below_52w_high": None, "pct_above_52w_low": None, "chg_52w_pct": None,
                "short_pct_float": None, "short_days_to_cover": None, "shares_short": None,
                "adv_3m": row.get("adv_lookback"), "enriched": False, "enrich_error": None,
                "leverage_metric": "trailing EBITDA", "leverage_basis": None})
    # SHELF FIRST, vendor second. The filing data is already on disk and cannot be rate-limited;
    # Yahoo then overwrites it where it has something better. Order matters: the other way round,
    # a rate-limited run produces a blank row that reads as "nothing known".
    row["market_cap"] = meta.get("shelf_mcap_usd")
    row["market_cap_local"] = meta.get("shelf_mcap_local")
    row["market_cap_ccy"] = meta.get("shelf_ccy")
    row["fin_ccy"] = meta.get("shelf_ccy")
    row.update(_shelf_leverage(meta))
    if enrich:
        try:
            tk = yf.Ticker(sym)
            info = tk.info or {}
            row["name"] = info.get("shortName") or row["name"]
            row["sector"] = info.get("sector") or row["sector"]
            row["industry"] = info.get("industry")
            # yfinance reports marketCap in the QUOTE currency, not USD (the house's standing
            # ADR/global lesson). A Tokyo line's ¥434B cap printed as "$434.0B" is a 150x
            # overstatement that reads as a mega-cap. Only USD quotes go in the USD slot.
            if info.get("marketCap"):
                qccy = info.get("currency") or row.get("market_cap_ccy")
                if qccy == "USD":
                    row["market_cap"] = info["marketCap"]
                    row["market_cap_local"] = None
                else:
                    row["market_cap"] = None
                    row["market_cap_local"] = info["marketCap"]
                    row["market_cap_ccy"] = qccy
            row["exchange"] = info.get("fullExchangeName") or row["exchange"]
            lev = _leverage(info)
            # only let the vendor displace the filing when it actually knows something
            if lev.get("leverage_read") != "UNKNOWN":
                lev.update({"leverage_metric": "trailing EBITDA", "leverage_basis": "yfinance"})
                row["fin_ccy"] = info.get("financialCurrency") or row.get("fin_ccy")
                row.update(lev)
            ec = _earnings_context(tk, {}, session)
            # Outside the US an absent calendar is the NORM. Never let "no earnings date found"
            # masquerade as "this was not a print" — the tape already said it was a repricing.
            if ec.get("drop_type") == "EARNINGS":
                row["drop_type"] = "EARNINGS"
            row["earnings_date"] = ec.get("earnings_date")
            row["days_from_earnings"] = ec.get("days_from_earnings")
            row["enriched"] = True
        except Exception as ex:
            row["enrich_error"] = str(ex)[:180]
    row.update(_known(sym))
    row["ledger_status"] = _ledger_status(row)
    d = row.get("drop_pct") or 0
    mc = row.get("market_cap") or 0
    row["severity"] = "HIGH" if (d <= -20 or (d <= -15 and mc >= 2e9) or row.get("held")) else "MED"
    return row


def _intl_fire_line(r: dict) -> str:
    """Same DETFIRE grammar and the same feed destination as the US leg (extractor
    detector_scan -> DETECTOR_FIRE), tagged with the shelf that put the name in scope and
    whether we have ever looked at it."""
    volx = f"{r['vol_x_adv']}x ADV" if r.get("vol_x_adv") else "turnover unknown"
    cap = f" at {_cap_str(r)}" if (r.get("market_cap") or r.get("market_cap_local")) else ""
    return (f"DETFIRE|broken_print_intl|{r['ticker']}|{r['severity']}|{r.get('name') or r['ticker']} "
            f"fell {r['drop_pct']:+.1f}% in one session on the {r.get('shelf_label')} shelf "
            f"({r.get('trigger', 'REACTION').lower()}){cap}, {volx}, {_leverage_phrase(r)} — "
            f"{r.get('ledger_status')}"
            f"{' — HELD' if r.get('held') else ''} — TRIAGE ONLY: cause-check -> discovery_state -> "
            f"court (v1.4) before any staging")


def _print_intl_summary(leg: str, session: str | None, rows: list[dict], deg: dict,
                        shelf_counts: dict, unresolved: dict, provisional: bool = False):
    scanned = ", ".join(f"{k} {v}" for k, v in sorted(shelf_counts.items()))
    print(f"\n[broken_print_radar/{leg}] session {session or 'UNKNOWN'} — {len(rows)} candidate "
          f"breaks from {deg['requested']} shelf symbols ({scanned})")
    print(f"  PRICING: {deg['priced']}/{deg['requested']} priced ({deg['priced_pct']}%)"
          + (" — DEGRADED, under half the universe returned data; treat 'quiet' as UNKNOWN"
             if deg["degraded"] else ""))
    if deg["unpriced"]:
        names = ", ".join(deg["unpriced_names"])
        more = f" (+{deg['unpriced_truncated']} more)" if deg["unpriced_truncated"] else ""
        print(f"  UNPRICED ({deg['unpriced']}): {names}{more}")
    for k, v in sorted(unresolved.items()):
        if v:
            print(f"  UNRESOLVED SYMBOLS on {k} ({len(v)}, no defensible Yahoo suffix — skipped, "
                  f"not guessed): {', '.join(v[:12])}")
    if provisional:
        print("  PROVISIONAL — this market has not settled; the move can deepen or recover.")
    if not rows:
        print("  no shelf name cleared the reaction bar (>=8% on >=3x ADV) or the hard -15% bar\n")
        return
    hdr = (f"  {'TICKER':<12}{'DROP':>8}{'VOL/ADV':>9}{'CAP':>9}  {'TRIGGER':<15}{'SHELF':<12}"
           f"{'STATUS':<14}NAME")
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    for r in rows:
        print(f"  {r['ticker']:<12}{r['drop_pct']:>7.1f}%"
              f"{(str(r['vol_x_adv'])+'x' if r.get('vol_x_adv') else '?'):>9}"
              f"{_cap_str(r) if (r.get('market_cap') or r.get('market_cap_local')) else '?':>9}  "
              f"{(r.get('trigger') or '')[:14]:<15}{(r.get('shelf') or '')[:11]:<12}"
              f"{(r.get('ledger_status') or '')[:13]:<14}{(r.get('name') or r['ticker'])[:30]}")
    print("\n  TRIAGE ONLY — no verdicts here. Each line is a question: what broke, is it already"
          "\n  crowded (discovery_state), and does the court clear it? A -20% day is usually correct.\n")
    for r in rows:
        print(_intl_fire_line(r))


def run_intl(leg: str = "europe", shelves: list[str] | None = None, cap: int | None = 700,
             min_move: float = REACT_MOVE, min_volx: float = REACT_VOLX,
             hard_drop: float = -15.0, max_enrich: int = 12, idx: int = -1,
             dry: bool = False, batch: int = 40, verbose: bool = True,
             email: bool = True) -> dict:
    """One international leg: load the shelves, price them politely, reaction-detect, enrich the
    worst few, merge into the SAME store as the US leg (the store is the history)."""
    keys = shelves or LEG_SHELVES.get(leg) or list(SHELVES)
    syms: list[str] = []
    meta: dict[str, dict] = {}
    shelf_counts, unresolved = {}, {}
    per_shelf = max(1, cap // max(1, len(keys))) if cap else None
    for k in keys:
        s, m, unres = load_shelf(k, cap=per_shelf)
        shelf_counts[k] = len(s)
        unresolved[k] = unres
        for y in s:
            if y not in meta:
                meta[y] = m[y]
                syms.append(y)
    if not syms:
        print(f"[broken_print_radar/{leg}] NO SHELF SYMBOLS RESOLVED — refusing to report a quiet "
              f"tape off an empty universe. Check the shelf files under {', '.join(keys)}.")
        return {"leg": leg, "session": None, "hits": [], "new": [], "stats": {"error": "empty universe"}}
    if verbose:
        print(f"[broken_print_radar/{leg}] pricing {len(syms)} shelf symbols "
              f"({', '.join(f'{k}={v}' for k, v in sorted(shelf_counts.items()))})…", flush=True)
    bars = batch_history(syms, batch=batch, verbose=verbose)
    deg = degraded_summary(syms, bars)
    rows = reaction_scan(bars, idx=idx, min_move=min_move, min_volx=min_volx, hard_drop=hard_drop)
    sessions = [r["session"] for r in rows if r.get("session")]
    if not sessions:
        # no fires: take the session date off the priced tape itself so a quiet day is still dated
        allds = [b["dates"][idx] for b in bars.values() if b.get("dates") and len(b["dates"]) >= abs(idx)]
        session = max(allds) if allds else None
    else:
        session = max(sessions)
    sd = datetime.date.fromisoformat(session) if session else datetime.date.today()
    for i, r in enumerate(rows):
        _intl_enrich(r, meta.get(r["ticker"], {}), sd, enrich=(i < max_enrich))
        if i < max_enrich:
            time.sleep(0.4)
    _print_intl_summary(leg, session, rows, deg, shelf_counts, unresolved)
    stats = {"leg": leg, "shelves": keys, "shelf_counts": shelf_counts,
             "min_drop": hard_drop, "min_mktcap": 0, "react_move": min_move,
             "react_volx": min_volx, "pricing": deg, "raw": deg["priced"],
             "excluded_otc": 0, "excluded_other": deg["unpriced"],
             "region": "intl", "market_state": None, "session_complete": True,
             "source": "desk shelves (EDINET/LSE/Euronext/KRX) + yfinance batched daily history"}
    new = [r["ticker"] for r in rows]
    if not dry and session:
        # A leg can span two calendar sessions (a Tokyo holiday leaves Japan on D-1 while Seoul
        # trades D). File each row under ITS OWN session date — one shared label would date a
        # Korean break to a Japanese holiday.
        by_sess: dict[str, list[dict]] = {}
        for r in rows:
            by_sess.setdefault(r.get("session") or session, []).append(r)
        new = []
        for s, rs in by_sess.items():
            _, n = merge_store(s, rs, stats)
            new += n
        if rows and new and email:
            ok = _email(session, rows, new, stats, leg_label=leg.upper())
            print(f"[broken_print_radar/{leg}] email {'sent' if ok else 'NOT sent (no SMTP credential)'}")
        elif rows and not new:
            print(f"[broken_print_radar/{leg}] no new names since the last scan of this session — no email")
    return {"leg": leg, "session": session, "hits": rows, "new": new, "stats": stats}


# ================================================================ v2: backfill

def _us_backfill_universe(size: int = 250, min_mktcap: float = 250e6) -> list[str]:
    """A US universe for HISTORICAL sweeps. The live screener has no history parameter, so a
    backfill cannot use it — it has to walk the cap ladder to enumerate names, then read their
    tape. Same rail, different question."""
    import yfinance as yf
    from yfinance import EquityQuery
    bands = [(4e11, 1e13), (1e11, 4e11), (4e10, 1e11), (1.5e10, 4e10),
             (7e9, 1.5e10), (3e9, 7e9), (1.2e9, 3e9), (min_mktcap, 1.2e9)]
    syms, seen = [], set()
    for lo, hi in bands:
        q = EquityQuery("and", [EquityQuery("gte", ["intradaymarketcap", lo]),
                                EquityQuery("lt", ["intradaymarketcap", hi]),
                                EquityQuery("eq", ["region", "us"])])
        try:
            res = yf.screen(q, size=size, sortField="intradaymarketcap", sortAsc=False)
        except Exception as ex:
            print(f"  [backfill] cap band {lo:.0e}-{hi:.0e} failed: {type(ex).__name__}")
            time.sleep(1.5)
            continue
        for r in (res.get("quotes") or []):
            t, ex_name = r.get("symbol"), (r.get("fullExchangeName") or "").upper()
            if t and t not in seen and "OTC" not in ex_name and "PINK" not in ex_name:
                seen.add(t)
                syms.append(t)
        time.sleep(0.5)
    return syms


def run_backfill(days: int = 5, legs: str = "all", us_size: int = 250, intl_cap: int = 700,
                 min_move: float = REACT_MOVE, min_volx: float = REACT_VOLX,
                 hard_drop: float = -15.0, batch: int = 40, dry: bool = True) -> dict:
    """--backfill N: sweep the last N sessions for breaks v1 could not have seen.

    Why this exists: v1's tape is a LAST-SESSION SNAPSHOT with no history parameter, so any day
    the cron missed (or any name below its bar, or any non-US name) is simply gone. This walks
    real price history instead, which means it can answer 'what did we miss' rather than only
    'what is happening now'. Every row is cross-checked against BROKEN_PRINTS.json: a row we
    already recorded is CAUGHT, a row we did not is MISSED-BY-v1.
    """
    store = _load_store()
    universes: list[tuple[str, list[str], dict]] = []
    if legs in ("all", "us"):
        us = _us_backfill_universe(size=us_size)
        print(f"[backfill] US universe: {len(us)} names off the cap ladder")
        universes.append(("US", us, {s: {"name": s, "shelf": "US_TAPE", "shelf_label": "US tape",
                                         "market": "US", "file": "yahoo cap-ladder screener"}
                                     for s in us}))
    if legs in ("all", "intl"):
        syms, meta = [], {}
        per = max(1, intl_cap // len(SHELVES))
        for k in SHELVES:
            s, m, _ = load_shelf(k, cap=per)
            for y in s:
                if y not in meta:
                    meta[y] = m[y]
                    syms.append(y)
        print(f"[backfill] INTL universe: {len(syms)} shelf names")
        universes.append(("INTL", syms, meta))

    found: dict[str, list[dict]] = {}
    degraded = {}
    for label, syms, meta in universes:
        if not syms:
            continue
        print(f"[backfill] pricing {label} ({len(syms)} symbols, {days}-session lookback)…", flush=True)
        bars = batch_history(syms, period="6mo", batch=batch)
        degraded[label] = degraded_summary(syms, bars)
        d = degraded[label]
        print(f"  {label} PRICING: {d['priced']}/{d['requested']} ({d['priced_pct']}%)"
              + (" — DEGRADED" if d["degraded"] else ""))
        if d["unpriced"]:
            print(f"  {label} UNPRICED ({d['unpriced']}): {', '.join(d['unpriced_names'])}"
                  + (f" (+{d['unpriced_truncated']} more)" if d["unpriced_truncated"] else ""))
        for back in range(days):
            rows = reaction_scan(bars, idx=-1 - back, min_move=min_move,
                                 min_volx=min_volx, hard_drop=hard_drop)
            for r in rows:
                sess = r.get("session")
                if not sess:
                    continue
                m = meta.get(r["ticker"], {})
                r.update({"leg": label, "shelf": m.get("shelf"), "shelf_label": m.get("shelf_label"),
                          "shelf_file": m.get("file"), "market": m.get("market"),
                          "name": m.get("name") or r["ticker"], "backfill": True})
                r.update(_known(r["ticker"]))
                r["ledger_status"] = _ledger_status(r)
                prior = ((store.get("sessions") or {}).get(sess) or {}).get("hits") or {}
                r["caught_by_v1"] = r["ticker"] in prior
                found.setdefault(sess, []).append(r)

    print(f"\n[backfill] {days}-session sweep — {sum(len(v) for v in found.values())} candidate "
          f"breaks across {len(found)} sessions")
    missed_total = []
    for sess in sorted(found, reverse=True):
        rows = sorted(found[sess], key=lambda r: r["drop_pct"])
        caught = [r for r in rows if r["caught_by_v1"]]
        missed = [r for r in rows if not r["caught_by_v1"]]
        missed_total += missed
        print(f"\n  {sess}: {len(rows)} breaks — {len(caught)} already in the v1 store, "
              f"{len(missed)} MISSED BY v1")
        for r in missed:
            print(f"    MISSED  {r['ticker']:<12}{r['drop_pct']:>7.1f}%  "
                  f"{(str(r['vol_x_adv'])+'x ADV' if r.get('vol_x_adv') else 'turnover ?'):<11} "
                  f"{(r.get('trigger') or '')[:13]:<14}{(r.get('shelf') or '')[:11]:<12}"
                  f"{(r.get('ledger_status') or '')[:13]:<14}{(r.get('name') or r['ticker'])[:34]}")
    if not dry:
        for sess, rows in found.items():
            merge_store(sess, rows, {"raw": len(rows), "excluded_otc": 0, "excluded_other": 0,
                                     "min_drop": hard_drop, "min_mktcap": 0, "region": "backfill",
                                     "backfill": True, "react_move": min_move, "react_volx": min_volx,
                                     "source": "backfill via yfinance daily history"})
    print("\n  BACKFILL IS HISTORY, NOT A TRADE LIST — these are questions that went unasked. "
          "PROPOSES ONLY:\n  cause-check -> discovery_state -> court (v1.4) before any staging.\n")
    return {"sessions": found, "missed": missed_total, "degraded": degraded}


# ---------------------------------------------------------------- main

def run(min_drop: float = -15.0, min_mktcap: float = 250e6, max_enrich: int = 25,
        region: str = "us", include_otc: bool = False, size: int = 100,
        email: bool = True, dry: bool = False) -> dict:
    try:
        quotes = screen_losers(min_drop, min_mktcap, region, size)
    except Exception as ex:
        # Yahoo rate-limits aggressively. Fail LOUD and write nothing: because the screener has no
        # history parameter, a session where every run fails is unrecoverable — that has to show up
        # in the log as a gap, not as a quiet "0 hits".
        print(f"[broken_print_radar] SCREENER UNAVAILABLE ({type(ex).__name__}: {str(ex)[:120]}) — "
              f"no scan, no store write. This session's break list is UNRECOVERABLE if every run "
              f"today fails; re-run before the tape moves on.")
        return {"session": None, "hits": [], "new": [], "stats": {"error": str(ex)[:200]}}
    raw = len(quotes)
    session = _session_date(quotes)
    if session is None:
        # No quotes at all: could be a genuinely quiet tape or a screener outage. Either way the
        # session is UNIDENTIFIED — report it and write nothing (DATA MISSING never a fabricated row).
        print("[broken_print_radar] screener returned nothing — no session date, no store write. "
              "Quiet tape or a screener outage; re-run to distinguish.")
        return {"session": None, "hits": [], "new": [], "stats": {"raw": 0}}
    sd = datetime.date.fromisoformat(session)

    kept, n_otc, n_other = [], 0, 0
    for q in quotes:
        if q.get("quoteType") != "EQUITY" or (q.get("regularMarketChangePercent") or 0) > min_drop:
            n_other += 1
            continue
        if q.get("exchange") not in US_PRIMARY:
            if include_otc:
                kept.append(q)
            else:
                n_otc += 1
            continue
        kept.append(q)
    kept.sort(key=lambda q: q.get("regularMarketChangePercent") or 0)

    rows = []
    for i, q in enumerate(kept):
        rows.append(triage(q, sd, enrich=(i < max_enrich)))
        time.sleep(0.4)    # Yahoo rate-limits by IP and enrichment is 2 calls/name — pace it, a
                           # tripped limit costs the whole session (the screener has no history)

    # Is this a FINISHED session? Only REGULAR means the numbers are still moving. PRE/PREPRE/POST/
    # CLOSED all report the LAST COMPLETED regular session (the overnight cron lands in PREPRE and
    # is reporting yesterday's settled close — an early version called that provisional, wrongly).
    states = [q.get("marketState") for q in quotes if q.get("marketState")]
    state = max(set(states), key=states.count) if states else None
    complete = state != "REGULAR"
    stats = {"raw": raw, "excluded_otc": n_otc, "excluded_other": n_other,
             "min_drop": min_drop, "min_mktcap": min_mktcap, "region": region,
             "market_state": state, "session_complete": complete,
             "source": "yahoo equity screener via yfinance.screen(EquityQuery)"}
    _print_summary(session, rows, stats)

    new = [r["ticker"] for r in rows]
    if not dry:
        _, new = merge_store(session, rows, stats)
        if rows and new and email:
            ok = _email(session, rows, new, stats)
            print(f"[broken_print_radar] email {'sent' if ok else 'NOT sent (no SMTP credential)'}")
        elif rows and not new:
            print("[broken_print_radar] no new names since the last scan of this session — no email")
    return {"session": session, "hits": rows, "new": new, "stats": stats}


def run_auto_window(a) -> dict:
    """--auto-window: THE ONON FIX, made cron-safe. Called every hour by the desk heartbeat, it
    asks what time it is in New York, runs only the legs whose tape is worth reading, and
    refuses to repeat a leg inside the same window. The US intraday leg runs at a lower
    PROVISIONAL bar (-12%) precisely because ONON sat at -14% for the morning: a bar set at the
    settled-session level cannot see a name on its way through it."""
    now = _now_et()
    due = legs_due(now)
    print(f"[broken_print_radar] auto-window {now:%Y-%m-%d %H:%M} ET "
          f"(US session {us_session_phase(now)}) — legs due: {', '.join(due) or 'none'}")
    out = {}
    for leg in due:
        key = _window_key(leg, now)
        if _leg_already_ran(leg, key) and not a.force:
            print(f"  {leg}: already ran for window {key} — skipping (use --force to override)")
            continue
        if leg == "us_intraday":
            out[leg] = run(min_drop=INTRADAY_MIN_DROP, min_mktcap=a.min_mktcap,
                           max_enrich=min(a.max_enrich, 10), region="us",
                           include_otc=a.include_otc, size=a.size, email=not a.no_email, dry=a.dry)
        elif leg == "us_settled":
            out[leg] = run(min_drop=a.min_drop, min_mktcap=a.min_mktcap, max_enrich=a.max_enrich,
                           region="us", include_otc=a.include_otc, size=a.size,
                           email=not a.no_email, dry=a.dry)
        else:
            out[leg] = run_intl(leg=leg, cap=a.intl_cap, max_enrich=a.intl_max_enrich,
                                hard_drop=a.min_drop, min_move=a.react_move,
                                min_volx=a.react_volx, dry=a.dry, batch=a.batch,
                                email=not a.no_email)
        if not a.dry:
            _mark_leg(leg, key)
    if not due:
        print("  no leg due — every tape either has not settled or was already read this window. "
              "This is the schedule doing its job, not a quiet market.")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="single-day-break triage radar (US + international)")
    ap.add_argument("--min-drop", type=float, default=-15.0, help="single-session %% change bar (default -15)")
    ap.add_argument("--min-mktcap", type=float, default=250e6, help="minimum market cap (default 250e6)")
    ap.add_argument("--max-enrich", type=int, default=25, help="cap per-name yfinance enrichment calls")
    ap.add_argument("--region", default="us")
    ap.add_argument("--size", type=int, default=100, help="screener page size")
    ap.add_argument("--include-otc", action="store_true", help="keep OTC/pink lines (stale-quote noise)")
    ap.add_argument("--no-email", action="store_true")
    ap.add_argument("--dry", action="store_true", help="print only — no store write, no email")
    # ---- v2
    ap.add_argument("--leg", default="us", choices=["us", "intl", "asia", "europe", "all"],
                    help="which tape to scan (default us = the v1 behaviour)")
    ap.add_argument("--auto-window", action="store_true",
                    help="scan only the legs whose market window is open right now (cron-safe)")
    ap.add_argument("--force", action="store_true", help="ignore the once-per-window guard")
    ap.add_argument("--shelves", default=None,
                    help="comma-separated shelf keys: " + ",".join(SHELVES))
    ap.add_argument("--intl-cap", type=int, default=700, help="max shelf symbols per intl leg")
    ap.add_argument("--intl-max-enrich", type=int, default=12)
    ap.add_argument("--react-move", type=float, default=REACT_MOVE,
                    help="reaction-detection single-day move bar (default -8)")
    ap.add_argument("--react-volx", type=float, default=REACT_VOLX,
                    help="reaction-detection volume multiple (default 3x)")
    ap.add_argument("--batch", type=int, default=40, help="history download batch size")
    ap.add_argument("--backfill", type=int, default=0, metavar="N",
                    help="sweep the last N sessions of history for breaks v1 never saw")
    ap.add_argument("--backfill-legs", default="all", choices=["all", "us", "intl"])
    ap.add_argument("--backfill-us-size", type=int, default=250, help="names per US cap band")
    a = ap.parse_args()

    shelves = [s.strip().upper() for s in a.shelves.split(",")] if a.shelves else None
    if a.backfill:
        run_backfill(days=a.backfill, legs=a.backfill_legs, us_size=a.backfill_us_size,
                     intl_cap=a.intl_cap, min_move=a.react_move, min_volx=a.react_volx,
                     hard_drop=a.min_drop, batch=a.batch, dry=a.dry)
    elif a.auto_window:
        run_auto_window(a)
    elif a.leg == "us":
        run(min_drop=a.min_drop, min_mktcap=a.min_mktcap, max_enrich=a.max_enrich, region=a.region,
            include_otc=a.include_otc, size=a.size, email=not a.no_email, dry=a.dry)
    else:
        legs = ["asia", "europe"] if a.leg in ("intl", "all") else [a.leg]
        if a.leg == "all":
            run(min_drop=a.min_drop, min_mktcap=a.min_mktcap, max_enrich=a.max_enrich,
                region=a.region, include_otc=a.include_otc, size=a.size,
                email=not a.no_email, dry=a.dry)
        for lg in legs:
            run_intl(leg=lg, shelves=shelves, cap=a.intl_cap, max_enrich=a.intl_max_enrich,
                     hard_drop=a.min_drop, min_move=a.react_move, min_volx=a.react_volx,
                     dry=a.dry, batch=a.batch, email=not a.no_email)
