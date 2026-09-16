"""Stage 1 (biotech): extract catalyst-relevant marketing claims (R) from the
blinded EDGAR corpus.

This reads ONLY the pre-cutoff 8-K EX-99 exhibits assembled by `corpus.py` (the
blind is already enforced there by EDGAR date stamps), and turns the promotional
prose into structured `Claim` records — the R of the R/f(M) pipeline.

Each claim is tagged with a `predicate` drawn from the biotech f-library's
`CLAIM_PREDICATES`, so Stage 3 can route it to the BioRule(s) that know how to
check it against an authoritative M-source. Claims whose predicate is not in the
catalog are dropped — an un-routable claim has no f, so it cannot be verified and
is noise for this pipeline.

We reuse the buyside_dd `Claim` schema verbatim: the contract (exact source_quote
for anti-hallucination, subject/predicate/object_value, scope) is identical; only
the predicate vocabulary is biotech-specific.

Blinding note: extraction sees marketing text only. The catalyst OUTCOME lives in
_sealed_outcomes.json and is never read here. Passing case.program / case.nct_ids
into the prompt is safe — trial identity is pre-cutoff public registration, not an
outcome.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from verticals.buyside_dd.schemas import Claim
from .catalyst_spec import CatalystCase, DATA_DIR
from .f_library_biotech import BIOTECH_RULES, CLAIM_PREDICATES


def _predicate_catalog() -> str:
    """Render the allowed predicate tags + what each one captures, for the prompt."""
    by_pred: dict[str, list] = {}
    for r in BIOTECH_RULES:
        by_pred.setdefault(r.claim_predicate, []).append(r)
    lines = []
    for pred in sorted(by_pred):
        chans = sorted({r.channel for r in by_pred[pred]})
        patt = by_pred[pred][0].r_pattern
        lines.append(f"- {pred}  [{', '.join(chans)}]\n    {patt}")
    return "\n".join(lines)


CLAIM_EXTRACTION_PROMPT = """You are extracting catalyst-relevant marketing claims from a biotech company's \
promotional disclosure (an 8-K press release or investor deck), for an investment \
diligence pipeline that predicts whether an upcoming clinical/regulatory catalyst \
will HIT or MISS.

COMPANY: {company} ({ticker})
PROGRAM (the asset behind the catalyst): {program}
INDICATION: {indication}
REGISTERED TRIAL(S) for this catalyst: {nct_ids}
CATALYST: {catalyst_type}

You extract only claims that bear on the PROBABILITY OF THE CATALYST SUCCEEDING and \
that could in principle be checked against an authoritative external source (the \
trial registry, FDA precedent, the peer-reviewed/registered record, prior filings). \
These are the claim shapes that matter, each with a PREDICATE tag you must assign:

{predicate_catalog}

ASSIGN EXACTLY ONE predicate from the list above to each claim. If a sentence is \
catalyst-relevant but fits none of these predicates, DROP it — this pipeline can \
only verify claims that map to a predicate.

