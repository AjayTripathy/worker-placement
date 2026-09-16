"""intake_chat — AI-2: conversational onboarding (the intake agent, live).

    python3 -m officekit_ai.intake_chat --dir ./office

The agent runs the INTAKE_AGENT.md contract as a conversation: freeform
descriptions and pasted statement text in, clarifying questions back (goals
especially — forms are bad at eliciting them), and a progressively-filled
answers draft out. Every turn returns strict JSON {reply, answers, complete}
via structured output, so the serve chat panel can FILL THE FORM VISIBLY and
the CLI can show the draft — the human always reviews before the build runs.

Never fabricate, mechanically enforced: the final answers pass through the
same build_from_answers/validate() gate as every other door, and a validation
failure is fed back to the agent as a correction turn, not papered over.
Model: Claude Opus 5, adaptive thinking (on by default). Each completed
emission is a frozen `agent_call` record (capability "intake").
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from officekit_ai import DEFAULT_MODEL
from officekit_ai import record_agent_call

# The answers draft is free-form (the answers contract), which strict
# structured outputs can't express (every object must close
# additionalProperties) — so it travels as a JSON STRING the code parses.
_TURN_SCHEMA = {
    "type": "object",
    "properties": {
        "reply": {"type": "string",
                  "description": "what you say to the user this turn — a question, a confirmation, or a summary"},
        "answers_json": {"type": "string",
                         "description": "the best-so-far answers draft as a JSON object string, or \"\" if nothing is known yet"},
        "complete": {"type": "boolean",
                     "description": "true only when the answers draft is ready to build"},
    },
    "required": ["reply", "answers_json", "complete"],
    "additionalProperties": False,
}


def _system(scope=None):
    """The system prompt IS the shipped contract, plus the conversational frame —
    one directive, not a parallel prompt stack (unified-agent-layer ruling).
    scope="assets": assets/debts/income only — the holdings table sits ABOVE
    the chat and goals are off-limits. scope="goals": life goals only — the
    goal fields sit ABOVE the chat and assets are off-limits."""
    contract = (Path(__file__).resolve().parent.parent / "officekit" / "INTAKE_AGENT.md").read_text()
    scope_block = ""
    if scope == "assets":
        scope_block = """

## Scope: ASSETS ONLY (this panel)

This chat captures assets, debts, and income. The holdings table sits ABOVE
this chat — you fill it. Goals have their OWN section and their own chat —
NEVER ask about goals, never mention them, and never include `goals` in
answers_json. No topic follow-ups at all: your reply is one short line, e.g.
"Filled in above — that look right? Anything else?"

If the user mentions a CAPITAL-LOSS CARRYFORWARD (banked/prior-year realized losses), capture it as top-level `loss_carryforward` (a dollar amount) — it offsets future gains and is tracked as a deferred tax asset; it also makes harvesting less urgent.

For a MORTGAGE (a `real_estate_debt` sleeve), ask ONE clarifying question if
the user hasn't said: is it FIXED-rate or ADJUSTABLE (ARM)? Set the sleeve's
`"style"` to `"fixed"` or `"arm"` accordingly (default `"fixed"` if they
don't know — most US mortgages are). It changes how the debt responds to rates
in the risk model (a fixed mortgage hedges rate risk; an ARM adds to it). Also
capture the rate as `rate_pct` when given. """
    elif scope == "goals":
        scope_block = """

## Scope: GOALS ONLY (this panel)

This chat captures LIFE GOALS. Kinds: retirement (date + annual spending),
dated spending targets (label + date + amount), a liquidity floor (amount),
and `tax_efficiency` — an ONGOING objective like harvesting losses / tax
efficiency (a label, no amount/date needed; it offers a lot-level-harvesting
strategy). Goals come ONLY from the user's own words.

CAPTURE, DON'T INTERROGATE. Fill what the user gives and STOP — do not ask a
pile of clarifying questions (timing, floor, retirement date) they didn't
raise. At most ONE short follow-up, only if a goal is unusable without it.

If the user mentions a WINDFALL / incoming money (e.g. "$X in September"),
that's an asset, not a goal: capture it under `incoming` ({amount, eta,
character, state, rate?}) so it lands in the assets panel — do NOT bounce the
user to the other chat, and do NOT interrogate whether a purchase is timed to
it. If it's a CAPITAL GAIN, ask ONE thing: which state they're taxed in (set
`incoming.state`, e.g. "CA") — the tax reserve is computed from a conservative
federal+state floor unless they give an exact `rate`. A gain is never modeled
tax-free. If they
also want to harvest losses (or "be tax-efficient"), add a `tax_efficiency`
goal with a clear label. Your reply is ONE short line, e.g. "Added — anything
else?" """
    return contract + scope_block + """

## Conversational mode (this session)

You are running this contract LIVE in a chat. Each turn, respond with the
structured JSON you were configured with: `reply` (what you say to the user),
`answers_json` (the best-so-far answers draft as a JSON object STRING —
include everything learned so far, every turn; "" until something is known),
and `complete` (true only when the draft is buildable).

- YOUR REPLY IS NOT THE DISPLAY SURFACE — the form is. Never
  enumerate or summarize captured data in prose; the fields you fill already
  show it (holdings and sleeves land in their tables, goals land in the Life
  goals section). Reply with ONE short line: confirm and ask for what's
  missing, e.g. "Filled in below — does that look right? Anything else —
  goals, income, a mortgage?" At most one or two asks per turn; goals matter
  most and people rarely volunteer them (retirement, big planned expenses, a
  comfortable cash floor).
- Never invent a number. Approximate figures the user gives get
  "confidence": "assumption"; things they can't value get "confidence": "tbd".
- If the user gives no first name, OMIT `owner` entirely — the dashboard
  greeting renders namelessly by design; never fill a placeholder name.
- `as_of` may be omitted (intake defaults it to today). Only set it when a
  real statement date exists — never invent a stand-in date.
- Goals come ONLY from the user's own words in this conversation.
- If the user pastes statement text, extract values from it faithfully.
- When the user says they're done (or you have sleeves + profile + at least
  been ASKED about goals), set complete=true; the reply stays one line
  ("All set — review the form and click Build."). No summary prose: the form
  IS the summary.
- If you receive a message starting with "VALIDATION FAILED:", fix exactly
  those problems in the draft and re-emit with complete=true."""


