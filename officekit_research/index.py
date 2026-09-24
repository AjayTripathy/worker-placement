"""The research index: everything this office knows, keyed and gradeable.

One queryable view over three kinds of research —

    general   the security, for no investor         (shareable by construction)
    ruling    suitability for THIS office/strategy  (private)
    case      a reviewed contextual case, imported  (someone else's investigation)

keyed by the dimensions research is actually asked about: WHO contributed it,
WHICH agent at WHAT intelligence level under WHICH protocol produced it, and
WHICH strategy it was serviced for — plus the factor profile of the subject.

The index is DERIVED: `build()` regenerates it from the office's own files, so
it can be deleted at any time and is never migrated. Two things are NOT
derived and are the durable record: the content-addressed research itself, and
`research/outcomes.jsonl` — the append-only log of how forecasts resolved.

Outcomes are what turn a library into a calibration engine. A forecast is
scored with the Brier score and benchmarked against its own stated BASE RATE —
never against a coin — because a lopsided category lets a forecaster who always
says "yes" look skilled. Skill is suppressed below MIN_RESOLVED resolutions:
a number from five forecasts is noise presented as knowledge.

This is the schema a central exchange would use. Nothing here touches a network.
"""
from datetime import datetime, timezone
import json
import hashlib
from pathlib import Path
import sqlite3

from officekit.office_lock import locked, transaction
from officekit_research import general as general_store
from officekit_research.cases import HASH, day, load_library, safe_url, text

MIN_RESOLVED = 20          # below this, report counts and Brier but never "skill"
GROUPS = {"adjudicate_model", "adjudicate_tier", "bench_model", "tier_label", "protocol_hash",
          "strategy", "contributor", "submitter", "agent", "submitter_agent", "kind", "symbol", "label"}

_SCHEMA = """
CREATE TABLE research (
    id TEXT PRIMARY KEY, kind TEXT NOT NULL, origin TEXT NOT NULL, contributor TEXT,
    symbol TEXT NOT NULL, instrument TEXT, as_of TEXT NOT NULL,
    strategy TEXT, life_stage TEXT, horizon TEXT, liquidity TEXT, country TEXT,
    bench_model TEXT, adjudicate_model TEXT, bench_tier INTEGER, adjudicate_tier INTEGER,
    tier_label TEXT, reasoning_configuration TEXT, protocol_hash TEXT, label TEXT,
    outcome_label TEXT, confidence INTEGER, general_id TEXT);
CREATE TABLE factor_exposure (research_id TEXT NOT NULL, factor TEXT NOT NULL, exposure TEXT NOT NULL,
    PRIMARY KEY (research_id, factor));
CREATE TABLE attribution (research_id TEXT NOT NULL, contributor TEXT, status TEXT NOT NULL);
CREATE TABLE forecasting_agent (research_id TEXT PRIMARY KEY, agent TEXT NOT NULL);
CREATE TABLE forecast (
    id TEXT PRIMARY KEY, research_id TEXT NOT NULL, statement TEXT NOT NULL,
    probability REAL NOT NULL, base_rate REAL NOT NULL, resolve_by TEXT NOT NULL,
    outcome INTEGER, resolved_at TEXT, source_url TEXT);
CREATE INDEX research_symbol ON research(symbol);
CREATE INDEX research_strategy ON research(strategy);
CREATE INDEX research_model ON research(adjudicate_model);
"""


def _tier(model):
    from officekit_ai.court import _tier_of
    return _tier_of(model)


def _reasoning(runs):
    run = (runs or {}).get("adjudicate") or {}
    value = run.get("reasoning_configuration")
    return value if isinstance(value, str) or value is None else json.dumps(value, sort_keys=True)


def index_path(folder):
    return Path(folder).resolve() / "research" / "index.sqlite"


def outcomes_path(folder):
    return Path(folder).resolve() / "research" / "outcomes.jsonl"


