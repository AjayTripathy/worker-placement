"""Gov-Contract Award-Flow engine (Phase 1).

Implements the §3 signal of GOV_CONTRACT_SPEC.md: trailing change in USASpending
*obligations* to the corporate FAMILY as a leading indicator of gov revenue.

Three public USASpending v2 endpoints (no auth):
  - spending_by_category/recipient        -> family obligation TOTAL in a window
  - spending_by_category/awarding_agency  -> DoD-vs-civilian split (Arm A classifier)
  - transactions/                         -> per-action_date obligation flow (point-in-time)
  - spending_by_award/ (+ Last Modified)  -> posting-lag instrumentation

ENTITY-RESOLUTION CONTRACT (the §5 hard part, the main failure mode):
  A company is defined by (search_terms, anchor_tokens, alias_recipients):
    * search_terms     : strings passed to recipient_search_text (fuzzy). MUST be a
                         distinctive name, NOT a short substring. "SAIC" pulls in
                         every "moSAIC*" recipient and MISSES the real SAIC -> use
                         "Science Applications". "VSE" returns net-negative noise.
    * anchor_tokens    : a recipient is kept only if its core tokens SUPERSET this set
                         (the connector subset-matcher). Rejects JVs/look-alikes
                         (Mission Support Alliance for Leidos; Mosaic* for SAIC).
    * alias_recipients : named subsidiaries that do NOT share the parent token and
                         would be missed by the anchor (QTC for Leidos, Dynetics for
                         Leidos, SemanticBits for ICF). Matched by exact-ish name.
  Point-in-time is enforced with date_type='action_date' time windows; we never
  backfill. Posting lag (action_date -> first-available) is a SEPARATE measured cost
  (see measure_posting_lag) and is NOT corrected here.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Optional

import requests

_BASE = "https://api.usaspending.gov/api/v2"
_RECIPIENT = f"{_BASE}/search/spending_by_category/recipient/"
_AGENCY = f"{_BASE}/search/spending_by_category/awarding_agency/"
_AWARD = f"{_BASE}/search/spending_by_award/"
_TX = f"{_BASE}/transactions/"
_CONTRACT_TYPES = ["A", "B", "C", "D"]  # prime contract award types

_SUFFIX = frozenset({"the", "inc", "inc.", "incorporated", "corp", "corp.", "corporation",
                     "co", "co.", "company", "llc", "l.l.c.", "lp", "l.p.", "ltd",
                     "limited", "pbc", "holdings"})
# Civilian = every awarding agency that is NOT DoD. Sub-$7.5M defense awards are still
# "un-announced" (below the DoD daily-contract press threshold) so the moat metric is
# civilian-share PLUS sub-threshold-defense-share; we report both.
_DOD = "Department of Defense"
_DOD_PRESS_THRESHOLD = 7_500_000  # DoD daily-contract-announcement floor


def _core(name: str) -> set:
    return {t for t in re.sub(r"[^a-z0-9 ]+", " ", (name or "").lower()).split()
            if t not in _SUFFIX}


def _parse_d(s: str) -> Optional[date]:
    if not s:
        return None
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


@dataclass
class Company:
    ticker: str
    name: str
    search_terms: list[str]
    anchor_tokens: set
    alias_recipients: list[str] = field(default_factory=list)  # exact-ish subsidiary names

    @staticmethod
    def make(ticker: str, name: str, search_terms, anchor: str, aliases=None) -> "Company":
        return Company(ticker=ticker, name=name,
                       search_terms=list(search_terms) if isinstance(search_terms, (list, tuple)) else [search_terms],
                       anchor_tokens=_core(anchor),
                       alias_recipients=list(aliases or []))


class AwardFlowEngine:
    def __init__(self, user_agent: str = "SignalOS-Frontrun/0.1 (research)", rate_min: int = 30):
        self.s = requests.Session()
        self.s.headers.update({"User-Agent": user_agent})
        self._gap = 60.0 / max(1, rate_min)
        self._last = 0.0

    def _post(self, url: str, body: dict, _retries: int = 3) -> dict:
        for attempt in range(_retries):
            dt = self._gap - (time.time() - self._last)
            if dt > 0:
                time.sleep(dt)
            self._last = time.time()
            r = self.s.post(url, json=body, timeout=90)
            if r.status_code == 429:
                time.sleep(2 ** attempt * 2)
                continue
            r.raise_for_status()
            return r.json()
        r.raise_for_status()
        return r.json()

    # ---- recipient matcher (the entity-resolution contract) ----
    def _matches(self, co: Company, recipient_name: str) -> bool:
        if co.anchor_tokens and co.anchor_tokens <= _core(recipient_name):
            return True
        rn = (recipient_name or "").upper()
        return any(a.upper() in rn or rn in a.upper() for a in co.alias_recipients)

    # ---- §3 family obligation total in a window (point-in-time, action_date) ----
    def family_obligations(self, co: Company, start: date, end: date) -> dict:
        """Sum prime-contract obligations to the matched corporate family in
        [start, end] by action_date. Returns total + matched recipients + rejects."""
        s, e = start.isoformat(), end.isoformat()
        kept: dict[str, float] = {}
        rejected: dict[str, float] = {}
        for st in co.search_terms:
            body = {"filters": {"recipient_search_text": [st],
                                "award_type_codes": _CONTRACT_TYPES,
                                "time_period": [{"start_date": s, "end_date": e}]},
                    "limit": 100, "page": 1}
            for x in self._post(_RECIPIENT, body).get("results", []):
                nm, amt = x.get("name", ""), x.get("amount") or 0.0
                if self._matches(co, nm):
                    kept[nm] = kept.get(nm, 0.0) + amt
                elif amt > 0:
                    rejected[nm] = rejected.get(nm, 0.0) + amt
        return {"total_usd": round(sum(kept.values())),
                "matched_recipients": {k: round(v) for k, v in sorted(kept.items(), key=lambda kv: -kv[1])},
                "rejected_lookalikes": {k: round(v) for k, v in sorted(rejected.items(), key=lambda kv: -kv[1])[:8]},
                "window": [s, e]}

    # ---- Arm-A classifier input: DoD vs civilian split ----
    def agency_split(self, co: Company, start: date, end: date) -> dict:
        s, e = start.isoformat(), end.isoformat()
        agg: dict[str, float] = {}
        for st in co.search_terms:
            body = {"filters": {"recipient_search_text": [st],
                                "award_type_codes": _CONTRACT_TYPES,
                                "time_period": [{"start_date": s, "end_date": e}]},
                    "limit": 50, "page": 1}
            for x in self._post(_AGENCY, body).get("results", []):
                agg[x.get("name")] = agg.get(x.get("name"), 0.0) + (x.get("amount") or 0.0)
        # NOTE: awarding_agency category does not let us re-apply the recipient anchor,
        # so for substring-prone names this inherits the search-term noise. Only trust it
        # when family_obligations confirms the search term is clean (rejected ~ 0).
        total = sum(agg.values())
        dod = agg.get(_DOD, 0.0)
        civ = total - dod
        return {"total_usd": round(total), "dod_usd": round(dod), "civilian_usd": round(civ),
                "civilian_share": round(civ / total, 3) if total > 0 else None,
                "by_agency": {k: round(v) for k, v in sorted(agg.items(), key=lambda kv: -kv[1])[:8]}}

    # ---- point-in-time transaction flow + sub-threshold-defense share ----
    def _award_ids(self, co: Company, start: date, end: date, limit: int = 100) -> list[dict]:
        s, e = start.isoformat(), end.isoformat()
        out = []
        for st in co.search_terms:
            body = {"filters": {"recipient_search_text": [st], "award_type_codes": _CONTRACT_TYPES,
                                "time_period": [{"start_date": s, "end_date": e, "date_type": "action_date"}]},
                    "fields": ["Award ID", "Recipient Name", "Award Amount", "Awarding Agency",
                               "generated_internal_id"],
                    "limit": limit, "sort": "Award Amount", "order": "desc", "page": 1}
            for a in self._post(_AWARD, body).get("results", []):
                if self._matches(co, a.get("Recipient Name", "")):
                    out.append(a)
        return out

    def signal_asof(self, co: Company, asof: date, lookback_days: int = 365,
                    gov_revenue_run_rate_usd: Optional[float] = None) -> dict:
        """§3 signal AS OF `asof`, point-in-time. Trailing-window family obligations vs
        prior-window, fires if |delta| >= 10% of trailing gov revenue run-rate.

        IMPORTANT: this reads obligations by action_date only — it does NOT subtract the
        posting lag. A live signal must additionally censor any action whose first-available
        date > asof (see measure_posting_lag); here we expose the window so the caller
        can apply a lag buffer (recommended: asof - 14d for the freshest edge of the window).
        """
        cur_start = asof - timedelta(days=lookback_days)
        prior_start = cur_start - timedelta(days=lookback_days)
        cur = self.family_obligations(co, cur_start, asof)["total_usd"]
        prior = self.family_obligations(co, prior_start, cur_start)["total_usd"]
        delta = cur - prior
        rr = gov_revenue_run_rate_usd
        fires = (rr is not None and rr > 0 and abs(delta) >= 0.10 * rr)
        return {"asof": asof.isoformat(), "trailing_obligations_usd": cur,
                "prior_obligations_usd": prior, "delta_usd": delta,
                "gov_revenue_run_rate_usd": rr,
                "delta_pct_of_gov_rev": round(delta / rr, 3) if (rr and rr > 0) else None,
                "fires": bool(fires), "direction": ("up" if delta > 0 else "down") if fires else None,
                "lag_caveat": "obligations by action_date; not censored for posting lag — "
                              "apply asof-14d buffer for a live point-in-time signal"}


# ---- feasibility instrumentation (Phase-1 make-or-break) ----

def measure_posting_lag(engine: AwardFlowEngine, search_terms: list[str],
                        asof: date, window_start: date, max_per: int = 30) -> list[dict]:
    """For freshly-LOADED award records (Last Modified Date within 3d of asof), measure
    how OLD the underlying newest action_date is. (asof - action_date) = the staleness of
    the freshest data we can pull = the floor cost of the frontrun window.

    Returns one row per (award): action_date, last_modified, load_lag_days, asof_minus_action.
    """
    rows = []
    for st in search_terms:
        body = {"filters": {"recipient_search_text": [st], "award_type_codes": _CONTRACT_TYPES,
                            "time_period": [{"start_date": window_start.isoformat(),
                                             "end_date": asof.isoformat(), "date_type": "action_date"}]},
                "fields": ["Award ID", "Award Amount", "Last Modified Date", "generated_internal_id"],
                "limit": max_per, "sort": "Last Modified Date", "order": "desc", "page": 1}
        for a in engine._post(_AWARD, body).get("results", []):
            lm = _parse_d(a.get("Last Modified Date"))
            if not lm or (asof - lm).days > 3:
                continue  # only freshly-loaded records
            gid = a.get("generated_internal_id")
            if not gid:
                continue
            tx = engine._post(_TX, {"award_id": gid, "limit": 1, "page": 1,
                                    "sort": "action_date", "order": "desc"}).get("results", [])
            if not tx:
                continue
            ad = _parse_d(tx[0].get("action_date"))
            if not ad:
                continue
            rows.append({"search": st, "award": a.get("Award ID"),
                         "action_date": ad.isoformat(), "last_modified": lm.isoformat(),
                         "load_lag_days": (lm - ad).days, "asof_minus_action": (asof - ad).days})
    return rows