def turn(messages, client=None, model=None, folder=None, scope=None, context=None):
    """One conversation turn. `messages` is the running [{role, content}] list
    (user/assistant strings). Returns {reply, answers, complete}. The model
    comes from the office's BYOM slot config (models.json slot "intake") when
    no client is injected. `context`: environment facts the serve layer already
    knows (e.g. the auto-adapter scan) — the agent builds on them instead of
    re-asking."""
    if client is None:
        from officekit_ai.models import client_for
        client, resolved = client_for("intake", folder)
        model = model or resolved
    model = model or DEFAULT_MODEL
    system = _system(scope)
    if context:
        system += ("\n\nAUTO-DETECTED ON THIS MACHINE (read-only scan; the user sees the same "
                   "list and an Import button on the form): " + context +
                   "\nDo not ask the user to type holdings a detected connection can import — "
                   "point them at the Import button instead, and focus your questions on what "
                   "no connection can see (other institutions, real estate, private holdings, debts).")
    resp = client.messages.create(
        model=model, max_tokens=8000, system=system, messages=messages,
        output_config={"format": {"type": "json_schema", "schema": _TURN_SCHEMA}})
    text = next(b.text for b in resp.content if b.type == "text")
    t = json.loads(text)
    raw = (t.pop("answers_json", "") or "").strip()
    try:
        t["answers"] = json.loads(raw) if raw else None
    except Exception:
        t["answers"] = None    # a malformed draft is "no draft", never a crash
    return t


def finalize(answers, folder, ledger=True):
    """The gate every door shares: validate via build_from_answers, write the
    folder (answers/balance sheet/personal-context skeleton/pages), freeze the
    intake agent_call. Raises ValueError with the validation problems on a bad
    draft — callers feed that back to the agent."""
    from officekit.serve import build_office
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    data = build_office(answers, folder)     # raises on invalid — the shared gate
    if ledger:
        try:
            record_agent_call(folder / "learning.jsonl", "intake", DEFAULT_MODEL,
                              {"n_sleeves": len(data.get("sleeves") or []),
                               "n_goals": len(data.get("goals") or []),
                               "has_income": bool(answers.get("income")),
                               "complete": True},
                              office_id=data.get("office_id"))
        except Exception:
            pass
    return data


def run_cli(folder, client=None, model=None, input_fn=input, print_fn=print):
    """The `init --chat` loop: converse, show the draft filling, validate-retry,
    build. input_fn/print_fn injectable for tests."""
    messages = []
    print_fn("officekit intake — describe your finances in your own words; 'done' when finished.\n")
    while True:
        user = input_fn("> ").strip()
        if not user:
            continue
        messages.append({"role": "user", "content": user})
        t = turn(messages, client=client, model=model, folder=folder)
        messages.append({"role": "assistant", "content": json.dumps(t)})
        print_fn(t["reply"])
        if t.get("answers"):
            n = len(t["answers"].get("sleeves") or [])
            g = len(t["answers"].get("goals") or [])
            print_fn(f"  [draft: {n} sleeves · {g} goals]")
        if t.get("complete") and t.get("answers"):
            try:
                data = finalize(t["answers"], folder)
            except (ValueError, Exception) as e:
                messages.append({"role": "user", "content": f"VALIDATION FAILED: {e}"})
                t2 = turn(messages, client=client, model=model, folder=folder)
                messages.append({"role": "assistant", "content": json.dumps(t2)})
                if not (t2.get("complete") and t2.get("answers")):
                    print_fn(f"couldn't repair the draft: {e}")
                    continue
                data = finalize(t2["answers"], folder)
            print_fn(f"\noffice built: {len(data.get('sleeves') or [])} sleeves -> "
                     f"{Path(folder) / 'pages'} (serve it: python3 -m officekit.serve --dir {folder})")
            return data


def main(argv=None):
    ap = argparse.ArgumentParser(prog="officekit_ai.intake_chat",
                                 description=__doc__.splitlines()[0])
    ap.add_argument("--dir", default="./office")
    args = ap.parse_args(argv)
    run_cli(args.dir)


if __name__ == "__main__":
    main()