def load_outcomes(folder, known_by=None):
    """Latest resolution per forecast; a correction appends, it never rewrites."""
    path, out = outcomes_path(folder), {}
    if path.is_symlink() or any(p.is_symlink() for p in path.parents):
        raise ValueError("Research storage cannot follow symbolic links")
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if type(row.get('outcome')) is not bool:
            raise ValueError('Invalid research outcome: expected true or false')
        safe_url(row['source_url'])
        when = datetime.fromisoformat(row['resolved_at'])
        if when.tzinfo is None or when > datetime.now(timezone.utc):
            raise ValueError('Invalid research outcome timestamp')
        known = datetime.fromisoformat(row.get('recorded_at', row['resolved_at']))
        if known.tzinfo is None or known > datetime.now(timezone.utc) or known < when:
            raise ValueError('Invalid outcome capture timestamp')
        if known_by is not None and known.date() > known_by:
            continue
        out[row['forecast_id']] = row
    return out


def resolve(folder, forecast_id, outcome, source_url, note="", resolved_at=None):
    """Record how a forecast resolved. Append-only and sourced: an outcome
    without a public locator is an opinion, and is refused."""
    if type(outcome) is not bool:
        raise ValueError("A forecast resolves true or false")
    safe_url(source_url)
    text(note, 600)
    gid, _, n = str(forecast_id).partition(":")
    record = general_store.load(folder, gid) if HASH.fullmatch(gid) else None
    from officekit_research import predictions
    prediction = next((r for r in predictions.load(folder) if r['id'] == gid), None) if n == '0' else None
    if record is None and prediction is None or record is not None and (not n.isdigit() or int(n) >= len(record['assessment']['forecasts'])):
        raise ValueError("Unknown forecast")
    made = record['as_of'] if record else prediction['recorded_at']
    when = resolved_at or datetime.now(timezone.utc).isoformat()
    instant = datetime.fromisoformat(when)
    if instant.tzinfo is None or instant > datetime.now(timezone.utc):
        raise ValueError('Resolution time must include a timezone and cannot be in the future')
    if day(when) < day(made) or prediction and instant < datetime.fromisoformat(made):
        raise ValueError("A forecast cannot resolve before it was made")
    row = {"forecast_id": forecast_id, "outcome": bool(outcome), "resolved_at": when,
           "source_url": source_url, "note": note, "recorded_at": datetime.now(timezone.utc).isoformat()}
    with locked(folder):
        path = outcomes_path(folder)
        if path.is_symlink() or any(p.is_symlink() for p in path.parents):
            raise ValueError("Research storage cannot follow symbolic links")
        path.parent.mkdir(parents=True, exist_ok=True)
        previous = load_outcomes(folder).get(forecast_id)
        row['supersedes'] = hashlib.sha256(json.dumps(previous, sort_keys=True).encode()).hexdigest() if previous else None
        with open(path, "a", encoding='utf-8') as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


