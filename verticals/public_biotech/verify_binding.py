"""Stage 0 (biotech): DETERMINISTIC pre-flight check that each case is bound to the
right trial — run BEFORE any LLM stage, no model, no credits.

Why a deterministic check (and not an LLM one)
----------------------------------------------
A `CatalystCase.nct_ids` is the trusted base of the whole backtest: every M
comparison downstream inherits the assertion "the catalyst that read out is THIS
trial." That assertion is hand-curated by the same un-blinded agent that runs the
pipeline, so an LLM "does this look right?" re-judge would carry the same blind
spots — it would read a confident-but-wrong spec comment and nod along (the AVIR
binding even said "Ph2 HCV combo — NOT the COVID trial" while pointing at the
COVID Ph3). The only check that adds real signal is a MECHANICAL one that confronts
the spec with the external registry on axes a string-compare can settle:

  phase        case.catalyst_type        vs  registry phases
  indication   case.indication           vs  registry conditions
  intervention case.program (drug names) vs  registry interventions
  sponsor      case.company              vs  registry leadSponsor
  timing       case.cutoff               vs  registry primaryCompletionDate

A genuine lie diverges on ONE axis; a MIS-BINDING diverges on the trial's IDENTITY
(>= 2 independent axes). AVIR's wrong NCT (SUNRISE-3) shares the drug
(bemnifosbuvir) and sponsor (Atea) with the real HCV trial, so intervention and
sponsor MATCH — only indication (HCV vs COVID) and phase (2 vs 3) catch it. That is
exactly why a single-axis rule is not enough and a >=2-axis rule is.

What this does NOT do (be honest): it cannot catch a SUBSTANTIVE wrong-trial pick
that is internally consistent (right disease, right phase, wrong study) — that
residual needs external ground truth (bind from the price-moving press release) and
separation of duties, not a self-check. This hardens the CLERICAL layer only.

BLIND: reads CT.gov as-of cutoff only; never opens _sealed_outcomes.json.
"""
from __future__ import annotations

import re
import sys

from .catalyst_spec import CASES, CatalystCase
from .m_asof import _BASE, _get_json, _snapshot

# Generic tokens that carry no disambiguating signal on their respective axis.
_DISEASE_STOP = {
    "chronic", "acute", "advanced", "severe", "moderate", "mild", "active",
    "recurrent", "refractory", "metastatic", "early", "late", "stage", "type",
    "disease", "disorder", "syndrome", "infection", "the", "and", "with", "due",
    "naive", "treatment", "patients", "adult", "adults", "pediatric", "study",
    "phase", "virus", "viral",
}
_SPONSOR_STOP = {
    "pharmaceuticals", "pharmaceutical", "pharma", "therapeutics", "therapeutic",
    "biosciences", "bioscience", "biopharma", "biopharmaceuticals", "sciences",
    "technologies", "holdings", "biotherapeutics", "oncology", "medicines",
    "inc", "corp", "corporation", "ltd", "limited", "llc", "plc", "co", "company",
    "the", "and", "group", "international", "usa", "us", "ag", "sa", "gmbh", "nv",
    "ab", "as", "bio", "biotech",
}
_DRUG_STOP = {"placebo", "matching", "comparator", "standard", "care", "vehicle",
              "saline", "sham", "best", "supportive"}

