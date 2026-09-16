"""ai_adopter_gates — the four disqualifying tests the courts extracted from the
AI-adopter screen, applied as a re-scoring pass over AI_ADOPTER_SMALLCAP.json.

The screen itself was produced as a data store with no module, so the gates live here
and run over the store. Each gate is a name the screen ranked highly that a court then
had to reject for a reason the score could not see:

  G1 MIX REGRESSION (from the CRVL court, PASS 3/10)
     A falling personnel/revenue ratio in a MULTI-LINE business is usually service-line
     mix, not automation. Fit labour = sum(beta_i x revenue_line_i) with NO productivity
     term; if that explains most of the decline, the "AI margin story" is arithmetic.
     CRVL: network solutions went 33.4% -> 37.7% of revenue at ~9% labour intensity vs
     ~72% for the TPA line; constant-intensity mix explained 89% of a 3.05pp fall, and
     headcount actually ROSE 3.2%.

  G2 BANK/HOLDCO DENOMINATOR (from the CASS court, 2/10)
     Never fire a cost-out detector on X/Revenue for a registrant with an ALCO table
     (SIC 6022 and friends): spread revenue inflates the denominator so the ratio
     improves while the operating business does not. CASS's Labour/Revenue improved
     while Labour/FEE-revenue worsened on the same audited inputs.

  G3 ONE-TIME BASE EFFECT (from the CASS court)
     Screen the PRIOR four quarters for discrete items before computing any delta-margin.
     77% of the CASS "inflection" was a base rolling off, not a new trend.

  G4 DISCLOSURE RECENCY (from the CASS court)
     An "absence of disclosure" archetype is only as good as its cutoff. CASS's "zero AI
     disclosure" was refuted by an 8-K eleven days before intake — and the signal-to-price
     latency in that archetype is ~7 sessions, so the edge had already elapsed.

    python3 verticals/generators/ai_adopter_gates.py [--apply]

Without --apply it reports; with --apply it writes the gate results and adjusted scores
back into the store. PROPOSES ONLY — nothing here stages an order.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STORE = ROOT / "verticals" / "generators" / "data" / "AI_ADOPTER_SMALLCAP.json"

# G2: registrants whose revenue line carries net interest income. A cost ratio measured
# against total revenue is meaningless here — the denominator is a rate bet.
ALCO_SIC = {"6022", "6021", "6020", "6035", "6036", "6199", "6111"}
ALCO_HINTS = ("bank", "bancorp", "bancshares", "savings", "trust company",
              "financial corp", "holdings inc" )   # last one is weak, used only with a SIC hit

MIX_R2_BLOCK = 0.80        # G1: mix explains >=80% of the ratio move -> not automation
BASE_EFFECT_BLOCK = 0.50   # G3: >=50% of the delta from a prior-period discrete item


def _f(x, d=None):
    try:
        v = float(x)
        return d if v != v else v
    except Exception:
        return d


def g1_mix_regression(rec) -> dict:
    """Constant-intensity mix test. Needs per-line revenue; when the store does not carry
    segment data we return UNKNOWN rather than a pass — an untested gate is not a clear one."""
    lines = rec.get("revenue_lines") or rec.get("segments")
    labour = rec.get("personnel_expense_series") or rec.get("labour_series")
    if not lines or not labour:
        multi = rec.get("multi_line") if rec.get("multi_line") is not None else True
        return {"gate": "G1_mix", "status": "UNKNOWN" if multi else "N/A",
                "note": "segment revenue x labour series absent from the store — the CRVL "
                        "failure mode (mix explaining 89% of a personnel-ratio fall) CANNOT "
                        "be excluded. Pull the 10-K segment table before promoting."}
    # fit labour_t = sum_i beta_i * rev_i,t with beta >= 0, no productivity term
    try:
        import numpy as np
        X = np.array([[_f(v, 0.0) for v in row] for row in lines], dtype=float)
        y = np.array([_f(v, 0.0) for v in labour], dtype=float)
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        pred = X @ beta
        ss_res = float(((y - pred) ** 2).sum())
        ss_tot = float(((y - y.mean()) ** 2).sum()) or 1e-9
        r2 = 1 - ss_res / ss_tot
        return {"gate": "G1_mix", "status": "BLOCK" if r2 >= MIX_R2_BLOCK else "PASS",
                "r2": round(r2, 3), "betas": [round(float(b), 4) for b in beta],
                "note": ("constant-intensity mix explains %.0f%% of the labour path — "
                         "this is service-line mix, not automation" % (r2 * 100))
                        if r2 >= MIX_R2_BLOCK else
                        "mix alone does not explain the labour path; a productivity term survives"}
    except Exception as e:
        return {"gate": "G1_mix", "status": "UNKNOWN", "note": f"regression failed: {type(e).__name__}"}


# XBRL tags only a spread lender files. Presence of ANY of these means the revenue line
# contains net interest income and a cost/revenue ratio is not measuring operations.
# Deliberately NARROW. "Deposits" alone was a false positive — any company holding
# customer funds files it (PHR processes patient payments). These four are filed only by
# a registrant earning a SPREAD.
ALCO_TAGS = ("InterestAndDividendIncomeOperating", "InterestExpenseDeposits",
             "InterestIncomeExpenseAfterProvisionForLoanLoss",
             "LoansAndLeasesReceivableNetReportedAmount")


def g2_alco_denominator(rec, probe=True) -> dict:
    """Cost ratios measured against a revenue line containing net interest income.
    Resolved from the registrant's OWN XBRL facts — a bank cannot hide an ALCO."""
    name = (rec.get("name") or rec.get("company") or "").lower()
    bucket = (rec.get("sector_bucket") or "").lower()
    hint = any(h in name for h in ALCO_HINTS[:5]) or bucket in ("bank", "lender", "consumer_lender")
    cik = str(rec.get("cik") or "").lstrip("0")
    if not probe or not cik:
        return {"gate": "G2_alco", "status": "BLOCK" if hint else "UNKNOWN",
                "note": "no CIK to probe; name/bucket heuristic only"}
    try:
        import urllib.request, json as _j
        req = urllib.request.Request(
            f"https://data.sec.gov/api/xbrl/companyfacts/CIK{int(cik):010d}.json",
            headers={"User-Agent": "ajay research 4tripathy@gmail.com"})
        facts = _j.loads(urllib.request.urlopen(req, timeout=25).read()).get("facts", {}).get("us-gaap", {})
        hits = [t for t in ALCO_TAGS if t in facts]
    except Exception as e:
        return {"gate": "G2_alco", "status": "UNKNOWN", "note": f"probe failed: {type(e).__name__}"}
    if not hits:
        return {"gate": "G2_alco", "status": "PASS"}
    has_fee = "FeesAndCommissions" in facts or "NoninterestIncome" in facts
    return {"gate": "G2_alco",
            "status": "PASS_WITH_FEE_BASIS" if has_fee else "BLOCK",
            "alco_tags_found": hits[:3],
            "note": ("registrant files spread-lender tags — the cost ratio MUST be recomputed "
                     "against FEE revenue and absolute dollars, never total revenue "
                     "(the CASS mechanism: Labour/Rev improved while Labour/FeeRev worsened "
                     "on the same audited inputs)")}


