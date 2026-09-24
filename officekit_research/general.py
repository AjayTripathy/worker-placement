"""General research: a security evaluated for NO particular investor.

The court's first pass. Its inputs are a symbol, an instrument kind and public
evidence — never an office, a mandate, a portfolio or a person. Inputs pass a
default-deny connector schema; publication separately requires a claim review.
Validation also refuses private field names and credential-shaped text.

A contextual court (officekit_ai.court) then rules on suitability for one
office and strategy ON TOP of this record. That ruling stays private.

Records are content-addressed and immutable. Freshness is a property of use,
not of the record: a reader decides how old is too old.
"""
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import math
import re

from officekit.migration import canonical, parse_json, SECRET
from officekit.office_lock import locked
from officekit_research.cases import (FACTORS, HASH, MAX_BYTES, _private_fields, _write, day, digest,
                                      exact, safe_url, strings, text)

SCHEMA = "general_research_v1"
STANDINGS = {"sound", "conditional", "impaired", "uninvestable"}
PUBLIC_SUBJECTS = {"stock", "etf"}          # listed securities: research on these may publish implicitly
SUBJECTS = PUBLIC_SUBJECTS | {"private"}    # a private company/deal: NEVER published without an explicit release
EXPOSURES = {"none", "low", "medium", "high"}
PRIVATE_SECTIONS = {"book", "program"}       # embed the office's holdings/facts
MAX_AGE_DAYS = 30
MAX_GENERAL = 2000
RUN_FIELDS = "requested_model resolved_model provider_client reasoning_configuration protocol_hash"


def public_pack(pack):
    """Default-deny projection. Connector names and caller labels grant no access.

    A trusted registry declaration AND the shared source's field schema are
    required. Errors are regenerated: raw exception strings can contain keys,
    requests or tenant data even when the connector's successful output is public.
    """
    from officekit_research import SOURCE_CLASSES
    from officekit_research.cases import source_of, validate_evidence
    pack = pack or {}
    sections, errors = {}, []
    for name, data in (pack.get("sections") or {}).items():
        visibility = SOURCE_CLASSES.get(name, "private")
        if visibility == "private":
            continue
        try:
            if visibility == "public_document":
                url, fetched = source_of(data)
                safe_url(url)
                validate_evidence({"section": name, "data": data, "source_url": url,
                                   "retrieved_at": fetched or pack.get("built")})
            elif name == "tape":
                exact(data, "last as_of wk52_hi wk52_lo off_high_pct off_low_pct", "market data")
                text(data["as_of"], 30)
                for key, value in data.items():
                    if key != "as_of" and (type(value) not in {int, float} or not math.isfinite(value)):
                        raise ValueError("Invalid market data")
            else:
                raise ValueError("No public field schema")
            _private_fields(data)
            if SECRET.search(canonical(data)):
                raise ValueError("Credential-shaped source content")
            sections[name] = data
        except (ValueError, KeyError, TypeError):
            errors.append(name + ": public evidence policy rejected this section")
    for error in pack.get("errors", []):
        name = str(error).split(":", 1)[0].strip()
        if SOURCE_CLASSES.get(name, "private") != "private":
            errors.append(name + ": source unavailable")
    return {"symbol": pack.get("symbol"), "built": pack.get("built"), "sections": sections, "errors": errors,
            "reuse": {k: v for k, v in (pack.get("reuse") or {}).items() if k in sections}}


def evidence_index(pack):
    """Locators and content hashes only; the documents stay with their source."""
    out = []
    for section, data in sorted(public_pack(pack)["sections"].items()):
        from officekit_research.cases import source_of
        url, fetched = source_of(data)
        try:
            safe_url(url)
        except ValueError:
            url = None
        origin = (pack.get("reuse") or {}).get(section, {})
        out.append({"section": section, "source_url": url,
                    "retrieved_at": day(origin.get("retrieved_at") or fetched or pack.get("built")).isoformat(),
                    "content_sha256": content_digest(section, data)})
    return out


def content_digest(section, data):
    """Hash what the source SAID, not when we asked. Two contributors reading
    identical content on different days must agree (see cases.content_sha256)."""
    from officekit_research.cases import content_sha256
    return content_sha256(section, data)


def seal(body):
    record = {"schema": SCHEMA, **body}
    record = {"id": digest(record), **record}
    return validate(record)


def validate(record):
    try:
        return _validate(record)
    except (KeyError, TypeError, AttributeError, OverflowError) as exc:
        raise ValueError("Malformed general research record") from exc