# Standard, unambiguous disease acronyms. An acronym and its spelled-out form share
# NO tokens, so a registry that lists "Non-Small Cell Lung Cancer" and a case that
# says "NSCLC" wrongly read as a mis-binding. Expanding both sides symmetrically (the
# equivalence is medical fact, not a per-name hack) removes the false positive without
# weakening the check — acronyms here are 1:1 with their expansions.
_DISEASE_ACRONYMS = {
    "nsclc": {"non", "small", "cell", "lung", "cancer"},
    "sclc": {"small", "cell", "lung", "cancer"},
    "rcc": {"renal", "cell", "carcinoma"},
    "hcc": {"hepatocellular", "carcinoma"},
    "dlbcl": {"diffuse", "large", "cell", "lymphoma"},
    "nhl": {"hodgkin", "lymphoma"},
    "uti": {"urinary", "tract"},
    "cuti": {"urinary", "tract"},
    "mash": {"steatohepatitis"},
    "nash": {"steatohepatitis"},
    "csu": {"spontaneous", "urticaria"},
    "gbm": {"glioblastoma"},
    "tnbc": {"triple", "negative", "breast", "cancer"},
    "et": {"essential", "thrombocythemia"},
    "pv": {"polycythemia", "vera"},
    "uc": {"ulcerative", "colitis"},
    "ga": {"geographic", "atrophy"},
    "ckd": {"kidney"},
    "ted": {"thyroid", "eye"},
}
# A basket / all-comers trial registers a generic condition ("Solid Tumor") that
# carries no organ-specific signal; the registrational cohort (e.g. ROS1+ NSCLC) is a
# sub-population, not the condition field. Indication is then non-informative -> SKIP,
# never MISMATCH (we cannot disambiguate from a generic basket label).
_BASKET = {"solid", "tumor", "tumors", "tumour", "tumours", "neoplasm", "neoplasms",
           "neoplastic", "malignancy", "malignancies", "cancer", "locally",
           "unresectable", "resectable", "advanced", "metastatic"}


def _tok(s: str) -> list[str]:
    return [t for t in re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).split() if t]


def _expand_disease(tokens: set[str]) -> set[str]:
    """Augment a disease-token set with acronym<->expansion equivalences."""
    out = set(tokens)
    for t in tokens:
        out |= _DISEASE_ACRONYMS.get(t, set())
    for acr, exp in _DISEASE_ACRONYMS.items():
        if exp and exp <= out:
            out.add(acr)
    return out


def _expected_phase(catalyst_type: str) -> str | None:
    """'phase2_topline' -> 'PHASE2'; 'phase2b_interim' -> 'PHASE2'; 'pdufa' -> None."""
    m = re.search(r"phase\s*([1-4])", catalyst_type or "", re.I)
    return f"PHASE{m.group(1)}" if m else None


def _ax(name: str, status: str, detail: str) -> dict:
    return {"axis": name, "status": status, "detail": detail}


def _check_phase(case: CatalystCase, snap: dict) -> dict:
    exp = _expected_phase(case.catalyst_type)
    reg = [p for p in (snap.get("phases") or []) if p and p != "NA"]
    if exp is None or not reg:
        return _ax("phase", "SKIP",
                   f"catalyst_type={case.catalyst_type!r} reg={snap.get('phases')}")
    status = "MATCH" if exp in reg else "MISMATCH"
    return _ax("phase", status, f"expected {exp}, registry {reg}")


def _check_indication(case: CatalystCase, snap: dict) -> dict:
    conds = snap.get("conditions") or []
    if not conds:
        return _ax("indication", "SKIP", "registry has no conditions")
    case_tok = {t for t in _tok(case.indication) if t not in _DISEASE_STOP and len(t) > 2}
    reg_tok = {t for c in conds for t in _tok(c) if t not in _DISEASE_STOP and len(t) > 2}
    if not case_tok:
        return _ax("indication", "SKIP", f"no disease tokens in {case.indication!r}")
    if reg_tok and reg_tok <= _BASKET:
        return _ax("indication", "SKIP",
                   f"registry condition is a generic basket {conds} (non-informative)")
    overlap = _expand_disease(case_tok) & _expand_disease(reg_tok)
    status = "MATCH" if overlap else "MISMATCH"
    return _ax("indication", status,
               f"case{sorted(case_tok)} vs registry{conds} -> overlap {sorted(overlap)}")


