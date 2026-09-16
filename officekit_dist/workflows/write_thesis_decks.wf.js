export const meta = {
  name: 'write-thesis-decks',
  description: 'Pitch-deck bot writes a strategy PACK (pack.json + DECK.md) per thesis sleeve',
  phases: [{ title: 'Write decks', detail: 'one pitch-builder agent per sleeve' },
           { title: 'Validate', detail: 'each pack must pass strategy_packs.validate' }],
}
// args: [{sid, name, thesis, edge, bucket, positions:[...]}] — the sleeves to write.
// Pass the sleeve list from the office (build_office desk_theses). No fs in the
// script itself; each AGENT writes the pack files with its own tools.
let sleeves = args
if (typeof sleeves === 'string') { try { sleeves = JSON.parse(sleeves) } catch (e) { sleeves = [] } }
if (!Array.isArray(sleeves)) sleeves = []
if (!sleeves.length) { log('no sleeves passed in args — nothing to write'); }

const results = await pipeline(
  sleeves,
  (s) => agent(
    `You are the pitch-deck bot. Write a Worker Placement STRATEGY PACK for the thesis sleeve "${s.sid}" (${s.name}).\n` +
    `Context — thesis: ${s.thesis || '(none on file; derive from the positions)'}; edge: ${s.edge || '?'}; ` +
    `suggested bucket: ${s.bucket || 'pick one'}; positions: ${(s.positions||[]).join(', ') || '(none)'}.\n` +
    `Do FIRST-PRINCIPLES diligence (Mode B disconfirm first), then write TWO files:\n` +
    `  strategies/${s.sid}/pack.json  — to the schema in strategies/CONTRIBUTING.md ` +
    `(id="${s.sid}", name, bucket ∈ {defensive,cyclical_value,growth,idiosyncratic}, thesis, author="pitch-bot", edge, positions, goal_kinds, betas)\n` +
    `  strategies/${s.sid}/DECK.md    — thesis, mechanism + falsifier, positions & sizing, risks/kill-triggers, and how it fits goals & scenarios. Honest: state the bear case.\n` +
    `Then VERIFY the pack is valid: run  python3 -c "from officekit import strategy_packs as p; import json; print(p.validate(json.load(open('strategies/${s.sid}/pack.json')),'strategies/${s.sid}'))"  and fix until it prints [].\n` +
    `Return one line: "<sid>: <bucket> — <n> positions, valid".`,
    { label: `deck:${s.sid}`, phase: 'Write decks', agentType: 'pitch-builder' }),
  (r, s) => agent(
    `Verify the strategy pack at strategies/${s.sid}/ is loadable and honest: run ` +
    `python3 -c "from officekit import strategy_packs as p; ps,pr=p.load_packs(); print([x for x in ps if x['id']=='${s.sid}'] and 'OK' or 'MISSING', pr)" ` +
    `— confirm it prints OK and no problems for ${s.sid}. Then skim DECK.md: does it state a falsifier / bear case? Return "<sid>: OK" or the exact problem.`,
    { label: `verify:${s.sid}`, phase: 'Validate', agentType: 'general-purpose' }))

log(`wrote ${results.filter(Boolean).length}/${sleeves.length} thesis packs`)
return results.filter(Boolean)
