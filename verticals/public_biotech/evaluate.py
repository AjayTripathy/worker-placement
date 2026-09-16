"""Stage 3 (biotech): run each extracted claim (R) through its f-rule against M,
and aggregate the honesty gap into a directional catalyst call.

For each claim we look up the BioRule(s) its predicate routes to, assemble the M
evidence that rule needs (CT.gov registration/history reconstructed as-of cutoff;
disclosure-integrity signals mined from the pre-cutoff corpus), and ask the LLM to
adjudicate R against M per the rule's refutes_if / affirms_if criteria. The output
is a Finding per (claim, rule): AFFIRMED / REFUTED / UNVERIFIABLE + severity.

Thesis (honesty-alpha): the edge is EXCLUSION. We are not forecasting biology; we
are scoring how far a program's marketing diverges from the authoritative record.
A program whose pivotal evidence is open-label extrapolation, whose registered
primary drifts from the marketed one, or that carries an authoritative
disclosure-integrity finding, is a MISS candidate. A program whose marketed
endpoint matches a stable, controlled, registered primary is clean.

Blinding: this module never imports _sealed_outcomes.json. M is CT.gov as-of
cutoff (leakage-guarded in m_asof) + the pre-cutoff corpus. Predictions are
written to disk BEFORE any unblinding.
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict

from verticals.buyside_dd.schemas import Severity
from .catalyst_spec import CatalystCase, DATA_DIR
from .f_library_biotech import BioRule, rules_by_predicate
from .m_asof import fetch_trial_asof
from .science_corpus import load_science_corpus

# Channels whose M includes the science corpus (actual reported data behind the
# marketing) so they can CONFIRM/refute rather than abstain pre-readout.
_SCIENCE_CHANNELS = {"evidence_quality_overreach", "statistical_framing"}

# Which M bundle a rule's channel consumes.
_CTGOV_CHANNELS = {
    "endpoint_manipulation", "operational_masking", "statistical_framing",
    "evidence_quality_overreach", "safety_masking", "selective_disclosure",
    "regulatory_spin",
}
_INTEGRITY_CHANNELS = {"disclosure_integrity"}

_BATCH = 20  # claims per adjudication call (keeps each JSON response complete)

_INTEGRITY_RE = re.compile(
    r"\b(SEC|Securities and Exchange|settlement|settled|retraction|retracted|"
    r"expression of concern|misconduct|subpoena|investigation|fraud|"
    r"restate|class action|Department of Justice|DOJ|whistleblower)\b", re.I)

_SEVERITY_WEIGHT = {
    Severity.CRITICAL: 5.0, Severity.SEVERE: 4.0, Severity.MODERATE: 2.0,
    Severity.MINOR: 1.0, Severity.PASS: 0.0, Severity.UNVERIFIABLE: 0.0,
}


def _scan_corpus_integrity(case: CatalystCase, *, max_hits: int = 25) -> list[dict]:
    """Mine pre-cutoff corpus exhibits for disclosure-integrity language.

    The company's own 8-Ks around an SEC action / journal concern appear in the
    marketing corpus as item-8.01 exhibits; their presence (or absence) IS the M
    for the disclosure-integrity channel.
    """
    corpus_dir = DATA_DIR / case.case_id / "corpus"
    idx = corpus_dir / "corpus_index.json"
    if not idx.exists():
        return []
    hits: list[dict] = []
    for ex in json.loads(idx.read_text())["exhibits"]:
        path = DATA_DIR / ex["path"]
        try:
            text = path.read_text(errors="replace")
        except Exception:
            continue
        for m in _INTEGRITY_RE.finditer(text):
            a, b = max(0, m.start() - 160), m.end() + 160
            hits.append({
                "filing_date": ex["filing_date"],
                "exhibit": ex["exhibit"],
                "term": m.group(0),
                "snippet": re.sub(r"\s+", " ", text[a:b]).strip(),
            })
            if len(hits) >= max_hits:
                return hits
    return hits


_NCT_RE = re.compile(r"NCT\d{8}")


def _collect_ncts(case: CatalystCase, claims: list[dict]) -> list[str]:
    """All trials the claims actually reference — not just the catalyst NCT.

    Claims routinely cite SISTER trials (e.g. an open-label safety study). If we
    only fetch the catalyst trial's M, the adjudicator will (wrongly) compare a
    sister-trial claim against the catalyst trial's registration. Gather every
    NCT mentioned in claim scope/quote/value so each claim can be matched to its
    own trial's M.
    """
    ncts = set(case.nct_ids)
    for c in claims:
        blob = " ".join([
            str(c.get("source_quote", "")), str(c.get("object_value", "")),
            json.dumps(c.get("scope", {}), default=str),
        ])
        ncts.update(_NCT_RE.findall(blob))
    return sorted(ncts)


def build_m_bundle(case: CatalystCase, claims: list[dict], *, verbose: bool = True) -> dict:
    ncts = _collect_ncts(case, claims)
    ctgov = {nct: fetch_trial_asof(nct, case.cutoff, verbose=verbose) for nct in ncts}
    integrity = _scan_corpus_integrity(case)
    science = load_science_corpus(case)
    catalyst_design = {}
    for nct in case.nct_ids:
        snap = ctgov.get(nct, {}).get("snapshot", {})
        catalyst_design[nct] = {
            "allocation": snap.get("allocation"), "masking": snap.get("masking"),
            "intervention_model": snap.get("intervention_model"),
            "phases": snap.get("phases"),
        }
    if verbose:
        print(f"[{case.ticker}] M-bundle: {len(ctgov)} trials ({', '.join(ncts)}), "
              f"{len(integrity)} integrity snippets, {len(science)} science records",
              file=sys.stderr)
    return {"ctgov": ctgov, "corpus_integrity": integrity,
            "catalyst_ncts": list(case.nct_ids), "catalyst_design": catalyst_design,
            "science": science}


def _m_slice_for_rule(rule: BioRule, m: dict, case: CatalystCase) -> dict:
    if rule.channel in _INTEGRITY_CHANNELS:
        return {"corpus_integrity_signals": m["corpus_integrity"],
                "note": "Absence of any authoritative integrity finding through "
                        "cutoff = AFFIRMS (no adverse finding). Presence of an SEC/"
                        "journal/misconduct finding re THIS program's data = REFUTES."}
    if rule.channel in _CTGOV_CHANNELS:
        # Trial registration as-of cutoff is the M for design/endpoint/timeline/etc.
        # Includes ALL referenced trials + per-version timelines so the
        # adjudicator can (a) match each claim to its OWN trial and (b) compare
        # against the registered value as of the claim's filing date.
        trials = {}
        for nct, rec in m["ctgov"].items():
            snap = rec.get("snapshot", {})
            trials[nct] = {
                "asof_version_date": rec.get("asof_version_date"),
                "phases": snap.get("phases"),
                "allocation": snap.get("allocation"),
                "intervention_model": snap.get("intervention_model"),
                "masking": snap.get("masking"),
                "primary_outcomes": snap.get("primary_outcomes"),
                "secondary_outcomes": snap.get("secondary_outcomes"),
                "enrollment_asof_cutoff": snap.get("enrollment"),
                "overall_status": snap.get("overall_status"),
                "primary_endpoint_timeline": rec.get("primary_endpoint_timeline"),
                "primary_completion_timeline": rec.get("primary_completion_timeline"),
                "enrollment_timeline": rec.get("enrollment_timeline"),
                "error": rec.get("error"),
            }
        slice_ = {"registered_trials_asof_cutoff": trials,
                  "catalyst_trial_ids": m["catalyst_ncts"],
                  "catalyst_trial_design": m["catalyst_design"],
                  "indication": case.indication}
        if rule.channel in _SCIENCE_CHANNELS:
            slice_["scientific_sources_asof_cutoff"] = [
                {"date": r["date"], "journal": r.get("journal") or r.get("source"),
                 "title": r["title"], "url": r["url"],
                 "abstract": r.get("abstract"),
                 "results_excerpt": (r.get("fulltext_excerpt") or "")[:2500] or None}
                for r in m.get("science", [])
            ]
            slice_["science_note"] = (
                "These are the actual dated scientific reports behind the marketing. "
                "Refute when the claim EXCEEDS what these support (uncontrolled data "
                "marketed as efficacy; post-hoc/subgroup as headline; magnitude over "
                "the reported effect; number absent from all sources). If a claim's "
                "basis is not present here, it is UNVERIFIABLE, not refuted.")
        return slice_
    return {}


ADJUDICATION_PROMPT = """You are an honesty-validator adjudicating biotech marketing claims against an \
authoritative source, for a blinded backtest that predicts whether a clinical/regulatory CATALYST will HIT or MISS.

