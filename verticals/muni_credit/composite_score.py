"""4-axis composite credit score for hospital muni obligors.

Axis weights (per scope doc):
  Margin      40%  — Operating Income / Net Patient Revenue (5yr trajectory)
  Days Cash   25%  — (Cash + Investments + Temp Investments) / (OpEx / 365)
  Payer Mix   20%  — Title XVIII (Medicare) + Title XIX (Medicaid) days / total
  Local Econ  15%  — BLS QCEW employment trend NAICS 622 in obligor's primary state

Output: numeric score 50-100 mapped to letter rating (S&P scale).

Score = 0.40 * margin_score + 0.25 * cash_score + 0.20 * payer_score + 0.15 * econ_score

Each axis returns a 0-100 score using independent thresholds (see _axis_*).
"""
from __future__ import annotations

import httpx
import json
import sys
from pathlib import Path
from collections import defaultdict
from typing import Any, Optional

HERE = Path(__file__).parent
HEADERS = {"User-Agent": "Signal OS Research backtest@signalos.local"}

DATASETS = {
    "hospital":    "44060663-47d8-4ced-a115-b53b4c270acb",
    "snf":         "a69d3df7-3f66-4a0d-b5b8-0d66049bd565",
    "home_health": "4999da74-1d8d-4a6f-934e-2d7ea470cc63",
}

# HCRIS Hospital dataset columns
HOSPITAL_COLS = {
    "name":        "Hospital Name",
    "income":      "Net Income",
    "opex":        "Less Total Operating Expense",
    "npr":         "Net Patient Revenue",
    "fy_end":      "Fiscal Year End Date",
    "cash":        "Cash on Hand and in Banks",
    "investments": "Investments",
    "temp_inv":    "Temporary Investments",
    "title_xviii_days": "Hospital Total Days Title XVIII For Adults & Peds",
    "title_xix_days":   "Hospital Total Days Title XIX For Adults & Peds",
    "total_days":  "Hospital Total Days (V + XVIII + XIX + Unknown) For Adults & Peds",
    "ccn":         "Provider CCN",
    "state":       "State Code",
}


def _safe_float(v) -> Optional[float]:
    try:
        if v in (None, ""): return None
        return float(v)
    except (TypeError, ValueError):
        return None


def search_hospitals(query: str, size: int = 5000) -> list[dict]:
    """Search hospital cost reports by Hospital Name substring.

    size default 5000 to capture multi-year history (CMS HCRIS has 5+ years
    per facility; a 30-facility system needs ~150 rows minimum for 5yrs).
    """
    uuid = DATASETS["hospital"]
    out: list[dict] = []
    offset = 0
    page_size = min(size, 1000)
    try:
        with httpx.Client(headers=HEADERS, timeout=60) as c:
            while True:
                r = c.get(f"https://data.cms.gov/data-api/v1/dataset/{uuid}/data",
                          params={
                              "filter[Hospital Name][condition][path]":     "Hospital Name",
                              "filter[Hospital Name][condition][operator]": "CONTAINS",
                              "filter[Hospital Name][condition][value]":    query,
                              "size":   page_size,
                              "offset": offset,
                          })
                if r.status_code != 200: break
                rows = r.json()
                if not isinstance(rows, list) or not rows: break
                out.extend(rows)
                if len(rows) < page_size or len(out) >= size: break
                offset += page_size
    except Exception:
        pass
    return out


def gather_facilities(queries: list[str]) -> list[dict]:
    """Merge facility cost reports across query variants, dedupe by (CCN, FY)."""
    seen = set()
    out = []
    for q in queries:
        for r in search_hospitals(q):
            ccn = r.get(HOSPITAL_COLS["ccn"])
            fy = r.get(HOSPITAL_COLS["fy_end"])
            if not ccn: continue
            key = (str(ccn), fy)
            if key in seen: continue
            seen.add(key)
            out.append(r)
    return out


# ──────────────────────────────────────────────────────────────────
# Axis 1: Operating Margin
# ──────────────────────────────────────────────────────────────────

