"""Quality overlay — turns the trap-DENSE 'cheapest' deep-value list into a cheap-AND-quality
survivor list (Greenblatt Magic-Formula style: earnings-yield + ROIC), with the guards the
2026-06-26 trap-filter batch demanded.

WHY: the top-4 cheapest screened names (GIII/UPBD/CRMD/SIGA) were ALL traps — stale-peak EBIT,
hidden leverage, reimbursement cliff, peak-gov lumpiness. Pure cheapness sorts the traps to the top.
Cheapness is the FINDER; QUALITY (durable, growing-or-stable, capital-efficient, not over-levered,
FRESH) is what keeps you out of them. The per-name R/f(M) trap-filter is still the final verifier —
this overlay just makes the shortlist far less trap-dense before you spend on diligence.

GATES (reject): stale (no fresh quarter), burning/WC-FCF mirage/neg-equity, EBIT collapsing >20% YoY
(the GIII stale-peak), net-debt/EBIT > 3.5x (the UPBD hidden-leverage), ROIC < 10% (junk), earnings-
yield < 8% (not actually cheap on a debt-adjusted EV). RANK survivors by Magic-Formula combined rank.
"""
from __future__ import annotations


def compute_quality(r: dict, f: dict) -> dict:
    """r = score.compute_metrics output; f = raw fundamentals row (Assets, prior EBIT)."""
    ebit, rev, ev = r.get("ebit"), r.get("rev"), r.get("ev")
    assets, cash = f.get("Assets"), r.get("cash") or 0
    prior_ebit = f.get("OperatingIncomeLoss_prior")
    invested = (assets - cash) if assets is not None else None
    q = {
        "roic": (ebit / invested) if (ebit and invested and invested > 0) else None,
        "ebit_margin": (ebit / rev) if (ebit and rev and rev > 0) else None,
        "ebit_growth": (ebit / prior_ebit - 1) if (ebit is not None and prior_ebit and prior_ebit > 0) else None,
        # netcash<0 => net debt; net-debt/EBIT leverage (the hidden-leverage guard)
        "net_debt_ebit": ((-r["netcash"]) / ebit) if (ebit and ebit > 0 and r.get("netcash") is not None) else None,
        "fcf_conv": (r["fcf"] / ebit) if (r.get("fcf") is not None and ebit and ebit > 0) else None,
        "earn_yield": (ebit / ev) if (ev and ev > 0 and ebit) else None,
    }
    # latest-QUARTER EBIT + its YoY (the recent-inflection guard) — now on EBIT NORMALIZED for one-time
    # gains (the BKE hole: a $19.1M litigation settlement read as +37% growth). Strip discrete one-time
    # gains from BOTH quarters; YoY is computed on the adjusted figures.
    q_e, q_ep = f.get("OperatingIncomeLoss_q"), f.get("OperatingIncomeLoss_q_prior")
    otg, otg_p = f.get("OneTimeGain_q") or 0, f.get("OneTimeGain_q_prior") or 0
    q_e_adj = (q_e - otg) if q_e is not None else None
    q_ep_adj = (q_ep - otg_p) if q_ep is not None else None
    q["latest_q_ebit"] = q_e_adj                 # the gate consumes the ADJUSTED quarter
    q["latest_q_ebit_reported"] = q_e
    q["latest_q_ebit_yoy"] = (q_e_adj / q_ep_adj - 1) if (q_e_adj is not None and q_ep_adj and q_ep_adj > 0) else None
    # how much of reported quarterly EBIT is discrete one-time gain
    q["one_time_pct"] = (otg / q_e) if (q_e and q_e > 0 and otg > 0) else 0.0
    # run-rate-spike BACKSTOP for UNTAGGED one-timers: reported quarterly EBIT vs TTM/4 implied run-rate.
    # A quarter far above run-rate is either a one-time item or strong seasonality -> can't tell from the
    # frame, so FLAG (force DD), don't trust the inflection as clean growth.
    ttm_ebit = r.get("ebit")
    q["q_vs_runrate"] = (q_e / (ttm_ebit / 4.0)) if (q_e is not None and ttm_ebit and ttm_ebit > 0) else None
    # ebit_quality verdict surfaced on every name — the screen no longer silently calls a name "clean".
    # KEY LESSON (BKE, 2nd skeptic pass): the strip-tag recall is only ~9% of the universe and the BKE
    # settlement was UNTAGGED, so one_time_pct read 0 and a fake +36.5% YoY passed as clean. You cannot
    # tell an untagged operating one-timer from real growth via frames — so DON'T try to reject it (that
    # would nuke genuine growth like NUTX +111%); instead REFUSE to certify it. Any large POSITIVE
    # quarterly EBIT inflection (the shape of a one-time gain) downgrades to needs-DD, never "clean".
    yoy = q.get("latest_q_ebit_yoy")
    if q["one_time_pct"] > 0.10:
        q["ebit_quality"] = f"one-time gain {q['one_time_pct']:.0%} of EBIT — DD"
    elif yoy is not None and yoy > 0.30:
        q["ebit_quality"] = f"+{yoy:.0%} YoY Q-EBIT jump — one-time vs growth UNVERIFIED, needs-DD"
    elif q["q_vs_runrate"] is not None and q["q_vs_runrate"] > 1.6:
        q["ebit_quality"] = f"Q EBIT {q['q_vs_runrate']:.1f}x run-rate (one-time? seasonal? — DD)"
    else:
        q["ebit_quality"] = "clean"
    return q


