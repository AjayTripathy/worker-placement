"""ai_minsky — financing-stage classifier for the AI-capex complex (ensemble member 'minsky_stage').

Member of the 6-model ensemble on the AI-capex credit cycle (frame: desk/models/ai_capex_break.py).
This member answers ONE question: on Minsky's taxonomy, what financing stage is the capex
complex actually in, measured from cash-flow statements rather than narrative?

THE TAXONOMY (encoded honestly — thresholds are stated, not tuned):
  HEDGE       capex fully funded by operating cash flow with room: capex/OCF < 0.70.
  SPECULATIVE OCF covers capex only by cutting shareholder returns or adding some debt:
              capex/OCF in [0.70, 1.00), or capex/OCF >= 1.00 WITHOUT structurally rising
              issuance (funded off the cash pile), or a returns-cut + positive issuance,
              or debt-funded returns ((capex+returns)/OCF > 1 with positive issuance).
  PONZI       capex + committed outflows exceed OCF AND the gap is funded by structurally
              RISING debt issuance: capex/OCF >= 1.00 and net issuance positive and rising.

WHY THE STAGE MATTERS MORE THAN THE LEVEL: Minsky's point is that the TRANSITION is the
cycle. A hyperscaler at 0.6 capex/OCF can fund a bust; a name at 1.7 funded by $40B/yr of
fresh bonds has handed its capex plan to the credit market — the plan now has a margin
clerk. The 2008 analogy in ai_capex_break.py maps: HPA deceleration hurt because the
marginal borrower was Ponzi-financed; here the marginal borrowers are ORCL (bond-funded
datacenters) and the LAB LAYER (OpenAI — obligations serviced by new liability issuance
by construction; see the refinance-wall piece of ai_capex_break).

MEASUREMENT: yfinance annual + quarterly cashflow for MSFT GOOGL AMZN META ORCL — last 3
fiscal years + trailing 4 quarters. Fiscal years are NOT calendar-aligned (MSFT ends Jun,
ORCL May, rest Dec); aggregates mix fiscal frames — fine for stage classification, do not
reuse as a calendar time series. Missing dividend/buyback rows (AMZN) are treated as 0,
which is factually right for AMZN (no dividend, de minimis buybacks).

HISTORICAL BASE RATE (conceptual tie to desk/models/ai_reference_class.py, not imported):
once the marginal financier of a capex boom is Ponzi-stage, the reference class (telecom
vendor financing 2000, subprime originators 2006, shale HY issuers 2014) shows the first
credit event within ~4-10 quarters of the financing-regime peak — the stage itself is the
clock-starter, independent of demand.

    python3 -m desk.models.ai_minsky
"""
from __future__ import annotations

import datetime as dt
import json
import math
from pathlib import Path

import yfinance as yf

TICKERS = ["MSFT", "GOOGL", "AMZN", "META", "ORCL"]

ROWS = {
    "capex": "Capital Expenditure",            # negative in yfinance
    "ocf": "Operating Cash Flow",
    "net_debt_iss": "Net Issuance Payments Of Debt",
    "div": "Cash Dividends Paid",              # negative
    "buyback": "Repurchase Of Capital Stock",  # negative
}

# ── The LAB layer: static parameters, not yfinance-observable ────────────────
LAB_LAYER = {
    "OpenAI": {
        "stage": "PONZI",
        "why": "Ponzi by construction: obligations (burn + take-or-pay coming due, ~$30-55B/yr "
               "2027-29 per ai_capex_break parameters) are serviced by NEW liability issuance — "
               "the $122B raise on the $852B mark ran at the ~15% private dilution ceiling. "
               "Sustainable iff d_max*V(t) >= Need(t); the IPO is the terminal refinance.",
        "source": "desk/models/ai_capex_break.py params (V_last=852 VERIFIED, raise=122 VERIFIED, "
                  "need-path article-parameterized UNVERIFIED)",
    },
    "neoclouds": {
        "stage": "PONZI",
        "why": "CRWV-style: GPU-collateralized DDTLs + ABS; debt service depends on re-leasing "
               "and re-financing depreciating collateral, not on contracted cash flow surviving "
               "a price decline. Static note — no live feed wired (Gate C of ai_capex_break).",
        "source": "ai_capex_break.py Gate C / article (CRWV DDTL 5.0 securitized May-26, UNVERIFIED)",
    },
}

BASE_RATE_NOTE = (
    "Base rate (reference class, conceptual — see desk/models/ai_reference_class.py): once the "
    "marginal financier of a capex boom reaches Ponzi stage, first visible credit event follows "
    "in ~4-10 quarters (telecom vendor-financing peak 2000 -> CLEC failures 2001Q1-Q2; subprime "
    "originator peak 2005H2 -> monoline originator failures 2006Q4-2007Q1; shale HY issuance peak "
    "2014 -> HY energy blowout 2015Q4). The stage is the clock, not the demand outlook."
)


# ── data pull ────────────────────────────────────────────────────────────────
def _get(df, row, col):
    try:
        v = df.loc[row, col]
    except (KeyError, IndexError):
        return None
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    return float(v)


