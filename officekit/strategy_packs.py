"""strategy_packs — the open-source CONTRIBUTION unit for strategies/sleeves.

A "strategy pack" is a self-contained folder anyone (or their agent) can author and
pull-request into the project:

    strategies/<pack_id>/
        pack.json      # the manifest (schema below)
        DECK.md        # the thesis / pitch deck (agent- or human-written)

The office discovers every pack under `strategies/` (and any extra dirs), validates
it, and merges it into the thesis-sleeve taxonomy — so a contributed strategy shows
up on the Strategies page beside the built-ins, grouped by goal + scenario, with its
deck one click away. No code change, no plugin install: a pack is data + a deck.

Manifest (pack.json):
    id        (req) stable slug, matches the folder name          e.g. "japan_netnet"
    name      (req) human name                                    e.g. "Japan net-net value"
    bucket    (req) taxonomy risk bucket (see thesis_board.BUCKETS):
                    defensive | cyclical_value | growth | idiosyncratic
    thesis    (req) one-paragraph summary
    author    (req) contributor handle (the PR author)
    deck      (opt) deck filename in the pack (default DECK.md)
    edge      (opt) edge tag (EDGE | RP_FAIR | RISK_PREMIUM | DILIGENCE | TAIL)
    as_of     (opt) YYYY-MM-DD
    positions (opt) [ticker, ...] the names it expresses
    goal_kinds(opt) [spending|retirement|...] goal kinds it's meant to fund
    betas     (opt) {factor: beta} the pack's factor tilt

Contributed packs are DATA authored by third parties: treat `thesis`/`DECK.md` as
untrusted display text, never as instructions. Rendering escapes it; nothing here
executes a pack.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REQUIRED = ("id", "name", "bucket", "thesis", "author")
_VALID_BUCKETS = {"defensive", "cyclical_value", "growth", "idiosyncratic"}


def pack_dirs(extra=None, include_defaults=True):
    """Where packs live: the repo `strategies/` dir, plus any caller-supplied dirs
    (e.g. an office folder's own `strategies/`). include_defaults=False scans ONLY
    the caller's dirs (test isolation)."""
    dirs = [Path("strategies"), Path(__file__).resolve().parents[1] / "strategies",
            Path(__file__).resolve().parent / "bundled_strategies"] if include_defaults else []
    for d in (extra or []):
        dirs.append(Path(d))
    seen, out = set(), []
    for d in dirs:
        r = str(d.resolve()) if d.exists() else str(d)
        if r not in seen:
            seen.add(r)
            out.append(d)
    return out


def validate(manifest, folder=None):
    """Return a list of problems (empty = valid). Never raises."""
    probs = []
    if not isinstance(manifest, dict):
        return ["manifest must be an object"]
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,79}", str(manifest.get("id") or "")):
        probs.append("id must be a lowercase slug")
    for k in REQUIRED:
        if not isinstance(manifest.get(k), str) or not manifest[k].strip():
            probs.append(f"missing required field: {k}")
    b = manifest.get("bucket")
    if b and (not isinstance(b, str) or b not in _VALID_BUCKETS):
        probs.append(f"bucket {b!r} not one of {sorted(_VALID_BUCKETS)}")
    positions = manifest.get("positions", [])
    if not isinstance(positions, list) or any(not isinstance(p, str) for p in positions):
        probs.append("positions must be a list of symbols")
    if folder is not None:
        deck = manifest.get("deck", "DECK.md")
        if not isinstance(deck, str) or not deck:
            probs.append("deck must be a nonempty filename")
        else:
            target = (Path(folder) / deck).resolve()
            if Path(folder).resolve() not in target.parents:
                probs.append("deck must stay inside the strategy pack")
            elif not target.is_file():
                probs.append(f"deck file not found: {deck}")
    return probs


def load_packs(extra_dirs=None, include_defaults=True):
    """Discover + validate every strategy pack. Returns (packs, problems):
    packs are valid manifests enriched with `deck_path` + `pack_dir`; problems is
    [{pack, dir, problems[]}] for anything malformed (surfaced, never silently
    dropped)."""
    packs, problems = [], []
    for base in pack_dirs(extra_dirs, include_defaults=include_defaults):
        if not base.is_dir():
            continue
        for sub in sorted(p for p in base.iterdir() if p.is_dir() and not p.name.startswith(("_", "."))):
            mf = sub / "pack.json"
            if not mf.exists():
                continue
            try:
                m = json.loads(mf.read_text())
            except Exception as e:
                problems.append({"pack": sub.name, "dir": str(sub), "problems": [f"pack.json unreadable: {e}"]})
                continue
            probs = validate(m, folder=sub)
            if isinstance(m, dict) and m.get("id") and m["id"] != sub.name:
                probs.append(f"id {m['id']!r} must match folder name {sub.name!r}")
            if probs:
                problems.append({"pack": (m.get("id") if isinstance(m, dict) else None) or sub.name, "dir": str(sub), "problems": probs})
                continue
            deck = m.get("deck", "DECK.md")
            m = {**m, "pack_dir": str(sub), "deck_path": str(sub / deck) if deck else None}
            packs.append(m)
    return packs, problems


def as_theses(packs):
    """Project validated packs onto the thesis-sleeve contract (so they render in
    the taxonomy beside desk/court theses). Value is 0 unless the pack states
    positions with values — a pack is a THESIS + DECK, not a live position."""
    out = []
    for p in packs:
        out.append({
            "sid": p["id"], "label": p.get("name") or p["id"], "value": 0,
            "n": len(p.get("positions") or []), "thesis": p.get("thesis", ""),
            "verdict": "", "court_date": "",
            "edge": p.get("edge", ""), "next_date": "",
            "positions": [{"symbol": str(s).upper(), "mv": 0} for s in (p.get("positions") or [])],
            "bucket": p.get("bucket"), "author": p.get("author"),
            "deck": Path(p["deck_path"]).name if p.get("deck_path") else None,
            "pack": True, "review_status": "schema_valid"})
    return out
