"""queue_hygiene — the court queue's relevance manager (principal directive 2026-08-16:
"we need to manage the queue because stuff gets less relevant as time goes on. can we
evict the large caps and focus just on where we think we have edge?").

DOCTRINE. The office thesis says our edge lives where institutions can't afford to look:
coverage orphans, small caps, odd-lot paper, mechanism-specific events. A LARGE cap that
arrived via a GENERIC drawdown sweep carries the efficient-pricing presumption the IBKR
court made explicit ("covered mega-cap — the tape fully knows") — courting it spends
bench tokens where we have no aggregation edge. And a dislocation row's premise DECAYS:
the screen froze a tape observation at enqueue time; two weeks later the market has
either repriced it or validated it, and the row is litigating a stale photograph.

RULES (deterministic, run at the top of every court_runner drain):
  1. LARGECAP  — resolved mcap >= MCAP_CEILING ($10B) AND the row came from a GENERIC
     sweep AND context is not a RE-COURT. Principal-directed, dogfood, and named-mechanism
     sources are EXEMPT regardless of size (APO/DDOG/RDDT/SBS/ai_faircarry all survive).
  2. STALE     — generic-sweep row older than STALE_DAYS (14) still pre-bench. The premise
     is the screen's dislocation; if it were still live, the screen would re-fire.
     Non-generic stale rows are FLAGGED, never silently evicted — they are work owed.

EVICTION MECHANICS: rows are DELETED from the queue (not moved to KILLED) — enqueue
dedups against ALL queue rows including terminal ones (the SBS re-enqueue lesson), so a
terminal EVICTED stage would permanently bar a name the screens may legitimately re-surface
on a FRESH dislocation. Every eviction is appended to court_queue_evictions.jsonl with the
full row + reason, so nothing silently disappears (no-silent-caps rule).

Missing mcaps are resolved live via yfinance once and cached onto the row
(screen_row.mcap_resolved) so the daily cost is ~zero.
"""
from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from desk.court_queue import QUEUE
from desk.store import append_jsonl

MCAP_CEILING = 10e9
STALE_DAYS = 14
PRE_BENCH = {"TRAP_VERIFY", "REFUTABILITY"}

# Sources whose rows are FAIR GAME for eviction — the generic screens that enqueue on a
# drawdown/velocity observation with no principal intent and no named mechanism behind them.
# Everything NOT matching these prefixes is exempt (principal_*, user_directive, dogfood_*,
# ai_faircarry_*, lithium_court_*, condo_event_*, ... — named one-off sources are edge-directed).
# EXPLICITLY NOT GENERIC — do not add these, ever. quality_drawdown is the edge-directed
# source calibrated on realised P&L, and its winners INCLUDE large caps (SAP, CTSH, KNSL,
# HUBS). Sweeping it into the large-cap eviction would delete exactly the pond the
# attribution said produced 94% of gains. Asserted in the test below.
EXEMPT_SOURCES = ("quality_drawdown", "principal_", "user_directive", "dogfood_",
                  "ai_faircarry", "band_touch_20260817")

GENERIC_SWEEP_PREFIXES = (
    "class_dislocation", "blob_sweep", "velocity_dislocation", "post_outage_sweep",
    "intl_dislocation_sweep", "convex_carry", "cause_reversal",
    "orphan_screen",
    # "band_touch" REMOVED 2026-08-26: band touches fire only on LEDGER names, whose bands are
    # court/ruling-placed (gate_basis) — court_queue.THESIS_SOURCES already counts band_touch_ as
    # thesis-derived, and the divergence evicted DOCU ($11B) 7 minutes after a principal-reviewed
    # flip-condition enqueue. The two taxonomies must never diverge again: exemption now ALSO
    # consults court_queue.is_thesis_sourced (single source of truth).
)


def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def _age_days(row: dict) -> float | None:
    try:
        t = datetime.datetime.fromisoformat(row["enqueued_utc"].replace("Z", "+00:00"))
        return (_now() - t).total_seconds() / 86400.0
    except (KeyError, ValueError, TypeError):
        return None


def _is_generic(row: dict) -> bool:
    src = str(row.get("source", ""))
    if any(src.startswith(p) for p in EXEMPT_SOURCES):
        return False
    return any(src.startswith(p) for p in GENERIC_SWEEP_PREFIXES)


def _is_recourt(row: dict) -> bool:
    return "RE-COURT" in str(row.get("context", "")).upper()


