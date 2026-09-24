"""Contextual cases: private capture, reviewable projection and portable exchange.

No network writes. Review is an attribution, not a proof of anonymity or truth.
Only reviewed source grants permit reuse; the recipient always runs its own court.
"""
from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
import re
from urllib.parse import urlsplit

from officekit.migration import canonical, parse_json, SECRET
from officekit.office_lock import locked

SCHEMA = "contextual_research_case_v1"
POLICY = "context_projection_v1"
MAX_BYTES = 512 * 1024
MAX_CASES = 1000
MAX_LIBRARY_BYTES = 32 * 1024 * 1024
PUBLIC_SECTIONS = {"fund_profile", "filings", "xbrl", "filing_text"}
CONTEXT_VALUES = {
    "life_stage": {"accumulating", "decumulating", "unknown"},
    "horizon": {"under_2y", "2_to_7y", "over_7y", "unknown"},
    "liquidity": {"dated_spending", "ongoing_spending", "reserve", "unspecified"},
    "country": {"US", "non_US", "unknown"},
}
GOALS = {"retirement", "spending", "liquidity_floor", "risk_reduction", "growth", "unknown"}
FACTORS = {"equity", "sector_concentration", "duration", "inflation", "liquidity", "tax", "convexity", "unknown"}
PRIVATE_KEYS = {"office_id", "user_id", "account_id", "account_number", "owner", "personal_context", "snapshot", "funding", "positions", "book"}
HASH = re.compile(r"[a-f0-9]{64}\Z")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


# Envelope fields say WHEN/HOW a source was read, not what it said.
ENVELOPE = {"fetched_at", "retrieved_at"}

# How long a contributor may grant reuse, by what KIND of thing the evidence is.
# A judgment about a household expires fast; a live web page drifts; a document
# filed with a regulator never changes (only newer ones appear). One number for
# all three made the corpus forget facts as quickly as opinions.
EVIDENCE_TTL_DAYS = {
    "fund_profile": 30,     # live issuer page — a snapshot that drifts
    "filings": 30,          # "most recent filings" index — stale when the next one lands
    "xbrl": 120,            # as-filed facts; one reporting quarter plus slack before a newer period exists
    "filing_text": 400,     # the text of one dated filing — immutable; covers an annual cycle
}
XBRL_KEYS = {"rev", "sbc", "dil_sh", "ocf"}
XBRL_FORMS = {"10-Q", "10-K", "20-F", "6-K"}


def source_of(data):
    """(url, fetched_at) for a section, wherever that section keeps its locator."""
    if not isinstance(data, dict):
        return None, None
    meta = data.get("_source") if isinstance(data.get("_source"), dict) else data
    return meta.get("url"), meta.get("fetched_at")


def content_sha256(section, data):
    """Identity of what a source SAID, independent of when it was read.

    `sha256` on an evidence entry covers the whole envelope (integrity of the
    exact bytes reviewed). Conflict detection must not use it: two contributors
    reading byte-identical text an hour apart would otherwise "contradict" each
    other and nobody could reuse either — reuse would collapse as the corpus
    grew. Whitespace is normalized because fetchers differ in trailing space.
    """
    if not isinstance(data, dict):
        return digest({"section": section, "content": data})
    def strip(value):
        if isinstance(value, dict):
            return {k: (" ".join(v.split()) if k == "text" and isinstance(v, str) else strip(v))
                    for k, v in value.items() if k not in ENVELOPE}
        if isinstance(value, list):
            return [strip(v) for v in value]
        return value
    return digest({"section": section, "content": strip(data)})


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def day(value):
    if not isinstance(value, str):
        raise ValueError("Research dates must be ISO dates or timestamps")
    return date.fromisoformat(value[:10])


def exact(value, keys, label):
    if not isinstance(value, dict) or set(value) != set(keys.split()):
        raise ValueError("Invalid " + label + " fields")


def text(value, limit=16000):
    if not isinstance(value, str) or len(value) > limit:
        raise ValueError("Invalid or oversized research text")


def strings(value, limit=40):
    if not isinstance(value, list) or len(value) > limit:
        raise ValueError("Invalid research list")
    for item in value:
        text(item)


def safe_url(value):
    text(value, 2000)
    u = urlsplit(value)
    if u.scheme != "https" or not u.hostname or u.username or u.password or u.query or u.fragment:
        raise ValueError("Research sources need public HTTPS URLs without credentials or query strings")


def _private_fields(value):
    if isinstance(value, dict):
        if PRIVATE_KEYS.intersection(value):
            raise ValueError("A public case contains private office fields")
        for child in value.values():
            _private_fields(child)
    elif isinstance(value, list):
        for child in value:
            _private_fields(child)


