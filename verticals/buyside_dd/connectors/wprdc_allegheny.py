"""Allegheny County (WPRDC) deed records, mortgages, assessments, code violations.

WPRDC is a CKAN datastore. We use datastore_search and datastore_search_sql.
No auth required.

Resources used:
  - Real Estate Sales       resource_id = 5bbe6c55-bce6-4edb-9d04-68edeb6bf7b1
  - Property Assessments    resource_id = 518b583f-7cc8-4f60-94d0-174cc98310dc
  - PLI Permits/Violations  (Pittsburgh only) — varies; resolved at runtime
"""

from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py) — added 2026-07-29 gap-close.
APPLIES_TO = {
    "kind": 'm_source',
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ['real_estate_development', 'real_estate_collateral'],
    "asset_classes": ['corporate_ipo_dd'],
    "applies_universally": False,
    "summary": 'Allegheny County PA deeds/mortgages/assessments/violations. Geographic: Pittsburgh metro.',
}

import json
import re
from typing import Optional

from .base import (
    BaseConnector,
    ConnectorRequest,
    ConnectorResult,
    ConnectorObservation,
    ErrorKind,
    safe_get,
)


CKAN_BASE = "https://data.wprdc.org/api/3/action"
RESOURCE_SALES = "5bbe6c55-bce6-4edb-9d04-68edeb6bf7b1"
RESOURCE_ASSESSMENT = "518b583f-7cc8-4f60-94d0-174cc98310dc"


