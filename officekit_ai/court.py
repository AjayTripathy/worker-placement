"""court — courtkit-lite: the productized adversarial court (I4, Q6-ratified).

Q6 update (2026-09-18): users generate their OWN contextual adjudications.
Reviewed projections may be exchanged through officekit_research.cases. Native
records and office identity stay private; a historical verdict never authorizes
a recipient's investment. The central exchange remains planned.

The runner composes the shipped court doctrine (officekit_agents court.md,
plane-2 gated) into three calls through the BYOM slots:

    RED bench  (slot: bench)      — attack the candidate inside the strategy
    BLUE bench (slot: bench)      — defend it, conceding what's true
    ADJUDICATE (slot: adjudicate) — weigh both briefs; never rubber-stamps

U2 tier enforcement, at runtime: within a rankable model family the
adjudicator may never be WEAKER than the bench (raises, fail-loud). An
equal-tier court is allowed but stamped "flat_tier" on the record — honest
labeling over false precision. Unrankable BYOM models stamp "unranked".

Evidence packs may contain fetched primary sources and explicitly permitted
shared snapshots, alongside the current office's book. Missing evidence stays
UNVERIFIED. EVIDENCED indicates a pack was supplied, not a source-quality grade;
otherwise the court is labeled LITE. Every call freezes agent provenance in the
private learning ledger; adjudications.jsonl retains the original court record.
"""
from __future__ import annotations

import json
import uuid
from datetime import date
from pathlib import Path

from officekit_ai import record_agent_call
from officekit_ai.provenance import invoke

# rankable capability tiers (anthropic family); BYOM models absent here are unranked
_TIER = {"haiku": 0, "sonnet": 1, "opus": 2, "fable": 3, "mythos": 3}


def _tier_of(model):
    m = (model or "").lower()
    for name, t in _TIER.items():
        if name in m:
            return t
    return None


def _create(client, **kw):
    """Streaming for real clients (long courts exceed the non-streaming
    limit), plain create for test fakes."""
    stream_fn = getattr(getattr(client, "messages", None), "stream", None)
    if stream_fn is None:
        return client.messages.create(**kw)
    with stream_fn(**kw) as s:
        return s.get_final_message()


def check_tier_order(bench_model, adjudicate_model):
    """U2: the adjudicator is never weaker than the bench. Returns the court's
    tier label; raises on a violation instead of silently degrading."""
    b, a = _tier_of(bench_model), _tier_of(adjudicate_model)
    if b is None or a is None:
        return "unranked"
    if a < b:
        raise RuntimeError(
            f"courtkit: adjudicate slot ({adjudicate_model}) is a weaker tier than "
            f"the bench ({bench_model}) — the adjudicator may never be weaker; "
            f"fix models.json")
    return "tiered" if a > b else "flat_tier"


_BENCH_SCHEMA = {
    "type": "object",
    "properties": {
        "case": {"type": "string", "description": "the brief: your strongest honest case, structured"},
        "key_points": {"type": "array", "items": {"type": "string"}},
        "unverified": {"type": "array", "items": {"type": "string"},
                       "description": "every load-bearing number/claim you could not verify"},
        "lean": {"type": "string", "enum": ["kill", "avoid", "watch", "starter", "own"]},
    },
    "required": ["case", "key_points", "unverified", "lean"],
    "additionalProperties": False,
}

_ADJ_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": ["KILL", "AVOID", "WATCH", "STARTER", "OWN"]},
        "conviction": {"type": "integer", "description": "1-10"},
        "rationale": {"type": "string"},
        "decisive_points": {"type": "array", "items": {"type": "string"}},
        "unverified_items": {"type": "array", "items": {"type": "string"},
                             "description": "the work queue: what a full court must verify at primary"},
    },
    "required": ["verdict", "conviction", "rationale", "decisive_points", "unverified_items"],
    "additionalProperties": False,
}


def _strategy_ctx(strategy_id, decision, lib=None):
    lib = lib or {}
    return (f"STRATEGY CONTEXT (the court is convened BY this strategy — judge fit "
            f"for THIS mandate, not the name in the abstract):\n"
            f"- strategy: {lib.get('title', strategy_id)} ({strategy_id})\n"
            f"- description: {lib.get('desc', decision.get('desc', ''))}\n"
            f"- status: {decision.get('status', 'considering')}"
            + (f"\n- target: {decision.get('target_pct')}% of NW" if decision.get('target_pct') is not None else "")
            + (f"\n- mandate note: {decision.get('note')}" if decision.get('note') else ""))