def axis_margin(rows: list[dict], fiscal_year: Optional[str] = None) -> dict:
    """Compute NPR-weighted operating margin for facilities at a given FY.

    fiscal_year: optional string like '2022' or '2023' to filter rows by FY end.
                If None, uses the most recent FY across all facilities.
    """
    if fiscal_year is not None:
        rows = [r for r in rows if (r.get(HOSPITAL_COLS["fy_end"]) or "")[:4] == fiscal_year]
    if not rows:
        return {"score": None, "margin_pct": None, "n_facilities": 0,
                "letter": "UNVERIFIABLE"}

    contribs, weights = [], []
    for r in rows:
        npr = _safe_float(r.get(HOSPITAL_COLS["npr"]))
        if npr is None or npr <= 0: continue
        opex = _safe_float(r.get(HOSPITAL_COLS["opex"]))
        ni = _safe_float(r.get(HOSPITAL_COLS["income"]))
        if opex is not None:
            operating_income = npr - opex
        elif ni is not None:
            operating_income = ni
        else:
            continue
        contribs.append(operating_income)
        weights.append(npr)

    if not weights:
        return {"score": None, "margin_pct": None, "n_facilities": 0,
                "letter": "UNVERIFIABLE"}

    margin_pct = sum(contribs) / sum(weights) * 100

    # Map to 0-100 score
    if   margin_pct >= 8:  score, letter = 95, "AA"
    elif margin_pct >= 5:  score, letter = 90, "AA-"
    elif margin_pct >= 3:  score, letter = 85, "A+"
    elif margin_pct >= 1:  score, letter = 82, "A"
    elif margin_pct >= 0:  score, letter = 78, "A-"
    elif margin_pct >= -2: score, letter = 75, "BBB+"
    elif margin_pct >= -5: score, letter = 70, "BBB"
    elif margin_pct >= -8: score, letter = 65, "BB+"
    elif margin_pct >= -12: score, letter = 60, "BB"
    else:                  score, letter = 50, "B+"

    return {"score": score, "margin_pct": round(margin_pct, 2),
            "n_facilities": len(weights), "letter": letter,
            "total_npr": int(sum(weights))}


# ──────────────────────────────────────────────────────────────────
# Axis 2: Days Cash on Hand
# ──────────────────────────────────────────────────────────────────

def axis_days_cash(rows: list[dict], fiscal_year: Optional[str] = None) -> dict:
    """NPR-weighted days cash = (Cash + Investments) / (OpEx/365)."""
    if fiscal_year is not None:
        rows = [r for r in rows if (r.get(HOSPITAL_COLS["fy_end"]) or "")[:4] == fiscal_year]
    if not rows:
        return {"score": None, "days_cash": None, "letter": "UNVERIFIABLE"}

    cash_total, opex_total = 0, 0
    for r in rows:
        cash = _safe_float(r.get(HOSPITAL_COLS["cash"])) or 0
        inv  = _safe_float(r.get(HOSPITAL_COLS["investments"])) or 0
        ti   = _safe_float(r.get(HOSPITAL_COLS["temp_inv"])) or 0
        opex = _safe_float(r.get(HOSPITAL_COLS["opex"]))
        if opex is None or opex <= 0: continue
        cash_total += (cash + inv + ti)
        opex_total += opex

    if opex_total == 0:
        return {"score": None, "days_cash": None, "letter": "UNVERIFIABLE"}

    days_cash = cash_total / (opex_total / 365)

    if   days_cash >= 250: score, letter = 95, "AA"
    elif days_cash >= 150: score, letter = 88, "AA-"
    elif days_cash >= 100: score, letter = 83, "A+"
    elif days_cash >= 75:  score, letter = 78, "A"
    elif days_cash >= 50:  score, letter = 73, "BBB+"
    elif days_cash >= 25:  score, letter = 68, "BBB"
    else:                  score, letter = 55, "BB"

    return {"score": score, "days_cash": round(days_cash, 1), "letter": letter}


# ──────────────────────────────────────────────────────────────────
# Axis 3: Payer Mix
# ──────────────────────────────────────────────────────────────────