def validate_context(ctx):
    exact(ctx, "strategy goal_types goal_basis life_stage horizon liquidity country", "research context")
    text(ctx["strategy"], 80)
    if not re.fullmatch(r"[a-z][a-z0-9_]{0,79}", ctx["strategy"]):
        raise ValueError("Invalid strategy context")
    strings(ctx["goal_types"], 8)
    if not ctx["goal_types"] or not set(ctx["goal_types"]) <= GOALS:
        raise ValueError("Unsupported research goal")
    if ctx["goal_basis"] not in {"linked_goal", "strategy_template", "declared", "unknown"}:
        raise ValueError("Invalid goal attribution")
    for field, choices in CONTEXT_VALUES.items():
        if ctx[field] not in choices:
            raise ValueError("Invalid research context: " + field)
    return ctx


def proposal_context(p):
    """Only declared facts and labeled template inferences; never infer a person."""
    from officekit.strategy_playbooks import STRATEGY_DEFAULT
    a = p["snapshot"]["answers"]
    pc = p["snapshot"].get("personal_context") or {}
    profile = a.get("profile") or {}
    stage = profile.get("decumulating")
    if p.get("research_context") is not None:
        ctx = deepcopy(validate_context(p["research_context"]))
        country = pc.get("jurisdictions", {}).get("country")
        known = {"life_stage": "decumulating" if stage is True else "accumulating" if stage is False else "unknown",
                 "country": "US" if country in {"US", "USA", "United States"} else "non_US" if country else "unknown"}
        for key, value in known.items():
            if value != "unknown" and ctx[key] != value:
                raise ValueError("Declared research context conflicts with saved office facts: " + key)
        return ctx
    sid = p["strategy_id"] if p["strategy_id"] in STRATEGY_DEFAULT else "custom"
    goal = next((g for g in a.get("goals", []) if p["source"] == "goal" and g.get("id") == p["source_ref"]), {})
    kind = goal.get("kind", "unknown")
    kind = kind if kind in GOALS else "unknown"
    basis = "linked_goal" if goal else "unknown"
    if not goal and p["source"] == "scenario":
        kind, basis = "risk_reduction", "strategy_template"
    horizon = "unknown"
    due = goal.get("date") or goal.get("target_date")
    if due and a.get("as_of"):
        years = (day(due) - day(a["as_of"])).days / 365.25
        horizon = "under_2y" if years < 2 else "2_to_7y" if years <= 7 else "over_7y"
    country = pc.get("jurisdictions", {}).get("country")
    return {"strategy": sid, "goal_types": [kind], "goal_basis": basis,
            "life_stage": "decumulating" if stage is True else "accumulating" if stage is False else "unknown",
            "horizon": horizon, "liquidity": {"spending": "dated_spending", "retirement": "ongoing_spending",
                "liquidity_floor": "reserve"}.get(kind, "unspecified"),
            "country": "US" if country in {"US", "USA", "United States"} else "non_US" if country else "unknown"}


def factor_topics(strategy):
    """Investigation topics from the mandate, not measured asset exposures."""
    return {"deploy_powder": ["equity", "sector_concentration"], "cash_mgmt": ["liquidity", "duration"],
            "core_equity": ["equity"], "bonds": ["duration"], "muni": ["tax", "duration"],
            "duration_mgmt": ["duration"], "real_assets": ["inflation"],
            "concentrated": ["sector_concentration", "tax"], "index_hedge": ["equity", "convexity"]}.get(strategy, ["unknown"])


def _write(path, value):
    if path.is_symlink() or any(p.is_symlink() for p in path.parents):
        raise ValueError("Research storage cannot follow symbolic links")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    if temporary.is_symlink():
        raise ValueError("Research temporary file is a symbolic link")
    temporary.write_bytes(canonical(value) + b"\n")
    temporary.replace(path)


def capture_private(folder, p):
    """The original proposal remains the exact source; no reconstructed motives."""
    import uuid
    pid = str(uuid.UUID(p["id"]))
    record = {"schema": SCHEMA, "proposal_id": pid, "office_id": p["snapshot"]["data"].get("office_id"),
              "proposal_digest": digest(p), "context": proposal_context(p),
              "question": {"source": p["source"], "request": p["brief"].get("request", ""), "brief": p["brief"]["thesis"]},
              "agent_recommendation": deepcopy(p.get("research")),
              "court_ids": [c["id"] for c in p.get("courts", [])],
              "decision": {"status": p["status"], "reason": None, "reason_origin": "not_recorded", "execution": "unconfirmed"},
              "reused_case_ids": sorted({c["id"] for r in proposal_retrievals(p) for c in r.get("matches", [])})}
    with locked(folder):
        _write(Path(folder).resolve() / "research" / "private_cases" / (pid + ".json"), record)
    return record


