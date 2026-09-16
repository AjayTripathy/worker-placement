"""Stage 3.25 (biotech): escalate the load-bearing findings to a context-rich,
higher-intelligence verification pass BEFORE they reach the reasoning adjudicator.

Why this stage exists
---------------------
`evaluate` is a cheap, high-recall first pass: it batches ~20 claims per call
against a compact M slice. That is the right economics for 50+ claims per case,
but it is structurally blind to two failure modes that produce the project's
false positives:

  1. DROPPED CONTEXT. Claim extraction severs a quote from the slide/table that
     frames it. The SLNO false positive flagged a "Primary Endpoint" table that
     the *same exhibit* explicitly headed "C601 — data through 2020, p=0.198" and
     disclosed as a miss two slides later. The first pass never saw the frame.

  2. MIS-BOUND M. If a case is wired to the wrong NCT, every comparison against
     that registry is an artifact. The AVIR false positive compared HCV marketing
     (SVR12 / 275 pts / Phase 2) against NCT05629962 — which is SUNRISE-3, a
     COVID-19 Phase 3 (hospitalization-or-death / 2,285 pts). The first pass and
     the adjudicator both read the divergence as the company lying, when the truth
     was that *we* bound the wrong trial.

The cure is not more guards on the cheap pass. It is to spend more intelligence,
with a fatter context window, ON THE FEW FINDINGS THAT ACTUALLY DECIDE THE CALL.
Leverage, not volume: a case has ~50 claims but only 0-4 severe refutes, and only
those can flip an EXCLUDE. We re-read each one's full source exhibit and re-check
its M binding, and let it exit through several legitimate verdicts — including
"this finding is withdrawn" and "M was bound to the wrong trial".

Guardrail (the MNPR/NMRA lesson): this stage must be allowed to REMOVE the only
signal. An honest company that simply fails biology has no marketing tell; if
every severe refute withdraws, the case correctly collapses to CLEAN. The prompt
forbids upgrading severity or manufacturing a tell to justify the escalation cost
— CONFIRMED requires citing the contradicting authority text, not absence of it.

BLIND: reads prediction.json + the pre-cutoff corpus exhibits + CT.gov as-of
cutoff only. It must NEVER open _sealed_outcomes.json.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from .catalyst_spec import CASES, CatalystCase, DATA_DIR
from .m_asof import fetch_trial_asof

# Verdicts a re-verified finding can exit through. Each maps to a concrete
# downstream effect on the finding's weight in the adjudicator's table.
VERDICTS = {
    # Full context + correct binding still show the catalyst's success-basis being
    # misrepresented. The finding stays REFUTED and load-bearing.
    "CONFIRMED",
    # Restored exhibit context makes the quote benign — the "masked" fact is
    # actually disclosed/contextualized in the same document. Neutralize.
    "FINDING_WITHDRAWN",
    # The claim's trial IDENTITY (indication / phase / endpoint family / enrollment
    # magnitude) diverges from the bound registry on multiple independent axes ->
    # we compared against the wrong NCT. Neutralize + flag the case for rebinding.
    "M_MISBOUND",
    # A real registry construct/endpoint change that the exhibit ITSELF discloses
    # and explains (protocol evolution, not concealment). Demote from decisive.
    "BENIGN_DISCLOSED_CHANGE",
    # The bound M is insufficient or stale to confirm or refute (e.g. registry
    # enrollment estimate not yet updated). Mark UNVERIFIABLE, never decisive.
    "NEEDS_MORE_M",
    # The claim states a PROGRAM/MULTI-TRIAL aggregate count (e.g. total patients
    # across two pivotal trials) but the bound M is ONE trial's enrollment, so the
    # "discrepancy" is just trials summed. Category error, not a lie — neutralize.
    "M_AGGREGATE_MISMATCH",
}

# What each verdict does to the finding when we amend the prediction. CONFIRMED
# keeps it; everything else removes it from the REFUTED set the adjudicator weighs.
_NEUTRALIZE = {"FINDING_WITHDRAWN", "M_MISBOUND", "NEEDS_MORE_M",
               "M_AGGREGATE_MISMATCH"}
_DEMOTE = {"BENIGN_DISCLOSED_CHANGE"}

# Only findings this severe are load-bearing enough to merit an escalation call.
# A minor/moderate refute cannot flip an EXCLUDE on its own; spending an expensive
# context-rich call on it is the volume trap this stage exists to avoid.
_LOAD_BEARING_SEVERITY = {"severe", "critical"}

# Program-aggregate enrollment conflation (CLDX: 1,939 across two EMBARQ trials
# refuted against one trial's 976) lands at MODERATE severity — below the severe+
# gate — yet the reasoning adjudicator weighs it and can wrongly EXCLUDE. So we
# also escalate a NARROW lower-severity class: REFUTED count/enrollment claims
# whose quote carries multi-trial aggregate language. Typically 0-1 per case.
_AGG_MARKER_RE = re.compile(
    r"\b(?:across\s+(?:both|all|the\s+two|the\s+three)"
    r"|both\s+(?:pivotal\s+)?(?:phase\s*\d+\s+)?(?:trials|studies)"
    r"|two\s+(?:pivotal\s+)?(?:phase\s*\d+\s+)?(?:trials|studies)"
    r"|(?:the\s+)?(?:phase\s*\d+\s+)?program\s+(?:enrolled|consists|comprises|includes|of)"
    r"|combined\s+enrollment|largest\s+program|across\s+the\s+program)\b", re.I)
_PATIENT_CTX_RE = re.compile(r"\b(?:patients?|subjects?|enroll(?:ed|ment)?|randomi[sz]ed)\b", re.I)


def _is_conflation_candidate(f: dict) -> bool:
    """A lower-severity REFUTE that looks like a program/multi-trial count compared
    against one trial's registry — worth an escalation call despite not being severe."""
    if f.get("verdict") != "REFUTED":
        return False
    q = str(f.get("R_source_quote") or "")
    numeric = bool(re.search(r"\d", str(f.get("R_object_value") or "")))
    return numeric and bool(_PATIENT_CTX_RE.search(q)) and bool(_AGG_MARKER_RE.search(q))