def _validate(r):
    exact(r, "id schema subject as_of assessment briefs evidence label tier models runs protocol_hash", "general research")
    if r["schema"] != SCHEMA or len(canonical(r)) > MAX_BYTES or SECRET.search(canonical(r)):
        raise ValueError("Unsupported, oversized or credential-bearing general research")
    if not HASH.fullmatch(r["id"]) or r["id"] != digest({k: v for k, v in r.items() if k != "id"}):
        raise ValueError("General research digest mismatch")
    _private_fields(r)
    exact(r["subject"], "symbol instrument", "subject")
    if not re.fullmatch(r"[A-Z0-9][A-Z0-9.^-]{0,14}", r["subject"]["symbol"]) or r["subject"]["instrument"] not in SUBJECTS:
        raise ValueError("Invalid general research subject")
    day(r["as_of"])
    a = r["assessment"]
    exact(a, "summary standing confidence factor_profile strengths risks kill_conditions unverified_items forecasts", "assessment")
    if not isinstance(a["forecasts"], list) or len(a["forecasts"]) > 5:
        raise ValueError("General research carries at most five forecasts")
    for f in a["forecasts"]:
        exact(f, "statement probability base_rate resolve_by", "forecast")
        text(f["statement"], 600)
        for key in ("probability", "base_rate"):
            if isinstance(f[key], bool) or not isinstance(f[key], (int, float)) or not 0 <= f[key] <= 1:
                raise ValueError("Forecast probabilities must be between 0 and 1")
        if not day(r["as_of"]) < day(f["resolve_by"]) <= day(r["as_of"]) + timedelta(days=760):
            raise ValueError("A forecast must resolve after the evaluation and within about two years")
    text(a["summary"])
    if a["standing"] not in STANDINGS or type(a["confidence"]) is not int or not 1 <= a["confidence"] <= 10:
        raise ValueError("Invalid general standing")
    if not isinstance(a["factor_profile"], list) or not 1 <= len(a["factor_profile"]) <= len(FACTORS):
        raise ValueError("General research needs a factor profile")
    seen = set()
    for f in a["factor_profile"]:
        exact(f, "factor exposure rationale", "factor exposure")
        if f["factor"] not in FACTORS - {"unknown"} or f["factor"] in seen or f["exposure"] not in EXPOSURES:
            raise ValueError("Invalid or duplicate factor exposure")
        seen.add(f["factor"])
        text(f["rationale"], 4000)
    for k in ("strengths", "risks", "kill_conditions", "unverified_items"):
        strings(a[k])
    exact(r["briefs"], "red blue", "general briefs")
    for brief in r["briefs"].values():
        exact(brief, "case key_points unverified lean", "bench")
        text(brief["case"], 96000)
        strings(brief["key_points"])
        strings(brief["unverified"])
    if r["label"] not in {"EVIDENCED", "LITE"} or r["tier"] not in {"tiered", "flat_tier", "unranked"}:
        raise ValueError("Invalid general research label")
    exact(r["models"], "bench adjudicate", "models")
    if not isinstance(r["runs"], dict) or set(r["runs"]) - {"red", "blue", "adjudicate"}:
        raise ValueError("Invalid general research runs")
    for run in r["runs"].values():
        exact(run, RUN_FIELDS, "agent run")
    if r["protocol_hash"] != "unknown" and not HASH.fullmatch(r["protocol_hash"]):
        raise ValueError("Invalid protocol identity")
    if not isinstance(r["evidence"], list) or len(r["evidence"]) > 8:
        raise ValueError("Invalid evidence index")
    for e in r["evidence"]:
        exact(e, "section source_url retrieved_at content_sha256", "evidence locator")
        from officekit_research import SOURCE_CLASSES
        if SOURCE_CLASSES.get(e["section"], "private") == "private" or not HASH.fullmatch(e["content_sha256"]):
            raise ValueError("Private or unhashed evidence in general research")
        if e["source_url"] is not None:
            safe_url(e["source_url"])
    return r


def _library(folder):
    library = Path(folder).resolve() / "research" / "general"
    if library.is_symlink() or library.parent.is_symlink():
        raise ValueError("Research library cannot follow symbolic links")
    return library