def _identifiers(p):
    """Supplement deterministic structure removal with known-string scrubbing.

    This is not an anonymity guarantee; the projection still requires review.
    """
    found = set()
    generic_labels = {"cash", "bank cash", "stocks", "bonds", "equities", "retirement", "college",
                      "home", "mortgage", "liquidity reserve", "liquidity floor", "spending", "income"}
    def walk(value, key=""):
        if isinstance(value, dict):
            for k, v in value.items():
                walk(v, k)
        elif isinstance(value, list):
            for v in value:
                walk(v, key)
        elif isinstance(value, str) and key in {"owner", "office_id", "account", "account_id", "account_number", "account_name", "email", "name", "label"} and len(value) >= 3:
            if key in {"name", "label"} and value.lower().strip() in generic_labels:
                return
            found.add(value)
            if key == "owner":
                found.update(word for word in value.split() if len(word) >= 3 and word.lower() not in {
                    "family", "office", "household", "test", "evaluation", "fictional", "private", "owner", "sentinel"})
        elif type(value) in {int, float} and math.isfinite(value) and abs(value) >= 1000 and key in {
                "amount", "value", "basis", "cost_basis", "annual_income", "income", "principal", "balance", "proceeds"}:
            for number in {value, abs(value)}:
                found.update({str(number), f"{number:,.2f}", f"{number:.2f}"})
                if number == int(number):
                    found.update({str(int(number)), f"{number:,.0f}"})
                if number % 1000 == 0:
                    found.add(f"{number / 1000:g}k")
    walk(p["snapshot"])
    return sorted(found, key=len, reverse=True)


def _redact(value, identifiers):
    if isinstance(value, dict):
        return {k: _redact(v, identifiers) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact(v, identifiers) for v in value]
    if isinstance(value, str):
        for token in identifiers:
            value = re.sub(r"(?<!\w)" + re.escape(token) + r"(?!\w)", "[private detail omitted]", value, flags=re.I)
        value = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[email omitted]", value)
        value = re.sub(r"\$\s*[\d,]+(?:\.\d+)?\s*(?:million|billion|[MBK]\b)?", "[amount omitted]", value, flags=re.I)
        value = re.sub(r"\b(?:[A-Z]\d{6,}|\d{8,})\b", "[identifier omitted]", value)
    return value


def prepare_case(p, symbol):
    """Make a PRIVATE draft. Nothing returned here is admitted to a public library."""
    symbol = symbol.upper()
    candidate = next((c for c in p.get("candidates", []) if c["symbol"] == symbol), None)
    court = next((c for c in p.get("courts", []) if c["symbol"] == symbol), None)
    if not candidate or not court:
        raise ValueError("A completed candidate court is required to prepare a case")
    if candidate["instrument"] not in {"stock", "etf", "options"}:
        raise ValueError("The research exchange pilot currently supports security and options investigations")
    pack = p.get("evidence", {}).get(symbol, {})
    evidence = []
    # Only primary public source sections; book and program embed private data.
    for section, data in pack.get("sections", {}).items():
        if section not in PUBLIC_SECTIONS:
            continue
        url, fetched = source_of(data)
        if not url:  # Legacy data without a source locator cannot be shared yet.
            continue
        try:
            safe_url(url)
        except ValueError:
            continue
        original = pack.get("reuse", {}).get(section, {})
        evidence.append({"section": section, "symbol": symbol, "retrieved_at": original.get("retrieved_at", fetched or pack["built"]),
                         "source_url": url, "data": deepcopy(data), "sha256": digest(data)})
    fields = {k: deepcopy(court.get(k)) for k in ("verdict", "rationale", "decisive_points", "unverified_items", "briefs")}
    fields["models"] = deepcopy(court.get("models") or {})
    status = p["status"] if p["status"] in {"adopted", "declined"} else "proposed"
    # Legacy calls have unknown protocol provenance; never assign today's prompts.
    protocol_hash = (p.get("research") or {}).get("run", {}).get("protocol_hash") or "unknown"
    case = {"schema": SCHEMA, "subject": {"symbol": symbol, "instrument": candidate["instrument"]},
            "as_of": p["created_at"], "context": proposal_context(p),
            "investigation": {"question": p["brief"].get("request") or p["brief"]["thesis"],
                              "thesis": (p.get("research") or {}).get("thesis", ""),
                              "candidate_rationale": candidate["rationale"],
                              "alternatives": (p.get("research") or {}).get("alternatives", []),
                              "assumptions": (p.get("research") or {}).get("assumptions", []),
                              "factors": factor_topics(proposal_context(p)["strategy"])},
            "court": fields, "decision": {"status": status, "reason": None, "reason_origin": "not_recorded", "execution": "unconfirmed"},
            "provenance": {"kind": "office_investigation", "analyst_model": (p.get("research") or {}).get("model", "unknown"),
                           "protocol_hash": protocol_hash, "runs": public_runs(p, court),
                           "derived_from": sorted({c["id"] for r in proposal_retrievals(p) for c in r.get("matches", [])})},
            "evidence": evidence,
            "privacy": {"policy": POLICY, "transformations": ["Office identity and raw portfolio omitted", "Context bucketed; unknown values retained", "Known private names, identifiers and dollar amounts removed from arguments"],
                        "limitations": ["Free text requires disclosure review", "No analysis of disclosure across a contributor's other cases", "Execution and the user's decision reason are not inferred"]}}
    # A security's own ticker is public and is the subject of the case: never
    # scrub it, even when the office happens to hold a sleeve of that name.
    identifiers = [t for t in _identifiers(p) if t.upper() != symbol]
    case["investigation"] = _redact(case["investigation"], identifiers)
    if court.get("general_id"):
        # Two-pass court: the briefs came from the GENERAL court, which never saw
        # this office. Redacting them would only destroy public facts (revenue,
        # prices, share counts). Only the suitability ruling is office-aware.
        briefs = case["court"].pop("briefs")
        case["court"] = {**_redact(case["court"], identifiers), "briefs": briefs,
                         "general_id": court["general_id"]}
    else:
        case["court"] = _redact(case["court"], identifiers)   # legacy single court: everything is office-aware
    # Leave source documents visible in the PRIVATE draft; publication requires
    # a reviewer to remove/replace material they do not have permission to share.
    return {"schema": "research_case_draft_v1", "case": case, "review_required": True}