def _check_intervention(case: CatalystCase, snap: dict) -> dict:
    interv = [i for i in (snap.get("interventions") or [])]
    drug_tok = [t for t in _tok(case.program) if t not in _DRUG_STOP and len(t) >= 5]
    reg_blob = " ".join(interv).lower()
    if not drug_tok or not interv:
        return _ax("intervention", "SKIP",
                   f"program={case.program!r} reg_interv={interv}")
    hit = [t for t in drug_tok if t in reg_blob]
    status = "MATCH" if hit else "MISMATCH"
    return _ax("intervention", status,
               f"program drugs {drug_tok} vs registry {interv} -> matched {hit}")


def _check_sponsor(case: CatalystCase, snap: dict) -> dict:
    spon = snap.get("lead_sponsor")
    if not spon:
        return _ax("sponsor", "SKIP", "registry has no lead sponsor")
    case_tok = {t for t in _tok(case.company) if t not in _SPONSOR_STOP and len(t) > 2}
    reg_tok = {t for t in _tok(spon) if t not in _SPONSOR_STOP and len(t) > 2}
    if not case_tok or not reg_tok:
        return _ax("sponsor", "SKIP", f"no distinctive token (case={case.company!r}, reg={spon!r})")
    overlap = case_tok & reg_tok
    status = "MATCH" if overlap else "MISMATCH"
    return _ax("sponsor", status, f"case{sorted(case_tok)} vs registry '{spon}'")


def _check_timing(case: CatalystCase, snap: dict) -> dict:
    """A topline can only have read out if the trial's primary completion is not in
    the future relative to the catalyst cutoff. Completion > 6 months AFTER cutoff
    is a hard logical violation (the catalyst supposedly reported, but the trial was
    not done) -> MISMATCH. Otherwise informational."""
    pcd = snap.get("primary_completion_date")
    if not pcd:
        return _ax("timing", "SKIP", "registry has no primary completion date")
    def ym(s):
        m = re.match(r"(\d{4})-(\d{2})", s)
        return (int(m.group(1)), int(m.group(2))) if m else None
    c, p = ym(case.cutoff), ym(pcd)
    if not c or not p:
        return _ax("timing", "SKIP", f"unparseable dates cutoff={case.cutoff} pcd={pcd}")
    months_after = (p[0] - c[0]) * 12 + (p[1] - c[1])
    status = "MISMATCH" if months_after > 6 else "MATCH"
    return _ax("timing", status,
               f"primary_completion {pcd} is {months_after:+d} mo vs cutoff {case.cutoff}")


def _asof_snapshot(nct: str, cutoff: str) -> tuple[dict | None, str | None]:
    """Latest pre-cutoff version snapshot (2 GETs — no full history walk)."""
    hist = _get_json(f"{_BASE}/{nct}/history")
    if not hist:
        return None, "history_unavailable"
    pre = [v for v in hist.get("changes", []) if v.get("date", "") <= cutoff]
    if not pre:
        return None, "no_pre_cutoff_version"
    rec = _get_json(f"{_BASE}/{nct}/history/{pre[-1]['version']}")
    if not rec:
        return None, "version_record_unavailable"
    snap = _snapshot(rec)
    snap["_asof_date"] = pre[-1]["date"]
    return snap, None


def check_nct(case: CatalystCase, nct: str) -> dict:
    snap, err = _asof_snapshot(nct, case.cutoff)
    if err:
        return {"nct": nct, "status": "ERROR", "error": err, "axes": []}
    axes = [
        _check_phase(case, snap), _check_indication(case, snap),
        _check_intervention(case, snap), _check_sponsor(case, snap),
        _check_timing(case, snap),
    ]
    mismatches = [a for a in axes if a["status"] == "MISMATCH"]
    # Two axis tiers. HARD = disease + phase: these settle trial IDENTITY and have
    # few false synonyms. SOFT = intervention + sponsor + timing: alias-prone (a drug
    # trades under a code name — AT-527 vs bemnifosbuvir; a trial is sponsored by a
    # PARTNER or CRO — Roche for Atea's MOONSONG). Two SOFT mismatches alone are
    # therefore NOT proof of a wrong trial. A FAIL requires a HARD divergence backed
    # by at least one more axis; otherwise we only WARN for human review.
    hard = {"phase", "indication"}
    hard_mm = [a for a in mismatches if a["axis"] in hard]
    if hard_mm and len(mismatches) >= 2:
        status = "FAIL"
    elif mismatches:
        status = "WARN"
    else:
        status = "PASS"
    return {"nct": nct, "status": status, "n_mismatch": len(mismatches),
            "asof": snap.get("_asof_date"), "axes": axes}