def passes_quality(r: dict, q: dict) -> tuple[bool, str]:
    if not r.get("ttm_rolling"):
        return False, "stale (no fresh quarter)"
    if r.get("burning") or r.get("wc_fcf") or r.get("neg_equity"):
        return False, "burn/WC-FCF/neg-equity"
    if not (r.get("ebit") and r["ebit"] > 0):
        return False, "no positive EBIT"
    if q["ebit_growth"] is not None and q["ebit_growth"] < -0.20:
        return False, f"EBIT collapsing {q['ebit_growth']:+.0%} YoY (stale-peak)"
    # latest-QUARTER inflection guard (UPWK/VITL/PSIX slipped the annual gate on a fresh-quarter collapse).
    # Now on ONE-TIME-ADJUSTED EBIT, so a settlement-inflated quarter can't pass on a fake number.
    if q.get("latest_q_ebit") is not None and q["latest_q_ebit"] < 0:
        return False, "adj latest-quarter EBIT negative (recent inflection / ex one-time)"
    if q.get("latest_q_ebit_yoy") is not None and q["latest_q_ebit_yoy"] < -0.15:
        return False, f"adj latest-Q EBIT {q['latest_q_ebit_yoy']:+.0%} YoY (recent inflection, ex one-time)"
    # material one-time gain inflating reported EBIT -> the multiple is struck on a non-operating peak (the
    # BKE/GIII asymmetry). Reject to DD rather than auto-promote.
    if q.get("one_time_pct", 0) > 0.20:
        return False, f"EBIT inflated by one-time gain ({q['one_time_pct']:.0%}) — needs DD (GIII/BKE class)"
    # extreme run-rate spike with no tag = unverifiable one-time/seasonality -> don't auto-promote
    if q.get("q_vs_runrate") is not None and q["q_vs_runrate"] > 2.2:
        return False, f"Q EBIT {q['q_vs_runrate']:.1f}x TTM run-rate — unverifiable spike, needs DD"
    if q["net_debt_ebit"] is not None and q["net_debt_ebit"] > 3.5:
        return False, f"over-levered {q['net_debt_ebit']:.1f}x net-debt/EBIT"
    if q["roic"] is not None and q["roic"] < 0.10:
        return False, f"ROIC {q['roic']:.0%} <10% (low quality)"
    if q["earn_yield"] is None or q["earn_yield"] < 0.08:
        return False, "earn-yield <8% (not cheap on debt-adj EV)"
    return True, "ok"


def magic_formula(cand: list[dict]) -> list[dict]:
    """Greenblatt: sum of {earnings-yield rank, ROIC rank}; lowest combined = cheap AND good."""
    by_ey = sorted(cand, key=lambda r: -(r["q"]["earn_yield"] or 0))
    by_roic = sorted(cand, key=lambda r: -(r["q"]["roic"] or 0))
    ey = {id(r): i for i, r in enumerate(by_ey)}
    rc = {id(r): i for i, r in enumerate(by_roic)}
    for r in cand:
        r["mf_rank"] = ey[id(r)] + rc[id(r)]
    return sorted(cand, key=lambda r: r["mf_rank"])