def validate_case(case):
    try:
        return _validate_case(case)
    except (KeyError, TypeError, AttributeError, OverflowError) as exc:
        raise ValueError("Malformed contextual research case") from exc


def _validate_case(case):
    exact(case, "schema subject as_of context investigation court decision provenance evidence privacy", "case")
    if case["schema"] != SCHEMA:
        raise ValueError("Unsupported contextual case version")
    if len(canonical(case)) > MAX_BYTES or SECRET.search(canonical(case)):
        raise ValueError("Case exceeds its size limit or contains credential-shaped text")
    _private_fields(case)
    exact(case["subject"], "symbol instrument", "subject")
    if not re.fullmatch(r"[A-Z0-9][A-Z0-9.^-]{0,14}", case["subject"]["symbol"]) or case["subject"]["instrument"] not in {"stock", "etf", "options"}:
        raise ValueError("Invalid case subject")
    day(case["as_of"])
    validate_context(case["context"])
    inv = case["investigation"]
    exact(inv, "question thesis candidate_rationale alternatives assumptions factors", "investigation")
    for k in ("question", "thesis", "candidate_rationale"):
        text(inv[k])
    for k in ("alternatives", "assumptions", "factors"):
        strings(inv[k])
    if not inv["factors"] or not set(inv["factors"]) <= FACTORS:
        raise ValueError("Invalid factor vocabulary")
    court = case["court"]
    if "general_id" in court:      # optional link to the shareable general evaluation it rules on
        if not HASH.fullmatch(str(court["general_id"])):
            raise ValueError("Invalid general research identity")
        exact({k: v for k, v in court.items() if k != "general_id"},
              "verdict rationale decisive_points unverified_items briefs models", "court")
    else:
        exact(court, "verdict rationale decisive_points unverified_items briefs models", "court")
    for k in ("verdict", "rationale"):
        text(court[k])
    for k in ("decisive_points", "unverified_items"):
        strings(court[k])
    exact(court["briefs"], "red blue", "court briefs")
    for brief in court["briefs"].values():
        exact(brief, "case key_points unverified lean", "bench")
        text(brief["case"], 96000)
        strings(brief["key_points"])
        strings(brief["unverified"])
        if brief["lean"] not in {"kill", "avoid", "watch", "starter", "own"}:
            raise ValueError("Invalid court lean")
    exact(court["models"], "bench adjudicate", "court models")
    for model in court["models"].values():
        text(model, 200)
    d = case["decision"]
    exact(d, "status reason reason_origin execution", "decision")
    if d["status"] not in {"proposed", "adopted", "declined"} or d["execution"] != "unconfirmed" or d["reason"] is not None or d["reason_origin"] != "not_recorded":
        raise ValueError("This schema records intent only; do not infer execution or user motivation")
    p = case["provenance"]
    exact(p, "kind analyst_model protocol_hash runs derived_from", "provenance")
    if p["kind"] not in {"office_investigation", "evaluation_scenario"} or (p["protocol_hash"] != "unknown" and not HASH.fullmatch(p["protocol_hash"])):
        raise ValueError("Invalid case provenance")
    if not isinstance(p["runs"], dict) or set(p["runs"]) - {"analyst", "red", "blue", "adjudicate"}:
        raise ValueError("Invalid agent provenance")
    for run in p["runs"].values():
        exact(run, "requested_model resolved_model provider_client reasoning_configuration protocol_hash", "agent run")
        for value in run.values():
            text(value, 300)
    text(p["analyst_model"], 200)
    strings(p["derived_from"], 16)
    if any(not HASH.fullmatch(i) for i in p["derived_from"]):
        raise ValueError("Invalid parent case identity")
    exact(case["privacy"], "policy transformations limitations", "privacy record")
    if case["privacy"]["policy"] != POLICY:
        raise ValueError("Unsupported context projection policy")
    strings(case["privacy"]["transformations"])
    strings(case["privacy"]["limitations"])
    if not isinstance(case["evidence"], list) or len(case["evidence"]) > 4:
        raise ValueError("Invalid evidence list")
    seen = set()
    for e in case["evidence"]:
        exact(e, "section symbol retrieved_at source_url data sha256", "evidence")
        if e["section"] not in PUBLIC_SECTIONS or e["section"] in seen or e["symbol"] != case["subject"]["symbol"]:
            raise ValueError("Invalid or duplicate public evidence section")
        seen.add(e["section"])
        day(e["retrieved_at"])
        safe_url(e["source_url"])
        if not isinstance(e["data"], dict) or digest(e["data"]) != e["sha256"]:
            raise ValueError("Evidence content does not match its digest")
        validate_evidence(e)
    return case


