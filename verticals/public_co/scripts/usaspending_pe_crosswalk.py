"""
USAspending → Pentagon Program Element (PE) crosswalk.

Honest framing of the problem:
- USAspending's public API does NOT expose PE numbers on contract awards.
  Treasury Account / Program Activity / Federal Account fields are
  consistently None for DoD contracts.
- However, the PE link is *recoverable* from contract metadata that IS
  exposed: PIID prefix (encodes the contracting office), awarding office,
  funding office, contract description, NAICS + PSC codes, solicitation ID.

Approach:
  For each ticker:
    1. Query USAspending for every DoD contract under any of the
       ticker's resolved name variants (so we catch IonQ Federal LLC,
       Capella Space Corp, Oxford Ionics, etc. — not just the parent).
    2. For each contract, gather: PIID, description, awarding office,
       funding office, sub-agency, solicitation ID, PSC, NAICS, amount.
    3. Hand the contract metadata + the full programs.json corpus to
       Claude. Ask: which PE (if any) is this contract most likely
       funded under? Output structured: {pe_number, program_id,
       confidence, reasoning}.
    4. Aggregate per ticker: {ticker, [PE matches with $obligated]}
       → cross-ref each PE's J-Book status (latest funding, trajectory).

Output: ticker_pe_crosswalk.json
  {
    "ticker": "IONQ",
    "contracts_total_M": 13.4,
    "matched_pes": [
      {"pe_number": "0603287F", "program_id": "afrl-quantum-networking-ionq",
       "n_contracts": 1, "obligated_M": 13.4, "status": "UNFUNDED_TWO_PLUS_YEARS",
       "confidence": "high", "reasoning": "..."}
    ],
    "unmatched_contracts": [...]
  }

This is forward-looking BECAUSE the PE status comes from the J-Book
(which is Pentagon's plan for next FY + the FYDP). Past contracts under
a PE that's now UNFUNDED is exactly the YSS/IONQ-pattern signal.
"""
from __future__ import annotations

import importlib
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Optional

import httpx

DATA = Path("verticals/public_co/data")
PROGRAMS_PATH = DATA / "_jbook_data" / "programs.json"
RESOLUTIONS_PATH = DATA / "_entity_resolution" / "ticker_entity_resolution.json"
OUT_PATH = DATA / "_entity_resolution" / "ticker_pe_crosswalk.json"

_USAS_URL = "https://api.usaspending.gov/api/v2/search/spending_by_award/"
_AWARD_FIELDS = [
    "Award ID", "Recipient Name", "Award Amount",
    "Description", "Awarding Sub Agency", "Awarding Office",
    "Funding Sub Agency", "Funding Office",
    "Period of Performance Start Date", "Period of Performance Current End Date",
    "NAICS Code", "NAICS Description", "PSC Code", "PSC Description",
]

_MODEL = os.environ.get("PE_CROSSWALK_MODEL", "claude-haiku-4-5-20251001")
_KEY_FILE = Path("~/.anthropic_api_key").expanduser()


def _get_client():
    from anthropic import Anthropic
    return Anthropic(api_key=_KEY_FILE.read_text().strip())


def _fetch_contracts_for_name(name: str, max_pages: int = 4,
                                max_retries: int = 5) -> list[dict]:
    """Pull every DoD contract for a given recipient-name search.

    Retries transient errors with exponential backoff — USAspending can
    temporarily refuse connections from a hammered IP."""
    out: list[dict] = []
    for page in range(1, max_pages + 1):
        body = {
            "filters": {
                "recipient_search_text": [name],
                "award_type_codes": ["A", "B", "C", "D"],
                "time_period": [{"start_date": "2018-01-01", "end_date": "2026-12-31"}],
                "agencies": [{"type": "awarding", "tier": "toptier",
                              "name": "Department of Defense"}],
            },
            "fields": _AWARD_FIELDS,
            "limit": 100, "page": page,
            "sort": "Award Amount", "order": "desc",
        }
        backoff = 2.0
        success = False
        last_err = None
        for attempt in range(max_retries):
            try:
                r = httpx.post(_USAS_URL, json=body, timeout=60)
                if r.status_code != 200:
                    last_err = f"HTTP {r.status_code}"
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                j = r.json()
                page_results = j.get("results", []) or []
                out.extend(page_results)
                success = True
                if len(page_results) < 100:
                    return out
                break
            except Exception as e:
                last_err = str(e)
                time.sleep(backoff)
                backoff = min(backoff * 2, 30.0)
                continue
        if not success:
            print(f"  ! USAspending error for {name!r} (page {page}): {last_err}",
                  file=sys.stderr)
            break
    return out