You judge ONE verification rule against a batch of marketing claims (R) that share its predicate.

RULE: {rule_id}  (channel: {channel})
  Verification method (f): {f_method}
  REFUTED if: {refutes_if}
  AFFIRMED if: {affirms_if}

AUTHORITATIVE SOURCE (M) — reconstructed as of the catalyst cutoff, nothing after:
{m_json}

CLAIMS (R) to adjudicate (each is a verbatim marketing assertion filed on/before cutoff):
{claims_json}

For EACH claim, return a verdict object:
- claim_id
- verdict: "REFUTED" | "AFFIRMED" | "UNVERIFIABLE"
- rationale: 1-2 sentences citing the specific M evidence (endpoint text, design field, date drift, integrity snippet). No hand-waving.
- m_evidence: the exact M field/value or snippet you relied on

ADJUDICATION DISCIPLINE — apply ALL of these (they prevent false REFUTES):

1. TRIAL IDENTITY. Each claim references a specific trial (by NCT or trial name in its quote/scope). Adjudicate it ONLY against THAT trial's registration in M. If the referenced trial is not present in M, return UNVERIFIABLE — NEVER compare a claim about one trial against a different trial's numbers.

2. TEMPORAL MATCH. M includes per-version TIMELINES (enrollment_timeline, primary_completion_timeline, primary_endpoint_timeline) with dates. Compare each claim against the registered value AS OF THE CLAIM'S FILING DATE (in its scope), not the cutoff snapshot. Trials legitimately expand enrollment (e.g. 900 → 2000) and adjust dates over time. A number that matched the registry when filed is consistent — do NOT refute it against a later value.