def pull(ticker: str) -> dict:
    """Return {'periods': [{label, end, capex, ocf, net_debt_iss, returns}, ...]} oldest->newest,
    last 3 FY + trailing-4Q. capex/returns are POSITIVE outflow magnitudes."""
    t = yf.Ticker(ticker)
    acf, qcf = t.cashflow, t.quarterly_cashflow
    periods = []
    cols = sorted(acf.columns)[-3:]  # last 3 fiscal years, oldest first
    for c in cols:
        r = {k: _get(acf, name, c) for k, name in ROWS.items()}
        periods.append(_period(f"FY{c.year}", str(c.date()), r))
    # trailing 4Q sum
    qcols = sorted(qcf.columns)[-4:]
    if len(qcols) == 4:
        r = {}
        for k, name in ROWS.items():
            vals = [_get(qcf, name, c) for c in qcols]
            r[k] = sum(v for v in vals if v is not None) if any(v is not None for v in vals) else None
        periods.append(_period("T4Q", str(qcols[-1].date()), r))
    return {"ticker": ticker, "periods": periods}


def _period(label, end, r):
    capex = abs(r["capex"]) if r["capex"] is not None else None
    ocf = r["ocf"]
    returns = sum(abs(r[k]) for k in ("div", "buyback") if r[k] is not None)  # missing -> 0 (AMZN)
    return {"label": label, "end": end, "capex_bn": _bn(capex), "ocf_bn": _bn(ocf),
            "net_debt_iss_bn": _bn(r["net_debt_iss"]), "returns_bn": _bn(returns),
            "_capex": capex, "_ocf": ocf, "_iss": r["net_debt_iss"] or 0.0, "_ret": returns}


def _bn(v):
    return None if v is None else round(v / 1e9, 1)


# ── classification ───────────────────────────────────────────────────────────
def metrics(p: dict) -> dict:
    if not p["_ocf"] or not p["_capex"]:
        return {}
    return {"capex_ocf": round(p["_capex"] / p["_ocf"], 2),
            "total_ocf": round((p["_capex"] + p["_ret"]) / p["_ocf"], 2)}


def classify(seq: list[dict]) -> list[dict]:
    """Stage per period given the full sequence (issuance/returns trends need history)."""
    out = []
    for i, p in enumerate(seq):
        m = metrics(p)
        if not m:
            out.append({**{k: p[k] for k in ("label", "end")}, "stage": "NO_DATA"})
            continue
        # prior period for trend tests; if T4Q coincides with the latest FY (just-reported
        # fiscal year, e.g. ORCL), compare against the prior distinct period instead.
        j = i - 1
        if j >= 0 and seq[j]["end"] == p["end"] and j > 0:
            j -= 1
        iss_rising = j >= 0 and p["_iss"] > 0 and p["_iss"] > seq[j]["_iss"]
        returns_cut = j >= 0 and seq[j]["_ret"] > 0 and p["_ret"] < 0.7 * seq[j]["_ret"]
        if m["capex_ocf"] >= 1.0 and p["_iss"] > 0 and iss_rising:
            stage, why = "PONZI", "capex/OCF >= 1.0 funded by rising net debt issuance"
        elif m["capex_ocf"] >= 1.0:
            stage, why = "SPECULATIVE", "capex/OCF >= 1.0 but funded off the cash pile, not structural issuance"
        elif m["capex_ocf"] >= 0.7:
            stage, why = "SPECULATIVE", "capex/OCF in [0.7, 1.0)"
        elif returns_cut and p["_iss"] > 0:
            stage, why = "SPECULATIVE", "capex funded by cutting shareholder returns + adding debt"
        elif m["total_ocf"] > 1.0 and p["_iss"] > 0:
            stage, why = "SPECULATIVE", "debt-funded shareholder returns ((capex+returns)/OCF > 1)"
        else:
            stage, why = "HEDGE", "capex/OCF < 0.7, self-funded with room"
        out.append({"label": p["label"], "end": p["end"], **m,
                    "capex_bn": p["capex_bn"], "ocf_bn": p["ocf_bn"],
                    "net_debt_iss_bn": p["net_debt_iss_bn"], "returns_bn": p["returns_bn"],
                    "stage": stage, "why": why,
                    "flags": [f for f, on in (("issuance_rising", iss_rising),
                                              ("returns_cut", returns_cut)) if on]})
    return out


