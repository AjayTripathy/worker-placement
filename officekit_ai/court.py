"""court — courtkit-lite: the productized adversarial court (I4, Q6-ratified).

Q6 ruling (principal, 2026-09-04): users generate their OWN adjudications —
a verdict only means something in the context of the strategy that convened
the court — and connected tenants exchange them two-way with the backend
(send theirs up, read ours down), building cross-tenant adjudication
intelligence over all equities. Every shared adjudication carries WHICH
STRATEGY built it, WHICH office, and WHEN.

The runner composes the shipped court doctrine (officekit_agents court.md,
plane-2 gated) into three calls through the BYOM slots:

    RED bench  (slot: bench)      — attack the candidate inside the strategy
    BLUE bench (slot: bench)      — defend it, conceding what's true
    ADJUDICATE (slot: adjudicate) — weigh both briefs; never rubber-stamps

U2 tier enforcement, at runtime: within a rankable model family the
adjudicator may never be WEAKER than the bench (raises, fail-loud). An
equal-tier court is allowed but stamped "flat_tier" on the record — honest
labeling over false precision. Unrankable BYOM models stamp "unranked".

Honest limitation, stamped on every verdict: courtkit-lite benches have NO
live data connectors — they deliberate from model knowledge plus the strategy
context, and are instructed to mark every load-bearing number UNVERIFIED
rather than assert it. Verdicts are labeled LITE; the flagship desk keeps its
full evidence-pack courts, and grading the lite court against it is the U3
dogfood diff. Every call freezes an agent_call; the adjudication record is
contract #11 (adjudications.jsonl).
"""
from __future__ import annotations

import json
import uuid
from datetime import date
from pathlib import Path

from officekit_ai import record_agent_call

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
        resp = _create(bench_client,
            model=bench_model, max_tokens=30000,
            system=doctrine + lite_note,
            messages=[{"role": "user", "content": content}],
            output_config={"format": {"type": "json_schema", "schema": _BENCH_SCHEMA}})
        if resp.stop_reason == "max_tokens":
            raise RuntimeError(f"court {role} bench truncated at max_tokens — raise the cap")
        out = json.loads(next(b.text for b in resp.content if b.type == "text"))
        rec = record_agent_call(ledger, f"court_{role.lower()}", bench_model,
                               {"symbol": symbol, "strategy": strategy_id,
                                "lean": out["lean"], "n_unverified": len(out["unverified"])},
                               office_id=office_id, today=today)
        return out, rec["id"]

    red, red_ref = bench(
        "RED", "Attack this candidate: the strongest honest case AGAINST owning it "
        "under this mandate. Hunt disconfirming angles the pitch-frame hides.")
    blue, blue_ref = bench(
        "BLUE", "Defend this candidate under this mandate — conceding every true "
        "red-team point. A defense that concedes nothing is invalid.", red_case=red)

    resp = _create(adj_client,
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
                                "verdict": adj["verdict"], "conviction": adj["conviction"]},
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


# The exchange allowlist (Q6): what a shared adjudication carries — the
# strategy that built it, the office, and when — NEVER position sizes or
# dollars. This is a SEPARATE sanctioned channel from the learning ledger
# (whose allowlist bans tickers); adjudications carry tickers by design.
_SHAREABLE_FIELDS = ("id", "office_id", "strategy", "symbol", "date",
                     "verdict", "rationale", "tier")


def export_shareable_adjudications(folder):
    """The only sanctioned exit path for the adjudication exchange."""
    return [{k: r.get(k) for k in _SHAREABLE_FIELDS}
            for r in load_adjudications(folder) if r.get("subject_kind", "security") == "security"]
