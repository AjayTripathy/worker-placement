"""TDLR Industrialized Housing & Buildings registry connector.

The Texas Department of Licensing and Regulation is the statutory registrar of
modular/industrialized-housing MANUFACTURERS and BUILDERS. Every plant that
fabricates modular homes in Texas must register and carries a registration
number, expiration date, and — crucially — a PHYSICAL PLANT ADDRESS. This is the
authoritative source for the "company X operates a factory" claim that a pitch
deck states without an address: TDLR turns 'Factory 1' into 4422 Supply Ct,
which the permit/OSHA verifiers can then query.

TDLR publishes the two rolls as PDFs (no JSON/API), refreshed periodically:
  - manufacturers: /ihb/pdf/4-Manufacturers_List.pdf  (one record per line)
  - builders:      /ihb/pdf/1-Bldr%20List.pdf         (records wrap columns)

Each record is `Reg# Name ExpDate PhysicalAddress MailingAddress Phone`. We
collapse the whole document to single-spaced text and split on the `IHM-/IHB-`
registration-number boundary, which survives the column wrapping in the builder
list. Matching is by distinctive name core (so 'The American Housing
Corporation' matches 'American Housing Corp'), not a shared-token contains.
"""

from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py) — added 2026-07-29 gap-close.
APPLIES_TO = {
    "kind": 'm_source',
    "sic_codes": [],
    "sic_prefixes": ['15', '24', '65'],
    "issuer_features": ['manufactured_housing_business'],
    "asset_classes": ['corporate_ipo_dd'],
    "applies_universally": False,
    "summary": 'Texas TDLR industrialized-housing registry. Geographic: TX modular builders.',
}

import io
import re
from typing import ClassVar, Optional

import pypdf

from .base import (
    BaseConnector, ConnectorObservation, ConnectorRequest, ConnectorResult,
    ErrorKind, safe_get,
)

_MFR_URL = "https://www.tdlr.texas.gov/ihb/pdf/4-Manufacturers_List.pdf"
_BLDR_URL = "https://www.tdlr.texas.gov/ihb/pdf/1-Bldr%20List.pdf"

# Record boundary: a registration number, optionally followed by a parenthetical
# code like "(CTS)". Everything up to the next reg number is one registrant.
_RECORD_RE = re.compile(
    r"(IH[MB]-\d+(?:\s*\([^)]*\))?)\s+(.*?)\s+(\d{1,2}/\d{1,2}/\d{4})\s+(.*?)(?=\s*IH[MB]-\d+|\Z)"
)
_PHONE_RE = re.compile(r"\(\d{3}\)\s*\d{3}-\d{4}")
# Physical address = leading text up to and including the first ZIP (5 or 5+4).
_ADDR_RE = re.compile(r"^(.*?\b\d{5}(?:-\d{4})?)\b")

# Corporate suffixes stripped to compare name cores.
_SUFFIXES = frozenset({
    "the", "inc", "inc.", "incorporated", "corp", "corp.", "corporation", "co",
    "co.", "company", "llc", "l.l.c.", "lp", "l.p.", "ltd", "limited", "holdings",
    "labs", "technologies", "technology", "homes", "housing", "modular",
})


def _core(name: str) -> str:
    toks = re.sub(r"[^a-z0-9 ]+", " ", (name or "").lower()).split()
    while toks and toks[0] in _SUFFIXES:
        toks.pop(0)
    while toks and toks[-1] in _SUFFIXES:
        toks.pop()
    return " ".join(toks)


def _parse_records(text: str, list_type: str) -> list[dict]:
    text = re.sub(r"\s+", " ", text)
    out: list[dict] = []
    for m in _RECORD_RE.finditer(text):
        reg, name, exp, rest = m.groups()
        rest = rest.strip()
        addr_m = _ADDR_RE.search(rest)
        phone_m = _PHONE_RE.search(rest)
        out.append({
            "reg_number": reg.strip(),
            "name": name.strip(),
            "exp_date": exp,
            "physical_address": addr_m.group(1).strip() if addr_m else None,
            "phone": phone_m.group(0) if phone_m else None,
            "list_type": list_type,
        })
    return out


class TdlrIhbConnector(BaseConnector):
    """Resolve a modular-builder company name to its registered TX plant address.

    Inputs (via ConnectorRequest):
      - entity_name: required — the operating company name to match.

    Returns one observation per matched registry record (a company may appear on
    BOTH the manufacturer and builder rolls), value = the parsed record dict.
    """

    source_id = "tdlr_ihb"
    rate_limit_per_min = 20
    user_agent = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    # Process-level cache: the two rolls are large and change rarely, so parse
    # once per process. Keyed by URL → list[record].
    _cache: ClassVar[dict[str, list[dict]]] = {}

    def _load(self, url: str, list_type: str) -> tuple[Optional[list[dict]], Optional[ErrorKind], Optional[str]]:
        if url in type(self)._cache:
            return type(self)._cache[url], None, None
        s = self._session()
        s.headers.update({"Accept": "application/pdf"})
        resp, ek, ed = safe_get(s, url, timeout=self.timeout_s)
        if resp is None:
            return None, ek, ed
        try:
            reader = pypdf.PdfReader(io.BytesIO(resp.content))
            txt = " ".join(p.extract_text() or "" for p in reader.pages)
        except Exception as e:  # pypdf raises a variety of parse errors
            return None, ErrorKind.PARSE_FAIL, f"pdf parse: {e}"
        recs = _parse_records(txt, list_type)
        type(self)._cache[url] = recs
        return recs, None, None

    def query(self, request: ConnectorRequest) -> ConnectorResult:
        if not request.entity_name:
            return self._fail(request, ErrorKind.UNSUPPORTED, "entity_name required")

        target = _core(request.entity_name)
        if not target or len(target) < 3:
            return self._fail(request, ErrorKind.UNSUPPORTED,
                              f"entity_name '{request.entity_name}' has no usable name core")

        self._throttle()
        all_recs: list[dict] = []
        last_err: Optional[tuple[ErrorKind, str]] = None
        for url, lt in ((_MFR_URL, "manufacturer"), (_BLDR_URL, "builder")):
            recs, ek, ed = self._load(url, lt)
            if recs is None:
                last_err = (ek or ErrorKind.UNKNOWN, ed or "load failed")
                continue
            all_recs.extend(recs)

        if not all_recs and last_err:
            return self._fail(request, last_err[0], last_err[1])

        # Match on name core. A record matches if the target core is contained in
        # the record's core or vice-versa (handles 'american' vs 'american pacific').
        matches = []
        for r in all_recs:
            rc = _core(r["name"])
            if not rc:
                continue
            if target == rc or target in rc or rc in target:
                matches.append(r)

        if not matches:
            return self._fail(
                request, ErrorKind.NOT_FOUND,
                f"no TDLR IHB manufacturer/builder registration matching '{request.entity_name}'",
            )

        observations = [
            ConnectorObservation(
                attribute="tdlr_ihb_registration",
                value=r,
                source_url=_MFR_URL if r["list_type"] == "manufacturer" else _BLDR_URL,
                confidence=1.0,
            )
            for r in matches
        ]
        return self._ok(request, observations)
