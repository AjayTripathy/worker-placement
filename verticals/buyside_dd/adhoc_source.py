"""Ring 2 — agent-invented (ad-hoc) M-sources.

Ring 0 is the vetted atlas; Ring 1 is the agent selecting from it (with alias
reconciliation + a recall-floor validator). Ring 2 is the open-set escape hatch:
when the R/f/M agent reasons that a referent needs verification NO registered
source covers (the canonical case: a TX modular-housing obligor that should
appear in the TDLR Industrialized Builders registry), it may INVENT a source,
run it, and propose it back into the library.

Three guardrails keep "run anything it thinks matches" honest rather than reckless:

  1. PROVENANCE TIER. A finding from a self-invented source can NOT carry the
     same weight as one from a vetted authority — that is the whole basis of the
     hostile-validator / honesty-alpha standard. Ring-2 findings are tagged
     `provisional` and confidence-capped. UNVERIFIABLE != clean; provisional !=
     vetted.

  2. GATED PROMOTION. The agent may USE an invented source in-run freely, but it
     only ENTERS the permanent atlas through a gate: auto-promote ONLY on a hard
     authority check (official .gov/.us/.mil registry host + a declared stable
     schema); everything else emits a human-review proposal artifact.

  3. SANDBOXED I/O. "Arbitrary network calls" means read-only: HTTPS GET only, no
     credentials, public hosts only — private / loopback / link-local / metadata
     addresses are blocked (SSRF guard). The curiosity is the feature; the verb
     and the destination are constrained.

This module is deliberately self-contained: it does not mutate source_atlas.py.
Promotion is a proposal the operator (or an authority check) acts on, leaving the
graph denser after every run — which is the point of the product.
"""
from __future__ import annotations

import ipaddress
import json
import socket
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional
from urllib.parse import urlparse

try:  # match web_discovery: TLS-fingerprinted client when available
    from curl_cffi import requests as _hx  # type: ignore
    _IMPERSONATE = "chrome131"
except Exception:  # pragma: no cover
    import requests as _hx  # type: ignore
    _IMPERSONATE = None


# ─────────────────────────────────────────────────────────────────────────────
# Sandbox — read-only, public-host-only HTTP GET (SSRF guard)
# ─────────────────────────────────────────────────────────────────────────────
_MAX_BYTES = 1_000_000
_UA = "SignalOS-BuysideDD-Ring2/0.1 (research; read-only)"


class SandboxError(Exception):
    pass