# The whole point of escalation is MORE intelligence on the decisive findings: the
# first pass batches claims through Sonnet; here we spend Opus on the few findings
# that flip the call. Scaling cost with decision-weight is the design — ~0-4 calls
# per case, not ~50.
ESCALATION_MODEL = "claude-opus-4-7"


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


def _exhibit_context(finding: dict, *, window: int = 1600) -> str:
    """Restore the dropped frame: the full-exhibit text AROUND the flagged quote.

    The cheap pass saw only `R_source_quote`. Here we re-open the exhibit named in
    `R_source_doc` and return a generous window centred on the quote, so the
    verifier can see the table header / disclosure / caption that contextualizes it
    (the SLNO 'C601 — p=0.198' frame the extractor severed)."""
    doc = finding.get("R_source_doc")
    if not doc:
        return "(no source doc recorded)"
    path = DATA_DIR / doc
    if not path.exists():
        return f"(source exhibit not found on disk: {doc})"
    text = path.read_text(errors="replace")
    quote = (finding.get("R_source_quote") or "").strip()
    idx = text.find(quote[:80]) if quote else -1
    if idx == -1:
        # quote not locatable verbatim; give the document head as fallback context
        body = re.sub(r"\s+", " ", text[:window * 2]).strip()
        return f"[quote not located verbatim; showing exhibit head]\n{body}"
    a, b = max(0, idx - window), idx + len(quote) + window
    framed = text[a:idx] + "\n>>> FLAGGED CLAIM >>> " + text[idx:idx + len(quote)] + \
        " <<<\n" + text[idx + len(quote):b]
    return re.sub(r"[ \t]+", " ", framed).strip()


def _registry_card(nct: str, rec: dict) -> str:
    """Compact human-legible registry card for the bound catalyst NCT."""
    if rec.get("error"):
        return f"  {nct}: (registry unavailable: {rec['error']})"
    s = rec.get("snapshot", {})
    pos = "; ".join(f"{p.get('measure')} [{p.get('timeFrame')}]"
                    for p in s.get("primary_outcomes", [])) or "(none)"
    return (
        f"  {nct} (registry as of {rec.get('asof_version_date')}):\n"
        f"    phases:            {s.get('phases')}\n"
        f"    enrollment:        {s.get('enrollment')} ({s.get('enrollment_type')})\n"
        f"    allocation/mask:   {s.get('allocation')} / {s.get('masking')}\n"
        f"    overall_status:    {s.get('overall_status')}\n"
        f"    PRIMARY outcome(s):{pos}\n"
        f"    primary construct changed (history): "
        f"{rec.get('catalyst_primary_construct_changed')}; "
        f"any primary text changed: {rec.get('primary_endpoint_changed')}")


