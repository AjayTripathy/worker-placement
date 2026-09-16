"""Composite deep-value score + quality/solvency guards.

Score = mean of rank-percentiles across {EV/EBIT, FCF-yield, P/B, net-cash/mktcap,
NCAV/mktcap}, higher = cheaper. Guards flag ADR, sub-cash (EV<0 — never let a negative
multiple sort as "cheapest"), cash-burners (EBIT<0 AND FCF<0), and holdco distortion
(material minority interest). EV includes total debt + minority interest, net of cash.
"""
from __future__ import annotations
import statistics as st


def compute_metrics(u: dict, f: dict) -> dict:
    """u = universe row (sym/mktcap/...), f = fundamentals cross-section row."""
    g = f.get
    ac, liab, eq = g("AssetsCurrent"), g("Liabilities"), g("StockholdersEquity")
    if liab is None and g("LiabilitiesCurrent") is not None:
        liab = g("LiabilitiesCurrent")            # weak fallback (current only)
    cash = (g("CashAndCashEquivalentsAtCarryingValue") or 0) + (g("ShortTermInvestments") or 0)
    # robust total debt — catch convertibles + custom term-loan tags (the COLL miss, where the screen
    # called a $803M-debt name "net cash"). Prefer the most comprehensive LT representation, ADD
    # separately-tagged convertibles + current debt, floor at any all-in combined tag. Bias = over-state
    # (conservative: bigger EV -> higher multiple -> won't manufacture a false bargain).
    _lt = max([x for x in (g("LongTermDebtNoncurrent"), g("LongTermDebt"),
                           g("LongTermDebtAndCapitalLeaseObligationsNoncurrent"),
                           g("LongTermDebtAndCapitalLeaseObligations")) if x is not None] or [0])
    _conv = max(g("ConvertibleLongTermNotesPayable") or 0, g("ConvertibleNotesPayable") or 0,
                g("ConvertibleDebtNoncurrent") or 0, g("ConvertibleDebt") or 0) \
            + (g("ConvertibleDebtCurrent") or 0)
    # M&A earnouts are debt-like in EV — the CRMD hole (DV5 2026-07-20: $105.6M Melinta contingent
    # consideration invisible -> 2.2x printed, true 3.8x)
    _earnout = (g("BusinessCombinationContingentConsiderationLiabilityNoncurrent") or 0) \
               + (g("BusinessCombinationContingentConsiderationLiabilityCurrent") or 0)
    # current-bucket debt: larger of the umbrella tag vs the sum of specific ones — a maturity-wall
    # name reclassifies ALL debt current (HAIN 2026-07-15: $549.8M under LongTermDebtCurrent, every
    # noncurrent tag 0, screen printed "net cash" on an explicit going-concern; SSTK same day: $158M
    # current debt missed -> "slight net cash" on ~$111M net debt). Overlap-safe via max().
    _stdebt = max(g("DebtCurrent") or 0,
                  (g("LongTermDebtCurrent") or 0) + (g("LinesOfCreditCurrent") or 0)
                  + (g("ShortTermBorrowings") or 0) + (g("OtherShortTermBorrowings") or 0)
                  + (g("SecuredDebtCurrent") or 0))
    _combined = g("DebtLongtermAndShorttermCombinedAmount") or 0
    debt = max(_lt + _conv + _stdebt, _combined) + _earnout
    mi = g("MinorityInterest") or 0
    ebit, cfo, capx = g("OperatingIncomeLoss"), g("NetCashProvidedByUsedInOperatingActivities"), g("PaymentsToAcquirePropertyPlantAndEquipment")
    fcf = (cfo - capx) if (cfo is not None and capx is not None) else cfo
    m = u["mktcap"]
    ev = m + debt + mi - cash
    ncav = (ac - liab) if (ac is not None and liab is not None) else None
    netcash = cash - debt
    r = {**u, **{k: f.get(k) for k in ("OperatingIncomeLoss",)},
         "ev": ev, "ebit": ebit, "fcf": fcf, "eq": eq, "ncav": ncav, "netcash": netcash,
         "debt": debt, "cash": cash, "mi": mi, "rev": g("Revenues"),
         "ttm_rolling": f.get("_ttm_rolling", False)}
    r["am"] = (ev / ebit) if (ev > 0 and ebit and ebit > 0) else None     # clean Acquirer's Multiple
    r["fcfy"] = (fcf / m) if fcf is not None else None
    r["pb"] = (m / eq) if (eq and eq > 0) else None
    r["ncav_r"] = (ncav / m) if ncav is not None else None
    r["ncash_r"] = netcash / m
    r["subcash"] = ev < 0
    r["burning"] = (ebit is not None and ebit < 0) and (fcf is not None and fcf < 0)
    r["holdco"] = mi > 0.10 * max(eq or 0, 1)                              # material NCI
    # MLP/consolidation artifact — NCI DOMINATES equity (the entity consolidates 100% of a
    # plant/OpCo it owns a sliver of; parent mkt-cap != consolidated EBIT -> EV/EBIT + earnings-yield
    # are FABRICATED). WLKP 2026-07-16: consolidates a ~$2B ethylene complex it owns ~23% of ->
    # screen printed EV/EBIT 2.0 / 50% earn-yield. Exclude by structure like ADRs.
    r["mlp_artifact"] = mi > max(eq or 0, 1)
    r["neg_equity"] = eq is not None and eq <= 0
    # FCF positive while EBIT negative => cash is working-capital-driven, not earnings
    # power (the DCGO one-time-receivable-liquidation mirage). Flag, don't trust.
    r["wc_fcf"] = (fcf is not None and fcf > 0) and (ebit is not None and ebit < 0)
    # one-time gains dominate TTM EBIT => the multiple is an artifact (the SPRO milestone /
    # AMPY divestiture-gain hole, DV5 2026-07-20: both "2x" names were ex-items EBIT-NEGATIVE)
    ot = f.get("OneTimeGain_ttm") or 0.0
    r["ebit_onetime"] = bool(ebit and ebit > 0 and ot > 0.4 * ebit)
    return r


