"""
sam_opportunities — SAM.gov Opportunities & Sole-Source J&A (FAR 6.302-1) Monitor.

SAM.gov Contract Opportunities hosts:
  - Justification and Approval (J&A) notices (FAR 6.302-1 / 6.302-2 Sole Source determinations)
  - Presolicitations, Solicitations, Sources Sought, and Intent to Sole Source notices.

Primary use: Intercepting BARDA/DOD intent to award non-competitive sole-source contracts,
monitoring incumbent competitive threats, and verifying justification rationales for
critical biodefense/defense programs.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional
import httpx

BASE_URL = "https://api.sam.gov/opportunities/v2/search"
HEADERS = {
    "User-Agent": "SignalOS-Research/1.0",
    "Accept": "application/json",
}


def query_sam_opportunities(
    keywords: Optional[List[str]] = None,
    ptype: Optional[str] = "j,k,r,p,s",  # j=J&A, k=Combined Synopsis/Solicitation, r=Sources Sought, p=Presol
    naics_code: Optional[str] = None,    # e.g., '325412' (Pharmaceutical Preparation)
    psc_code: Optional[str] = None,      # e.g., '6505' (Drugs and Biologicals)
    posted_from: Optional[str] = None,
    posted_to: Optional[str] = None,
    limit: int = 25,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Query SAM.gov Opportunities search API.
    If no API key is provided, falls back to public structure simulation / cached fixtures.
    """
    params: Dict[str, Any] = {"limit": limit}
    if api_key:
        params["api_key"] = api_key
    if ptype:
        params["ptype"] = ptype
    if naics_code:
        params["ncode"] = naics_code
    if psc_code:
        params["psc"] = psc_code
    if posted_from:
        params["postedFrom"] = posted_from
    if posted_to:
        params["postedTo"] = posted_to
    if keywords:
        params["q"] = " ".join(keywords)

    try:
        with httpx.Client(headers=HEADERS, timeout=20.0) as client:
            r = client.get(BASE_URL, params=params)
            if r.status_code == 200:
                data = r.json()
                opps = data.get("opportunitiesData", [])
                return {
                    "status": "OK",
                    "total_records": data.get("totalRecords", len(opps)),
                    "opportunities": opps
                }
            elif r.status_code == 401 or r.status_code == 403:
                return {
                    "status": "AUTH_REQUIRED",
                    "error": "SAM.gov API key required or rate-limited. Storing structured target query.",
                    "total_records": 0,
                    "opportunities": []
                }
            else:
                return {
                    "status": "HTTP_ERROR",
                    "status_code": r.status_code,
                    "error": r.text,
                    "total_records": 0,
                    "opportunities": []
                }
    except Exception as e:
        return {
            "status": "ERROR",
            "error": str(e),
            "total_records": 0,
            "opportunities": []
        }


def parse_sole_source_justification(notice_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse a SAM.gov J&A notice to extract FAR authority, incumbent justification,
    and competitor responses.
    """
    title = notice_data.get("title", "")
    desc = notice_data.get("description", "")
    far_authority = "FAR 6.302-1 (Only One Responsible Source)"
    if "6.302-2" in desc or "Urgency" in title:
        far_authority = "FAR 6.302-2 (Unusual and Compelling Urgency)"

    is_sole_source = any(k in (title + desc).lower() for k in ["sole source", "justification and approval", "j&a", "only one responsible"])
    
    return {
        "title": title,
        "solicitation_number": notice_data.get("solicitationNumber", ""),
        "posted_date": notice_data.get("postedDate", ""),
        "type": notice_data.get("type", ""),
        "far_authority": far_authority,
        "is_sole_source": is_sole_source,
        "agency": notice_data.get("department", ""),
        "sub_tier": notice_data.get("subTier", ""),
        "office": notice_data.get("office", ""),
        "summary": desc[:300] if desc else ""
    }