def g3_base_effect(rec) -> dict:
    """Was the margin 'inflection' a prior-period discrete item rolling off?
    Uses the store's own 8-quarter operating-margin series: if the PRIOR-4 window contains
    an outlier quarter, the last4-vs-prior4 delta is measuring that quarter leaving, not a
    new trend. (CASS: 77% of the 'inflection' was base rolloff.)"""
    x = (rec.get("audited_xbrl") or {})
    ser = x.get("op_margin_8q_pct")
    delta = _f(x.get("op_margin_delta_pp"))
    if not ser or len(ser) < 8 or delta in (None, 0):
        return {"gate": "G3_base_effect", "status": "UNKNOWN",
                "note": "no 8-quarter margin series — base-effect cannot be excluded"}
    vals = [_f(v[1]) for v in ser if _f(v[1]) is not None]
    if len(vals) < 8:
        return {"gate": "G3_base_effect", "status": "UNKNOWN"}
    prior, last = vals[:4], vals[4:]
    med_p = sorted(prior)[len(prior)//2]
    # how much of the delta disappears if the prior window's WORST quarter is replaced by its median?
    worst = min(prior)
    adj_prior_avg = (sum(prior) - worst + med_p) / 4
    adj_delta = (sum(last)/4) - adj_prior_avg
    share_from_base = 1 - (adj_delta / delta) if delta else 0
    if share_from_base > 1.0:
        return {"gate": "G3_base_effect", "status": "BLOCK",
                "base_effect_share": ">1.0", "raw_delta_pp": round(delta, 2),
                "delta_ex_outlier_pp": round(adj_delta, 2),
                "note": ("the delta REVERSES sign once the prior window's outlier quarter is "
                         "normalised (%.2fpp -> %.2fpp) — there is no inflection, only a weak "
                         "base" % (delta, adj_delta))}
    return {"gate": "G3_base_effect",
            "status": "BLOCK" if share_from_base >= BASE_EFFECT_BLOCK else "PASS",
            "base_effect_share": round(share_from_base, 2),
            "raw_delta_pp": round(delta, 2), "delta_ex_outlier_pp": round(adj_delta, 2),
            "note": ("%.0f%% of the margin delta comes from one weak prior quarter rolling off"
                     % (share_from_base * 100))}


def g4_disclosure_recency(rec, cutoff_days: int = 7) -> dict:
    """The absence-of-disclosure archetype decays fast and must be re-checked to the cutoff."""
    prog = (rec.get("named_ai_cost_program") or "")
    absence = rec.get("thesis_is_absence_of_disclosure") or prog.strip().upper().startswith("NO")
    if not absence:
        return {"gate": "G4_recency", "status": "N/A"}
    last = rec.get("days_since_last_8k")
    if last is None:
        return {"gate": "G4_recency", "status": "UNKNOWN",
                "note": "8-K venue not re-checked to the cutoff — the CASS refutation came "
                        "from an 8-K 11 days before intake"}
    return {"gate": "G4_recency",
            "status": "BLOCK" if last <= cutoff_days else "PASS",
            "note": "signal-to-price latency in this archetype is ~7 sessions; a fresh "
                    "disclosure means the edge has already elapsed"}


def run(apply: bool = False):
    store = json.loads(STORE.read_text())
    names = store.get("universe") or store.get("names") or store.get("top_8") or []
    if isinstance(names, dict):
        names = list(names.values())
    out, blocked, unknown = [], 0, 0
    for rec in names:
        if not isinstance(rec, dict):
            continue
        gates = [g1_mix_regression(rec), g2_alco_denominator(rec),
                 g3_base_effect(rec), g4_disclosure_recency(rec)]
        statuses = [g["status"] for g in gates]
        verdict = ("BLOCKED" if "BLOCK" in statuses
                   else "UNRESOLVED" if "UNKNOWN" in statuses else "CLEAR")
        blocked += verdict == "BLOCKED"
        unknown += verdict == "UNRESOLVED"
        rec["court_gates_20260804"] = {"verdict": verdict, "gates": gates}
        out.append((rec.get("ticker") or rec.get("symbol") or "?", verdict, statuses))

    print(f"[ai_adopter_gates] {len(out)} names | BLOCKED {blocked} | "
          f"UNRESOLVED {unknown} | CLEAR {len(out)-blocked-unknown}\n")
    for t, v, s in sorted(out, key=lambda r: (r[1] != "BLOCKED", r[0]))[:40]:
        print(f"  {t:8s} {v:11s} {' '.join(s)}")
    if unknown:
        print(f"\n  NOTE: {unknown} names are UNRESOLVED — the store lacks segment revenue, "
              f"labour series, prior-period discrete items or 8-K recency.\n"
              f"  An untested gate is NOT a passed gate: these cannot be promoted to court "
              f"until the missing fields are pulled from the filings.")
    if apply:
        STORE.write_text(json.dumps(store, indent=1))
        print(f"\n  written back to {STORE}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    run(ap.parse_args().apply)