def check_binding(case: CatalystCase) -> dict:
    """Case-level verdict. A case FAILs if ANY bound NCT fails identity — a
    wrong-disease NCT is a binding error even alongside a correct sibling."""
    if not case.nct_ids:
        return {"case_id": case.case_id, "ticker": case.ticker,
                "status": "UNBOUND", "ncts": []}
    ncts = [check_nct(case, nct) for nct in case.nct_ids]
    order = {"FAIL": 0, "ERROR": 1, "WARN": 2, "PASS": 3}
    status = min((n["status"] for n in ncts), key=lambda s: order.get(s, 9))
    return {"case_id": case.case_id, "ticker": case.ticker,
            "status": status, "ncts": ncts}


class BindingError(RuntimeError):
    """Raised by assert_binding when a case is mis-bound — use as a pre-flight gate."""


def assert_binding(case: CatalystCase) -> dict:
    """Pre-flight gate: raise before spending credits if the binding fails."""
    r = check_binding(case)
    if r["status"] == "FAIL":
        bad = "; ".join(
            f"{n['nct']}: " + ", ".join(a["detail"] for a in n["axes"]
                                        if a["status"] == "MISMATCH")
            for n in r["ncts"] if n["status"] == "FAIL")
        raise BindingError(f"[{case.ticker}] mis-bound NCT — {bad}")
    return r


def _print_case(r: dict) -> None:
    icon = {"PASS": "ok  ", "WARN": "warn", "FAIL": "FAIL", "ERROR": "err ",
            "UNBOUND": "----"}.get(r["status"], "?   ")
    print(f"[{icon}] {r['ticker']:<6} {r['case_id']:<34} {r['status']}", file=sys.stderr)
    for n in r.get("ncts", []):
        if n["status"] in ("PASS",):
            continue
        print(f"         {n['nct']} -> {n['status']}"
              + (f" ({n['error']})" if n.get("error") else ""), file=sys.stderr)
        for a in n.get("axes", []):
            if a["status"] in ("MISMATCH", "ERROR"):
                print(f"            {a['axis']}: {a['status']} — {a['detail']}",
                      file=sys.stderr)


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Deterministic pre-flight NCT-binding check")
    ap.add_argument("case_ids", nargs="*", help="case ids (default: all sealed CASES)")
    ap.add_argument("--live", action="store_true", help="include the live cohort")
    args = ap.parse_args()

    cases = dict(CASES)
    if args.live:
        from .live_catalysts import LIVE_CASES
        cases.update(LIVE_CASES)
    ids = args.case_ids or list(cases)

    results = []
    for cid in ids:
        try:
            r = check_binding(cases[cid])
        except Exception as ex:
            r = {"case_id": cid, "ticker": cases[cid].ticker, "status": "ERROR",
                 "ncts": [], "error": str(ex)}
        results.append(r)
        _print_case(r)

    from collections import Counter
    tally = Counter(r["status"] for r in results)
    print(f"\n==== BINDING AUDIT: {dict(tally)} over {len(results)} cases ====",
          file=sys.stderr)
    fails = [r["ticker"] for r in results if r["status"] == "FAIL"]
    if fails:
        print(f"FAIL (likely wrong NCT): {fails}", file=sys.stderr)
        sys.exit(1)