@transaction()
def build(folder):
    """Regenerate the index from the office's files. Returns the sqlite path."""
    from officekit_ai.court import load_adjudications
    folder = Path(folder)
    rows, factors, forecasts, attributions, agents = [], [], [], [], []
    from officekit_research import predictions
    outcomes = load_outcomes(folder)

    for r in general_store.load_all(folder):
        agents.append((r["id"], predictions.agent_identity(r)))
        m = r["models"]
        provenance = general_store.provenance(folder, r["id"])
        people = provenance["contributors"]
        who = "self" if provenance["origin"] == "own" else (people[0]["contributor"] if len(people) == 1 else None)
        attributions += [(r["id"], item["contributor"], item["attribution"]) for item in people]
        rows.append((r["id"], "general", provenance["origin"], who, r["subject"]["symbol"], r["subject"]["instrument"], r["as_of"],
                     None, None, None, None, None, m["bench"], m["adjudicate"], _tier(m["bench"]), _tier(m["adjudicate"]),
                     r["tier"], _reasoning(r["runs"]), r["protocol_hash"], r["label"],
                     r["assessment"]["standing"], r["assessment"]["confidence"], None))
        factors += [(r["id"], f["factor"], f["exposure"]) for f in r["assessment"]["factor_profile"]]
        for i, f in enumerate(r["assessment"]["forecasts"]):
            fid = f"{r['id']}:{i}"
            o = outcomes.get(fid)
            if o and day(o['resolved_at']) < day(r['as_of']):
                raise ValueError('Research outcome predates forecast')
            forecasts.append((fid, r["id"], f["statement"], float(f["probability"]), float(f["base_rate"]), f["resolve_by"],
                              None if o is None else int(o["outcome"]), o and o["resolved_at"], o and o["source_url"]))

    for r in predictions.load(folder):
        rid = r['id']
        rows.append((rid, 'prediction', 'own', r['submitter'], r['symbol'], None, r['recorded_at'],
                     r['strategy'] or None, None, None, None, None, None, r['model'], None, _tier(r['model']),
                     None, None, r['protocol'], None, None, None, None))
        attributions.append((rid, r['submitter'], 'claimed'))
        agents.append((rid, r['agent'] + ' / ' + r['model'] + ' / ' + r['protocol']))
        o = outcomes.get(rid + ':0')
        if o and datetime.fromisoformat(o['resolved_at']) < datetime.fromisoformat(r['recorded_at']):
            raise ValueError('Prediction outcome predates capture')
        forecasts.append((rid + ':0', rid, r['statement'] + ' — ' + r['resolution_criteria'],
                          r['probability'], r['base_rate'], r['resolve_by'],
                          None if o is None else int(o['outcome']), o and o['resolved_at'], o and o['source_url']))

    for a in load_adjudications(folder):
        if not a.get("id") or not a.get("symbol"):
            continue
        m = a.get("models") or {}
        verdict, _, rest = str(a.get("verdict", "")).partition(" ")
        conviction = rest.split("/")[0] if "/" in rest else None
        label = "EVIDENCED" if "(EVIDENCED)" in str(a.get("verdict")) else "LITE" if "(LITE)" in str(a.get("verdict")) else None
        rows.append((a["id"], "ruling", "own", "self", a["symbol"], None, a.get("date") or "", a.get("strategy"),
                     None, None, None, None, m.get("bench"), m.get("adjudicate"), _tier(m.get("bench")), _tier(m.get("adjudicate")),
                     a.get("tier"), _reasoning(a.get("runs")), ((a.get("runs") or {}).get("adjudicate") or {}).get("protocol_hash"),
                     label, verdict or None, int(conviction) if conviction and conviction.isdigit() else None, a.get("general_id")))

    bundles, _ = load_library(folder)
    for b in bundles:
        c = b["case"]
        m, ctx = c["court"]["models"], c["context"]
        verdict = c["court"]["verdict"].partition(" ")[0]
        # A contextual case is anonymous unless its reviewer opted in to a pseudonym.
        rows.append((b["id"], "case", "imported", b["review"].get("contributor"), c["subject"]["symbol"], c["subject"]["instrument"], c["as_of"][:10],
                     ctx["strategy"], ctx["life_stage"], ctx["horizon"], ctx["liquidity"], ctx["country"],
                     m["bench"], m["adjudicate"], _tier(m["bench"]), _tier(m["adjudicate"]), None,
                     (c["provenance"]["runs"].get("adjudicate") or {}).get("reasoning_configuration"),
                     c["provenance"]["protocol_hash"], None, verdict, None, c["court"].get("general_id")))

    with locked(folder):
        path = index_path(folder)
        if path.is_symlink() or any(p.is_symlink() for p in path.parents):
            raise ValueError("Research storage cannot follow symbolic links")
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".building")
        temporary.unlink(missing_ok=True)
        db = sqlite3.connect(temporary)
        try:
            db.executescript(_SCHEMA)
            db.executemany("INSERT OR REPLACE INTO research VALUES (" + ",".join("?" * 23) + ")", rows)
            db.executemany("INSERT OR REPLACE INTO factor_exposure VALUES (?,?,?)", factors)
            db.executemany("INSERT INTO attribution VALUES (?,?,?)", attributions)
            db.executemany("INSERT INTO forecasting_agent VALUES (?,?)", agents)
            db.executemany("INSERT OR REPLACE INTO forecast VALUES (?,?,?,?,?,?,?,?,?)", forecasts)
            db.commit()
        finally:
            db.close()
        temporary.replace(path)
    return path


@transaction()
def forecast_rows(folder):
    """One row per prediction and original submitter. Imported identity is retained."""
    db = sqlite3.connect(build(folder))
    db.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in db.execute(
            "SELECT f.*, r.kind, r.symbol, r.as_of, r.strategy, r.label, r.protocol_hash, "
            "r.adjudicate_model, r.adjudicate_tier, r.bench_model, r.tier_label, g.agent, "
            "COALESCE(a.contributor,r.contributor) AS contributor, COALESCE(a.status, r.origin) AS attribution "
            "FROM forecast f JOIN research r ON r.id=f.research_id "
            "JOIN forecasting_agent g ON g.research_id=r.id "
            "LEFT JOIN attribution a ON a.research_id=r.id ORDER BY f.resolve_by,f.id")]
    finally:
        db.close()


