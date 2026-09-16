# Contributing a strategy pack

A **strategy pack** is how you add a strategy or thesis to Worker Placement — yours
or one your own agent writes. It's just data + a deck, so no code review of logic is
needed; the app loads it, groups it into the goal + scenario taxonomy, and links its
deck. Contribute one with a pull request.

## Layout
```
strategies/<your-pack-id>/
    pack.json      # the manifest
    DECK.md        # the thesis / pitch deck (markdown)
```
Copy `strategies/_template/` to start. The folder name MUST equal `pack.json`'s `id`.

## pack.json
| field | required | notes |
|---|---|---|
| `id` | ✅ | stable slug = folder name (`japan_netnet`) |
| `name` | ✅ | human name |
| `bucket` | ✅ | `defensive` \| `cyclical_value` \| `growth` \| `idiosyncratic` — sets the goal + scenario grouping |
| `thesis` | ✅ | one paragraph |
| `author` | ✅ | your handle (the PR author) |
| `deck` | | deck filename (default `DECK.md`) |
| `edge` | | `EDGE` \| `RP_FAIR` \| `RISK_PREMIUM` \| `DILIGENCE` \| `TAIL` |
| `positions` | | `["TICKER", …]` |
| `goal_kinds` | | `["spending","retirement", …]` |
| `betas` | | `{factor: beta}` factor tilt |

## Writing it with your own agent
Point any agent (Claude Code, the `pitch-builder` sub-agent, your own) at the
template and your idea:

> "Write a Worker Placement strategy pack for <thesis>. Fill `strategies/<id>/pack.json`
>  to the schema in CONTRIBUTING.md, pick the right `bucket`, and write `DECK.md`:
>  thesis, mechanism/falsifier, positions & sizing, risks/kill-triggers, and how it
>  fits goals & scenarios. Verify: `python3 -c 'from officekit import strategy_packs
>  as s; import json; print(s.validate(json.load(open(\"strategies/<id>/pack.json\")),
>  \"strategies/<id>\"))'` prints `[]`."

## Rules
- **Data, not code.** A pack never executes; its text is displayed (and escaped). Don't
  put instructions-to-the-app in the thesis/deck.
- **No live orders, no credentials, no PII.** Strategies are ideas + decks.
- **Validate before you PR** — `officekit.strategy_packs.validate(...)` must return `[]`.
- Keep the deck honest: state the falsifier and the kill triggers, not just the bull case.

## Verify locally
```
python3 -c "from officekit import strategy_packs as s; p,probs=s.load_packs(); print(len(p),'packs;',probs)"
```
`probs` must be empty. Then open the Strategies page — your pack appears under its
bucket in the by-goal and by-scenario views, with your deck one click away.