def _pctile(vals, reverse=False):
    xs = sorted(v for v in vals if v is not None)
    n = len(xs) or 1
    def f(v):
        if v is None:
            return None
        r = sum(1 for x in xs if x <= v) / n
        return (1 - r) if reverse else r
    return f


def composite(records: list[dict], min_metrics=3) -> list[dict]:
    have = [r for r in records if (r["ebit"] is not None or r["fcf"] is not None)]
    p = {"am": _pctile([r["am"] for r in have], True),
         "fcfy": _pctile([r["fcfy"] for r in have]),
         "pb": _pctile([r["pb"] for r in have], True),
         "ncash_r": _pctile([r["ncash_r"] for r in have]),
         "ncav_r": _pctile([r["ncav_r"] for r in have])}
    for r in have:
        parts = [p[k](r[k]) for k in p]
        parts = [x for x in parts if x is not None]
        r["score"] = round(st.mean(parts), 3) if len(parts) >= min_metrics else None
        r["nmetrics"] = len(parts)
    return have


def clean_shortlist(records, exclude_adr=True):
    """Profitable, US, non-burning, scored — the names worth R/f(M)."""
    out = [r for r in records if r.get("score") is not None and not r["burning"]
           and ((r["ebit"] and r["ebit"] > 0) or (r["fcf"] and r["fcf"] > 0))
           and not r.get("mlp_artifact")            # MLP/NCI-consolidation artifact (WLKP) — metrics fabricated
           and not r.get("ebit_onetime")            # one-time-gain-dominated TTM EBIT (SPRO/AMPY) — multiple fabricated
           and not (exclude_adr and r.get("adr"))]
    out.sort(key=lambda r: -r["score"])
    return out