3. ABSENCE ≠ CONTRADICTION. Topline efficacy/safety RESULTS are not posted to CT.gov until AFTER the readout — so before the catalyst they are necessarily absent. A marketing number being absent from CT.gov results is EXPECTED → UNVERIFIABLE, never REFUTED. REFUTE on cross-venue only when two sources state materially DIFFERENT values for the SAME fact.

4. ENDPOINT: TWO INDEPENDENT AXES + SUCCESS-SLOT, NOT WORDING. Separate two axes that are NOT the same thing: (i) efficacy-vs-safety = what an endpoint MEASURES; (ii) primary-vs-secondary = its HIERARCHY SLOT (what the trial is powered/gated on). A SECONDARY endpoint can be a perfectly legitimate EFFICACY endpoint — a claim that merely names or describes a secondary efficacy endpoint is NOT masking. Do NOT refute "endpoint X is an efficacy endpoint" just because X is registered as a secondary.
   The masking signal is SLOT SUBSTITUTION: marketing places a NON-PRIMARY endpoint (secondary / post-hoc subgroup / biomarker) into the SUCCESS-DETERMINING slot — presenting it as the basis on which THIS catalyst succeeds or approval rests — displacing the registered primary that actually gates the catalyst. REFUTE (severe) for that.
   STAGGERED CO-PRIMARIES: a trial may register multiple co-primaries with DIFFERENT timeFrames serving DIFFERENT approval pathways (e.g. a near-term surrogate co-primary for accelerated approval + a long-horizon clinical-outcome co-primary for full approval). Match the catalyst to the co-primary whose timeFrame aligns with the readout. Emphasizing that near-term co-primary, and not reciting the years-away co-primary, is CORRECT scoping to the imminent event — AFFIRM, do NOT read the omission as a swap. Refute on over-reach ONLY if marketing claims the near-term surrogate delivers the benefit the registry ties to the LATER endpoint.
   CONSTRUCT NOT WORDING: `primary_endpoint_changed` and the timeline text-diffs flip on ANY edit including pure rephrasing — not evidence by themselves. A registry restating the SAME measured construct in different words is ADMINISTRATIVE. REFUTE (severe) on a real CONSTRUCT/TYPE change only: endpoint TYPE change (clinical->biomarker/surrogate, hard->soft), a different scale family, or a co-primary genuinely added/dropped — especially near readout. If the marketed success-basis endpoint is a registered primary whose timeFrame aligns with the catalyst, with construct intact, AFFIRM.
   TIMEFRAME / TIMEPOINT IS NOT CONSTRUCT: a difference in an endpoint's timeFrame or readout timepoint alone — e.g. marketing says "PANSS total at Week 6" while the registry says "PANSS total at Week 5", or "Day 28" vs "Week 4" — on an OTHERWISE-IDENTICAL measured construct is a marketing RESTATEMENT ERROR, not endpoint manipulation. Grade it UNVERIFIABLE (or MODERATE at most if clearly self-serving); NEVER severe. The masked-catalyst signal lives in WHAT is measured and WHICH slot it sits in, not in a one-week timepoint discrepancy.