class WprdcAlleghenyConnector(BaseConnector):
    source_id = "wprdc_allegheny"
    rate_limit_per_min = 60

    def query(self, request: ConnectorRequest) -> ConnectorResult:
        # Mode is governed by request.extra['table']: 'sales' (default) | 'assessment'
        table = (request.extra.get("table") if request.extra else None) or "sales"
        if table == "sales":
            return self._query_sales(request)
        if table == "assessment":
            return self._query_assessment(request)
        return self._fail(request, ErrorKind.UNSUPPORTED, f"unknown table={table}")

    # ── Sales (deed records) ────────────────────────────────────────────────
    def _query_sales(self, request: ConnectorRequest) -> ConnectorResult:
        if not (request.address or request.parcel_id):
            return self._fail(request, ErrorKind.UNSUPPORTED, "need address or parcel_id")

        sql = self._build_sql(RESOURCE_SALES, request, fields=[
            "PARID", "FULL_ADDRESS", "PROPERTYHOUSENUM", "PROPERTYADDRESSSTREET",
            "PROPERTYCITY", "PROPERTYZIP", "PRICE", "SALEDATE", "RECORDDATE",
            "SALEDESC", "SALECODE", "INSTRTYP", "INSTRTYPDESC",
            "DEEDBOOK", "DEEDPAGE",
        ], order_by='"SALEDATE" DESC', limit=20)

        url = f"{CKAN_BASE}/datastore_search_sql?sql={sql}"
        self._throttle()
        sess = self._session()
        r, ek, ed = safe_get(sess, url)
        if r is None:
            return self._fail(request, ek, ed)
        try:
            data = r.json()
        except ValueError as e:
            return self._fail(request, ErrorKind.PARSE_FAIL, f"json: {e}", raw=r.text)

        if not data.get("success"):
            return self._fail(request, ErrorKind.PARSE_FAIL, f"ckan error: {data.get('error')}", raw=r.text[:1000])

        records = data.get("result", {}).get("records", [])
        if not records:
            return self._fail(request, ErrorKind.NOT_FOUND, "no sale records match", raw=r.text[:500])

        obs = []
        for i, rec in enumerate(records):
            obs.append(ConnectorObservation(
                attribute=f"sale[{i}].deed_consideration",
                value=float(rec.get("PRICE")) if rec.get("PRICE") is not None else None,
                value_unit="USD",
                observation_date=self._parse_date(rec.get("SALEDATE")),
                source_url=url,
                extra={
                    "parid": rec.get("PARID"),
                    "full_address": rec.get("FULL_ADDRESS"),
                    "saledesc": rec.get("SALEDESC"),
                    "salecode": rec.get("SALECODE"),
                    "instrtyp": rec.get("INSTRTYP"),
                    "instrtypdesc": rec.get("INSTRTYPDESC"),
                    "deedbook": rec.get("DEEDBOOK"),
                    "deedpage": rec.get("DEEDPAGE"),
                    "recorddate": rec.get("RECORDDATE"),
                },
            ))
        return self._ok(request, obs, raw=r.text)

    def _query_assessment(self, request: ConnectorRequest) -> ConnectorResult:
        if not (request.address or request.parcel_id):
            return self._fail(request, ErrorKind.UNSUPPORTED, "need address or parcel_id")
        sql = self._build_sql(RESOURCE_ASSESSMENT, request, fields=[
            "PARID", "PROPERTYHOUSENUM", "PROPERTYADDRESS", "PROPERTYCITY",
            "PROPERTYZIP", "FAIRMARKETBUILDING", "FAIRMARKETLAND",
            "FAIRMARKETTOTAL", "USECODE", "USEDESC", "YEARBLT",
        ], limit=5)
        url = f"{CKAN_BASE}/datastore_search_sql?sql={sql}"
        self._throttle()
        sess = self._session()
        r, ek, ed = safe_get(sess, url)
        if r is None:
            return self._fail(request, ek, ed)
        try:
            data = r.json()
        except ValueError as e:
            return self._fail(request, ErrorKind.PARSE_FAIL, f"json: {e}", raw=r.text)
        if not data.get("success"):
            return self._fail(request, ErrorKind.PARSE_FAIL, f"ckan error: {data.get('error')}", raw=r.text[:500])
        records = data.get("result", {}).get("records", [])
        if not records:
            return self._fail(request, ErrorKind.NOT_FOUND, "no assessment record", raw=r.text[:500])
        rec = records[0]
        obs = [
            ConnectorObservation(attribute="parcel_id", value=rec.get("PARID"), source_url=url),
            ConnectorObservation(
                attribute="assessor_market_value_total",
                value=float(rec.get("FAIRMARKETTOTAL")) if rec.get("FAIRMARKETTOTAL") else None,
                value_unit="USD", source_url=url,
            ),
            ConnectorObservation(
                attribute="assessor_year_built",
                value=int(rec.get("YEARBLT")) if rec.get("YEARBLT") else None,
                source_url=url,
            ),
            ConnectorObservation(
                attribute="assessor_use_desc",
                value=rec.get("USEDESC"),
                source_url=url,
            ),
        ]
        return self._ok(request, [o for o in obs if o.value is not None], raw=r.text)

    # ── helpers ─────────────────────────────────────────────────────────────
    def _build_sql(self, resource_id: str, request: ConnectorRequest, fields: list[str], order_by: str = "", limit: int = 10) -> str:
        from urllib.parse import quote
        col_list = ", ".join(f'"{f}"' for f in fields)
        where_parts = []
        if request.parcel_id:
            where_parts.append(f"\"PARID\" = '{self._sanitize(request.parcel_id)}'")
        elif request.address:
            num, street = self._split_address(request.address)
            if num:
                where_parts.append(f"\"PROPERTYHOUSENUM\" = '{num}'")
            if street:
                # Match against FULL_ADDRESS rather than just street name to allow suffix flexibility
                where_parts.append(f"UPPER(\"FULL_ADDRESS\") LIKE '%{street.upper()}%'")
        where = (" WHERE " + " AND ".join(where_parts)) if where_parts else ""
        order = f" ORDER BY {order_by}" if order_by else ""
        sql = f'SELECT {col_list} FROM "{resource_id}"{where}{order} LIMIT {limit}'
        return quote(sql)

    @staticmethod
    def _sanitize(s: str) -> str:
        return re.sub(r"[^A-Za-z0-9_\-]", "", s)

    @staticmethod
    def _split_address(address: str) -> tuple[Optional[str], Optional[str]]:
        m = re.match(r"\s*(\d+)\s+(.+)", address)
        if not m:
            return None, address
        num = m.group(1)
        rest = m.group(2)
        # Strip city/state if present
        rest = re.split(r",", rest)[0]
        # Drop street suffix words to maximize match (Allegheny stores e.g. "EUREKA ST")
        return num, rest.strip()

    @staticmethod
    def _parse_date(s):
        from datetime import datetime
        if not s:
            return None
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%m/%d/%Y"):
            try:
                return datetime.strptime(s[:19], fmt)
            except (ValueError, TypeError):
                continue
        return None


if __name__ == "__main__":
    c = WprdcAlleghenyConnector()
    req = ConnectorRequest(address="722 Eureka St, Pittsburgh PA")
    result = c.query(req)
    print(f"success={result.success} error={result.error_kind}/{result.error_detail}")
    for o in result.observations[:5]:
        print(f"  {o.attribute} = {o.value} {o.value_unit or ''} @ {o.observation_date}")