_VERIFY_RUBRIC = """\
You are a senior buy-side biotech analyst doing a SECOND, deeper pass on a SINGLE
finding that is currently load-bearing for a recommendation to EXCLUDE a name from
a long basket ahead of a binary catalyst. A cheap first pass flagged it; you have
more context and more time. Your job is to decide whether it survives scrutiny.

You do NOT know the trial outcome. You are detecting whether the company's PRE-
catalyst marketing MASKS a likely miss on THIS catalyst trial — not forecasting
biology. An honest company that simply fails has no tell; if this finding does not
hold up, say so plainly. Do NOT invent a concern to justify the flag.

Return STRICT JSON, exactly one verdict from this set:

  CONFIRMED — with full exhibit context AND the correct registry, the marketing
     genuinely places a non-primary / over-reached / contradicted basis into the
     success-determining slot for THIS catalyst. You MUST quote the specific
     authority text (registry primary, integrity finding) that contradicts the
     claim. Absence of evidence is NOT confirmation.

  FINDING_WITHDRAWN — the restored exhibit context shows the flagged fact is
     actually DISCLOSED / contextualized in the same document (e.g. the "primary
     endpoint" table is explicitly a PRIOR trial's data labelled as a miss; the
     number carries a caveat the extracted quote dropped). The first pass severed
     the frame. This is transparency, not masking.

  M_MISBOUND — the claim's TRIAL IDENTITY diverges from the bound registry on
     MULTIPLE INDEPENDENT AXES: indication/disease, phase, primary-endpoint FAMILY
     (e.g. virologic cure vs hospitalization/death), and enrollment ORDER OF
     MAGNITUDE. A genuine lie diverges on ONE axis while AGREEING on trial identity
     (same disease, same phase, same population) — the company misstates a detail
     of the RIGHT trial. When two or more identity axes disagree, the registry
     almost certainly describes a DIFFERENT trial than the claim — we bound the
     wrong NCT. Prefer M_MISBOUND over CONFIRMED in that case, and propose the
     correct trial's identity (disease + phase + endpoint) in `rebind_hint`.

  BENIGN_DISCLOSED_CHANGE — the registry shows a real primary-endpoint/construct
     change, but the exhibit ITSELF discloses and explains the protocol evolution
     (e.g. an earlier study missed, so a new pivotal with a revised endpoint was
     run, and the marketing says so). Real change, openly disclosed -> not masking.

  NEEDS_MORE_M — the bound registry is insufficient or stale to confirm or refute
     (e.g. a registered enrollment estimate not yet updated to actual; the relevant
     field absent). Do not guess; mark unverifiable.

  M_AGGREGATE_MISMATCH — the claim states a PROGRAM-level or MULTI-TRIAL aggregate
     count (e.g. "1,939 patients across both pivotal trials", "the program enrolled
     N"), but the bound M is a SINGLE trial's enrollment. The apparent inflation is
     just multiple trials summed vs one trial — a category error, not a lie. Use
     this whenever a count claim spans more than one trial yet was scored against
     one trial's registered number. (If the claim is about a single trial and the
     number genuinely contradicts that trial's registry, that is CONFIRMED instead.)

Output:
{
  "verdict": "<one of the six>",
  "confidence": "high" | "medium" | "low",
  "evidence": "1-3 sentences. For CONFIRMED quote the contradicting authority text.
     For M_MISBOUND name the >=2 axes that diverge. For FINDING_WITHDRAWN quote the
     contextualizing text from the exhibit. Plain analyst language, no jargon.",
  "rebind_hint": "only if M_MISBOUND: disease + phase + primary endpoint the claim
     actually describes, so the trial can be re-identified. else null"
}"""


def _build_prompt(case: CatalystCase, finding: dict, context: str,
                  cards: str) -> str:
    return f"""{_VERIFY_RUBRIC}

================ CATALYST (blind context) ================
Company:    {case.company} ({case.ticker})
Program:    {case.program}
Indication: {case.indication}
Catalyst:   {case.catalyst_type}
Bound NCT:  {', '.join(case.nct_ids)}
Cutoff:     {case.cutoff}

================ BOUND REGISTRY (M) — catalyst trial(s) as of cutoff ============
{cards}

================ THE FINDING UNDER RE-VERIFICATION ================
channel:           {finding['channel']}
severity (1st pass): {finding['severity']}
claim subject:     {finding.get('subject')}
claim value:       {finding.get('R_object_value')}
1st-pass rationale: {finding.get('rationale')}
M evidence cited:  {finding.get('m_evidence')}

================ RESTORED EXHIBIT CONTEXT (around the flagged claim) ============
source exhibit: {Path(finding['R_source_doc']).name}
---
{context[:9000]}
---

Now produce the JSON verdict."""