_LITE_NOTE = ("\n\nCOURTKIT-LITE LIMITATION (binding): you have NO live data connectors. "
              "Deliberate from your knowledge and the context above; NEVER assert a "
              "load-bearing number you cannot verify — list it in `unverified` instead. "
              "Per the doctrine, unverifiable is never clean; the adjudicator weighs the "
              "unverified queue explicitly.")


def run_court(symbol, strategy_id, decision, personal_context, folder,
              lib=None, clients=None, today=None, context=None,
              evidence="auto", office_data=None, contact=None, subject_kind="security", proposal_id=None):
    """Convene a lite court on one candidate inside one strategy. Returns the
    adjudication record (contract #11), already appended to the office's
    adjudications.jsonl and frozen call-by-call to the learning ledger.

    `clients`: optional {"bench": (client, model), "adjudicate": (client, model)}
    for tests; production resolves through models.json slots.
    """
    import officekit_agents as agents
    from officekit_ai.models import client_for, resolve

    if clients is None:
        bench_client, bench_model = client_for("bench", folder)
        adj_client, adj_model = client_for("adjudicate", folder)
    else:
        bench_client, bench_model = clients["bench"]
        adj_client, adj_model = clients["adjudicate"]
    tier_label = check_tier_order(bench_model, adj_model)

    doctrine = agents.compose("court", personal_context)
    ctx = _strategy_ctx(strategy_id, decision, lib)
    if subject_kind != "security":
        ctx += (f"\nSUBJECT KIND: {subject_kind}. Judge the proposed structure/program, not a purchase of "
                "the displayed underlying. Missing contracts, terms and quotes remain unverified.")
    if subject_kind == "program":
        ctx += ("\nFor a program, OWN/STARTER means support pursuing this program, not ownership of a security. "
                "Assess eligibility, provider terms, liquidity, tax, operational failure modes and concrete deliverables. "
                "Corporate stock valuation tests that do not apply to this program are out of scope.")
    cand = symbol + (f" — {context}" if context else "")

    # F1 (court unification): the deterministic evidence pack — the desk's
    # dataroom isomorphism, promoted. "auto" builds it when a contact is
    # available and degrades LOUD to a LITE court when it can't.
    pack = None
    pack_errors = []
    if evidence == "auto":
        try:
            from officekit_research import build_pack
            pack = build_pack(symbol, office_data=office_data, contact=contact)
        except Exception as e:
            pack_errors.append(f"evidence: {type(e).__name__}: {e}")
    elif isinstance(evidence, dict):
        pack = evidence
    evidenced = bool(pack and pack.get("sections"))
    pack_md = ""
    if evidenced:
        from officekit_research import render_pack
        pack_md = "\n\n" + render_pack(pack)
    label = "EVIDENCED" if evidenced else "LITE"
    lite_note = "" if evidenced else _LITE_NOTE
    folder = Path(folder)
    ledger = folder / "learning.jsonl"
    office_id = (personal_context or {}).get("office_id")

    def bench(role, instruction, red_case=None):
        # F2: the desk's battle-tested bench templates, promoted — the full
        # prosecution/defense doctrine (FATAL-tag discipline, Up-C artifacts,
        # divergence-not-coverage, tape-verify) rides into every tenant court.
        # The JSON schema still governs output shape; the template governs the
        # reasoning discipline. Falls back to the inline instruction if the
        # template is missing (never blocks a court).
        body = None
        try:
            tpl_path = Path(agents.__file__).parent / "templates" / f"court_{role.lower()}.md"
            tpl = tpl_path.read_text()
            body = (tpl.replace("{TICKER}", symbol)
                    .replace("{THESIS}", f"{ctx}\n\nCANDIDATE: {cand}")
                    .replace("{EVIDENCE_PACK}", pack_md.strip() if evidenced else
                             "(no evidence pack — LITE court; mark every load-bearing number UNVERIFIED)")
                    .replace("{RED_CASE}", json.dumps(red_case, indent=1) if red_case else ""))
            body += ("\n\nOUTPUT SHAPE: respond in the required JSON schema — put the full "
                     "bench brief (findings, sections, dispositions the template demands) in "
                     "`case`, one finding per entry in `key_points`, and every unverifiable "
                     "load-bearing claim in `unverified`.")
        except Exception:
            pass
        content = body if body else (
            f"{ctx}{pack_md}\n\nCANDIDATE: {cand}\n\nYou are the {role} bench. {instruction}"
            + (f"\n\nRED BRIEF:\n{json.dumps(red_case, indent=1)}" if red_case else ""))
        resp, run = invoke(bench_client,
            model=bench_model, max_tokens=30000,
            system=doctrine + lite_note,
            messages=[{"role": "user", "content": content}],
            output_config={"format": {"type": "json_schema", "schema": _BENCH_SCHEMA}})
        if resp.stop_reason == "max_tokens":
            raise RuntimeError(f"court {role} bench truncated at max_tokens — raise the cap")
        out = json.loads(next(b.text for b in resp.content if b.type == "text"))
        rec = record_agent_call(ledger, f"court_{role.lower()}", bench_model,
                               {"symbol": symbol, "strategy": strategy_id,
                                "lean": out["lean"], "n_unverified": len(out["unverified"]), "run": run},
                               office_id=office_id, today=today)
        return out, rec["id"], run

    red, red_ref, red_run = bench(
        "RED", "Attack this candidate: the strongest honest case AGAINST owning it "
        "under this mandate. Hunt disconfirming angles the pitch-frame hides.")
    blue, blue_ref, blue_run = bench(
        "BLUE", "Defend this candidate under this mandate — conceding every true "
        "red-team point. A defense that concedes nothing is invalid.", red_case=red)

    resp, adj_run = invoke(adj_client,
        model=adj_model, max_tokens=30000,
        system=doctrine + lite_note +
        "\n\nYou are the ADJUDICATOR. You never rubber-stamp: weigh both briefs, "
        "lean conservative where they conflict, and treat the union of their "
        "unverified lists as a mandatory work queue in your verdict.",
        messages=[{"role": "user", "content":
                   f"{ctx}{pack_md}\n\nCANDIDATE: {cand}\n\nRED BRIEF:\n{json.dumps(red, indent=1)}"
                   f"\n\nBLUE BRIEF:\n{json.dumps(blue, indent=1)}\n\nAdjudicate."}],
        output_config={"format": {"type": "json_schema", "schema": _ADJ_SCHEMA}})
    if resp.stop_reason == "max_tokens":
        raise RuntimeError("court adjudication truncated at max_tokens — raise the cap")
    adj = json.loads(next(b.text for b in resp.content if b.type == "text"))
    adj["unverified_items"] = list(dict.fromkeys(
        red["unverified"] + blue["unverified"] + adj["unverified_items"]))
    adj_rec = record_agent_call(ledger, "court_adjudicate", adj_model,
                               {"symbol": symbol, "strategy": strategy_id,
                                "verdict": adj["verdict"], "conviction": adj["conviction"], "run": adj_run},
                               office_id=office_id, today=today)

    record = {
        "id": str(uuid.uuid4()),
        "office_id": office_id,
        "strategy": strategy_id,                 # WHICH strategy convened it (Q6)
        "symbol": symbol.upper(),
        "date": (today or date.today()).isoformat(),   # WHEN (Q6)
        "verdict": f"{adj['verdict']} {adj['conviction']}/10 ({label})",
        "rationale": adj["rationale"],
        "decisive_points": adj["decisive_points"],
        "unverified_items": adj["unverified_items"],
        "briefs": {"red": red, "blue": blue},   # the full adversarial record — the pitch deck's body
        "evidence": ({"built": pack["built"], "sections": sorted(pack["sections"]),
                      "errors": pack.get("errors", []), "md": pack_md.strip()}
                     if evidenced else {"errors": pack_errors or ["no evidence pack (LITE court)"]}),
        "tier": tier_label,
        "models": {"bench": bench_model, "adjudicate": adj_model},
        "refs": {"red": red_ref, "blue": blue_ref, "adjudicate": adj_rec["id"]},
        "runs": {"red": red_run, "blue": blue_run, "adjudicate": adj_run},
    }
    if subject_kind != "security":
        record["subject_kind"] = subject_kind
    if proposal_id:
        record["proposal_id"] = proposal_id
    path = folder / "adjudications.jsonl"
    from officekit.office_lock import locked
    with locked(folder):
        with open(path, "a") as f:
            f.write(json.dumps(record) + "\n")
    return record


def load_adjudications(folder):
    path = Path(folder) / "adjudications.jsonl"
    if not path.exists():
        return []
    out = []
    for line in path.read_text().splitlines():
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


def export_shareable_adjudications(folder):
    """Reviewed contextual bundles only; the old Q6 raw export is retired.

    Field allowlisting did not anonymize rationale text or office identifiers.
    Legacy native records need an explicit projection/review before exchange.
    The versioned bundle preserves context, source lineage and review scope.
    """
    from officekit_research.cases import load_library
    bundles, _ = load_library(folder)
    return [b for b in bundles if b["case"]["subject"]["instrument"] in {"stock", "etf"}]