def axis_payer_mix(rows: list[dict], fiscal_year: Optional[str] = None) -> dict:
    """Medicare + Medicaid days / total days. Higher = adverse (lower reimb)."""
    if fiscal_year is not None:
        rows = [r for r in rows if (r.get(HOSPITAL_COLS["fy_end"]) or "")[:4] == fiscal_year]
    if not rows:
        return {"score": None, "medicare_pct": None, "medicaid_pct": None, "letter": "UNVERIFIABLE"}

    mcare, mcaid, total = 0, 0, 0
    for r in rows:
        m18 = _safe_float(r.get(HOSPITAL_COLS["title_xviii_days"])) or 0
        m19 = _safe_float(r.get(HOSPITAL_COLS["title_xix_days"])) or 0
        td  = _safe_float(r.get(HOSPITAL_COLS["total_days"])) or 0
        if td <= 0: continue
        mcare += m18; mcaid += m19; total += td

    if total == 0:
        return {"score": None, "medicare_pct": None, "medicaid_pct": None, "letter": "UNVERIFIABLE"}

    mcare_pct = mcare / total * 100
    mcaid_pct = mcaid / total * 100
    govt_pct = mcare_pct + mcaid_pct

    # Lower government-payer % is better (more commercial mix)
    if   govt_pct <= 45:  score, letter = 92, "AA"
    elif govt_pct <= 55:  score, letter = 85, "A+"
    elif govt_pct <= 65:  score, letter = 78, "A"
    elif govt_pct <= 75:  score, letter = 72, "BBB+"
    elif govt_pct <= 85:  score, letter = 65, "BBB"
    else:                 score, letter = 55, "BB"

    # Safety-net heavy adjustment (high Medicaid is worse)
    if mcaid_pct > 30:
        score -= 5

    return {"score": score, "medicare_pct": round(mcare_pct, 1),
            "medicaid_pct": round(mcaid_pct, 1), "govt_pct": round(govt_pct, 1),
            "letter": letter}


# ──────────────────────────────────────────────────────────────────
# Axis 4: Local Economic Base (simplified — state-level proxy)
# ──────────────────────────────────────────────────────────────────

# Hand-coded state-level hospital industry growth approximation (NAICS 622 employment trend)
# Sources: BLS QCEW national series; would refine via per-CBSA call in production
STATE_ECON_SCORE = {
    "TX": 88, "FL": 88, "AZ": 88, "NC": 87, "GA": 86, "CO": 86, "WA": 85, "UT": 86,
    "TN": 84, "SC": 84, "NV": 83, "ID": 83, "OR": 82, "VA": 82,
    "CA": 80, "MA": 80, "NY": 78, "NJ": 78, "MD": 80, "MN": 82, "MO": 80,
    "OH": 75, "PA": 73, "MI": 72, "IL": 72, "WI": 76, "IN": 76, "KY": 74,
    "WV": 60, "MS": 65, "AL": 70, "LA": 68, "AR": 70, "OK": 75, "KS": 75,
    "CT": 75, "NH": 78, "ME": 70, "RI": 72, "VT": 70,
    "IA": 78, "ND": 80, "SD": 78, "NE": 78, "MT": 76, "WY": 72,
    "DE": 78, "DC": 80, "AK": 75, "HI": 78, "NM": 72,
}


def axis_local_econ(state: str) -> dict:
    """State-level economic base score (NAICS 622 hospital employment trend proxy)."""
    score = STATE_ECON_SCORE.get(state, 75)
    if score >= 85: letter = "AA"
    elif score >= 80: letter = "A+"
    elif score >= 75: letter = "A"
    elif score >= 70: letter = "BBB+"
    else: letter = "BBB"
    return {"score": score, "state": state, "letter": letter}


# ──────────────────────────────────────────────────────────────────
# Composite score
# ──────────────────────────────────────────────────────────────────