def aggregate(all_data: list[dict]) -> list[dict]:
    """Aggregate by period POSITION (FY-3..FY-1, T4Q) — fiscal frames differ (MSFT Jun,
    ORCL May, rest Dec); this is a stage series, not a calendar series."""
    n = min(len(d["periods"]) for d in all_data)
    agg = []
    for i in range(n):
        ps = [d["periods"][i] for d in all_data]
        tot = {k: sum(p[f"_{k}"] or 0 for p in ps) for k in ("capex", "ocf", "iss", "ret")}
        # aggregate label: T4Q if all trailing rows, else the median FY label (fiscal frames differ)
        label = ps[0]["label"] if ps[0]["label"] == "T4Q" else sorted(p["label"] for p in ps)[len(ps) // 2]
        agg.append({"label": label, "end": max(p["end"] for p in ps),
                    "_capex": tot["capex"], "_ocf": tot["ocf"], "_iss": tot["iss"], "_ret": tot["ret"],
                    "capex_bn": _bn(tot["capex"]), "ocf_bn": _bn(tot["ocf"]),
                    "net_debt_iss_bn": _bn(tot["iss"]), "returns_bn": _bn(tot["ret"])})
    return classify(agg)


def state_of(per_name: dict, agg: list[dict]) -> tuple[str, list[str]]:
    """Contract map: aggregate HEDGE=GREEN, SPECULATIVE=AMBER, any-hyperscaler-PONZI or
    aggregate capex/OCF >= 1 = RED."""
    notes = []
    latest_agg = agg[-1]
    ponzi = [t for t, seq in per_name.items() if seq[-1]["stage"] == "PONZI"]
    if ponzi:
        return "RED", [f"hyperscaler(s) at PONZI stage: {', '.join(ponzi)}"]
    if latest_agg.get("capex_ocf", 0) >= 1.0:
        return "RED", ["aggregate capex/OCF >= 1.0"]
    if latest_agg["stage"] == "SPECULATIVE":
        return "AMBER", ["aggregate SPECULATIVE"]
    return "GREEN", ["aggregate HEDGE"] + notes


# ── main ─────────────────────────────────────────────────────────────────────
def main():
    asof = dt.date.today().isoformat()
    print(f"=== AI MINSKY FINANCING-STAGE CLASSIFIER ({asof}) ===\n")
    all_data, per_name = [], {}
    for tk in TICKERS:
        d = pull(tk)
        all_data.append(d)
        per_name[tk] = classify(d["periods"])

    for tk in TICKERS:
        print(f"-- {tk} --")
        for r in per_name[tk]:
            if r["stage"] == "NO_DATA":
                print(f"  {r['label']:7} NO_DATA")
                continue
            fl = f"  [{','.join(r['flags'])}]" if r["flags"] else ""
            print(f"  {r['label']:7}({r['end']}) capex/OCF {r['capex_ocf']:.2f}  "
                  f"(capex+ret)/OCF {r['total_ocf']:.2f}  netDebtIss {r['net_debt_iss_bn']:>6}B  "
                  f"-> {r['stage']}{fl}")
        print()

    agg = aggregate(all_data)
    print("-- AGGREGATE (5 hyperscalers; mixed fiscal frames) --")
    for r in agg:
        print(f"  {r['label']:7} capex/OCF {r['capex_ocf']:.2f}  (capex+ret)/OCF {r['total_ocf']:.2f}  "
              f"netDebtIss {r['net_debt_iss_bn']:>6}B  -> {r['stage']}")
    migration = " -> ".join(f"{r['label']}:{r['stage']}" for r in agg)
    print(f"\n  stage migration: {migration}")

    print("\n-- LAB LAYER (static parameters) --")
    for name, v in LAB_LAYER.items():
        print(f"  {name}: {v['stage']} — {v['why']}")

    state, why = state_of(per_name, agg)
    print(f"\n-- STATE: {state} ({'; '.join(why)}) --")
    print(f"\n{BASE_RATE_NOTE}")

    out = {
        "member": "minsky_stage",
        "asof": asof,
        "state": state,
        "reading": {
            "per_name": {tk: [{k: v for k, v in r.items() if not k.startswith("_")}
                              for r in per_name[tk]] for tk in TICKERS},
            "aggregate": [{k: v for k, v in r.items() if not k.startswith("_")} for r in agg],
            "stage_migration": migration,
            "latest_stages": {tk: per_name[tk][-1]["stage"] for tk in TICKERS},
            "lab_layer": LAB_LAYER,
            "state_why": why,
        },
        # This member is a STAGE classifier, not a hazard model; break-timing probabilities
        # live in the reference_class member. Nulls are intentional, not missing data.
        "P_break_by_2027": None,
        "P_break_by_2028": None,
        "notes": [
            BASE_RATE_NOTE,
            "Thresholds: HEDGE capex/OCF<0.7; SPECULATIVE 0.7-1.0 or returns-cut/debt-funded-returns "
            "or >=1.0-off-cash-pile; PONZI >=1.0 + rising net issuance.",
            "Fiscal frames mixed (MSFT Jun / ORCL May / rest Dec) — stage series, not calendar series.",
            "AMZN dividends/buybacks missing in yfinance -> treated as 0 (factually correct).",
            "Capex is TOTAL capex, not AI-only — conservative for AMZN (fulfillment mixed in), "
            "immaterial for ORCL/MSFT/META/GOOGL where the delta is datacenter-driven.",
        ],
    }
    path = Path(__file__).resolve().parents[1] / "data" / "ai_ensemble" / "minsky.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=1))
    print(f"\nwrote {path}")


if __name__ == "__main__":
    main()
