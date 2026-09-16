"""court_dispatch — puts the desk's detector brain INSIDE every court (R1.11).

Principal diagnosis 2026-08-08: the KG holds 165 detectors / 44 mechanisms / 85
channels with APPLIES_TO dispatch contracts, and the courts were consulting NONE
of it — benches ran generic adversarial reasoning plus a static trap catalog.
That inverted the standing rule (route all DD through the pipeline, never ad hoc):
the courts WERE the ad hoc path relative to the detector library.

Mechanism (three-ring doctrine, applied to courts):
  Ring 0/1  atlas_for(ticker, context) queries knowledge_graph dispatch_index —
            applies_universally + SIC-prefix match (issuer SIC from SEC submissions,
            cached) + issuer_feature keyword match against the case context —
            and injects the matched entries into RED and BLUE prompts. Benches
            must file a DETECTORS CONSULTED section: each entry FIRED /
            NOT-FIRED / UNCHECKABLE(+what evidence would check it). Validator-
            enforced (an unconsulted atlas is a rejected artifact).
  Ring 2    benches are invited to propose NEW mechanism/detector candidates in
            ```kg_candidate json fences; harvest_candidates() collects them to
            knowledge_graph/candidates.jsonl at artifact-record time. The graph
            grows FROM the courts — the knowledge is the product; verdicts are
            byproducts.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KG = ROOT / "knowledge_graph" / "knowledge_graph.json"
CANDIDATES = ROOT / "knowledge_graph" / "candidates.jsonl"
SIC_CACHE = ROOT / "desk" / "data" / "issuer_sic_cache.json"
UA = "SignalOS research desk (contact: 4tripathy@gmail.com)"
MAX_ENTRIES = 14

_kg_cache: list | None = None


def _index() -> list:
    global _kg_cache
    if _kg_cache is None:
        _kg_cache = json.loads(KG.read_text()).get("dispatch_index", [])
    return _kg_cache


def _issuer_sic(ticker: str) -> str | None:
    try:
        cache = json.loads(SIC_CACHE.read_text())
    except Exception:
        cache = {}
    if ticker in cache:
        return cache[ticker]
    sic = None
    try:
        from desk.court_evidence import _cik
        cik = _cik(ticker)
        if cik:
            r = subprocess.run(["curl", "-s", "--max-time", "15",
                                f"https://data.sec.gov/submissions/CIK{cik:010d}.json",
                                "-H", f"User-Agent: {UA}"], capture_output=True, text=True)
            sic = str(json.loads(r.stdout).get("sic") or "") or None
    except Exception:
        pass
    cache[ticker] = sic
    try:
        SIC_CACHE.write_text(json.dumps(cache, indent=1))
    except Exception:
        pass
    return sic


def _feature_tokens(feature: str) -> list[str]:
    """'cayman_or_bvi_holdco' -> ['cayman', 'bvi', 'holdco'] (stopwords dropped)."""
    return [w for w in re.split(r"[_\W]+", feature.lower())
            if w and w not in ("or", "and", "of", "the", "a", "an", "claimed", "is")]


def atlas_for(ticker: str, context: str) -> list[dict]:
    """Dispatch-matched KG entries for this case, ranked SIC > feature > universal."""
    sic = _issuer_sic(ticker) if not ("." in ticker) else None   # SEC SIC = US filers only
    blob = context.lower()
    hits = []
    for e in _index():
        at = e.get("applies_to") or {}
        why = None
        if sic and (sic in [str(s) for s in at.get("sic_codes", [])]
                    or any(sic.startswith(str(p)) for p in at.get("sic_prefixes", []) if p)):
            why, rank = f"SIC {sic} match", 0
        elif at.get("issuer_features"):
            feats = [f for f in at["issuer_features"]
                     if any(re.search(rf"\b{re.escape(tok)}\b", blob)
                            for tok in _feature_tokens(f))]
            if feats:
                why, rank = f"feature match: {','.join(feats[:3])}", 1
        if why is None and at.get("applies_universally"):
            why, rank = "universal", 2
        if why:
            hits.append({"name": e.get("name"), "vertical": e.get("vertical"),
                         "kind": e.get("kind", "detector"),
                         "summary": (at.get("summary") or e.get("summary") or "")[:160],
                         "why": why, "_rank": rank})
    # Facilities-aware dispatch (2026-08-09, the BTDR blindspot): SIC lies about
    # physical footprint — a crypto miner files as finance (6199) yet operates data
    # centers. If the issuer's OWN Properties disclosure resolved real operating
    # sites, the physical-verification connectors get TOP rank regardless of SIC —
    # promote-not-inject: at 90+ raw feature hits the MAX_ENTRIES slice otherwise
    # truncates them in arbitrary index order (how BTDR's contested miss happened).
    try:
        from desk.facilities_resolver import resolve
        ops = [s for s in resolve(ticker).get("sites", [])
               if s.get("lat") is not None and not re.search(
                   r"office|headquarters|hq\b", (s.get("purpose") or "") + (s.get("name") or ""), re.I)]
    except Exception:
        ops = []
    if ops:
        site = ops[0]
        why = f"facilities-resolved: {site.get('name','site')[:40]} @ {site.get('location','')[:30]}"
        have = {h["name"]: h for h in hits}
        by = {e.get("name"): e for e in _index()}
        for name in ("sentinel2_buildout", "plant_thermal"):
            if name in have:
                have[name]["_rank"] = 0
                have[name]["why"] = why + " (+" + have[name]["why"] + ")"
            elif name in by:
                e = by[name]
                at = e.get("applies_to") or {}
                hits.append({"name": name, "vertical": e.get("vertical"),
                             "kind": e.get("kind", "m_source"),
                             "summary": (at.get("summary") or e.get("summary") or "")[:160],
                             "why": why, "_rank": 0})
    hits.sort(key=lambda h: h["_rank"])
    return hits[:MAX_ENTRIES]


def render_atlas(ticker: str, context: str) -> str:
    """The prompt section. NEVER empty — on any failure it still mandates the
    DETECTORS CONSULTED section (the validator requires it unconditionally)."""
    try:
        hits = atlas_for(ticker, context)
    except Exception as ex:
        hits = []
        note = f"(atlas query failed: {type(ex).__name__} — consult from first principles)"
    else:
        note = ""
    lines = [f"- {h['name']} [{h['vertical']}/{h['kind']}] ({h['why']}): {h['summary']}"
             for h in hits] or ["- (no dispatch-matched entries — the desk library may have a "
                                "coverage GAP here; say so explicitly)"]
    try:
        from desk.facilities_resolver import render_facilities
        fac = render_facilities(ticker)
        if fac:
            lines.append("\n" + fac)
    except Exception:
        pass
    return f"""## DESK DETECTOR ATLAS — dispatch-matched entries for {ticker} {note}