def _piid_prefix_clue(piid: str) -> str:
    """Map common DoD contract-office prefixes to a likely contracting activity.

    Not authoritative — used as one signal among many for the LLM matcher."""
    if not piid:
        return ""
    p = piid.upper()
    # AFRL / Air Force Research Lab
    if p.startswith(("FA8750",)):
        return "AFRL Rome Research Site (IT, sensors, quantum networking)"
    if p.startswith(("FA9550",)):
        return "AFOSR — Air Force Office of Scientific Research (basic research)"
    if p.startswith(("FA8650",)):
        return "AFRL Wright-Patterson (advanced aerospace, materials)"
    if p.startswith(("FA8730",)):
        return "AFLCMC (acquisitions)"
    # Army
    if p.startswith(("W911NF", "W911QX")):
        return "ARL — Army Research Lab (basic + applied)"
    if p.startswith(("W31P4Q",)):
        return "Army AMCOM / aviation"
    # Navy
    if p.startswith(("N00014",)):
        return "ONR — Office of Naval Research (basic research)"
    if p.startswith(("N00024",)):
        return "NAVSEA (sea systems)"
    if p.startswith(("N00019",)):
        return "NAVAIR (aviation)"
    # DARPA
    if p.startswith(("HR00",)):
        return "DARPA (any directorate)"
    # SOCOM
    if p.startswith(("H92222",)):
        return "USSOCOM Acquisition"
    # MDA
    if p.startswith(("HQ0147", "HQ0276")):
        return "Missile Defense Agency"
    # Space Force / SDA / SSC
    if p.startswith(("FA8810", "FA8814")):
        return "Space Systems Command / SDA"
    return ""


_SYSTEM = """You match a single DoD contract award to the Pentagon Program Element (PE) it was most likely funded under, given a corpus of known PEs.

INPUTS:
- One contract: PIID, description, awarding/funding office, NAICS, PSC, amount.
- The corpus: a JSON list of PEs with their PE number, title, agency/service, status.

YOUR JOB:
- Pick the SINGLE most-likely PE (or no_match if no PE in the corpus fits).
- Be CONSERVATIVE. If the contract description is vague ("R&D services," "professional support"), and no specific PE narrative aligns, return no_match.
- Use PIID prefix as a strong agency signal (e.g., FA8750 = AFRL Rome; HR00 = DARPA; N00014 = ONR).
- Use PSC + NAICS to filter (AC12 = National Defense R&D Services; 541715 = Physical Engineering R&D).

CRITICAL — AVOID AGGREGATE PE TRAPS:
- DARPA has aggregate "umbrella" PEs whose narratives describe the entire technology area, NOT specific contracts (e.g., 0603287E "Space Programs and Technology", 0605502E "SBIR", 0603760E "Command Control Communications", 0603286E "Advanced Aerospace Systems"). These are reorganization umbrellas — do NOT default to them as a "good-enough" match for a specific contract awarded by AFRL / SDA / Navy / Space Force. Only match a contract to a DARPA aggregate PE if the PIID prefix is HR00 (DARPA) AND the description specifically aligns with one of that PE's stated thrust areas.
- A contract awarded by AFRL Rome (FA8750) belongs to an AFRL PE, not a DARPA PE — even if the description sounds similar. Match by AGENCY first, then by topic.
- When no AFRL/SDA/Navy/Space-Force-specific PE exists in the corpus for a topic, return no_match rather than fall back to a DARPA umbrella.

OUTPUT — strict JSON, no markdown:
{
  "best_match": {
    "program_id": "afrl-quantum-networking-ionq",
    "pe_number": "0603287F",
    "confidence": "high" | "medium" | "low",
    "reasoning": "one-sentence justification citing specific PIID prefix / description / corpus match"
  } | null,
  "alternatives": [{"program_id": "...", "pe_number": "...", "reason": "..."}],
  "no_match": false | true
}

If the contract is clearly not RDT&E (e.g., procurement, services, construction), return no_match=true.

Be honest. We'd rather have 5 high-confidence matches than 50 noisy ones."""


