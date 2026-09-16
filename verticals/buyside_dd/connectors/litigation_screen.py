"""litigation_screen — federal court / docket background screen on a deal's principals & entities.

WHY THIS EXISTS. Every operator/sponsor/GP DD needs a litigation background check, and it should run
AUTOMATICALLY — not be a "recommended next step" an analyst may skip (the gap caught on PCM Hospitality
and flagged on Pearlmark). A large restaurant/real-estate operator WILL carry routine employment / ADA /
wage-hour suits; those are NOT red flags. What matters is the MATERIAL categories: securities/fraud, RICO,
investor / stockholder / breach-of-fiduciary, franchisor termination, and bankruptcy where the subject is
the DEBTOR (not a creditor in someone else's case). This connector pulls federal dockets + opinions from
CourtListener/RECAP (the free, scriptable proxy for PACER) and classifies each hit by materiality and by
the subject's posture (defendant/debtor vs. plaintiff/creditor).

COVERAGE / ESCALATION. RECAP indexes federal dockets that have been uploaded — broad but not 100% of PACER;
STATE courts have no unified free API. So a clean result = "federal-clean of material categories; full PACER,
state courts, and UCC remain a paid/manual escalation." Common personal names (e.g., "Barry Dubin") produce
false positives in multi-party cases — flagged as disambiguation_needed.

CONTRACT: query(ConnectorRequest with entity_name / person_name, extra={"aliases":[...]}) -> ConnectorResult.
"""

from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py) — added 2026-07-29 gap-close.
APPLIES_TO = {
    "kind": 'm_source',
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": [],
    "asset_classes": ['corporate_ipo_dd'],
    "applies_universally": True,
    "summary": 'Federal docket screen on principals via recall-floor categories. Every deal principal.',
}
import urllib.parse, urllib.request, json, time
from datetime import datetime, timezone

from .base import BaseConnector, ConnectorRequest, ConnectorObservation, ConnectorResult, ErrorKind

CL = "https://www.courtlistener.com/api/rest/v4/search/"
UA = {"User-Agent": "Mozilla/5.0 (signalos-diligence-litigation-screen)"}

# Nature-of-Suit / case-name signals → materiality bucket. MATERIAL fires the detector; BASELINE does not.
MATERIAL_NOS = {  # federal NOS codes that are diligence-material when the subject is a defendant
    "850": "securities/commodities", "370": "fraud", "375": "false_claims", "371": "truth_in_lending",
    "470": "rico", "160": "stockholders_suit", "480": "consumer_credit", "190": "contract_other",
    "195": "contract_product_liability", "196": "franchise",
}
BASELINE_NOS = {  # routine operational litigation for any large operator — NOT a red flag
    "710": "flsa_wage_hour", "442": "civil_rights_jobs", "445": "civil_rights_ada_employment",
    "446": "civil_rights_ada_access", "440": "civil_rights_other", "751": "family_medical_leave",
    "360": "personal_injury_other", "290": "real_property_other",
}
MATERIAL_NAME = ("fraud", "securities", "ponzi", "breach of fiduciary", "rico", "racketeer",
                 "misrepresentation", "investor", "shareholder", "stockholder")


def _classify(case_name: str, nos: str, subject_q: str) -> dict:
    cn = (case_name or "").lower(); nos = (nos or "")
    code = next((c for c in MATERIAL_NOS if c in nos), None)
    base = next((c for c in BASELINE_NOS if c in nos), None)
    is_bk = any(x in cn for x in ("in re", "liquidation", "chapter 11", "chapter 7")) or \
            any(s in (nos or "").lower() for s in ("bankruptcy",))
    # subject posture: in "A v. B", defendant is after " v. "
    defendant = False
    if " v. " in cn:
        defendant = subject_q.lower() in cn.split(" v. ", 1)[1]
    # debtor posture for bankruptcy: subject IS the case caption (In re <subject> / <subject>, LLC)
    debtor = is_bk and subject_q.lower() in cn and " v. " not in cn
    material = bool(code) or any(k in cn for k in MATERIAL_NAME) or debtor
    bucket = ("MATERIAL" if material else ("BASELINE" if (base or " v. " in cn) else "OTHER"))
    return {"bucket": bucket, "nos_code": code or base, "is_bankruptcy": is_bk,
            "subject_is_defendant": defendant, "subject_is_debtor": debtor,
            "label": MATERIAL_NOS.get(code or "") or BASELINE_NOS.get(base or "") or "uncategorized"}