5. CONTROLLED-PIVOTAL CONTEXT (open-label / evidence-quality rules). M gives the CATALYST trial's design (catalyst_trial_design). If the catalyst trial is randomized + masked (a controlled pivotal), then open-label / single-arm data CITED ABOUT A DIFFERENT cohort or supporting study is supporting color, NOT a substitute for the pivotal → UNVERIFIABLE, not REFUTED. REFUTE (severe) ONLY when uncontrolled/open-label data is presented as the PRIMARY efficacy basis for the catalyst itself AND the catalyst lacks a controlled comparison.

6. PROGRAM-AGGREGATE vs SINGLE-TRIAL COUNTS. Each claim carries `trial_scope`. If trial_scope is "program_aggregate" (a patient-enrollment, site, or country count that spans MULTIPLE trials / is a program total — e.g. "1,939 patients across both pivotal trials", "the program enrolled N"), you must NOT compare it against any one trial's registered enrollment. A single trial registers a SMALLER number, so the comparison manufactures false inflation (a ~2x "discrepancy" that is just two trials summed). Return UNVERIFIABLE unless M carries a matching PROGRAM-level aggregate (e.g. the two trials' registered enrollments SUM to the claimed total — that AFFIRMS). A single trial's registry enrollment NEVER REFUTES a stated multi-trial total. Likewise a "different_trial" claim is scored against THAT trial's record (via nct_refs), never the catalyst's.

GENERAL:
- UNVERIFIABLE is NOT clean, but it is NOT evidence of dishonesty either — use it whenever M neither corroborates nor contradicts.
- AFFIRMED requires positive corroboration in M.
- REFUTED requires M to actively contradict the claim per the rule's refutes_if AND survive disciplines 1-5.
- Do NOT speculate about the trial outcome. You score honesty/consistency vs the record, not biology.

Return ONLY a JSON array of verdict objects, no preamble."""


def _parse_json_array(raw: str) -> list[dict]:
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    s, e = raw.find("["), raw.rfind("]")
    if s == -1 or e == -1 or e < s:
        return []
    try:
        return [d for d in json.loads(raw[s:e + 1]) if isinstance(d, dict)]
    except json.JSONDecodeError:
        return []


# Program-aggregate language near a patient count: the deterministic tell that a
# stated number sums MULTIPLE trials (so it must not be refuted against one trial).
_AGG_MARKER_RE = re.compile(
    r"\b(?:across\s+(?:both|all|the\s+two|the\s+three)"
    r"|both\s+(?:pivotal\s+)?(?:phase\s*\d+\s+)?(?:trials|studies)"
    r"|two\s+(?:pivotal\s+)?(?:phase\s*\d+\s+)?(?:trials|studies)"
    r"|(?:the\s+)?(?:phase\s*\d+\s+)?program\s+(?:enrolled|consists|comprises|includes|of)"
    r"|combined\s+enrollment|largest\s+program|across\s+the\s+program)\b", re.I)
_PATIENT_CTX_RE = re.compile(r"\b(?:patients?|subjects?|enroll(?:ed|ment)?|randomi[sz]ed)\b", re.I)


def _is_program_aggregate_count(f: dict, scope: dict | None) -> bool:
    """True if a REFUTED count finding is a program/multi-trial total mis-compared
    against one trial's registry (the CLDX 1,939-across-two-EMBARQ-trials case)."""
    if scope:
        if scope.get("trial_scope") == "program_aggregate":
            return True
        if len(scope.get("nct_refs") or []) > 1:
            return True
    q = str(f.get("R_source_quote") or "")
    numeric = bool(re.search(r"\d", str(f.get("R_object_value") or "")))
    return numeric and bool(_PATIENT_CTX_RE.search(q)) and bool(_AGG_MARKER_RE.search(q))