def _parse_json(text: str) -> dict:
    t = (text or "").strip()
    if t.startswith("```"):
        t = re.sub(r"^```(?:json)?\s*", "", t)
        t = re.sub(r"\s*```\s*$", "", t)
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", t, re.DOTALL)
        if m:
            return json.loads(m.group(0))
        raise


def _build_corpus_summary(programs: list[dict]) -> str:
    """Compact corpus listing for the LLM (one line per PE)."""
    lines = []
    for p in programs:
        pid = p.get("program_id")
        pe = p.get("pe_number")
        title = p.get("program_name", "")
        agency = p.get("agency") or p.get("service") or ""
        status = p.get("status") or "?"
        lines.append(f"- program_id={pid}; PE {pe}; {title}; "
                      f"agency={agency}; status={status}")
    return "\n".join(lines)


def match_contract_to_pe(client, contract: dict, corpus_text: str) -> dict:
    piid = contract.get("Award ID", "")
    prefix_clue = _piid_prefix_clue(piid)
    contract_block = (
        f"CONTRACT:\n"
        f"  PIID: {piid}\n"
        f"  Recipient: {contract.get('Recipient Name','')}\n"
        f"  Amount: ${contract.get('Award Amount',0):,.0f}\n"
        f"  Description: {contract.get('Description','')}\n"
        f"  Awarding Sub Agency: {contract.get('Awarding Sub Agency','')}\n"
        f"  Awarding Office: {contract.get('Awarding Office','')}\n"
        f"  Funding Sub Agency: {contract.get('Funding Sub Agency','')}\n"
        f"  Funding Office: {contract.get('Funding Office','')}\n"
        f"  NAICS: {contract.get('NAICS Code','')} "
        f"({contract.get('NAICS Description','')})\n"
        f"  PSC: {contract.get('PSC Code','')} "
        f"({contract.get('PSC Description','')})\n"
        f"  PIID prefix clue: {prefix_clue or '(unknown)'}\n"
    )
    user_msg = f"{contract_block}\nProduce the JSON."
    # The corpus (~69K tokens at 2,365 programs) is identical across every contract call,
    # so cache it as a static system block — written once, read cheaply thereafter (~10x).
    sys_blocks = [
        {"type": "text", "text": _SYSTEM},
        {"type": "text",
         "text": f"CORPUS (known PEs in programs.json):\n{corpus_text}",
         "cache_control": {"type": "ephemeral"}},
    ]
    backoffs = [0, 2, 5]
    for delay in backoffs:
        if delay:
            time.sleep(delay)
        try:
            resp = client.messages.create(
                model=_MODEL,
                max_tokens=500,
                system=sys_blocks,
                messages=[{"role": "user", "content": user_msg}],
            )
            text = resp.content[0].text if resp.content else ""
            return _parse_json(text)
        except Exception as e:
            print(f"    LLM err: {e}", file=sys.stderr)
    return {"best_match": None, "alternatives": [], "no_match": True,
             "error": "llm_failed_after_retries"}


def gather_cohort() -> list[dict]:
    relevant = ["defense_cohort", "space_cohort",
                "quantum_cohort", "robotics_cohort"]
    universe = {}
    for modname in relevant:
        m = importlib.import_module(f"verticals.public_co.{modname}")
        for member in m.COHORT:
            tk = member.ticker.upper()
            if tk not in universe:
                universe[tk] = {
                    "ticker": tk, "cik": member.cik,
                    "name": getattr(member, "name", "") or "",
                    "cohort": modname,
                }
    return list(universe.values())


