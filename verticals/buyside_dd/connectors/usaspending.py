"""USASpending.gov federal procurement connector — primary source for government-revenue claims.

WHY — when an issuer claims "X% of revenue is government / defense," the audited 10-K rarely
discloses a customer-type split (Planet's only cuts revenue by geography), so the claim is
management commentary. USASpending is the authoritative PUBLIC record of federal contract
obligations to a recipient — independent, primary (Tier-1), auditable. It corroborates the
existence and rough scale of US government revenue and splits defense vs civil.

LIMITS (disclosed, not corrected): PRIME contracts only (Planet is often a subcontractor to
integrators -> understates), award totals are multi-year obligations not annual revenue, and
classified IC work (NRO/NGA National Intelligence Program) + FOREIGN sovereign contracts
(Germany/NATO/Japan) are NOT here -> a "% government" claim can be largely UNVERIFIABLE from
this source even when real. Use alongside the J-book (DoD program elements) and the 10-K
geography table; treat a low USASpending total as "US-federal-prime portion is modest", NOT
"government revenue is small."

Inputs (ConnectorRequest): entity_name (the recipient/issuer legal name).
"""

from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py) — added 2026-07-29 gap-close.
APPLIES_TO = {
    "kind": 'm_source',
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ['mentions_dod_program', 'government_customer_concentration_above_5pct'],
    "asset_classes": ['corporate_ipo_dd'],
    "applies_universally": True,
    "summary": 'Federal award/obligation flow incl corporate family roll-up. Universal; decisive when gov revenue is claimed.',
}

import re
from typing import ClassVar

from .base import BaseConnector, ConnectorObservation, ConnectorRequest, ConnectorResult, ErrorKind

_API = "https://api.usaspending.gov/api/v2/search/spending_by_award/"
_CONTRACT_TYPES = ["A", "B", "C", "D"]   # prime contract award types
_DEFENSE_TOKENS = ("defense", "army", "navy", "air force", "space force", "marine",
                   "missile", "reconnaissance", "geospatial-intelligence", "intelligence",
                   "dod", "darpa", "socom")
# LEGAL-FORM suffixes only — do NOT strip distinctive words like "labs"/"federal", else the
# core collapses to a generic token ("planet") that would match unrelated firms (Planet Fitness)
# AND fail to span the corporate family (Planet Labs Inc / Federal Inc / PBC).
_SUFFIXES = frozenset({"the", "inc", "inc.", "incorporated", "corp", "corp.", "corporation",
                       "co", "co.", "company", "llc", "l.l.c.", "lp", "l.p.", "ltd", "limited",
                       "pbc", "holdings"})


def _core_tokens(name: str) -> set:
    toks = re.sub(r"[^a-z0-9 ]+", " ", (name or "").lower()).split()
    return {t for t in toks if t not in _SUFFIXES}


def _family_name(name: str) -> str:
    """Strip the legal-form suffix so the recipient search spans the whole corporate family
    (a parent's gov contracts often sit in subsidiaries: 'Planet Labs Federal, Inc.')."""
    toks = [t for t in re.sub(r"[^A-Za-z0-9 ]+", " ", name or "").split() if t.lower() not in _SUFFIXES]
    return " ".join(toks) or name


class UsaSpendingConnector(BaseConnector):
    source_id = "usaspending"
    rate_limit_per_min = 30
    user_agent = "SignalOS-BuysideDD/0.1 (research; usaspending)"

    def query(self, request: ConnectorRequest) -> ConnectorResult:
        if not request.entity_name:
            return self._fail(request, ErrorKind.UNSUPPORTED, "entity_name required")
        search_name = _family_name(request.entity_name)   # span the corporate family, not just the parent
        body = {"filters": {"recipient_search_text": [search_name],
                            "award_type_codes": _CONTRACT_TYPES},
                "fields": ["Award ID", "Recipient Name", "Awarding Agency", "Awarding Sub Agency",
                           "Award Amount", "Period of Performance Start Date",
                           "Period of Performance Current End Date", "Description"],
                "limit": 100, "sort": "Award Amount", "order": "desc", "page": 1}
        self._throttle()
        try:
            r = self._session().post(_API, json=body, timeout=self.timeout_s)
        except Exception as e:
            return self._fail(request, ErrorKind.NETWORK, f"post: {e}")
        if r.status_code == 429:
            return self._fail(request, ErrorKind.RATE_LIMIT, "http 429")
        if r.status_code >= 400:
            return self._fail(request, ErrorKind.UNKNOWN, f"http {r.status_code}: {r.text[:160]}")
        try:
            results = r.json().get("results", [])
        except ValueError as e:
            return self._fail(request, ErrorKind.PARSE_FAIL, f"json: {e}", raw=r.text)

        # keep only recipients whose name core matches the query (recipient_search_text is fuzzy)
        want = _core_tokens(request.entity_name)
        matched = [a for a in results if want and want <= _core_tokens(a.get("Recipient Name", ""))]
        if not matched:
            return self._fail(request, ErrorKind.NOT_FOUND,
                              f"no federal prime contracts matching '{request.entity_name}'")

        total = sum(a.get("Award Amount") or 0 for a in matched)
        by_agency: dict[str, float] = {}
        defense = 0.0
        for a in matched:
            ag = a.get("Awarding Agency") or "?"
            by_agency[ag] = by_agency.get(ag, 0.0) + (a.get("Award Amount") or 0)
            blob = f"{ag} {a.get('Awarding Sub Agency') or ''}".lower()
            if any(tok in blob for tok in _DEFENSE_TOKENS):
                defense += a.get("Award Amount") or 0
        civil = total - defense

        obs = [
            ConnectorObservation(
                attribute="government_contracts",
                value={"federal_prime_total_usd": round(total),
                       "n_awards": len(matched),
                       "defense_usd": round(defense), "civil_usd": round(civil),
                       "defense_pct_of_visible": round(100 * defense / total, 1) if total else None,
                       "recipient_names": sorted({a.get("Recipient Name") for a in matched})},
                confidence=1.0, source_url="https://www.usaspending.gov/",
                extra={"caveat": "PRIME contracts only (subs invisible), multi-year obligation totals "
                                 "(not annual revenue), classified IC (NRO/NGA NIP) + FOREIGN sovereign "
                                 "contracts NOT included -> understates total government revenue; a low "
                                 "total means the US-federal-prime portion is modest, not that gov revenue is small."}),
            ConnectorObservation(attribute="government_customer_confirmed", value=True,
                                 confidence=1.0, source_url="https://www.usaspending.gov/"),
            ConnectorObservation(attribute="federal_awards_by_agency",
                                 value={k: round(v) for k, v in sorted(by_agency.items(), key=lambda kv: -kv[1])},
                                 confidence=1.0, source_url="https://www.usaspending.gov/"),
        ]
        for i, a in enumerate(matched[:10]):
            obs.append(ConnectorObservation(
                attribute=f"federal_award[{i}]",
                value={"id": a.get("Award ID"), "agency": a.get("Awarding Agency"),
                       "sub_agency": a.get("Awarding Sub Agency"),
                       "amount_usd": round(a.get("Award Amount") or 0),
                       "start": a.get("Period of Performance Start Date"),
                       "desc": (a.get("Description") or "")[:120]},
                confidence=1.0,
                source_url=f"https://www.usaspending.gov/award/{a.get('Award ID')}"))
        return self._ok(request, obs, raw=r.text[:2048])