def save(folder, record, *, origin=None, attributions=()):
    validate(record)
    metadata = None
    if origin is not None:
        people = []
        for item in attributions:
            if not isinstance(item, dict) or item.get("record_id") != record["id"]:
                raise ValueError("Attribution does not identify this research")
            people.append({"contributor": item.get("contributor"), "attribution": item.get("attribution")})
        metadata = _origin({"record_id": record["id"], "origin": origin, "contributors": people}, record["id"])
    with locked(folder):
        library = _library(folder)
        path = library / (record["id"] + ".json")
        if len(list(library.glob("*.json"))) + (not path.exists()) > MAX_GENERAL:
            raise ValueError("This office's general research library is full")
        _write(path, record)
        if metadata is not None:
            # Local custody metadata is separate from immutable research. Import
            # and subsequent reuse must never mint a new author or record ID.
            meta = library.parent / "origins" / (record["id"] + ".json")
            if not meta.exists():
                _write(meta, metadata)
    return record["id"]


def _origin(meta, record_id):
    """Validate custody data separately from the immutable producer's record."""
    from officekit_research.contributor import valid
    exact(meta, "record_id origin contributors", "research origin")
    if meta["record_id"] != record_id or meta["origin"] not in {"own", "imported"}:
        raise ValueError("Invalid research origin")
    if not isinstance(meta["contributors"], list):
        raise ValueError("Invalid contributor attributions")
    people = {}
    for item in meta["contributors"]:
        exact(item, "contributor attribution", "contributor attribution")
        key, status = item["contributor"], item["attribution"]
        if not valid(key) or status not in {"claimed", "verified", "anonymous"} or (key is None) != (status == "anonymous"):
            raise ValueError("Invalid contributor attribution")
        # One producer contributes once to a forecast's calibration, even when
        # multiple transport envelopes name the same key.
        if key not in people or status == "verified":
            people[key] = item
    return {**meta, "contributors": [people[k] for k in sorted(people, key=lambda k: k or "")]}


def provenance(folder, record_id):
    """Read custody metadata; recover legacy origins from frozen proposals.

    Missing producer evidence is unknown, never an assertion of authorship.
    Legacy imports have no retained attribution and must stay unattributed.
    """
    if not HASH.fullmatch(str(record_id)):
        raise ValueError("Invalid general research identity")
    path = _library(folder).parent / "origins" / (record_id + ".json")
    if path.exists() and not path.is_symlink() and not path.parent.is_symlink():
        try:
            if path.stat().st_size <= MAX_BYTES:
                return _origin(parse_json(path.read_bytes()), record_id)
        except (ValueError, TypeError, OSError):
            pass
    from officekit.strategy_proposals import list_proposals
    for p in reversed(list_proposals(folder)):
        for entry in p.get("general", {}).values():
            if (entry.get("record") or {}).get("id") == record_id:
                if entry.get("source") in {"exchange", "hosted exchange"}:
                    return {"origin": "imported", "contributors": []}
                if entry.get("source") == "this proposal":
                    return {"origin": "own", "contributors": []}
    return {"origin": "unknown", "contributors": []}


def load_all(folder):
    out = []
    for path in sorted(_library(folder).glob("*.json")):
        try:
            if path.is_symlink() or path.stat().st_size > MAX_BYTES:
                continue
            record = validate(parse_json(path.read_bytes()))
            if path.stem == record["id"]:
                out.append(record)
        except (ValueError, OSError):
            continue                       # an invalid file is never evidence
    return out


def load(folder, general_id):
    if not HASH.fullmatch(str(general_id)):
        raise ValueError("Invalid general research identity")
    return next((r for r in load_all(folder) if r["id"] == general_id), None)


def find(folder, symbol, instrument, protocol_hash, today=None, minimum_tier=None, tier_of=None):
    """The newest still-usable general evaluation of this subject, or None.

    Usable = same protocol (a different doctrine is a different experiment),
    evidenced, fresh, and — when the reader can rank models — produced by an
    adjudicator at least as strong as the reader requires. Intelligence level
    is a gate here, not a label: weaker general research is re-run, not reused.
    """
    today = today or datetime.now(timezone.utc).date()
    best = None
    for r in load_all(folder):
        if r["subject"] != {"symbol": symbol.upper(), "instrument": instrument}:
            continue
        age = (today - day(r["as_of"])).days
        if not 0 <= age <= MAX_AGE_DAYS or r["protocol_hash"] != protocol_hash or r["label"] != "EVIDENCED":
            continue
        if minimum_tier is not None and tier_of is not None:
            produced = tier_of(r["models"]["adjudicate"])
            if produced is None or produced < minimum_tier:
                continue
        if best is None or day(r["as_of"]) > day(best["as_of"]):
            best = r
    return best
