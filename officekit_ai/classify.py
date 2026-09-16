"""classify — AI-1: the symbol-classification fallback (Claude Haiku 4.5).

Unknown tickers currently pool into "individual stocks" with a listed name —
honest, but a muni fund the FUND_MAP doesn't know deserves better. With the
plugin: unknowns go to a small model with strict structured output, and the
suggestions render as a CONFIRMATION step — the human accepts, never a silent
write. Confirmed mappings persist twice:

  - answers["fund_map"]           — the durable copy: rebuilds re-classify
                                    identically without another API call
  - fund_map_learned.json         — the office-local cache that seeds future
                                    onboardings (and, via OSS PRs, the shared
                                    FUND_MAP itself)

Every suggestion batch is a frozen `agent_call` ledger record (capability
"classify") BEFORE it is shown — the gradeable trail. Any API failure returns
no suggestions and the deterministic path proceeds unchanged (degrade to
today's behavior, never an error in the user's face).
"""
from __future__ import annotations

import json
from pathlib import Path

from officekit_ai import CLASSIFY_MODEL
from officekit_ai import record_agent_call

# categories the classifier may propose — a deliberate subset of schema
# CATEGORIES: things a ticker can actually BE. "single_name_equity" means
# "it's an individual stock" (no mapping needed — that's already the default).
CLASSIFIABLE = ("public_equity", "fixed_income", "municipal_credit", "cash",
                "single_name_equity")
STYLES = ("intl", "tech", "target_date", "short_duration", "megacap_tech")

_SCHEMA = {
    "type": "object",
    "properties": {
        "classifications": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "category": {"type": "string", "enum": list(CLASSIFIABLE)},
                    "style": {"enum": list(STYLES) + [None]},
                    "confidence": {"type": "number",
                                   "description": "probability in [0,1] the category is right"},
                },
                "required": ["symbol", "category", "style", "confidence"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["classifications"],
    "additionalProperties": False,
}

_PROMPT = """Classify each ticker symbol below into one of these categories:
- public_equity: a pooled equity fund/ETF (styles: intl, tech, target_date, or null for broad US)
- fixed_income: a bond fund/ETF (style: short_duration or null)
- municipal_credit: a municipal bond fund
- cash: a money-market fund or cash equivalent
- single_name_equity: an individual company's stock (style: megacap_tech or null)

Rules: classify only what you actually recognize. If you do not recognize a
symbol, return it as single_name_equity with confidence 0. Confidence is your
honest probability the category is right — never inflate it.

Conventions and known traps (eval-derived, 2026-09-04):
- Individual company stocks vastly OUTNUMBER funds in any ticker universe.
  Unless you specifically recognize the symbol as a fund/ETF, classify it
  single_name_equity — never infer fund-ness from how a symbol looks or
  sounds (universe eval: RMBS is a chip company, not a bond fund; LQDT is
  Liquidity Services, an auction marketplace, not a money-market fund).
- Ultra-short treasury / T-bill ETFs (SGOV, BIL class) count as `cash`, not
  fixed_income — they are cash equivalents in this taxonomy.
- Five-letter mutual-fund tickers (especially Vanguard V***X) are frequently
  AMBIGUOUS from the symbol alone — lookalike families span equity, bond, and
  muni funds. Without a description, cap your confidence at 0.5 for these
  unless you are certain of the specific fund.

Symbols (with statement descriptions where available — the description is
strong evidence; a symbol that LOOKS like one fund family may be another):
{symbols}"""


def suggest(symbols, client=None, model=None, ledger_path=None, office_id=None,
            folder=None, descs=None):
    """Ask the classify model about unknown symbols. `descs` ({SYM: statement
    description}) sharpens lookalike tickers — a fund's own name is stronger
    evidence than its symbol (live finding 2026-09-04: VWLUX symbol-only was
    confidently misread as intl equity; it is a muni fund). Returns
    fund-suggestions [{symbol, category, style, confidence}] — single-stock and
    low-confidence verdicts are dropped (they match the deterministic default,
    so there is nothing to confirm). Raises nothing to the caller's user: any
    failure returns []."""
    symbols = sorted({str(s).upper().strip() for s in symbols if str(s).strip()})
    if not symbols:
        return []
    descs = {k.upper(): v for k, v in (descs or {}).items() if v}
    listing = "\n".join(f"- {s}" + (f": {descs[s]}" if s in descs else "") for s in symbols)
    try:
        if client is None:
            from officekit_ai.models import client_for
            client, resolved = client_for("classify", folder)
            model = model or resolved
        model = model or CLASSIFY_MODEL
        resp = client.messages.create(
            model=model, max_tokens=2000,
            messages=[{"role": "user", "content": _PROMPT.format(symbols=listing)}],
            output_config={"format": {"type": "json_schema", "schema": _SCHEMA}})
        text = next(b.text for b in resp.content if b.type == "text")
        out = json.loads(text)["classifications"]
    except Exception:
        return []   # degrade to the deterministic path, never an error page
    sugg = [c for c in out
            if c.get("symbol", "").upper() in symbols
            and c.get("category") in CLASSIFIABLE
            and c["category"] != "single_name_equity"
            and (c.get("confidence") or 0) >= 0.6]
    if ledger_path is not None:
        try:   # freeze the claim before it is shown — the gradeable trail
            record_agent_call(ledger_path, "classify", model,
                              {"symbols": symbols, "suggestions": sugg},
                              office_id=office_id)
        except Exception:
            pass
    return sugg


def learned_path(folder):
    return Path(folder) / "fund_map_learned.json"


def load_learned(folder):
    """The office-local confirmed-mapping cache: {SYM: [category, style|null]}."""
    p = learned_path(folder)
    if not p.exists():
        return {}
    try:
        return {k.upper(): tuple(v) for k, v in json.loads(p.read_text()).items()}
    except Exception:
        return {}


from officekit.office_lock import transaction

@transaction()
def save_confirmed(folder, mappings):
    """Append human-CONFIRMED mappings to the office cache (merge, never drop)."""
    cur = {k: list(v) for k, v in load_learned(folder).items()}
    for sym, (cat, style) in mappings.items():
        cur[sym.upper()] = [cat, style]
    learned_path(folder).write_text(json.dumps(cur, indent=1, sort_keys=True) + "\n")
    return cur


def apply_confirmed(answers, mappings):
    """Write confirmed mappings into answers["fund_map"] — the durable copy that
    makes every rebuild re-classify identically with no further API calls."""
    fm = answers.setdefault("fund_map", {})
    for sym, (cat, style) in mappings.items():
        fm[sym.upper()] = [cat, style]
    return answers