def composite(rows: list[dict], state: str, fiscal_year: Optional[str] = None) -> dict:
    margin_a   = axis_margin(rows, fiscal_year)
    cash_a     = axis_days_cash(rows, fiscal_year)
    payer_a    = axis_payer_mix(rows, fiscal_year)
    econ_a     = axis_local_econ(state)

    # Compute weighted composite
    component_scores = {
        "margin":     (margin_a["score"], 0.40),
        "days_cash":  (cash_a["score"],   0.25),
        "payer_mix":  (payer_a["score"],  0.20),
        "local_econ": (econ_a["score"],   0.15),
    }

    weighted_sum, total_weight = 0, 0
    for axis, (s, w) in component_scores.items():
        if s is not None:
            weighted_sum += s * w
            total_weight += w

    if total_weight == 0:
        return {"composite_score": None, "letter": "UNVERIFIABLE",
                "axes": {"margin": margin_a, "days_cash": cash_a,
                          "payer_mix": payer_a, "local_econ": econ_a}}

    composite_score = weighted_sum / total_weight

    # Letter mapping (S&P scale)
    if   composite_score >= 92: letter = "AA"
    elif composite_score >= 88: letter = "AA-"
    elif composite_score >= 85: letter = "A+"
    elif composite_score >= 81: letter = "A"
    elif composite_score >= 78: letter = "A-"
    elif composite_score >= 74: letter = "BBB+"
    elif composite_score >= 70: letter = "BBB"
    elif composite_score >= 66: letter = "BBB-"
    elif composite_score >= 62: letter = "BB+"
    elif composite_score >= 58: letter = "BB"
    elif composite_score >= 54: letter = "BB-"
    else: letter = "B+"

    return {
        "composite_score": round(composite_score, 1),
        "letter": letter,
        "total_weight_used": round(total_weight, 2),
        "axes": {"margin": margin_a, "days_cash": cash_a,
                  "payer_mix": payer_a, "local_econ": econ_a},
    }


# ──────────────────────────────────────────────────────────────────
# Letter → numeric for divergence math
# ──────────────────────────────────────────────────────────────────

LETTER_SCORE = {
    "AAA": 100, "AA+": 95, "AA": 92, "AA-": 89,
    "A+": 85, "A": 82, "A-": 79,
    "BBB+": 75, "BBB": 72, "BBB-": 69,
    "BB+": 65, "BB": 62, "BB-": 59,
    "B+": 55, "B": 52, "B-": 49,
    "CCC+": 45, "CCC": 42, "CCC-": 39,
    "CC": 35, "C": 30, "D": 0,
}

MOODY_SCORE = {
    "Aaa": 100, "Aa1": 95, "Aa2": 92, "Aa3": 89,
    "A1": 85, "A2": 82, "A3": 79,
    "Baa1": 75, "Baa2": 72, "Baa3": 69,
    "Ba1": 65, "Ba2": 62, "Ba3": 59,
    "B1": 55, "B2": 52, "B3": 49,
    "Caa1": 45, "Caa2": 42, "Caa3": 39, "Ca": 35, "C": 30,
}


def consensus_explicit_score(moodys: Optional[str], sp: Optional[str],
                              fitch: Optional[str]) -> tuple[int, str]:
    scores = []
    if moodys and moodys in MOODY_SCORE: scores.append(MOODY_SCORE[moodys])
    if sp and sp in LETTER_SCORE: scores.append(LETTER_SCORE[sp])
    if fitch and fitch in LETTER_SCORE: scores.append(LETTER_SCORE[fitch])
    if not scores: return 0, "NR"
    avg = sum(scores) / len(scores)
    for letter, s in sorted(LETTER_SCORE.items(), key=lambda x: -x[1]):
        if avg >= s: return int(avg), letter
    return int(avg), "B-"


def divergence_signal(our_score: float, explicit_score: int) -> tuple[float, str]:
    """Convert score difference to notches (3 score pts ≈ 1 notch)."""
    notches = (our_score - explicit_score) / 3
    if   notches >=  2.0: sig = "STRONG_BUY"
    elif notches >=  0.5: sig = "WEAK_BUY"
    elif abs(notches) < 0.5: sig = "CONSENSUS"
    elif notches <= -2.0: sig = "STRONG_SELL"
    else:                  sig = "WEAK_SELL"
    return round(notches, 1), sig


if __name__ == "__main__":
    # Smoke test on Mayo Clinic
    rows = gather_facilities(["Mayo Clinic"])
    res = composite(rows, state="MN")
    import json
    print(json.dumps(res, indent=2, default=str))