def summarize(rows, group_by, today=None):
    """Unique forecasts, visible denominators and a descriptive pooled estimate.

    The pool contributes at most 20 observations from OTHER forecasts, excluding
    every forecast in the group. It is smoothing, not a confidence interval or a
    routing/eligibility gate. Correlated events do not become independent trials.
    """
    from officekit_research.predictions import joint_identity
    today = (today or datetime.now(timezone.utc).date()).isoformat()
    groups, all_scored = {}, {}
    for row in rows:
        if row['as_of'][:10] > today:
            continue
        r = dict(row)
        r['submitter'] = r['contributor']
        r['submitter_agent'] = joint_identity(r['contributor'], r['agent'])
        # Historical reports must not consume outcomes learned later.
        if r.get('resolved_at') and r['resolved_at'][:10] > today:
            r['outcome'] = None
        groups.setdefault(r[group_by], {})[r['id']] = r
        if r['outcome'] is not None:
            all_scored[r['id']] = (r['probability'] - r['outcome']) ** 2
    result = []
    for key, members in sorted(groups.items(), key=lambda pair: (-len(pair[1]), str(pair[0]))):
        values = list(members.values())
        scored = [r for r in values if r['outcome'] is not None]
        n = len(scored)
        brier = sum((r['probability'] - r['outcome']) ** 2 for r in scored) / n if n else None
        reference = sum((r['base_rate'] - r['outcome']) ** 2 for r in scored) / n if n else None
        others = [v for fid, v in all_scored.items() if fid not in members]
        weight = min(MIN_RESOLVED, len(others))
        pooled = (n * brier + weight * sum(others) / len(others)) / (n + weight) if n and weight else None
        enough = n >= MIN_RESOLVED and bool(reference)
        result.append({group_by: key, 'forecasts': len(values), 'resolved': n,
                       'pending': len(values) - n,
                       'overdue_unresolved': sum(r['outcome'] is None and r['resolve_by'] < today for r in values),
                       'brier': round(brier, 4) if brier is not None else None,
                       'brier_base_rate': round(reference, 4) if reference is not None else None,
                       'pooled_brier': round(pooled, 4) if pooled is not None else None,
                       'pool_resolved': len(others), 'pool_weight': weight,
                       'attribution': sorted({r.get('attribution', 'unknown') for r in values}),
                       'skill_vs_base_rate': round(1 - brier / reference, 3) if enough else None,
                       'note': None if enough else f'needs {MIN_RESOLVED} resolved forecasts and a nonzero baseline before skill is reported'})
    return result


def scoreboard(folder, group_by="adjudicate_model", today=None):
    if group_by not in GROUPS:
        raise ValueError('Unsupported grouping')
    rows = forecast_rows(folder)
    if today is not None:
        known = load_outcomes(folder, known_by=today)
        for r in rows:
            o = known.get(r['id'])
            r.update(outcome=None if o is None else int(o['outcome']), resolved_at=o and o['resolved_at'])
    return summarize(rows, group_by, today)


@transaction()
def query(folder, symbol=None, strategy=None, minimum_tier=None, kind=None):
    """All research on a subject, optionally gated by the intelligence that produced it."""
    clauses, values = [], []
    for column, value in (("symbol", symbol and symbol.upper()), ("strategy", strategy), ("kind", kind)):
        if value:
            clauses.append(f"{column} = ?")
            values.append(value)
    if minimum_tier is not None:
        clauses.append("adjudicate_tier >= ?")
        values.append(int(minimum_tier))
    db = sqlite3.connect(build(folder))
    db.row_factory = sqlite3.Row
    try:
        sql = "SELECT * FROM research" + (" WHERE " + " AND ".join(clauses) if clauses else "") + " ORDER BY as_of DESC, id"
        result = [dict(row) for row in db.execute(sql, values)]
        for row in result:
            row["contributors"] = [dict(item) for item in db.execute(
                "SELECT contributor, status FROM attribution WHERE research_id = ? ORDER BY contributor", (row["id"],))]
        return result
    finally:
        db.close()