def validate_evidence(e):
    """Validate the shapes render_pack consumes, before admission or model use."""
    d, section = e["data"], e["section"]
    if section == "fund_profile":
        if set(d) - {"url", "fetched_at", "text", "truncated", "note"} or not {"url", "fetched_at", "text", "truncated"} <= set(d):
            raise ValueError("Invalid fund evidence fields")
        if d["url"] != e["source_url"] or day(d["fetched_at"]) != day(e["retrieved_at"]) or type(d["truncated"]) is not bool:
            raise ValueError("Fund evidence source and collection date disagree")
        text(d["text"], 30000)
        text(d.get("note", ""))
    elif section == "filing_text":
        if set(d) - {"url", "form", "date", "text", "chars", "truncated"} or not {"url", "form", "date", "text", "chars", "truncated"} <= set(d):
            raise ValueError("Invalid filing evidence fields")
        if d["url"] != e["source_url"] or type(d["chars"]) is not int or d["chars"] < len(d["text"]) or type(d["truncated"]) is not bool:
            raise ValueError("Invalid filing coverage")
        text(d["form"], 80)
        day(d["date"])
        text(d["text"], 300000)
    elif section == "xbrl":
        # As-filed SEC facts: public domain and machine-verifiable. Every number
        # carries the taxonomy tag and accession number it can be checked against.
        meta = d.get("_source")
        exact(meta, "cik url fetched_at", "XBRL source")
        if type(meta["cik"]) is not int or not 0 < meta["cik"] < 10**10:
            raise ValueError("Invalid XBRL registrant")
        if meta["url"] != e["source_url"] or meta["url"] != f"https://data.sec.gov/api/xbrl/companyfacts/CIK{meta['cik']:010d}.json":
            raise ValueError("XBRL facts must cite the registrant's SEC companyfacts document")
        if day(meta["fetched_at"]) != day(e["retrieved_at"]):
            raise ValueError("XBRL source and collection date disagree")
        facts = {k: v for k, v in d.items() if k != "_source"}
        if not facts or set(facts) - XBRL_KEYS:
            raise ValueError("Unsupported XBRL fact series")
        for rows in facts.values():
            if not isinstance(rows, list) or not 1 <= len(rows) <= 8:
                raise ValueError("Invalid XBRL fact series")
            for row in rows:
                exact(row, "end val form tag accn", "XBRL fact")
                day(row["end"])
                if isinstance(row["val"], bool) or not isinstance(row["val"], (int, float)) or not math.isfinite(row["val"]):
                    raise ValueError("XBRL values must be finite numbers")
                if row["form"] not in XBRL_FORMS or not re.fullmatch(r"[A-Za-z][A-Za-z0-9]{0,119}", str(row["tag"])):
                    raise ValueError("Invalid XBRL form or taxonomy tag")
                if not re.fullmatch(r"\d{10}-\d{2}-\d{6}", str(row["accn"])):
                    raise ValueError("Each XBRL fact needs the accession number of the filing it came from")
    elif section == "filings":
        exact(d, "entity recent cik url fetched_at", "filings index")
        if type(d["cik"]) is not int or d["url"] != e["source_url"] or d["url"] != f"https://data.sec.gov/submissions/CIK{d['cik']:010d}.json":
            raise ValueError("A filings index must cite the registrant's SEC submissions document")
        if day(d["fetched_at"]) != day(e["retrieved_at"]):
            raise ValueError("Filings source and collection date disagree")
        text(d["entity"] or "", 300)
        if not isinstance(d["recent"], list) or len(d["recent"]) > 15:
            raise ValueError("Invalid filings index")
        for row in d["recent"]:
            exact(row, "form date acc", "filing")
            text(row["form"], 40)
            day(row["date"])
            if not re.fullmatch(r"\d{10}-\d{2}-\d{6}", str(row["acc"])):
                raise ValueError("Invalid accession number")
    else:
        raise ValueError("This evidence section needs a source schema before it can be shared")


