"""Phase-2 (G-4) load-date-censored point-in-time panel + signal builder.

GOV_CONTRACT_SPEC.md LOCKED + amendments G-1..G-4. This module builds, per
(name, quarter), the civilian-only family-obligation award-flow signal computed
POINT-IN-TIME as of a decision date D ~14 trading days before earnings, censored
by USASpending **load date** (summary `Last Modified Date`), NOT action_date.

THE G-4 CORRECTNESS ITEM
------------------------
USASpending exposes, per *award*, a mutable summary `Last Modified Date` = the
date of the award's most-recent posted modification. That is the best public
load-date proxy. The category/recipient aggregation endpoint accepts
`date_type=action_date` OR `date_type=last_modified_date`. Neither single call
yields the exact set "action in trailing window AND loaded by D", so we build
the censored panel at the AWARD level:

  1. pull every family award whose action_date falls in the trailing window
     [D-lookback, D]  (date_type=action_date), capturing per-award
     `Last Modified Date` and `Award Amount`;
  2. CENSORED flow  = sum of award obligations over awards with
     `Last Modified Date <= D`   (the awards we would actually have seen at D);
  3. LEAKY flow     = sum over ALL such awards (the naive action_date panel).

The gap (LEAKY - CENSORED) IS the look-ahead G-4 removes. We report it per event.
Censoring by the *latest* Last Modified is CONSERVATIVE: an award first loaded
before D but re-modified after D is dropped (never a leak; only over-exclusion).

We restrict the live/tradeable signal to CIVILIAN awarding agencies (G-1): the
defense leg posts on a ~98-day batch lag (Phase-1) and is untradeable as a lead.
Award-level rows carry Awarding Agency, so the civilian filter is applied exactly.
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

import requests

BASE = "https://api.usaspending.gov/api/v2"
AWARD = f"{BASE}/search/spending_by_award/"
CONTRACT_TYPES = ["A", "B", "C", "D"]
DOD = "Department of Defense"
HERE = Path(__file__).resolve().parent
UA = {"User-Agent": "SignalOS-Frontrun/0.2 (research; 4tripathy@gmail.com)"}

_SUFFIX = frozenset({"the", "inc", "inc.", "incorporated", "corp", "corp.", "corporation",
                     "co", "co.", "company", "llc", "l.l.c.", "lp", "l.p.", "ltd",
                     "limited", "pbc", "holdings"})


def _core(name: str) -> set:
    return {t for t in re.sub(r"[^a-z0-9 ]+", " ", (name or "").lower()).split()
            if t not in _SUFFIX}


def _pd(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


@dataclass
class Co:
    ticker: str
    search_terms: list
    anchor: set
    aliases: list

    @staticmethod
    def make(ticker, search_terms, anchor, aliases=None):
        return Co(ticker, list(search_terms), _core(anchor), [a.upper() for a in (aliases or [])])

    def matches(self, recipient: str) -> bool:
        if self.anchor and self.anchor <= _core(recipient):
            return True
        rn = (recipient or "").upper()
        return any(a in rn or rn in a for a in self.aliases)


class Session:
    def __init__(self, rate_min=40):
        self.s = requests.Session()
        self.s.headers.update(UA)
        self._gap = 60.0 / rate_min
        self._last = 0.0

    def post(self, url, body, retries=9):
        last_exc = None
        for attempt in range(retries):
            dt = self._gap - (time.time() - self._last)
            if dt > 0:
                time.sleep(dt)
            self._last = time.time()
            try:
                r = self.s.post(url, json=body, timeout=120)
            except requests.RequestException as e:
                last_exc = e
                time.sleep(min(60, 3 * (2 ** attempt)))  # disconnect/timeout -> long backoff
                continue
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(min(60, 3 * (2 ** attempt)))  # transient USASpending errors -> backoff
                continue
            r.raise_for_status()
            return r.json()
        if last_exc:
            raise last_exc
        r.raise_for_status()
        return r.json()


def family_awards(sess: Session, co: Co, start: date, end: date, pages=2) -> list:
    """All family-matched prime awards with action_date in [start,end], carrying
    Award Amount, Last Modified Date, Awarding Agency. Anchor+alias entity-resolution."""
    out, seen = [], set()
    for st in co.search_terms:
        for page in range(1, pages + 1):
            body = {"filters": {"recipient_search_text": [st], "award_type_codes": CONTRACT_TYPES,
                                "time_period": [{"start_date": start.isoformat(),
                                                 "end_date": end.isoformat(), "date_type": "action_date"}]},
                    "fields": ["Award ID", "Recipient Name", "Award Amount", "Last Modified Date",
                               "Awarding Agency", "generated_internal_id"],
                    "limit": 100, "sort": "Award Amount", "order": "desc", "page": page}
            res = sess.post(AWARD, body).get("results", [])
            if not res:
                break
            for a in res:
                if not co.matches(a.get("Recipient Name", "")):
                    continue
                gid = a.get("generated_internal_id") or a.get("Award ID")
                if gid in seen:
                    continue
                seen.add(gid)
                out.append(a)
            if len(res) < 100:
                break
    return out


def flows_asof(awards: list, D: date) -> dict:
    """Given the action-window award set, compute CENSORED (load<=D, civilian) and
    LEAKY (all civilian) obligation totals + the defense/leak diagnostics."""
    civ_censored = civ_leaky = dod_censored = 0.0
    n_civ = n_civ_censored = n_dropped = 0
    for a in awards:
        amt = a.get("Award Amount") or 0.0
        agency = a.get("Awarding Agency") or ""
        lm = _pd(a.get("Last Modified Date"))
        is_dod = agency == DOD
        loaded = lm is not None and lm <= D
        if is_dod:
            if loaded:
                dod_censored += amt
            continue
        # civilian
        n_civ += 1
        civ_leaky += amt
        if loaded:
            civ_censored += amt
            n_civ_censored += 1
        else:
            n_dropped += 1
    return {"civ_censored_usd": round(civ_censored), "civ_leaky_usd": round(civ_leaky),
            "dod_censored_usd": round(dod_censored), "n_civ_awards": n_civ,
            "n_civ_loaded_by_D": n_civ_censored, "n_civ_dropped_future_load": n_dropped,
            "leak_gap_usd": round(civ_leaky - civ_censored)}


def signal(sess: Session, co: Co, D: date, gov_rr_usd: float, lookback_days=365) -> dict:
    """§3 signal AS OF D, civilian-only (G-1), load-date-censored (G-4).
    Trailing-window civilian flow vs prior window; fires if |delta|>=10% gov-rev run-rate."""
    cur_start = D - timedelta(days=lookback_days)
    prior_start = cur_start - timedelta(days=lookback_days)
    cur_aw = family_awards(sess, co, cur_start, D)
    prior_aw = family_awards(sess, co, prior_start, cur_start)
    cur = flows_asof(cur_aw, D)
    prior = flows_asof(prior_aw, D)  # prior window also censored at D (we only know what's loaded by D)

    def fire(metric):
        delta = cur[metric] - prior[metric]
        fires = gov_rr_usd > 0 and abs(delta) >= 0.10 * gov_rr_usd
        return {"cur": cur[metric], "prior": prior[metric], "delta": delta,
                "delta_pct_gov_rr": round(delta / gov_rr_usd, 3) if gov_rr_usd else None,
                "fires": bool(fires), "direction": ("up" if delta > 0 else "down") if fires else None}

    return {"asof": D.isoformat(), "gov_rev_run_rate_usd": round(gov_rr_usd),
            "censored": fire("civ_censored_usd"), "leaky": fire("civ_leaky_usd"),
            "cur_diag": cur, "prior_diag": prior}


# ---- the live scored universe (Phase-1 VERIFIED, G-3 in-band) ----
LIVE = {
    "DLHC": Co.make("DLHC", ["DLH"], "DLH", ["DLH CORPORATION", "DLH SOLUTIONS"]),
    "ICFI": Co.make("ICFI", ["ICF"], "ICF",
                    ["SEMANTICBITS", "INCENTIVE TECHNOLOGY GROUP", "ICF MACRO"]),
}
# survivorship signal-only (no live equity): NCI/Empower, ManTech, Vertex
SURV = {
    "EMPOWERAI": Co.make("NCI", ["Empower AI", "NCI Information"], "Empower", ["EMPOWER AI"]),
    "MANTECH": Co.make("MANT", ["ManTech"], "ManTech", ["MANTECH", "SRS TECHNOLOGIES"]),
    "VERTEX": Co.make("VVX", ["Vertex Aerospace"], "Vertex", ["VERTEX AEROSPACE"]),
}
# Arm-B control (a representative set across hardware + IT-services sub-strata, G-2)
ARMB = {
    "LMT": Co.make("LMT", ["Lockheed Martin"], "Lockheed Martin", ["SIKORSKY"]),
    "GD": Co.make("GD", ["General Dynamics"], "General Dynamics", ["GULFSTREAM", "BATH IRON"]),
    "BAH": Co.make("BAH", ["Booz Allen"], "Booz Allen"),
    "LDOS": Co.make("LDOS", ["Leidos"], "Leidos", ["QTC MEDICAL", "DYNETICS", "GIBBS & COX"]),
    "SAIC": Co.make("SAIC", ["Science Applications"], "Science Applications"),
    "CACI": Co.make("CACI", ["CACI"], "CACI", ["MASTODON DESIGN"]),
}
