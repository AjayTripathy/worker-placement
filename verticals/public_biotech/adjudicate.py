"""Stage 3.5 (biotech): reason over the f-library's findings and render an
analyst judgment.

Motivation: the deterministic decisive-refute GATE in evaluate._aggregate counts
high-precision SEVERE refutes. Counting cannot ask the question that actually
decides the call — "does this finding bear on THIS catalyst, and does it indicate
the company is masking a likely miss?" — so every false positive has demanded
another hand-tuned guard (construct-change, controlled-pivotal, program scoping).
This module replaces the count with reasoning over the SAME structured findings.

Two design rules learned the hard way:
  1. Reasoning belongs at AGGREGATION, not at per-claim severity grading. The
     per-claim adjudicator is unreliable about severity (it grades restatement
     typos SEVERE); we do NOT re-grade findings here. We reason about RELEVANCE
     and WEIGHT over the already-graded findings.
  2. The judgment must be auditable: every driver is cited by claim_id and every
     dismissed SEVERE refute is explained, so a human can check the call was not
     rationalized either way.

BLIND: this module reads prediction.json + the catalyst spec only. It must NEVER
open _sealed_outcomes.json — scoring of the reasoned call lives in score.py.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from .catalyst_spec import CASES, CatalystCase, DATA_DIR

# Reasoned call -> predicted catalyst label. EXCLUDE/ELEVATED both predict the
# program will disappoint (the thesis is exclusion); CLEAN predicts HIT-consistent
# (an honest readout — which can be a real HIT or an honestly-disclosed MISS).
ADJ_CALL_TO_PRED = {"EXCLUDE": "MISS", "ELEVATED": "MISS", "CLEAN": "HIT"}


def _parse_json_object(raw: str) -> dict:
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    s, e = raw.find("{"), raw.rfind("}")
    if s == -1 or e == -1 or e < s:
        return {}
    try:
        return json.loads(raw[s:e + 1])
    except json.JSONDecodeError:
        return {}


_RUBRIC = """\
You are a buy-side biotech analyst. A binary catalyst (a trial topline readout) is
imminent for the program below. You do NOT know the outcome. Your job is to judge,
from the company's PRE-catalyst marketing, whether that marketing is MASKING a
likely clinical MISS on THIS specific catalyst trial — i.e. whether an
honesty-aware analyst would EXCLUDE this name from a long basket going into the
print.

You are handed a table of FINDINGS already adjudicated by a verification library:
each is a marketing claim (R) checked against an authoritative as-of-cutoff source
(M) via a method (f), with a verdict and severity. Do NOT re-grade the verdicts or
severities — trust them. Reason about which findings are MATERIAL to THIS
catalyst, and what they collectively imply.

Decision principles (apply them; they encode hard-won precision lessons):

1. COMPANY-LEVEL HONESTY TRANSFERS ACROSS PROGRAMS. An authoritative finding that
   the company previously deceived investors about clinical data (SEC/DOJ
   settlement, securities-fraud finding, journal retraction, misconduct finding)
   is a tell about the SPONSOR's truthfulness. It weighs toward EXCLUDE even if it
   concerns a DIFFERENT molecule than the catalyst — a company that lied about
   drug A is a higher prior to be masking drug B.

2. TRIAL-SPECIFIC FINDINGS ONLY COUNT IF THEY ARE ABOUT THE CATALYST TRIAL.
   Efficacy-magnitude overreach, endpoint-construct manipulation, enrollment or
   timeline masking, venue inconsistency — these are claims about a PARTICULAR
   trial's data. If the underlying claim describes a DIFFERENT program or
   indication than the catalyst (e.g. a Phase 2 in lung cancer when the catalyst
   is a Phase 3 in prostate cancer), it does NOT bear on whether THIS readout is
   masked. Dismiss it (state why).

3. NORMAL EARLY-STAGE IR IS NOT MASKING. Touting uncontrolled / open-label / single
   -arm data with reasonable context is standard biotech promotion. When the
   catalyst trial is itself a randomized controlled pivotal, citing open-label
   extension or earlier-phase data alongside it is supporting color, not a
   misrepresentation of the catalyst's basis.

4. RESTATEMENTS ARE NOT MANIPULATION. A timepoint reword (Week 5 vs Week 6), a
   rounding (21.5h ~ 24h), a "percentage" vs "number" phrasing, or a synonym for
   the same endpoint construct is not a tell.