def approve(draft, expected_digest, reuse=(), reviewed_at=None, contributor=None):
    """Explicit review binds the exact edited projection and per-source grants.

    reuse: [{section, basis: public_domain|licensed|original_summary, valid_until}]
    These assertions are visible claims by the contributor, not publisher trust.
    """
    case = deepcopy(draft["case"])
    if expected_digest != digest(case):
        raise ValueError("The case changed since review; review the current projection")
    validate_case(case)
    body = {"schema": "reviewed_research_case_v1", "case": case,
            "review": {"case_sha256": digest(case), "reviewed_at": reviewed_at or utcnow(),
                       "publication_review": "explicit", "reuse": list(reuse)}}
    if contributor is not None:
        # OPT-IN only. A contextual case carries bucketed household context; several
        # under one pseudonym are a fingerprint. Absent means anonymous, the default.
        body["review"]["contributor"] = contributor
    bundle = {"id": digest(body), **body}
    validate_bundle(bundle)
    return bundle


def validate_bundle(bundle):
    try:
        return _validate_bundle(bundle)
    except (KeyError, TypeError, AttributeError, OverflowError) as exc:
        raise ValueError("Malformed contextual research bundle") from exc


def _validate_bundle(bundle):
    exact(bundle, "id schema case review", "research bundle")
    if len(canonical(bundle)) > MAX_BYTES or bundle["schema"] != "reviewed_research_case_v1":
        raise ValueError("Unsupported or oversized research bundle")
    if not HASH.fullmatch(bundle["id"]) or bundle["id"] != digest({k: v for k, v in bundle.items() if k != "id"}):
        raise ValueError("Research bundle digest mismatch")
    validate_case(bundle["case"])
    r = bundle["review"]
    if "contributor" in r:
        from officekit_research.contributor import KEY
        if not isinstance(r["contributor"], str) or not KEY.fullmatch(r["contributor"]):
            raise ValueError("Invalid contributor key")
    exact({k: v for k, v in r.items() if k != "contributor"}, "case_sha256 reviewed_at publication_review reuse", "publication review")
    if r["case_sha256"] != digest(bundle["case"]) or r["publication_review"] != "explicit":
        raise ValueError("Publication review does not match the case")
    day(r["reviewed_at"])
    if not isinstance(r["reuse"], list) or len(r["reuse"]) > 4:
        raise ValueError("Invalid reuse grants")
    evidence = {e["section"]: e for e in bundle["case"]["evidence"]}
    seen = set()
    for grant in r["reuse"]:
        exact(grant, "section basis valid_until", "reuse grant")
        section = grant["section"]
        if section in seen or section not in evidence or grant["basis"] not in {"public_domain", "licensed", "original_summary"}:
            raise ValueError("Invalid public evidence reuse permission")
        seen.add(section)
        fetched = day(evidence[section]["retrieved_at"])
        limit = EVIDENCE_TTL_DAYS[section]
        if not fetched <= day(grant["valid_until"]) <= fetched + timedelta(days=limit):
            raise ValueError(f"Reusable {section} evidence must expire within {limit} days of collection")
    return bundle


def read_bundle(path):
    path = Path(path)
    if path.is_symlink() or path.stat().st_size > MAX_BYTES:
        raise ValueError("Invalid research bundle file")
    return validate_bundle(parse_json(path.read_bytes()))


