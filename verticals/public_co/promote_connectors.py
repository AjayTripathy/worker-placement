"""
Promote previously-PROPOSED claims to MAPPED when their connector now exists.

When a planner proposes a connector and that connector later lands in
m_source_catalog, the old plan.json still marks the claim as PROPOSED.
This module deterministically rewrites those plan entries to MAPPED with
source_params synthesized from the claim's metadata (subject, claim_text,
focal CIK), so plan_executor can dispatch the now-promoted connector
without a planner re-run.

We only promote claims where the param synthesis is unambiguous. Any case
the heuristics can't handle is left as PROPOSED and falls through to
UNVERIFIABLE in the deterministic scorer — better to acknowledge a gap
than to silently fabricate params.

Usage:
    python3 -m verticals.public_co.promote_connectors TICKER [TICKER ...]
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from .m_source_catalog import CATALOG

HERE  = Path(__file__).parent
LOCAL = HERE / "data" / "_local"


def _focal_cik_from_filing(plan: dict) -> str | None:
    f = plan.get("filing") or ""
    head = f.split("-")[0]
    if head.isdigit() and len(head) == 10:
        return head
    return None


# Match a capitalized phrase ending in one of the named entity suffixes
# (Inc., LLC, Bank, & Co., etc.). This is suffix-anchored so it cleanly
# separates "Capital One Securities, Inc., KippsDeSanto & Company, ..."
# into three distinct entities instead of one greedy run.
_SUFFIX = r"(?:Inc\.?|LLC|L\.L\.C\.?|Corp\.?|Co\.|Company|Bank|Securities|N\.A\.?|Trust|Holdings|& Company)"
_ENTITY_RE = re.compile(
    r"\b([A-Z][A-Za-z0-9&\.]+(?:\s+(?:&\s+)?[A-Z][A-Za-z0-9&\.]+){0,5}"
    r"(?:,?\s+" + _SUFFIX + r")+)"
)


# Regulatory bodies / standards orgs / generic acronyms that the entity
# regex tends to false-match. Filter these out.
_NOT_ENTITIES = {
    "finra", "sec", "fdic", "occ", "cftc", "nfa", "irs", "doj", "ftc",
    "fhfa", "nmls", "epa", "fda", "uspto", "nyse", "nasdaq", "fed",
    "gaap", "cecl", "esg", "kyc", "aml", "rcr",
}


def _entities_in(text: str) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for m in _ENTITY_RE.finditer(text or ""):
        e = m.group(1).strip(" ,.")
        if e.lower() in seen or len(e) < 4:
            continue
        # Reject if the leading token is a regulatory-body acronym.
        first_token = e.split()[0].rstrip(".,").lower()
        if first_token in _NOT_ENTITIES:
            continue
        seen.add(e.lower())
        out.append(e)
    return out


def _synth_params(claim: dict, prop_name: str, plan: dict) -> dict | None:
    """Return synthesized source_params for a now-promoted claim, or None
    if the heuristic can't make a confident call."""
    text = " ".join([claim.get("claim_text", ""), claim.get("source_quote", "")])
    subject = claim.get("subject", "") or ""
    cutoff = plan.get("cutoff", "")

    if prop_name == "finra_brokercheck.query_firm":
        # Extract proper-noun firm names directly from claim_text (more
        # reliable than parsing the subject field, which the planner sometimes
        # collapses with "/" separators).
        ents = [e for e in _entities_in(text)
                if any(suf in e for suf in ["Inc", "LLC", "L.L.C", "Corp", "Co.", "& Company", "Securities", "Capital"])]
        if not ents:
            ents = _entities_in(text)
        # Pick the most prominent (longest) firm name; FINRA returns up to
        # `limit` matches per query so subsequent firms can be checked
        # post-hoc by the scorer's interpretation note.
        if not ents:
            return None
        ents.sort(key=len, reverse=True)
        primary = ents[0]
        return {"firm_name": primary, "limit": 5, "_other_named_firms": ents[1:5]}

    if prop_name == "fdic_bankfind.query_institution":
        cand = subject.split(",")[0].strip() if "," in subject else subject.strip()
        if not cand:
            return None
        return {"name": cand}

    if prop_name == "fdic_call_reports.consumer_loan_originations":
        # First try claim_text; if the claim doesn't NAME the banks (e.g.
        # "top three lending partners" without specific names), fall back to
        # the proposed_connector's description and rationale fields — the
        # planner often lists the candidate banks there.
        text_with_proposal = " ".join([
            claim.get("claim_text", ""),
            claim.get("source_quote", ""),
            (claim.get("proposed_connector") or {}).get("description", ""),
            (claim.get("proposed_connector") or {}).get("rationale", ""),
        ])
        cands = [e for e in _entities_in(text_with_proposal) if "Bank" in e]
        cands = list(dict.fromkeys(cands))[:5]
        if not cands:
            return None
        return {"bank_names": cands, "quarters": 4}

    if prop_name in ("sec_abs15g.query_securitizer_filings",
                     "sec_edgar.absee_loan_disclosures",
                     "sec_filings.list_filings_by_form"):
        # Form-cadence claim. Use the focal CIK and the form types implied by
        # the claim category / proposal name.
        cik = _focal_cik_from_filing(plan)
        if not cik:
            return None
        form_set = []
        if "abs15g" in prop_name or "ABS-15G" in text:
            form_set.append("ABS-15G")
        if "absee" in prop_name or "ABS-EE" in text:
            form_set.append("ABS-EE")
        if "10-D" in text:
            form_set.append("10-D")
        if "424B" in text:
            form_set.extend(["424B5", "424B2", "424B3", "424B4"])
        if not form_set:
            form_set = ["ABS-15G", "ABS-EE", "10-D"]
        return {"cik": cik, "forms": form_set, "cutoff_date": cutoff}

    return None


