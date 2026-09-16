"""City of Austin building permits via Socrata open data.

Dataset: "Issued Construction Permits"
Resource: 3syk-w9eu
URL: https://data.austintexas.gov/resource/3syk-w9eu.json

Used to verify "we have an Austin pipeline project at X" claims and to confirm
factory existence (commercial / industrial permits at the factory address).

Fields include: applieddate, status_current, project_name, original_address1,
city, zip, contractor_company_name, contractor_full_name, applicant_org,
total_existing_bldg_sqft, total_new_add_sqft, project_class, work_class,
permit_type_desc, permit_class_mapped.
"""

from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py) — added 2026-07-29 gap-close.
APPLIES_TO = {
    "kind": 'm_source',
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ['real_estate_development', 'construction_activity_claim'],
    "asset_classes": ['corporate_ipo_dd'],
    "applies_universally": False,
    "summary": 'City of Austin permits via Socrata. Geographic: Austin TX projects.',
}

import json
from urllib.parse import quote_plus

from .base import (
    BaseConnector,
    ConnectorRequest,
    ConnectorResult,
    ConnectorObservation,
    ErrorKind,
    safe_get,
)


AUSTIN_PERMITS = "https://data.austintexas.gov/resource/3syk-w9eu.json"


class AustinPermitsConnector(BaseConnector):
    source_id = "austin_permits"
    rate_limit_per_min = 60

    def query(self, request: ConnectorRequest) -> ConnectorResult:
        # Two query modes (mutually exclusive — pick the more specific one):
        #   1) ADDRESS mode (preferred when an address is present): list ALL
        #      permits at that address regardless of who filed them. Tenants
        #      don't appear on permits — GCs and property owners do — so an
        #      AND with entity_name produces a textbook false negative.
        #   2) ENTITY mode (only when no address): search applicant/contractor
        #      for the entity across all projects.
        where_clause = None
        if request.address:
            parts = request.address.split(",")[0].strip().split()
            if parts and parts[0].isdigit():
                num = parts[0]
                street = " ".join(parts[1:]).upper()
                where_clause = f"original_address1 like '%{num} {street}%'"
        if where_clause is None and request.entity_name:
            name_upper = request.entity_name.upper()
            where_clause = (
                f"(upper(contractor_company_name) like '%{name_upper}%' "
                f"or upper(contractor_full_name) like '%{name_upper}%' "
                f"or upper(description) like '%{name_upper}%')"
            )
        if where_clause is None:
            return self._fail(request, ErrorKind.UNSUPPORTED, "need address or entity_name")

        where = where_clause
        # Limit fields and order by most recent
        select_fields = ",".join([
            "permit_number", "permit_type_desc", "permit_class_mapped", "work_class",
            "status_current", "applieddate", "issue_date",
            "original_address1", "original_city", "original_zip",
            "contractor_company_name", "contractor_full_name",
            "description",
        ])
        url = (f"{AUSTIN_PERMITS}?$select={quote_plus(select_fields)}"
               f"&$where={quote_plus(where)}"
               f"&$order=applieddate DESC&$limit=25")

        self._throttle()
        sess = self._session()
        r, ek, ed = safe_get(sess, url)
        if r is None:
            return self._fail(request, ek, ed)
        try:
            data = r.json()
        except ValueError as e:
            return self._fail(request, ErrorKind.PARSE_FAIL, f"json: {e}", raw=r.text[:500])

        if not isinstance(data, list):
            return self._fail(request, ErrorKind.PARSE_FAIL, f"unexpected shape: {type(data).__name__}", raw=r.text[:500])
        if not data:
            return self._ok(request, [
                ConnectorObservation(attribute="austin_permit_count", value=0, source_url=url),
            ], raw=r.text)

        obs = [ConnectorObservation(attribute="austin_permit_count", value=len(data), source_url=url)]
        for i, p in enumerate(data[:15]):
            obs.append(ConnectorObservation(
                attribute=f"austin_permit[{i}]",
                value={
                    "permit_number": p.get("permit_number"),
                    "type": p.get("permit_type_desc"),
                    "class": p.get("permit_class_mapped"),
                    "work_class": p.get("work_class"),
                    "status": p.get("status_current"),
                    "applied": p.get("applieddate"),
                    "issued": p.get("issued_date"),
                    "address": p.get("original_address1"),
                    "applicant_org": p.get("applicant_org"),
                    "applicant_name": p.get("applicant_full_name"),
                    "contractor": p.get("contractor_company_name"),
                    "new_sqft": p.get("total_new_add_sqft"),
                    "project_name": p.get("project_name"),
                },
                source_url=url,
            ))
        return self._ok(request, obs, raw=r.text)


if __name__ == "__main__":
    c = AustinPermitsConnector()
    r = c.query(ConnectorRequest(entity_name="American Housing Corporation"))
    print(f"success={r.success} error={r.error_kind}/{r.error_detail}")
    for o in r.observations[:5]:
        print(f"  {o.attribute} = {o.value}")