TRIAL ATTRIBUTION (critical — each claim is later scored against a SPECIFIC trial's \
registry; mis-attribution manufactures false discrepancies):
- A company markets several trials at once. Bind each claim to the trial(s) it \
ACTUALLY describes, not reflexively to the catalyst trial above.
- COUNT / AGGREGATE claims: if a patient-enrollment, site, or country count is a \
PROGRAM total or spans MULTIPLE trials ("the program enrolled N", "1,939 patients \
across both pivotal trials", "the Phase 3 program consists of two trials … N \
patients"), it is a PROGRAM AGGREGATE. Set trial_scope="program_aggregate", set \
subject to the PROGRAM name (NOT a single NCT), and list EVERY trial it spans in \
nct_refs. NEVER attribute a multi-trial total to one NCT — that single trial's \
registry will show a smaller number and the claim will look falsely inflated. The \
word "program" or "across both/two trials" near a patient count is the tell, even \
when the individual trial names are in a neighbouring sentence.
- DIFFERENT-TRIAL claims: if a claim describes a trial/indication OTHER than the \
catalyst (a sister program, an earlier phase, a different disease), still extract \
it but set subject + nct_refs to THAT trial so it is scored against its own record.
- Otherwise set trial_scope="single_trial" and bind subject/nct_refs to the one \
trial the claim is about (the catalyst trial when the claim is plainly about it).

DROP entirely (do not extract):
- Pure financing / cash-runway / share-count / governance / personnel items
- Generic boilerplate, mission statements, forward-looking-statement safe-harbor text
- Aspirations with no concrete asserted fact ("we believe simufilam could transform...")

For each kept claim, output a JSON object:
- claim_id: short unique id, e.g. "{ticker_lc}_001"
- subject: for trial_scope="single_trial" the NCT id (or trial name) the claim is about; for trial_scope="program_aggregate" the PROGRAM name (use "{program}"), NEVER a single NCT
- trial_scope: "single_trial" | "program_aggregate" | "different_trial" — see TRIAL ATTRIBUTION above
- nct_refs: list of every NCT id the claim spans (one for single_trial; the multiple it aggregates for program_aggregate; the sister trial's id for different_trial; [] if no NCT is identifiable)
- predicate: EXACTLY one tag from the catalog above
- object_value: the asserted value (a number, an endpoint name, a date, a status string, a yes/no assertion)
- object_unit: unit if applicable (%, mg, patients, months, etc.), else null
- scope: dict with any of {{nct, indication, trial_phase, data_source (e.g. "open-label", "Phase 2b", "interim")}}
- source_quote: EXACT verbatim text from the document supporting the claim. Required. Anti-hallucination check — copy it character-for-character.
- confidence: 0-1, your confidence this is a real, intended, catalyst-relevant claim
- extraction_notes: 1 short phrase on why this claim matters to the catalyst

Extract every distinct catalyst-relevant claim; do not collapse different facts into one. \
A single press release often yields 0 claims (pure financing) or many (a data PR).

DOCUMENT TEXT:
---
{text}
---

Return ONLY a JSON array of claim objects, no preamble or commentary."""


def _parse_json_array(raw: str) -> list[dict]:
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    start = raw.find("[")
    end = raw.rfind("]")
    if start == -1 or end == -1 or end < start:
        return []
    try:
        data = json.loads(raw[start : end + 1])
    except json.JSONDecodeError:
        return []
    return [d for d in data if isinstance(d, dict)]


def extract_exhibit(case: CatalystCase, exhibit_path: Path, llm,
                    *, max_chars: int = 40000) -> list[dict]:
    """Run claim extraction over a single exhibit; return raw claim dicts."""
    text = exhibit_path.read_text(errors="replace")[:max_chars]
    prompt = CLAIM_EXTRACTION_PROMPT.format(
        company=case.company,
        ticker=case.ticker,
        ticker_lc=case.ticker.lower(),
        program=case.program,
        indication=case.indication,
        nct_ids=", ".join(case.nct_ids),
        catalyst_type=case.catalyst_type,
        predicate_catalog=_predicate_catalog(),
        text=text,
    )
    out = llm(prompt)
    return _parse_json_array(out)


def extract_case_claims(case: CatalystCase, llm, *, limit: int | None = None,
                        verbose: bool = True, allow_leak: bool = False) -> list[Claim]:
    """Extract claims across the whole pre-cutoff corpus for `case`.

    Reads data/<ticker>/corpus/corpus_index.json, runs the extractor over each
    exhibit, validates predicates against CLAIM_PREDICATES, and writes typed
    Claim records to data/<ticker>/claims.json. Returns the Claim list.

    Pre-flight (no credits): assert_no_leak raises if the catalyst's topline has
    already leaked into the pre-cutoff corpus — a live case is only a blind forward
    test if its readout is in the FUTURE. Pass allow_leak=True to extract anyway
    (e.g. a deliberately-leaked control where the outcome is used as a label).
    """
    if not allow_leak:
        from .verify_corpus_leak import assert_no_leak
        assert_no_leak(case)  # raises LeakError before any LLM call

    corpus_dir = DATA_DIR / case.case_id / "corpus"
    index_path = corpus_dir / "corpus_index.json"
    if not index_path.exists():
        raise FileNotFoundError(f"no corpus for {case.ticker}; run corpus.py first")
    exhibits = json.loads(index_path.read_text())["exhibits"]
    if limit:
        exhibits = exhibits[:limit]

    claims: list[Claim] = []
    seen: set[tuple] = set()
    n_dropped_pred = 0
    for ex in exhibits:
        ex_path = DATA_DIR / ex["path"]
        try:
            raw = extract_exhibit(case, ex_path, llm)
        except Exception as e:
            print(f"  EXTRACT FAIL {ex['exhibit']}: {e}", file=sys.stderr)
            continue
        kept = 0
        for c in raw:
            pred = (c.get("predicate") or "").strip()
            if pred not in CLAIM_PREDICATES:
                n_dropped_pred += 1
                continue
            quote = (c.get("source_quote") or "").strip()
            if not quote:
                continue
            dedup_key = (pred, quote[:120])
            if dedup_key in seen:
                continue
            seen.add(dedup_key)
            scope = dict(c.get("scope") or {})
            scope.setdefault("filing_date", ex["filing_date"])
            scope.setdefault("case_id", case.case_id)
            # Per-claim trial attribution: which trial(s) the claim describes, so
            # Stage 3 scores it against the RIGHT registry. A program_aggregate
            # count (a multi-trial total) must never be refuted against one trial.
            ts = (c.get("trial_scope") or "single_trial").strip()
            scope["trial_scope"] = ts if ts in {
                "single_trial", "program_aggregate", "different_trial"} else "single_trial"
            refs = c.get("nct_refs") or []
            scope["nct_refs"] = [r for r in refs if isinstance(r, str) and r.startswith("NCT")]
            claims.append(Claim(
                claim_id=f"{case.ticker.lower()}_{len(claims)+1:03d}",
                source_doc=ex["path"],
                source_quote=quote,
                subject=(c.get("subject") or case.program).strip(),
                predicate=pred,
                object_value=c.get("object_value"),
                object_unit=c.get("object_unit"),
                scope=scope,
                confidence=float(c.get("confidence", 1.0) or 1.0),
                extraction_notes=c.get("extraction_notes"),
            ))
            kept += 1
        if verbose and kept:
            print(f"  + {ex['filing_date']} {ex['exhibit']}: {kept} claims",
                  file=sys.stderr)

    out_path = DATA_DIR / case.case_id / "claims.json"
    out_path.write_text(json.dumps({
        "case_id": case.case_id,
        "cutoff": case.cutoff,
        "n_claims": len(claims),
        "n_dropped_unroutable_predicate": n_dropped_pred,
        "claims": [json.loads(c.model_dump_json()) for c in claims],
    }, indent=2))
    if verbose:
        by_pred: dict[str, int] = {}
        for c in claims:
            by_pred[c.predicate] = by_pred.get(c.predicate, 0) + 1
        print(f"[{case.ticker}] {len(claims)} claims "
              f"({n_dropped_pred} dropped non-routable) -> {out_path}", file=sys.stderr)
        for p in sorted(by_pred, key=lambda k: -by_pred[k]):
            print(f"    {by_pred[p]:>3}  {p}", file=sys.stderr)
    return claims


def get_llm():
    """Anthropic streaming callable (text -> text). Requires ANTHROPIC_API_KEY in env."""
    import os
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY not set in environment")
    import anthropic
    client = anthropic.Anthropic()

    def llm(prompt: str, model: str = "claude-sonnet-4-5") -> str:
        parts: list[str] = []
        with client.messages.stream(
            model=model,
            max_tokens=16000,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            for chunk in stream.text_stream:
                parts.append(chunk)
        return "".join(parts)

    return llm


if __name__ == "__main__":
    import argparse
    from .catalyst_spec import CASES

    ap = argparse.ArgumentParser()
    ap.add_argument("case_id", nargs="?", help="case id, or 'all'")
    ap.add_argument("--limit", type=int, default=None, help="cap exhibits per case")
    args = ap.parse_args()

    llm = get_llm()
    targets = list(CASES.values()) if args.case_id in (None, "all") else [CASES[args.case_id]]
    for case in targets:
        extract_case_claims(case, llm, limit=args.limit)