# yfinance marketCap arrives in the LISTING currency (the priceMagnifier lesson: unit
# conventions never transfer across venues — SILEX.ST read "19B" = SEK ~$1.8B, BRBY.L
# "387B" = PENCE ~$4.9B). Coarse static FX is fine for a $10B threshold decision; a name
# within FX-drift of the ceiling is not the kind of eviction that needs precision.
_FX_TO_USD = {"USD": 1.0, "GBp": 0.0127, "GBX": 0.0127, "GBP": 1.27, "EUR": 1.09,
              "SEK": 0.095, "NOK": 0.093, "DKK": 0.146, "CHF": 1.13, "JPY": 0.0066,
              "HKD": 0.128, "KRW": 0.00072, "BRL": 0.18, "CAD": 0.73, "AUD": 0.66,
              "PLN": 0.25, "ILA": 0.0027, "ILS": 0.27, "TWD": 0.031, "INR": 0.0115}


def _resolve_mcap(row: dict) -> float | None:
    """Resolve market cap in USD. Screen-stamped mcaps are trusted as USD (US screens);
    live yfinance resolutions are FX-normalized from the listing currency."""
    sr = row.get("screen_row") or {}
    for k in ("mcap", "mcap_resolved", "market_cap"):
        v = sr.get(k)
        if isinstance(v, (int, float)) and v > 0:
            return float(v)
    try:
        import yfinance as yf
        fi = yf.Ticker(row["ticker"]).fast_info
        m, ccy = fi.get("marketCap"), fi.get("currency") or "USD"
        if isinstance(m, (int, float)) and m > 0:
            fx = _FX_TO_USD.get(ccy)
            if fx is None:
                return None                     # unknown currency: refuse to guess a unit
            usd = float(m) * fx
            sr["mcap_resolved"] = usd           # cache on the row — one lookup per name, ever
            sr["mcap_resolved_ccy"] = f"{ccy}@{fx}"
            row["screen_row"] = sr
            return usd
    except Exception:
        pass
    return None


def run_hygiene(dry_run: bool = False, verbose: bool = True) -> dict:
    """Returns {"evicted": [...], "flagged": [...], "kept": n}. Mutates the queue unless dry_run."""
    rows = QUEUE.rows()
    live = [r for r in rows if r.get("stage") in PRE_BENCH]
    evict, flagged, dirty = [], [], False
    for r in live:
        from desk.court_queue import is_thesis_sourced as _its
        generic = _is_generic(r) and not _its(r.get("source"))
        if _is_recourt(r):
            continue                             # re-courts are adjudicator-ordered; never touch
        age = _age_days(r)
        if generic:
            m = _resolve_mcap(r)
            if m is not None and "mcap_resolved" in (r.get("screen_row") or {}):
                dirty = True
            if m is not None and m >= MCAP_CEILING:
                evict.append({**r, "_evict_reason": f"LARGECAP ${m/1e9:.0f}B >= ${MCAP_CEILING/1e9:.0f}B via generic sweep — no aggregation edge (office thesis; IBKR efficient-pricing precedent)"})
                continue
            if age is not None and age > STALE_DAYS:
                evict.append({**r, "_evict_reason": f"STALE {age:.0f}d pre-bench — the screen's dislocation premise decayed; a live premise would re-fire the sweep"})
                continue
        else:
            if age is not None and age > STALE_DAYS:
                flagged.append(f"{r['ticker']}: non-generic source {r.get('source')} is {age:.0f}d old pre-bench — work owed, NOT auto-evicted; drain or evict deliberately")
    if evict and not dry_run:
        for e in evict:
            append_jsonl("desk/data/court_queue_evictions.jsonl",
                         {**{k: v for k, v in e.items() if k != "_evict_reason"},
                          "evicted_utc": _now().isoformat(timespec="seconds"),
                          "reason": e["_evict_reason"]},
                         generated_by="queue_hygiene")
        QUEUE.upsert([], generated_by="queue_hygiene:evict",
                     delete_keys={e["ticker"] for e in evict})
    elif dirty and not dry_run:
        QUEUE.upsert(live, generated_by="queue_hygiene:mcap_cache")
    if verbose:
        for e in evict:
            print(f"[hygiene] EVICT {e['ticker']:8s} — {e['_evict_reason']}")
        for f in flagged:
            print(f"[hygiene] FLAG  {f}")
        print(f"[hygiene] evicted={len(evict)} flagged={len(flagged)} "
              f"kept={len(live) - len(evict)}{' (DRY RUN)' if dry_run else ''}")
    return {"evicted": [e["ticker"] for e in evict], "flagged": flagged,
            "kept": len(live) - len(evict)}


if __name__ == "__main__":
    run_hygiene(dry_run="--dry-run" in sys.argv)