Calls:
  EXCLUDE  — the marketing materially masks a likely miss on this catalyst (a
             company-honesty tell per #1, or genuine catalyst-trial masking per #2).
  ELEVATED — a real, non-dismissed concern about the catalyst trial that is not
             decisive on its own (e.g. a single moderate masking signal).
  CLEAN    — no material masking detected. Consistent with an HONEST readout. Note:
             an honest company that simply fails is CLEAN — you are detecting
             lying, not forecasting biology.

Output STRICT JSON (no prose outside it):
{
  "call": "EXCLUDE" | "ELEVATED" | "CLEAN",
  "drivers": [ {"claim_id": "...", "channel": "...", "why_material": "..."} ],
  "dismissed": [ {"claim_id": "...", "why_not_material": "..."} ],
  "analyst_note": "2-5 sentence note for an institutional analyst. Justify the call
     by referencing the material findings in plain R / f(M) / Finding terms (claim,
     what was checked against which authority, what was found). If you set aside any
     SEVERE refute, say so and why. No framework jargon, no claim_ids in the prose."
}
Only list as "drivers" the findings that actually move your call. Put every SEVERE
refute you decline to act on into "dismissed" with a reason."""


_NCT_RE = re.compile(r"NCT\d{8}")


def _is_artifact_binding(f: dict, case: CatalystCase, _cache: dict) -> bool:
    """True if a finding's subject NCT was assigned by the extractor but never
    appears in the company's source text — an extraction-artifact binding, not a
    company claim.

    Why this guard exists: on ADCT/LOTIS-5 the extractor stamped subject=
    NCT05635266 (a 20,000-pt observational biospecimen registry) onto a press
    release that names NO NCT and plainly reports real LOTIS-7 Phase 1b data. The
    venue/marketing rules then compared the marketed 'Phase 1b' against that
    observational registry and emitted a 'fabricated trial design' REFUTE, which
    the adjudicator escalated to a company-level EXCLUDE under principle #1. The
    company fabricated nothing; the NCT mismatch is an extraction artifact. Per the
    asymmetric-error rule, a misbound NCT can only manufacture false REFUTEs, so we
    suppress these before reasoning. A genuine different-trial finding survives —
    its NCT is one the company itself named in the source."""
    subj = (f.get("subject") or "").strip()
    if not _NCT_RE.fullmatch(subj):
        return False  # not an NCT-keyed finding; nothing to corroborate
    if subj in case.nct_ids:
        return False  # the bound catalyst trial
    doc = f.get("R_source_doc") or ""
    if doc not in _cache:
        p = DATA_DIR / doc
        try:
            _cache[doc] = p.read_text(errors="ignore")
        except OSError:
            _cache[doc] = ""
    return subj not in _cache[doc]  # company never wrote this NCT -> artifact


def _findings_for_prompt(pred: dict, case: CatalystCase) -> tuple[str, int, int, int]:
    """Render REFUTED findings as a compact table; summarize the rest by count."""
    _cache: dict = {}
    all_refuted = [f for f in pred["findings"] if f["verdict"] == "REFUTED"]
    refuted = [f for f in all_refuted if not _is_artifact_binding(f, case, _cache)]
    n_artifact = len(all_refuted) - len(refuted)
    # Most-severe first so the reasoning sees the load-bearing claims early.
    order = {"critical": 0, "severe": 1, "moderate": 2, "minor": 3}
    refuted.sort(key=lambda f: order.get(f["severity"].lower(), 9))
    lines = []
    for f in refuted:
        lines.append(
            f"- claim_id={f['claim_id']} | channel={f['channel']} | "
            f"severity={f['severity']}\n"
            f"    R (claim): \"{(f['R_source_quote'] or '')[:240]}\"\n"
            f"    R source doc: {Path(f['R_source_doc']).name}\n"
            f"    f (method): {(f['f_method'] or '')[:300]}\n"
            f"    M (source): {f['m_source']}\n"
            f"    Finding: REFUTED ({f['severity']}) — {(f.get('rationale') or '')[:400]}")
    vc = pred["summary"].get("verdict_counts", {})
    return ("\n".join(lines) or "(no refuted findings)",
            vc.get("AFFIRMED", 0), vc.get("UNVERIFIABLE", 0), n_artifact)


def _build_prompt(case: CatalystCase, pred: dict) -> str:
    table, n_aff, n_unv, _ = _findings_for_prompt(pred, case)
    prov = pred.get("m_bundle_provenance", {}).get("ctgov", {})
    design = "; ".join(
        f"{nct}: primary_changed={rec.get('primary_endpoint_changed')}, "
        f"completion_slipped={rec.get('primary_completion_slipped')}"
        for nct, rec in prov.items()) or "(no registry provenance)"
    return f"""{_RUBRIC}

================ CATALYST (blind context) ================
Company:    {case.company} ({case.ticker})
Program:    {case.program}
Indication: {case.indication}
Catalyst:   {case.catalyst_type}
Trial NCT:  {', '.join(case.nct_ids)}
Cutoff:     {case.cutoff}
Registry provenance (catalyst trial, as-of cutoff): {design}

The findings below were extracted from this company's marketing exhibits filed
BEFORE the cutoff. A finding's "R source doc" is the press-release exhibit the
claim came from. Use the claim text + indication to judge whether each finding is
about the CATALYST trial/program above or some OTHER program.

================ FINDINGS (REFUTED; do not re-grade) ================
{table}

(Also adjudicated but not shown: {n_aff} AFFIRMED, {n_unv} UNVERIFIABLE.)

Now produce the JSON judgment."""


# Endpoint-emphasis / slot-substitution channels. A driver on one of these is only
# masking if the marketing presents a SECONDARY endpoint AS the primary. When the
# marketing ACCURATELY labels it "secondary" (a pre-specified, often alpha-allocated
# key secondary), that is honest disclosure of a hierarchical endpoint, NOT masking.
# We do NOT suppress it (it is a real microstructure tell about endpoint difficulty) —
# we RECLASSIFY it from a verdict driver into review_flags for an agent to weigh.
_ENDPOINT_FLAG_KEYS = ("endpoint", "slot")


def _claim_quotes(case: CatalystCase) -> dict:
    """claim_id -> source_quote, for review-flag reclassification."""
    p = DATA_DIR / case.case_id / "claims.json"
    if not p.exists():
        return {}
    raw = json.loads(p.read_text())
    cl = raw if isinstance(raw, list) else raw.get("claims", [])
    return {c.get("claim_id"): (c.get("source_quote") or "") for c in cl}


def _is_secondary_emphasis_flag(driver: dict, quotes: dict) -> bool:
    """True if an endpoint-emphasis/slot-substitution driver cites marketing that
    ACCURATELY calls the endpoint a 'secondary' — honest hierarchical-endpoint
    disclosure, not masking. RARE/GTX-102 Aspire: the MDRI is the registered 10%-alpha
    key SECONDARY; the adjudicator misread 'key secondary endpoint' as 'key endpoint'
    and over-elevated. Surface as a review flag, not a verdict driver."""
    ch = (driver.get("channel") or "").lower()
    if not any(k in ch for k in _ENDPOINT_FLAG_KEYS):
        return False
    quote = (quotes.get(driver.get("claim_id")) or "").lower()
    return "secondary" in quote


def _enrich_flag(case: CatalystCase, quote: str, llm) -> str:
    """Add VERDICT-NEUTRAL microstructure intelligence to a review flag. Decoupling the
    verdict axis from the intelligence axis: a flag does NOT drive EXCLUDE, but it still
    earns *more analysis* after it is raised (otherwise 'flag for agent review' is inert).
    This pass never recommends exclusion — it only reads what the disclosed design choice
    implies for the catalyst PoS, feeding the analyst note / microstructure KG."""
    prompt = (
        "You are adding VERDICT-NEUTRAL microstructure intelligence to a FLAGGED (not "
        "excluded) catalyst finding. The marketing is honest disclosure of a "
        "pre-specified SECONDARY endpoint; this does NOT change the honesty verdict and "
        "you must NOT recommend exclusion.\n\n"
        f"Company/program: {case.company} - {case.program}\n"
        f"Indication: {case.indication}\n"
        f"Catalyst trial(s): {', '.join(case.nct_ids)}\n"
        f"Flagged marketing quote: \"{quote}\"\n\n"
        "In 2-4 sentences for an institutional analyst: what does the sponsor's emphasis "
        "on (and alpha-allocation to) this secondary endpoint imply about confidence in "
        "the PRIMARY endpoint, and which DIRECTION (and rough magnitude) should it nudge "
        "the probability-of-success read for the catalyst? Be concrete; do not restate "
        "that it is honest; do not recommend exclusion."
    )
    try:
        return (llm(prompt) or "").strip()
    except Exception as exc:  # enrichment is best-effort; never block the verdict
        return f"(enrichment unavailable: {exc})"


def adjudicate_case(case: CatalystCase, llm, *, verbose: bool = True) -> dict:
    pred_path = DATA_DIR / case.case_id / "prediction.json"
    if not pred_path.exists():
        raise FileNotFoundError(f"no prediction for {case.ticker}; run evaluate first")
    pred = json.loads(pred_path.read_text())

    # Pipeline ordering: the verification stage can block a case whose catalyst M is
    # mis-bound (REBIND_REQUIRED). Every finding is then a comparison against the
    # wrong registry, so we must NOT reason a verdict over them — adjudicating
    # anyway emits EXCLUDE/ELEVATED calls built on poisoned M (the bug that produced
    # spurious verdicts for 8 names). Short-circuit to an explicit BLOCKED record.
    summ = pred.get("summary", {})
    gate_call = summ.get("call", "")
    if summ.get("rebind_needed") or str(gate_call).startswith("REBIND_REQUIRED"):
        out = {
            "case_id": case.case_id, "ticker": case.ticker,
            "call": "BLOCKED", "predicted": None,
            "blocked_reason": "rebind_required",
            "drivers": [], "dismissed": [],
            "analyst_note": (
                "Adjudication suppressed. The verification stage flagged the "
                "catalyst trial M-binding as mis-bound (REBIND_REQUIRED): the "
                "findings compare marketing against the wrong registry, so no "
                "HIT/MISS verdict is emitted. Resolve the trial binding "
                "(see verification.json rebind_hints) and re-run."),
            "gate_call": gate_call,
        }
        (DATA_DIR / case.case_id / "adjudication.json").write_text(
            json.dumps(out, indent=2, default=str))
        if verbose:
            print(f"[{case.ticker}] BLOCKED — rebind required; adjudication suppressed",
                  file=sys.stderr)
        return out

    _, _, _, n_artifact = _findings_for_prompt(pred, case)
    if verbose and n_artifact:
        print(f"[{case.ticker}] suppressed {n_artifact} extraction-artifact "
              f"REFUTE(s) (subject NCT absent from source) before reasoning",
              file=sys.stderr)
    prompt = _build_prompt(case, pred)
    raw = llm(prompt)
    obj = _parse_json_object(raw)
    call = (obj.get("call") or "").upper()
    if call not in ADJ_CALL_TO_PRED:
        call = "CLEAN"  # default to no-exclude if the model returns garbage

    # Reclassify accurately-labeled-secondary endpoint emphasis out of the verdict
    # path: it is surfaced for agent review, not penalized as masking. If the call was
    # driven SOLELY by such flags, it reverts to CLEAN.
    quotes = _claim_quotes(case)
    drivers, review_flags = [], []
    for d in obj.get("drivers", []):
        (review_flags if _is_secondary_emphasis_flag(d, quotes) else drivers).append(d)
    for f in review_flags:
        f.setdefault("flag_reason",
                     "marketing accurately labels this a pre-specified SECONDARY "
                     "endpoint — microstructure tell about endpoint difficulty, not "
                     "masking; surfaced for agent review, not a verdict driver")
        # Intelligence axis (decoupled from the verdict): a flag still earns MORE
        # analysis, routed to the analyst note / KG rather than the EXCLUDE call.
        f["flag_intelligence"] = _enrich_flag(case, quotes.get(f.get("claim_id"), ""), llm)
    if review_flags and not drivers and call in ("ELEVATED", "EXCLUDE"):
        call = "CLEAN"

    out = {
        "case_id": case.case_id,
        "ticker": case.ticker,
        "call": call,
        "predicted": ADJ_CALL_TO_PRED[call],
        "drivers": drivers,
        "review_flags": review_flags,
        "dismissed": obj.get("dismissed", []),
        "analyst_note": obj.get("analyst_note", ""),
        "gate_call": pred["summary"]["call"],  # what the deterministic gate said
    }
    if verbose and review_flags:
        print(f"[{case.ticker}] reclassified {len(review_flags)} endpoint-emphasis "
              f"driver(s) (accurately-labeled secondary) -> review_flags",
              file=sys.stderr)
    out_path = DATA_DIR / case.case_id / "adjudication.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    if verbose:
        print(f"[{case.ticker}] reasoned={call} (gate={out['gate_call']}) "
              f"drivers={len(out['drivers'])} -> {out_path}", file=sys.stderr)
    return out


if __name__ == "__main__":
    import argparse
    from .extract_claims import get_llm

    ap = argparse.ArgumentParser()
    ap.add_argument("case_ids", nargs="*", help="case ids (default: all with predictions)")
    ap.add_argument("--force", action="store_true",
                    help="re-adjudicate even if adjudication.json exists")
    args = ap.parse_args()
    llm = get_llm()
    ids = args.case_ids or [
        cid for cid in CASES
        if (DATA_DIR / cid / "prediction.json").exists()]
    for cid in ids:
        if not args.force and (DATA_DIR / cid / "adjudication.json").exists():
            print(f"[{CASES[cid].ticker}] skip — already adjudicated", file=sys.stderr)
            continue
        try:
            adjudicate_case(CASES[cid], llm)
        except Exception as ex:
            print(f"  ADJUDICATE FAIL {cid}: {ex}", file=sys.stderr)