def import_bundle(folder, bundle):
    """Explicit import admits data for consideration, never a verdict or a trade."""
    validate_bundle(bundle)
    with locked(folder):
        library = Path(folder).resolve() / "research" / "shared_cases"
        if library.is_symlink() or library.parent.is_symlink():
            raise ValueError("Research library cannot follow symbolic links")
        path = library / (bundle["id"] + ".json")
        paths = list(library.glob("*.json"))
        # Refuse the addition before it would make the whole library unreadable.
        # Reimporting the same artifact remains idempotent at the limit.
        if len(paths) + (path not in paths) > MAX_CASES:
            raise ValueError("This import would exceed the research library's case limit")
        size = sum(p.stat().st_size for p in paths if p != path and not p.is_symlink())
        if size + len(canonical(bundle)) + 1 > MAX_LIBRARY_BYTES:
            raise ValueError("This import would exceed the research library's size limit")
        _write(path, bundle)
    return bundle["id"]


def load_library(folder):
    library = Path(folder) / "research" / "shared_cases"
    if library.is_symlink() or library.parent.is_symlink():
        raise ValueError("Research library cannot follow symbolic links")
    bundles, errors = [], []
    paths = sorted(library.glob("*.json"))
    if len(paths) > MAX_CASES:
        raise ValueError("This research library exceeds the 1,000-case pilot limit")
    if sum(p.stat().st_size for p in paths if not p.is_symlink()) > MAX_LIBRARY_BYTES:
        raise ValueError("This research library exceeds the 32 MiB pilot limit")
    for path in paths:
        try:
            bundle = read_bundle(path)
            if path.stem != bundle["id"]:
                raise ValueError("Case filename and content identity disagree")
            bundles.append(bundle)
        except (ValueError, OSError, KeyError, TypeError, AttributeError) as exc:
            # No raw content/path is surfaced to models or browsers.
            errors.append({"file": path.name, "reason": "Invalid research case; excluded from retrieval"})
    return bundles, errors


def retrieve(folder, p, today=None, include_evaluation=False):
    today = today or datetime.now(timezone.utc).date()
    context = proposal_context(p)
    candidates = {s.upper() for s in p["brief"].get("candidates", [])}
    candidates.update(c["symbol"].upper() for c in p.get("candidates", []))
    excluded = {str(e["value"]).upper() for e in (p["snapshot"].get("personal_context") or {}).get("exclusions", []) if e.get("scope") == "ticker"}
    bundles, errors = load_library(folder)
    matches, rejected = [], []
    for b in bundles:
        c, reasons, differences = b["case"], [], []
        if c["subject"]["symbol"] not in candidates and (context["strategy"] == "custom" or c["context"]["strategy"] != context["strategy"]):
            continue
        if c["provenance"]["kind"] == "evaluation_scenario" and not include_evaluation:
            reasons.append("Evaluation-only case")
        if day(c["as_of"]) > today or day(b["review"]["reviewed_at"]) > today:
            reasons.append("Case was not available at the decision date")
        if (today - day(c["as_of"])).days > 90:
            reasons.append("Case context is older than the 90-day pilot window")
        if c["subject"]["symbol"] in excluded:
            reasons.append("Investment is excluded by this office")
        if c["subject"]["instrument"] == "options" and p["brief"]["kind"] != "options":
            reasons.append("Options case does not match this proposal's instrument scope")
        if p["brief"]["kind"] == "program":
            reasons.append("A security case cannot stand in for program diligence")
        for key in ("strategy", "goal_types", "life_stage", "horizon", "liquidity", "country"):
            old, new = c["context"][key], context[key]
            if old != new or old == "unknown" or old == ["unknown"] or old == "unspecified":
                differences.append({"field": key, "prior": old, "current": new})
        # Short-horizon equity cases cannot authorize a long-horizon allocation
        # in reverse, nor can a foreign tax case establish local suitability.
        if c["context"]["horizon"] != "unknown" and context["horizon"] != "unknown" and (c["context"]["horizon"] == "under_2y") != (context["horizon"] == "under_2y"):
            reasons.append("Near-term and longer-term goals require different suitability analysis")
        if c["context"]["country"] != "unknown" and context["country"] != "unknown" and c["context"]["country"] != context["country"]:
            reasons.append("Different tax jurisdictions")
        if reasons:
            rejected.append({"id": b["id"], "symbol": c["subject"]["symbol"], "reasons": reasons})
        else:
            matches.append({"id": b["id"], "context_fit": "needs_comparison" if differences else "comparable",
                            "differences": differences, "bundle": b})
    # Conflict checking covers all eligible cases, even those outside the prompt
    # budget. Repetition cannot crowd contrary evidence out of this gate.
    claims = {}
    for m in matches:
        b = m["bundle"]
        grants = {g["section"]: g for g in b["review"]["reuse"]}
        for e in b["case"]["evidence"]:
            g = grants.get(e["section"])
            if g and day(e["retrieved_at"]) <= today <= day(g["valid_until"]):
                claims.setdefault(e["symbol"], {}).setdefault(e["section"], set()).add(content_sha256(e["section"], e["data"]))
    conflicts = {symbol: sorted(section for section, hashes in sections.items() if len(hashes) > 1)
                 for symbol, sections in claims.items()}
    # Re-reviewing identical case content does not create independent evidence.
    distinct = {}
    for m in sorted(matches, key=lambda m: (-len(m["bundle"]["review"]["reuse"]), m["id"])):
        distinct.setdefault(m["bundle"]["review"]["case_sha256"], m)
    duplicates = len(matches) - len(distinct)
    matches = list(distinct.values())
    matches.sort(key=lambda m: (len(m["differences"]), -day(m["bundle"]["case"]["as_of"]).toordinal(), m["id"]))
    return {"protocol": "context_retrieval_v1", "queried_at": today.isoformat(), "context": context,
            "matches": matches[:6], "rejected": rejected, "errors": errors,
            "omitted_matches": max(0, len(matches) - 6), "duplicate_reviews": duplicates,
            "evidence_conflicts": conflicts}