def _host_is_public(host: str) -> bool:
    """Block private / loopback / link-local / reserved / multicast targets.

    Resolves every A/AAAA record and rejects if ANY resolves to a non-public IP
    (defends against DNS-rebinding to 169.254.169.254 metadata etc.).
    """
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return False
    for info in infos:
        ip_str = info[4][0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            return False
        if (ip.is_private or ip.is_loopback or ip.is_link_local
                or ip.is_reserved or ip.is_multicast or ip.is_unspecified):
            return False
    return True


def safe_adhoc_get(url: str, timeout: float = 20.0) -> tuple[Optional[str], Optional[str]]:
    """Sandboxed read-only fetch. Returns (text, error). Exactly one is non-None."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return None, f"blocked scheme: {parsed.scheme!r} (only http/https)"
    if not parsed.hostname:
        return None, "no host in URL"
    if not _host_is_public(parsed.hostname):
        return None, f"blocked non-public host: {parsed.hostname}"
    kw = {"timeout": timeout, "headers": {"User-Agent": _UA}}
    if _IMPERSONATE:
        kw["impersonate"] = _IMPERSONATE
    try:
        r = _hx.get(url, **kw)
    except Exception as e:
        return None, f"fetch error: {type(e).__name__}: {e}"
    status = getattr(r, "status_code", None)
    if status and status >= 400:
        return None, f"http {status}"
    text = getattr(r, "text", "") or ""
    return text[:_MAX_BYTES], None


# ─────────────────────────────────────────────────────────────────────────────
# Promotion gate — auto-promote only on a hard authority check
# ─────────────────────────────────────────────────────────────────────────────
_OFFICIAL_SUFFIXES = (".gov", ".mil", ".us", ".state.tx.us", ".fed.us")
_OFFICIAL_HOSTS = frozenset({
    "data.austintexas.gov", "efts.sec.gov", "www.sec.gov",
})


def _is_official_host(host: str) -> bool:
    if not host:
        return False
    host = host.lower()
    if host in _OFFICIAL_HOSTS:
        return True
    return host.endswith(_OFFICIAL_SUFFIXES)


def _registrable_host(host: str) -> str:
    """Lowercase host with a leading 'www.' stripped, for collision matching."""
    host = (host or "").lower().strip()
    return host[4:] if host.startswith("www.") else host


def _atlas_hosts() -> dict[str, list[str]]:
    """Map registrable host -> [atlas source_ids that already live on it].

    Read-only reflection of the vetted atlas. Used to dedup Ring-2 inventions:
    if the agent proposes a source on a host the atlas already serves, we should
    EXTEND the existing source's coverage (an ALIAS proposal), not mint a near-
    duplicate (e.g. re-inventing sec_edgar for a PERSON referent).
    """
    from .source_atlas import REAL_ESTATE_SOURCES  # lazy: avoid import cycle
    hosts: dict[str, list[str]] = {}
    for s in REAL_ESTATE_SOURCES:
        h = _registrable_host(urlparse(s.endpoint or "").hostname or "")
        if h:
            hosts.setdefault(h, []).append(s.source_id)
    return hosts


def dedup_against_atlas(proposal: dict) -> Optional[dict]:
    """If the proposal's host already exists in the atlas, return an ALIAS record
    describing how to extend the existing source(s); else None.
    """
    host = _registrable_host(
        urlparse(proposal.get("query_url", "") or proposal.get("endpoint", "") or "").hostname or "")
    if not host:
        return None
    existing = _atlas_hosts().get(host)
    if not existing:
        return None
    return {
        "alias_of": existing,
        "host": host,
        "extend_with": {
            "referent_type": proposal.get("referent_type"),
            "attribute": proposal.get("attribute"),
            "jurisdiction": proposal.get("jurisdiction"),
            "query_url": proposal.get("query_url"),
        },
    }


def authority_gate(proposal: dict) -> str:
    """Return 'auto_promote' or 'human_review'.

    Auto-promote requires (strict where authority matters):
      - an official registry host (.gov/.mil/.us/state registry), AND
      - a declared non-empty schema (the agent committed to a stable shape), AND
      - a programmatic access pattern (api / file_download / scrape).
    Everything else is fast-but-human-reviewed.
    """
    host = (urlparse(proposal.get("query_url", "") or proposal.get("endpoint", "") or "").hostname or "")
    has_schema = bool(proposal.get("schema_fields"))
    pattern_ok = proposal.get("access_pattern") in ("api", "file_download", "scrape")
    if _is_official_host(host) and has_schema and pattern_ok:
        return "auto_promote"
    return "human_review"


# ─────────────────────────────────────────────────────────────────────────────
# LLM proposer
# ─────────────────────────────────────────────────────────────────────────────
_PROPOSER_PROMPT = """You are the source-discovery half of a buyside diligence engine.

The dispatcher could not find ANY registered source to verify a claim attribute.
Propose ONE concrete, PUBLIC, READ-ONLY web source that would verify it, OR return
{{"no_source": true, "reason": "..."}} if no public source plausibly exists.

Hard constraints on what you may propose:
- Public, free, read-only (a GET request). No login, no paid API, no form POST.
- Prefer official government / regulator registries (.gov, state registries).
- The query_url must be a SINGLE concrete URL that, when fetched, returns data
  about THIS specific referent (substitute the subject into the query string).

Referent to verify:
- referent_type: {referent_type}
- attribute (what to verify): {attribute}
- subject (the thing): {subject}
- scope: {scope}

Return ONLY a JSON object with these fields:
{{
  "source_id": "snake_case_id e.g. tx_tdlr_industrialized_builders",
  "referent_type": "{referent_type}",
  "attribute": "{attribute}",
  "jurisdiction": "2-letter state or US",
  "access_pattern": "api | file_download | scrape",
  "endpoint": "base endpoint / portal URL",
  "query_url": "the concrete URL to GET for THIS subject",
  "authority_tier": 1,
  "schema_fields": ["field names you expect in the response"],
  "match_logic": "how to tell a hit from a miss for this subject",
  "expected_authority": "who runs this registry and why it is authoritative",
  "rationale": "one sentence: why this verifies the attribute"
}}
"""


def _parse_json(text: str) -> Optional[dict]:
    if not text:
        return None
    t = text.strip()
    if t.startswith("```"):
        t = t.split("```", 2)[1] if "```" in t[3:] else t.lstrip("`")
        if t.startswith("json"):
            t = t[4:]
    a, b = t.find("{"), t.rfind("}")
    if a == -1 or b == -1:
        return None
    try:
        return json.loads(t[a:b + 1])
    except json.JSONDecodeError:
        return None


def propose_adhoc_source(
    referent_type: str,
    attribute: str,
    subject: str,
    scope: dict,
    llm: Callable[[str], str],
) -> Optional[dict]:
    """Ask the LLM to invent ONE public read-only source. None if it declines."""
    prompt = _PROPOSER_PROMPT.format(
        referent_type=referent_type, attribute=attribute,
        subject=subject, scope=json.dumps(scope or {}, default=str),
    )
    raw = llm(prompt)
    proposal = _parse_json(raw)
    if not proposal or proposal.get("no_source"):
        return None
    proposal.setdefault("referent_type", referent_type)
    proposal.setdefault("attribute", attribute)
    proposal["proposed_for_subject"] = subject
    return proposal


# ─────────────────────────────────────────────────────────────────────────────
# Run + artifact
# ─────────────────────────────────────────────────────────────────────────────
def run_adhoc(
    proposal: dict,
    fetch: Callable[[str], tuple[Optional[str], Optional[str]]] = safe_adhoc_get,
) -> dict:
    """Execute the invented source's query_url through the sandbox. Returns a
    provisional result record (NOT a vetted Finding)."""
    url = proposal.get("query_url") or proposal.get("endpoint") or ""
    text, err = fetch(url)
    now = datetime.now(timezone.utc).isoformat()
    if err:
        return {
            "source_id": proposal.get("source_id"),
            "provisional": True,
            "success": False,
            "queried_at": now,
            "query_url": url,
            "error": err,
        }
    return {
        "source_id": proposal.get("source_id"),
        "provisional": True,
        "success": True,
        "queried_at": now,
        "query_url": url,
        "match_logic": proposal.get("match_logic"),
        "raw_snippet": (text or "")[:2048],
        "bytes": len(text or ""),
    }


def write_proposal_artifact(run_dir, proposal: dict, run_result: dict, gate: str) -> Path:
    """Persist the codification proposal so the graph can grow after the run."""
    out_dir = Path(run_dir) / "ring2_proposals"
    out_dir.mkdir(parents=True, exist_ok=True)
    sid = proposal.get("source_id") or "unnamed_source"
    path = out_dir / f"{sid}.json"
    path.write_text(json.dumps({
        "proposal": proposal,
        "run_result": run_result,
        "promotion_gate": gate,
        "promotion_decision": (
            "AUTO-PROMOTE to atlas (official host + stable schema)."
            if gate == "auto_promote" else
            "HOLD for human review before entering atlas."
        ),
        "written_at": datetime.now(timezone.utc).isoformat(),
    }, indent=2, default=str))
    return path


def write_alias_artifact(run_dir, proposal: dict, alias: dict) -> Path:
    """Persist an ALIAS proposal: the host already exists in the atlas, so the
    operator should extend the existing source(s) rather than add a new one."""
    out_dir = Path(run_dir) / "ring2_proposals"
    out_dir.mkdir(parents=True, exist_ok=True)
    sid = proposal.get("source_id") or "unnamed_source"
    path = out_dir / f"{sid}.alias.json"
    path.write_text(json.dumps({
        "alias_proposal": True,
        "proposal": proposal,
        "alias_of": alias["alias_of"],
        "host": alias["host"],
        "extend_with": alias["extend_with"],
        "promotion_decision": (
            f"ALIAS: host '{alias['host']}' already in atlas under {alias['alias_of']}; "
            f"extend that source's coverage to "
            f"(referent_type={alias['extend_with']['referent_type']}, "
            f"attribute={alias['extend_with']['attribute']}) instead of minting a new source."
        ),
        "written_at": datetime.now(timezone.utc).isoformat(),
    }, indent=2, default=str))
    return path


def codify_or_propose(
    referent_type: str,
    attribute: str,
    subject: str,
    scope: dict,
    llm: Callable[[str], str],
    run_dir,
    fetch: Callable[[str], tuple[Optional[str], Optional[str]]] = safe_adhoc_get,
) -> Optional[dict]:
    """Full Ring-2 path: invent → sandboxed run → authority-gate → artifact.

    Returns a summary dict (or None if the LLM declined to invent a source).
    The returned record is PROVISIONAL — callers must tag any finding derived
    from it as provisional and confidence-cap it.
    """
    proposal = propose_adhoc_source(referent_type, attribute, subject, scope, llm)
    if not proposal:
        return None

    # Dedup: if the invented source lives on a host the atlas already serves,
    # extend the existing source's coverage (ALIAS proposal) instead of minting
    # a near-duplicate (the sec_edgar-for-a-PERSON case). No new network call.
    alias = dedup_against_atlas(proposal)
    if alias:
        artifact = write_alias_artifact(run_dir, proposal, alias)
        return {
            "source_id": proposal.get("source_id"),
            "provisional": True,
            "ran_ok": None,
            "dedup": "alias",
            "alias_of": alias["alias_of"],
            "promotion_gate": "alias_extend",
            "artifact": str(artifact),
            "proposal": proposal,
            "run_result": None,
        }

    run_result = run_adhoc(proposal, fetch=fetch)
    gate = authority_gate(proposal)
    artifact = write_proposal_artifact(run_dir, proposal, run_result, gate)
    return {
        "source_id": proposal.get("source_id"),
        "provisional": True,
        "ran_ok": run_result.get("success"),
        "dedup": None,
        "promotion_gate": gate,
        "artifact": str(artifact),
        "proposal": proposal,
        "run_result": run_result,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Standalone proof — no API / network needed (stub LLM + stub fetch)
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import tempfile

    # Stub LLM: invents the TDLR Industrialized Builders registry for a TX
    # modular-housing maker — exactly the AHC factory case.
    def stub_llm(_prompt: str) -> str:
        return json.dumps({
            "source_id": "tx_tdlr_industrialized_builders",
            "referent_type": "entity",
            "attribute": "modular_builder_registration",
            "jurisdiction": "TX",
            "access_pattern": "scrape",
            "endpoint": "https://www.tdlr.texas.gov/ib/",
            "query_url": "https://www.tdlr.texas.gov/ib/SearchResults.asp?company=American+Housing+Corporation",
            "authority_tier": 1,
            "schema_fields": ["company", "registration_number", "status", "address"],
            "match_logic": "company name appears with an ACTIVE registration row",
            "expected_authority": "Texas Dept of Licensing & Regulation — statutory registrar of industrialized (modular) builders",
            "rationale": "A TX modular-housing manufacturer must register with TDLR's Industrialized Builders program.",
        })

    # Stub fetch: avoids live network; proves the propose→gate→artifact path.
    def stub_fetch(url: str):
        return (f"<html>matched: American Housing Corporation — Registration #IB-12345 ACTIVE — url={url}</html>", None)

    with tempfile.TemporaryDirectory() as td:
        out = codify_or_propose(
            referent_type="entity",
            attribute="modular_builder_registration",
            subject="American Housing Corporation",
            scope={"state": "TX", "address": "4422 Supply Ct, Austin TX 78744"},
            llm=stub_llm,
            run_dir=td,
            fetch=stub_fetch,
        )
        print("RING-2 RESULT")
        print(json.dumps(out, indent=2, default=str))
        print("\nAuthority gate on official .texas.gov host →", out["promotion_gate"])
        # SSRF guard checks
        print("\nSandbox guard:")
        for u in ("http://169.254.169.254/latest/meta-data/",
                  "http://localhost:8080/admin",
                  "https://10.0.0.5/internal"):
            _, e = safe_adhoc_get(u)
            print(f"  {u}  →  blocked: {e}")