The desk maintains a validated detector/mechanism library (165 detectors, 44 mechanisms).
These entries matched this case's APPLIES_TO contracts:
{chr(10).join(lines)}

REQUIRED in your output — a section headed exactly "DETECTORS CONSULTED":
for EACH entry above, one line: name — FIRED (what it caught, with the evidence) /
NOT-FIRED (checked, clean) / UNCHECKABLE (name the missing evidence that would check it).
Do not skip entries; an unconsulted atlas is a validator reject.

RING-2 (invited, not required): if this case exhibits a mechanism the library does NOT
cover (a new dislocation cause, masking pattern, microstructure tell — e.g. the HTZ
JPM share-lend convert-arb supply), propose it as a candidate in a fenced block:
```kg_candidate
{{"name": "snake_case_name", "kind": "mechanism|detector", "one_line": "...", "fires_on": "...", "evidence_here": "...", "applies_to_guess": {{"issuer_features": [], "sic_prefixes": []}}}}
```
Candidates are harvested into the knowledge graph for session review — a good candidate
from a killed name outlives the verdict.
"""


CAND_PAT = re.compile(r"```kg_candidate\s*(\{.*?\})\s*```", re.S)


def harvest_candidates(ticker: str, stage: str, text: str) -> int:
    """Collect Ring-2 proposals from a bench artifact into candidates.jsonl."""
    n = 0
    for m in CAND_PAT.finditer(text):
        try:
            c = json.loads(m.group(1))
        except Exception:
            continue
        row = {"ticker": ticker, "stage": stage, "status": "proposed",
               "candidate": c}
        with CANDIDATES.open("a") as f:
            f.write(json.dumps(row) + "\n")
        n += 1
    return n