# Map the planner's proposal-name to the catalog name we built. (For most
# connectors these match exactly; this dict captures the cases where the
# planner named the proposal something close-but-not-identical.)
_PROPOSAL_TO_CATALOG = {
    "sec_abs15g.query_securitizer_filings": "sec_filings.list_filings_by_form",
    "sec_edgar.absee_loan_disclosures":     "sec_filings.list_filings_by_form",
}


def promote_ticker(ticker: str) -> dict:
    plan_path = LOCAL / f"{ticker}.plan.json"
    if not plan_path.exists():
        return {"error": f"no plan: {plan_path}"}
    plan = json.loads(plan_path.read_text())
    promoted: list[str] = []
    declined: list[tuple[str, str]] = []
    for claim in plan.get("claims", []):
        if claim.get("m_source_status") != "PROPOSED":
            continue
        prop = claim.get("proposed_connector") or {}
        prop_name = prop.get("name", "")
        canonical = _PROPOSAL_TO_CATALOG.get(prop_name, prop_name)
        if canonical not in CATALOG:
            declined.append((claim["claim_id"], f"not in catalog: {canonical}"))
            continue
        params = _synth_params(claim, canonical, plan)
        if not params:
            declined.append((claim["claim_id"], "no param synth heuristic matched"))
            continue
        claim["m_source_status"] = "MAPPED"
        claim["source_id"] = canonical
        claim["source_params"] = params
        # Keep the original proposed_connector for audit trail
        claim.setdefault("promotion_note",
                          f"auto-promoted from proposal {prop_name!r} -> {canonical!r} via promote_connectors")
        promoted.append(f"{claim['claim_id']} -> {canonical} {params}")
    if promoted:
        plan_path.write_text(json.dumps(plan, indent=2, default=str))
    return {"ticker": ticker, "promoted": promoted, "declined": declined}


def main():
    if len(sys.argv) < 2:
        print("usage: python3 -m verticals.public_co.promote_connectors TICKER [TICKER ...]", file=sys.stderr)
        sys.exit(2)
    for tk in sys.argv[1:]:
        r = promote_ticker(tk.upper())
        if "error" in r:
            print(f"  {tk}: {r['error']}")
            continue
        print(f"=== {r['ticker']} ===")
        for p in r["promoted"]:
            print(f"  promoted:  {p}")
        for cid, reason in r["declined"]:
            print(f"  declined:  {cid} ({reason})")


if __name__ == "__main__":
    main()