def verify_case(case: CatalystCase, llm, *, model: str = ESCALATION_MODEL,
                verbose: bool = True) -> dict:
    """Re-verify the load-bearing (severe+) REFUTED findings of one case.

    Writes verification.json, and amends prediction.json in place: neutralized
    findings have their verdict rewritten to UNVERIFIABLE (with a verify_* trail),
    demoted findings are annotated, and the summary is re-aggregated from the
    surviving set. The PRE-verify findings + summary are preserved under
    `findings_pre_verify` / `summary_pre_verify` for audit. Returns the
    verification record.
    """
    pred_path = DATA_DIR / case.case_id / "prediction.json"
    if not pred_path.exists():
        raise FileNotFoundError(f"no prediction for {case.ticker}; run evaluate first")
    pred = json.loads(pred_path.read_text())

    load_bearing = [
        f for f in pred["findings"]
        if f["verdict"] == "REFUTED"
        and (f["severity"].lower() in _LOAD_BEARING_SEVERITY
             or _is_conflation_candidate(f))]

    # Pre-fetch a registry card for every catalyst NCT once (not per finding).
    cards = "\n".join(
        _registry_card(nct, fetch_trial_asof(nct, case.cutoff, verbose=False))
        for nct in case.nct_ids) or "  (no catalyst NCT bound)"

    results: list[dict] = []
    rebind_needed = False
    rebind_hints: list[str] = []
    for f in load_bearing:
        context = _exhibit_context(f)
        prompt = _build_prompt(case, f, context, cards)
        try:
            raw = llm(prompt, model=model)
        except TypeError:
            raw = llm(prompt)  # llm callable without a model kwarg
        obj = _parse_json_object(raw)
        verdict = (obj.get("verdict") or "").upper()
        if verdict not in VERDICTS:
            verdict = "NEEDS_MORE_M"  # conservative: don't act on a garbled verdict
        rec = {
            "claim_id": f["claim_id"],
            "channel": f["channel"],
            "original_verdict": f["verdict"],
            "original_severity": f["severity"],
            "verify_verdict": verdict,
            "confidence": obj.get("confidence"),
            "evidence": obj.get("evidence"),
            "rebind_hint": obj.get("rebind_hint"),
        }
        results.append(rec)
        if verdict == "M_MISBOUND":
            rebind_needed = True
            if obj.get("rebind_hint"):
                rebind_hints.append(obj["rebind_hint"])
        if verbose:
            print(f"  [{case.ticker}] {f['claim_id']} ({f['channel']}): "
                  f"{f['severity']} -> {verdict}", file=sys.stderr)

    verification = {
        "case_id": case.case_id,
        "ticker": case.ticker,
        "n_load_bearing": len(load_bearing),
        "rebind_needed": rebind_needed,
        "rebind_hints": rebind_hints,
        "results": results,
    }
    (DATA_DIR / case.case_id / "verification.json").write_text(
        json.dumps(verification, indent=2, default=str))

    _amend_prediction(case, pred, results, rebind_needed)
    if verbose:
        held = sum(1 for r in results if r["verify_verdict"] == "CONFIRMED")
        print(f"[{case.ticker}] verify: {len(load_bearing)} load-bearing, "
              f"{held} CONFIRMED, rebind_needed={rebind_needed}", file=sys.stderr)
    return verification


def _amend_prediction(case: CatalystCase, pred: dict, results: list[dict],
                      rebind_needed: bool) -> None:
    """Rewrite prediction.json from the verified findings (preserving the original).

    A finding the verifier neutralized has its verdict flipped to UNVERIFIABLE so it
    leaves the REFUTED set the adjudicator weighs; a demoted finding keeps REFUTED
    but is marked benign. When the case is mis-bound, every comparison against that
    registry is poisoned, so we block the call outright pending a rebind."""
    from .evaluate import _aggregate

    if "findings_pre_verify" not in pred:
        pred["findings_pre_verify"] = json.loads(json.dumps(pred["findings"]))
        pred["summary_pre_verify"] = json.loads(json.dumps(pred["summary"]))

    by_id = {r["claim_id"]: r for r in results}
    for f in pred["findings"]:
        r = by_id.get(f["claim_id"])
        if not r:
            continue
        v = r["verify_verdict"]
        f["verify_verdict"] = v
        f["verify_evidence"] = r.get("evidence")
        if v in _NEUTRALIZE:
            f["verdict"] = "UNVERIFIABLE"
            f["severity"] = "unverifiable"
        elif v in _DEMOTE:
            f["verify_demoted"] = True

    summary = _aggregate(case, pred["findings"])
    if rebind_needed:
        summary["call"] = "REBIND_REQUIRED (blocked — wrong NCT)"
        summary["rebind_needed"] = True
    summary["verified"] = True
    pred["summary"] = summary
    (DATA_DIR / case.case_id / "prediction.json").write_text(
        json.dumps(pred, indent=2, default=str))


if __name__ == "__main__":
    import argparse
    from .extract_claims import get_llm

    ap = argparse.ArgumentParser()
    ap.add_argument("case_ids", nargs="*", help="case ids (default: all with predictions)")
    args = ap.parse_args()
    llm = get_llm()
    ids = args.case_ids or [
        cid for cid in CASES
        if (DATA_DIR / cid / "prediction.json").exists()]
    for cid in ids:
        try:
            verify_case(CASES[cid], llm)
        except Exception as ex:
            print(f"  VERIFY FAIL {cid}: {ex}", file=sys.stderr)