def _neutralize_aggregate_conflations(findings: list[dict],
                                      claims_by_id: dict) -> int:
    """Flip single-trial-vs-program-aggregate count REFUTES to UNVERIFIABLE.

    Deterministic backstop to the extractor's `trial_scope` tag and adjudication
    discipline #6: a multi-trial/program total compared against one trial's
    registered enrollment is a category error, not a lie. Idempotent."""
    n = 0
    for f in findings:
        if f.get("verdict") != "REFUTED":
            continue
        scope = (claims_by_id.get(f.get("claim_id")) or {}).get("scope", {})
        if _is_program_aggregate_count(f, scope):
            f["verdict"] = "UNVERIFIABLE"
            f["severity"] = Severity.UNVERIFIABLE.value
            f["conflation_neutralized"] = (
                "program/multi-trial aggregate count is not refutable against a "
                "single trial's registered enrollment")
            n += 1
    return n


def evaluate_case(case: CatalystCase, llm, *, verbose: bool = True) -> dict:
    # Pre-flight: a mis-bound NCT poisons every M comparison (HCV marketing scored
    # against a COVID registry manufactures spurious SEVERE refutes). Refuse to
    # spend credits on a case whose binding fails the deterministic identity check.
    from .verify_binding import assert_binding
    assert_binding(case)

    claims_path = DATA_DIR / case.case_id / "claims.json"
    if not claims_path.exists():
        raise FileNotFoundError(f"no claims for {case.ticker}; run extract_claims first")
    claims = json.loads(claims_path.read_text())["claims"]
    by_pred: dict[str, list[dict]] = defaultdict(list)
    for c in claims:
        by_pred[c["predicate"]].append(c)

    m = build_m_bundle(case, claims, verbose=verbose)
    rules_idx = rules_by_predicate()

    findings: list[dict] = []
    for pred, pred_claims in by_pred.items():
        for rule in rules_idx.get(pred, []):
            m_slice = _m_slice_for_rule(rule, m, case)
            m_json = json.dumps(m_slice, indent=2, default=str)[:24000]
            # Batch claims so each adjudication call returns a COMPLETE, parseable
            # JSON array — truncating a 110-claim batch mid-array would silently
            # drop every verdict for that predicate.
            vmap: dict[str, dict] = {}
            for i in range(0, len(pred_claims), _BATCH):
                batch = pred_claims[i:i + _BATCH]
                claims_min = [{
                    "claim_id": c["claim_id"],
                    "subject": c["subject"],
                    "trial_scope": c.get("scope", {}).get("trial_scope", "single_trial"),
                    "nct_refs": c.get("scope", {}).get("nct_refs", []),
                    "object_value": c["object_value"],
                    "source_quote": c["source_quote"],
                    "scope": c.get("scope", {}),
                } for c in batch]
                prompt = ADJUDICATION_PROMPT.format(
                    rule_id=rule.rule_id, channel=rule.channel,
                    f_method=rule.f_method, refutes_if=rule.refutes_if,
                    affirms_if=rule.affirms_if, m_json=m_json,
                    claims_json=json.dumps(claims_min, indent=2, default=str),
                )
                try:
                    for v in _parse_json_array(llm(prompt)):
                        if v.get("claim_id"):
                            vmap[v["claim_id"]] = v
                except Exception as ex:
                    print(f"  ADJUDICATE FAIL {rule.rule_id} batch {i}: {ex}",
                          file=sys.stderr)
            for c in pred_claims:
                v = vmap.get(c["claim_id"])
                if not v:
                    continue
                verdict = (v.get("verdict") or "UNVERIFIABLE").upper()
                sev = rule.severity_if_refuted if verdict == "REFUTED" else (
                    Severity.PASS if verdict == "AFFIRMED" else Severity.UNVERIFIABLE)
                findings.append({
                    "claim_id": c["claim_id"],
                    "rule_id": rule.rule_id,
                    "channel": rule.channel,
                    "predicate": pred,
                    "subject": c["subject"],
                    "R_source_quote": c["source_quote"],
                    "R_object_value": c["object_value"],
                    "R_source_doc": c["source_doc"],
                    "f_method": rule.f_method,
                    "m_source": rule.m_source,
                    "verdict": verdict,
                    "severity": sev.value,
                    "rationale": v.get("rationale"),
                    "m_evidence": v.get("m_evidence"),
                })
            if verbose:
                vc = defaultdict(int)
                for c in pred_claims:
                    vv = vmap.get(c["claim_id"])
                    if vv:
                        vc[(vv.get("verdict") or "UNVERIFIABLE").upper()] += 1
                print(f"  {rule.rule_id}: {dict(vc)}", file=sys.stderr)

    # Deterministic per-claim trial-attribution guard: neutralize any REFUTE that
    # compares a program/multi-trial aggregate count against one trial's registry.
    claims_by_id = {c["claim_id"]: c for c in claims}
    n_conflation = _neutralize_aggregate_conflations(findings, claims_by_id)
    if verbose and n_conflation:
        print(f"  [{case.ticker}] neutralized {n_conflation} program-aggregate "
              f"count conflation(s)", file=sys.stderr)

    # Scope the endpoint-manipulation gate to the CATALYST trial(s) only, and use
    # the anchored-swap signal (a real success-slot construct substitution), NOT the
    # bundle-wide "any primary text changed" — a sister trial's registry edit, or a
    # mere rewording of THIS trial's primary, must not admit an endpoint-manipulation
    # finding to the decisive set.
    endpoint_construct_changed = any(
        bool(m["ctgov"].get(nct, {}).get("catalyst_primary_construct_changed"))
        for nct in case.nct_ids)
    catalyst_controlled = any(
        bool(m["ctgov"].get(nct, {}).get("controlled_pivotal"))
        for nct in case.nct_ids)
    summary = _aggregate(case, findings,
                         endpoint_construct_changed=endpoint_construct_changed,
                         catalyst_controlled=catalyst_controlled)
    out = {
        "case_id": case.case_id, "ticker": case.ticker, "cutoff": case.cutoff,
        "catalyst_type": case.catalyst_type,
        "m_bundle_provenance": {
            "ctgov": {nct: {k: rec.get(k) for k in
                            ("asof_version", "asof_version_date",
                             "n_versions_pre_cutoff", "primary_endpoint_changed",
                             "primary_completion_slipped", "error")}
                      for nct, rec in m["ctgov"].items()},
            "n_corpus_integrity_signals": len(m["corpus_integrity"]),
        },
        "summary": summary,
        "findings": findings,
    }
    out_path = DATA_DIR / case.case_id / "prediction.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    if verbose:
        print(f"[{case.ticker}] {len(findings)} findings -> {out_path}", file=sys.stderr)
        print(f"  CALL: {summary['call']}  gap={summary['honesty_gap_normalized']:.3f}  "
              f"decisive={len(summary['decisive_refutes_high_precision'])}  "
              f"REFUTED={summary['verdict_counts'].get('REFUTED',0)} "
              f"UNVERIFIABLE={summary['verdict_counts'].get('UNVERIFIABLE',0)} "
              f"AFFIRMED={summary['verdict_counts'].get('AFFIRMED',0)}", file=sys.stderr)
    return out