def main():
    universe = gather_cohort()
    resolutions = json.loads(RESOLUTIONS_PATH.read_text())["tickers"]
    corpus = json.loads(PROGRAMS_PATH.read_text())["programs"]
    corpus_text = _build_corpus_summary(corpus)
    print(f"Corpus: {len(corpus)} PEs in programs.json", file=sys.stderr)
    client = _get_client()

    out: dict[str, dict] = {}
    for i, c in enumerate(universe, 1):
        tk = c["ticker"]
        info = resolutions.get(tk) or {}
        print(f"\n[{i}/{len(universe)}] {tk:6} {c['name'][:50]}",
              file=sys.stderr)

        # Pull contracts under each US-domestic resolved variant
        seen_piid: set[str] = set()
        all_contracts: list[dict] = []
        for v in (info.get("name_variants") or []):
            vtype = v.get("type", "")
            # Skip pure foreign / acquisition-shell entries
            if any(k in vtype.lower() for k in ("foreign", "shell")):
                continue
            name = v.get("name", "")
            if len(name) < 5:
                continue
            cs = _fetch_contracts_for_name(name)
            for ct in cs:
                pid = ct.get("Award ID")
                if pid in seen_piid:
                    continue
                seen_piid.add(pid)
                ct["_searched_under"] = name
                all_contracts.append(ct)
        # Always include the canonical registered name
        cs = _fetch_contracts_for_name(c["name"])
        for ct in cs:
            pid = ct.get("Award ID")
            if pid in seen_piid:
                continue
            seen_piid.add(pid)
            ct["_searched_under"] = c["name"]
            all_contracts.append(ct)

        total_M = sum((ct.get("Award Amount") or 0) for ct in all_contracts) / 1e6
        print(f"   {len(all_contracts)} contracts, ${total_M:.1f}M total",
              file=sys.stderr)

        # LLM-match each contract to a PE
        pe_buckets: dict[str, dict] = {}
        unmatched: list[dict] = []
        if all_contracts:
            # Cap to top 25 by $ to save LLM cost on noise
            top_contracts = sorted(
                all_contracts, key=lambda x: -(x.get("Award Amount") or 0)
            )[:25]
            for j, ct in enumerate(top_contracts, 1):
                amt = (ct.get("Award Amount") or 0) / 1e6
                desc = (ct.get("Description") or "")[:60]
                print(f"     [{j}/{len(top_contracts)}] {ct.get('Award ID',''):<20} "
                      f"${amt:>7.2f}M {desc}",
                      file=sys.stderr)
                result = match_contract_to_pe(client, ct, corpus_text)
                bm = result.get("best_match")
                if bm and not result.get("no_match"):
                    pid = bm["program_id"]
                    if pid not in pe_buckets:
                        # Find the canonical PE entry for status/funding
                        canon = next((p for p in corpus
                                       if p.get("program_id") == pid), {})
                        pe_buckets[pid] = {
                            "program_id":     pid,
                            "pe_number":      bm.get("pe_number"),
                            "program_name":   canon.get("program_name"),
                            "status":         canon.get("status"),
                            "latest_fy":      None,
                            "n_contracts":    0,
                            "obligated_M":    0.0,
                            "confidence_max": bm.get("confidence"),
                            "contracts": [],
                            "reasoning":      bm.get("reasoning"),
                        }
                    pe_buckets[pid]["n_contracts"] += 1
                    pe_buckets[pid]["obligated_M"] += (ct.get("Award Amount") or 0) / 1e6
                    pe_buckets[pid]["contracts"].append({
                        "piid": ct.get("Award ID"),
                        "amount_M": (ct.get("Award Amount") or 0) / 1e6,
                        "description": ct.get("Description"),
                        "confidence": bm.get("confidence"),
                    })
                else:
                    unmatched.append({
                        "piid": ct.get("Award ID"),
                        "amount_M": (ct.get("Award Amount") or 0) / 1e6,
                        "description": ct.get("Description"),
                    })

        out[tk] = {
            "ticker": tk,
            "name": c["name"],
            "cohort": c["cohort"],
            "n_contracts_total": len(all_contracts),
            "contracts_total_M": round(total_M, 2),
            "n_pes_matched": len(pe_buckets),
            "matched_pes": list(pe_buckets.values()),
            "unmatched_count": len(unmatched),
            "unmatched_sample": unmatched[:5],
        }

    OUT_PATH.write_text(json.dumps({"_meta": {"n_tickers": len(out)},
                                      "tickers": out}, indent=2, default=str))
    print(f"\nWrote {OUT_PATH}", file=sys.stderr)

    print(f"\n{'TICKER':<7} {'#CTR':>5} {'$TOTAL':>9} {'#PE':>4}  TOP MATCHES (PE | status | $M)")
    print("=" * 100)
    rows = sorted(out.values(), key=lambda r: -r["n_pes_matched"])
    for r in rows:
        top = []
        for pe in r["matched_pes"][:3]:
            top.append(f"{pe['pe_number']}({pe.get('status') or '?'}) ${pe['obligated_M']:.1f}M")
        print(f"{r['ticker']:<7} {r['n_contracts_total']:>5} "
              f"${r['contracts_total_M']:>7.1f}M {r['n_pes_matched']:>4}  "
              f"{' | '.join(top)[:75]}")


if __name__ == "__main__":
    main()
