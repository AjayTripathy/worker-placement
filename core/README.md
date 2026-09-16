# core

Framework primitives shared across all verticals. Vertical code in `verticals/` imports from here.

## Files

| File | Role |
|---|---|
| `engine.py` | `SignalEngine` — orchestrates per-entity runs: pulls records via Sources, computes gap via GapFunction, applies SignalRules, scores. |
| `models.py` | Dataclasses + Pydantic models — `Entity`, `Record`, `GapResult`, `SignalRule`, `RuleMatch`, `Signal`, `VerticalManifest`, `RunSummary`. |
| `protocols.py` | Runtime-checkable Protocol types — `Source`, `GapFunction`, `RuleInterpreter`, `Scorer`, `SignalStore`. Verticals satisfy these structurally; no inheritance required. |
| `registry.py` | Per-jurisdiction registry: maps `(vertical, jurisdiction)` to its Sources, GapFunction, and SignalRule list. Lets `cli/main.py` instantiate any built jurisdiction by name. |
| `interpreter.py` | LLM-backed RuleInterpreter for SignalRules whose `implementation` is None — falls back to LLM applying the statute text in `source_text`. |
| `llm.py` | Anthropic SDK adapter; reads key from `~/.anthropic_api_key`. |
| `exceptions.py` | `SourceError` and friends. |

## Concepts (see `ARCHITECTURE.md` Layer 1 for full detail)

- An **Entity** (parcel, vessel, company) belongs to one (vertical, jurisdiction).
- A **Source** fetches Records about an Entity. Sources are vertical-specific (e.g. Detroit assessor scraper) but conform to the same Protocol.
- A **GapFunction** computes a `GapResult` from records — the raw R-vs-f(M) divergence value.
- A **SignalRule** is a statute or contract clause that may modify or explain the gap (exemption, capped value, transfer-of-ownership exception). Rules with code `implementation` use that path; rules without fall back to the LLM interpreter applying `source_text`.
- A **Scorer** turns the gap + matched rules into a final `Signal` with severity tier and dollar impact.
- A **SignalStore** persists signals (currently `store/sqlite.py`).

The engine itself is vertical-agnostic; everything domain-specific lives in `verticals/`.
