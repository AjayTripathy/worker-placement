"""personal_context — plane 2 of the agent memory model: the tenant's own
constraints, as a first-class contract.

Ruling (principal, 2026-09-04): personal context never ships as content but
ALWAYS ships as structure. Every shipped agent must load its tenant's
personal-context document before advising — require() is the gate, and an
empty-but-asserted document counts (the tenant has said "no constraints"),
while a MISSING document does not. Deterministic checks enforce what code can
enforce (exclusions); agents consume the rest (doctrine, coordination
surfaces) as directive input.

Contract #9 (personal_context.json, office folder):
  office_id     the office's UUID (join key, same as every other document)
  v             schema version (1)
  exclusions[]  {scope: ticker|issuer|sector, value, reason?, date?} —
                assets the office must never hold or be advised into
                (employment conflicts, ethical lines). Checked in CODE at
                build time, not just prompted.
  jurisdictions {tax_state?, country?} — governs tax posture reads
  doctrine[]    {id, rule, date?} — the principal's standing rulings in plain
                language ("no premium selling in taxable", "net buyer: no
                index insurance while cash-rich"); agents must argue within
                them, and cite the id when a ruling shapes an answer
  external[]    {name, why} — holdings/accounts OUTSIDE this office that
                advice must coordinate with (wash-sale surfaces, a spouse's
                ballast fund that must never be duplicated)
  notes[]       free-text context that fits nowhere above

Privacy: this document is the most personal thing an office emits. It is
NEVER an input to the learning ledger's shareable path, never leaves through
export_shareable(), and at the hosted tier it uploads only as the tenant's own
envelope-encrypted document — the cross-tenant learning store never sees it.
"""
from __future__ import annotations

import json
from pathlib import Path

SCOPES = ("ticker", "issuer", "sector")


def validate(pc):
    """Return a list of problems (empty = valid)."""
    p = []
    if not isinstance(pc, dict):
        return ["personal_context must be a dict"]
    if pc.get("v") != 1:
        p.append("personal_context: v must be 1")
    for i, e in enumerate(pc.get("exclusions") or []):
        if e.get("scope") not in SCOPES:
            p.append(f"personal_context.exclusions[{i}]: scope must be one of {SCOPES}")
        if not e.get("value"):
            p.append(f"personal_context.exclusions[{i}]: value is required")
    for i, d in enumerate(pc.get("doctrine") or []):
        if not d.get("id") or not d.get("rule"):
            p.append(f"personal_context.doctrine[{i}]: id and rule are required")
    for i, x in enumerate(pc.get("external") or []):
        if not x.get("name"):
            p.append(f"personal_context.external[{i}]: name is required")
    return p


def empty(office_id=None):
    """The empty-but-asserted document every new office gets at onboarding:
    structure present, content the tenant's to fill."""
    pc = {"v": 1, "exclusions": [], "jurisdictions": {}, "doctrine": [],
          "external": [], "notes": []}
    if office_id:
        pc = {"office_id": office_id, **pc}
    return pc


def load(folder):
    """Load personal_context.json from an office folder, or None if absent.
    Raises on an invalid document — a malformed constraint file must never be
    silently ignored."""
    path = Path(folder) / "personal_context.json"
    if not path.exists():
        return None
    pc = json.loads(path.read_text(encoding="utf-8"))
    probs = validate(pc)
    if probs:
        raise ValueError("personal_context.json invalid: " + "; ".join(probs))
    return pc


def require(pc, capability="advise"):
    """The plane-2 gate: shipped agents call this before doing anything.
    An empty document passes (the tenant asserted no constraints); a missing
    one refuses, loudly."""
    if pc is None:
        raise RuntimeError(
            f"personal context required: no personal_context.json loaded — an agent "
            f"never {capability}s without the tenant's constraints (empty is fine; "
            f"absent is not)")
    return pc


def check_exclusions(data, pc):
    """Deterministic enforcement of what code can enforce: return violations —
    sleeves or holdings matching an excluded ticker/issuer (substring match on
    names, exact match on holding symbols). Sector exclusions are advisory
    (agents enforce); code has no sector map to check against."""
    out = []
    for e in (pc or {}).get("exclusions") or []:
        if e["scope"] == "sector":
            continue
        val = str(e["value"]).upper()
        for s in data.get("sleeves") or []:
            if val in str(s.get("name", "")).upper().split() or val in [
                    w.strip("()") for w in str(s.get("name", "")).upper().split()]:
                out.append({"exclusion": e, "where": f'sleeve "{s.get("name")}"'})
            for h in s.get("holdings") or []:
                if str(h.get("company", "")).upper() == val:
                    out.append({"exclusion": e,
                                "where": f'holding {h.get("company")} in "{s.get("name")}"'})
    return out