def reusable_sections(retrieval, symbol, today=None):
    """Conflicting evidence is not resolved by vote or by contributor recency."""
    today = today or datetime.now(timezone.utc).date()
    by_section = {}
    for match in retrieval.get("matches", []):
        b = validate_bundle(match["bundle"])
        grants = {g["section"]: g for g in b["review"]["reuse"]}
        for e in b["case"]["evidence"]:
            g = grants.get(e["section"])
            if e["symbol"] != symbol or not g or not day(e["retrieved_at"]) <= today <= day(g["valid_until"]):
                continue
            by_section.setdefault(e["section"], []).append((e, g, b["id"]))
    reused, conflicts = {}, list(retrieval.get("evidence_conflicts", {}).get(symbol, []))
    for section, entries in by_section.items():
        if section in conflicts or len({content_sha256(section, e[0]["data"]) for e in entries}) != 1:
            if section not in conflicts:
                conflicts.append(section)
            continue
        # Agreeing contributors corroborate; reuse the most recently read copy.
        e, g, cid = max(entries, key=lambda row: (row[0]["retrieved_at"], row[2]))
        reused[section] = {"data": deepcopy(e["data"]), "case_ids": sorted({row[2] for row in entries}),
                           "source_url": e["source_url"], "retrieved_at": e["retrieved_at"],
                           "sha256": e["sha256"], "basis": g["basis"], "valid_until": g["valid_until"]}
    return reused, conflicts


def model_cases(retrieval):
    """Bounded context for an analyst; full evidence goes separately to the court."""
    def bounded(value):
        if isinstance(value, str):
            return value if len(value) <= 1800 else value[:1800] + " [EXCERPT: remainder retained in case]"
        if isinstance(value, list):
            return [bounded(v) for v in value[:8]] + (["Additional items retained in case"] if len(value) > 8 else [])
        if isinstance(value, dict):
            return {k: bounded(v) for k, v in value.items()}
        return value
    out, used = [], 0
    for m in retrieval.get("matches", []):
        case = m["bundle"]["case"]
        item = {"case_id": m["id"], "context_fit": m["context_fit"], "differences": m["differences"],
                "subject": case["subject"], "context": case["context"],
                "investigation": bounded(case["investigation"]), "court": bounded(case["court"]), "decision": case["decision"]}
        size = len(canonical(item))
        if used + size > 40000:
            item = {"case_id": m["id"], "subject": case["subject"], "differences": m["differences"],
                    "omitted": "Arguments omitted due to prompt budget; do not infer agreement or a verdict"}
        used += len(canonical(item))
        out.append(item)
    return out


def proposal_retrievals(p):
    return [p.get("research_reuse") or {}] + list((p.get("candidate_reuse") or {}).values())


def public_runs(p, court):
    # The general court's own adjudication is identified on the general record.
    runs = {"analyst": (p.get("research") or {}).get("run"),
            **{role: run for role, run in court.get("runs", {}).items() if role in {"red", "blue", "adjudicate"}}}
    fields = {"requested_model", "resolved_model", "provider_client", "reasoning_configuration", "protocol_hash"}
    return {role: {k: (json.dumps(v, sort_keys=True) if not isinstance(v, str) else v) for k, v in run.items() if k in fields}
            for role, run in runs.items() if run}