def _search(q: str, typ: str, retries: int = 3):
    url = CL + "?type=" + typ + "&q=" + urllib.parse.quote(f'"{q}"')
    for _ in range(retries):
        try:
            d = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25).read())
            if d.get("count") is not None:
                return d
        except Exception:
            pass
        time.sleep(5)
    return None


def screen_entity(name: str, is_person: bool, session=None) -> dict:
    """Return classified federal-litigation hits for one entity/person name."""
    out = {"name": name, "is_person": is_person, "dockets": 0, "opinions": 0, "hits": [],
           "material_hits": [], "disambiguation_needed": False}
    rr = _search(name, "r"); time.sleep(1.5)
    if rr is None:
        out["error"] = "rate_limited"; return out
    out["dockets"] = rr.get("count") or 0
    for r in (rr.get("results") or [])[:15]:
        cn = r.get("caseName") or ""; nos = r.get("suitNature") or ""
        c = _classify(cn, nos, name)
        hit = {"case": cn[:90], "court": r.get("court_id"), "date": str(r.get("dateFiled"))[:10],
               "docket": r.get("docketNumber"), **c}
        out["hits"].append(hit)
        if c["bucket"] == "MATERIAL" and (c["subject_is_defendant"] or c["subject_is_debtor"]
                                          or any(k in cn.lower() for k in MATERIAL_NAME)):
            out["material_hits"].append(hit)
    # common personal-name false-positive guard: many hits, none clearly material on the entity
    if is_person and out["dockets"] >= 4 and not out["material_hits"]:
        out["disambiguation_needed"] = True
    return out


class LitigationScreenConnector(BaseConnector):
    """Federal court / docket background screen (CourtListener / RECAP).

    request.entity_name and/or request.person_name; request.extra:
      aliases: [str]      additional entity/person names (LLCs, prior names, operating partners)
    """
    source_id = "litigation_screen"
    timeout_s = 90.0

    def query(self, request: ConnectorRequest) -> ConnectorResult:
        names = []
        if request.person_name: names.append((request.person_name, True))
        if request.entity_name: names.append((request.entity_name, False))
        for a in (request.extra or {}).get("aliases", []):
            # crude person-vs-entity guess: entity if it has a corp suffix or >1 capitalized token w/ LLC/Inc
            is_p = not any(s in a.lower() for s in ("llc", "inc", "lp", "l.p", "ltd", "corp", "company",
                                                    "holdings", "partners", "capital", "group", "fund",
                                                    "investments", "eats", "restaurants", "brands"))
            names.append((a, is_p))
        if not names:
            return self._fail(request, ErrorKind.UNSUPPORTED, "need entity_name/person_name or extra.aliases")
        now = datetime.now(timezone.utc); obs = []
        for nm, is_p in names:
            try:
                s = screen_entity(nm, is_p)
            except Exception as e:
                obs.append(ConnectorObservation(attribute="litigation_screen", value=nm,
                           confidence=0.0, source_url=CL, extra={"error": str(e)[:80]}))
                continue
            obs.append(ConnectorObservation(
                attribute="litigation_history", value=nm, observation_date=now,
                confidence=0.7 if s.get("disambiguation_needed") else 0.9,
                source_url=f"https://www.courtlistener.com/?q=%22{urllib.parse.quote(nm)}%22&type=r",
                extra={"federal_dockets": s["dockets"], "material_hits": s["material_hits"],
                       "n_material": len(s["material_hits"]), "all_hits": s["hits"][:10],
                       "disambiguation_needed": s.get("disambiguation_needed"),
                       "coverage_note": "RECAP/federal only; state courts + full PACER + UCC = paid/manual escalation"}))
        return self._ok(request, obs, raw=str([o.value for o in obs]))


if __name__ == "__main__":
    # PCM Hospitality operator screen (validated 2026-06-17)
    c = LitigationScreenConnector()
    r = c.query(ConnectorRequest(person_name="Barry Dubin",
        extra={"aliases": ["B Wild Investments", "7 Star Eats", "Sublime Huts", "Fresh Dining Concepts",
                           "KBP Brands", "US Laundry Holdings"]}))
    for o in r.observations:
        e = o.extra
        print(f"{o.value:26} dockets={e.get('federal_dockets')} material={e.get('n_material')} "
              f"disambig={e.get('disambiguation_needed')}")
        for h in e.get("material_hits", []):
            print(f"    MATERIAL: {h['case']} [{h['label']}]")