# Channels where a SEVERE refute is a genuine, high-precision masking signal —
# i.e. evidence the program is misrepresenting the basis for the catalyst, not
# just routine trial noise. The directional call hinges on these, not on raw
# counts of low-severity / high-base-rate refutes (timeline slippage, etc.).
_HIGH_PRECISION_CHANNELS = {
    "endpoint_manipulation", "evidence_quality_overreach", "disclosure_integrity",
}


def _aggregate(case: CatalystCase, findings: list[dict], *,
               endpoint_construct_changed: bool = False,
               catalyst_controlled: bool = False) -> dict:
    verdict_counts: dict[str, int] = defaultdict(int)
    channel_refutes: dict[str, int] = defaultdict(int)
    weighted = 0.0
    decisive_refutes: list[dict] = []   # SEVERE/CRITICAL in a high-precision channel
    other_severe: list[dict] = []
    n_adjudicated = len(findings)
    for f in findings:
        verdict_counts[f["verdict"]] += 1
        if f["verdict"] != "REFUTED":
            continue
        channel_refutes[f["channel"]] += 1
        sev = Severity(f["severity"])
        weighted += _SEVERITY_WEIGHT.get(sev, 0.0)
        if sev in (Severity.SEVERE, Severity.CRITICAL):
            entry = {"rule_id": f["rule_id"], "channel": f["channel"],
                     "claim_id": f["claim_id"], "rationale": f["rationale"],
                     "R": f["R_source_quote"][:200]}
            # An endpoint-manipulation SEVERE refute is admitted to the DECISIVE
            # set only when the registry version history corroborates a genuine
            # construct/type change of the success-slot primary. A marketing-vs-
            # registry mismatch with NO registry construct change (a timeFrame
            # restatement like Week-5-vs-6, a rewording, or a slot-description
            # quibble) is demoted to other_severe — still reported, but it cannot
            # trip the MISS gate on its own. This is the precision fix for the
            # KRTX false positive; it trades a little recall on slot-substitution-
            # only cases for not excluding HITs on restatement typos.
            # open_label_extrapolation is decisive ONLY when the catalyst readout
            # itself lacks a controlled comparison (single-arm/open-label is the
            # SOLE efficacy basis). When the catalyst trial is a randomized
            # controlled pivotal, citing open-label extension data alongside it is
            # normal supporting color, not masking — demote. This is the precision
            # fix for the MDGL/CYTK false-positive HITs (both ran controlled
            # pivotals + cited an open-label extension symmetrically).
            if (f["channel"] == "endpoint_manipulation"
                    and not endpoint_construct_changed):
                entry["demoted"] = "no_registry_construct_change"
                other_severe.append(entry)
            elif (f["rule_id"] == "bio.open_label_extrapolation"
                    and catalyst_controlled):
                entry["demoted"] = "catalyst_is_controlled_pivotal"
                other_severe.append(entry)
            elif f["channel"] in _HIGH_PRECISION_CHANNELS:
                decisive_refutes.append(entry)
            else:
                other_severe.append(entry)

    # Normalize the weighted gap by the number of claims adjudicated so a
    # claim-rich (verbose) program is not penalized for volume alone.
    honesty_gap = round(weighted / n_adjudicated, 3) if n_adjudicated else 0.0

    # Exclusion call is driven by GENUINE high-precision masking, not volume:
    #   ≥1 decisive (severe, high-precision) refute → MISS candidate
    #   else elevated only if many severe refutes cluster in other channels
    #   else clean / HIT-consistent.
    # A DEMOTED severe refute was deliberately ruled benign on THIS catalyst (no
    # registry construct change; or open-label cited alongside a controlled
    # pivotal). It is reported for diligence but must NOT count toward ELEVATED_RISK
    # — ELEVATED_RISK maps to a MISS/exclude prediction, so letting demoted findings
    # accumulate there would re-impose the very auto-exclusion the demotion removed.
    non_demoted_severe = [e for e in other_severe if not e.get("demoted")]
    if decisive_refutes:
        call = "MISS_CANDIDATE (EXCLUDE)"
    elif len(non_demoted_severe) >= 3:
        call = "ELEVATED_RISK"
    else:
        call = "CLEAN (HIT-consistent)"
    return {
        "call": call,
        "honesty_gap_normalized": honesty_gap,
        "n_findings": n_adjudicated,
        "verdict_counts": dict(verdict_counts),
        "refutes_by_channel": dict(channel_refutes),
        "decisive_refutes_high_precision": decisive_refutes,
        "other_severe_refutes": other_severe,
    }


if __name__ == "__main__":
    import argparse
    from .catalyst_spec import CASES
    from .extract_claims import get_llm

    ap = argparse.ArgumentParser()
    ap.add_argument("case_id", nargs="?", help="case id, or 'all'")
    args = ap.parse_args()
    llm = get_llm()
    targets = list(CASES.values()) if args.case_id in (None, "all") else [CASES[args.case_id]]
    for case in targets:
        evaluate_case(case, llm)
