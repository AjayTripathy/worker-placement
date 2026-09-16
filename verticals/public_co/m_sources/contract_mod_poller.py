"""
contract_mod_poller — Real-time USAspending Contract Modification & Transaction Poller.

Tracks federal prime award contract modifications (MOD_NUMBER), action dates,
incremental/delta obligations, funding sub-agencies, and period of performance changes.

Primary use: Monitoring high-value government contracts (e.g. BARDA 75A50118C00019 for SIGA)
to detect option exercises, CLIN activations, and funding de-obligations ahead of SEC 8-K filings.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional
import httpx

BASE_URL = "https://api.usaspending.gov/api/v2"
HEADERS = {
    "User-Agent": "SignalOS-Research/1.0",
    "Accept": "application/json",
    "Content-Type": "application/json",
}


def fetch_award_summary(generated_award_id: str, client: Optional[httpx.Client] = None) -> Dict[str, Any]:
    """Fetch top-level award metadata for a specific generated unique award ID."""
    url = f"{BASE_URL}/awards/{generated_award_id}/"
    close_client = False
    if client is None:
        client = httpx.Client(headers=HEADERS, timeout=20.0)
        close_client = True
    try:
        r = client.get(url)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e), "generated_award_id": generated_award_id}
    finally:
        if close_client:
            client.close()


def fetch_award_transactions(
    award_id_piid: str,
    page: int = 1,
    limit: int = 50,
    client: Optional[httpx.Client] = None
) -> Dict[str, Any]:
    """
    Fetch all award transactions/modifications for an award by its PIID (e.g., '75A50118C00019').
    """
    url = f"{BASE_URL}/search/spending_by_award/"
    payload = {
        "filters": {
            "award_type_codes": ["A", "B", "C", "D"],
            "award_ids": [award_id_piid]
        },
        "fields": [
            "Award ID",
            "Modification Number",
            "Recipient Name",
            "Action Date",
            "Federal Action Obligation",
            "Award Amount",
            "Awarding Agency",
            "Awarding Sub Agency",
            "Description",
            "Period of Performance Current End Date",
            "generated_internal_id"
        ],
        "page": page,
        "limit": limit,
        "sort": "Award Amount",
        "order": "desc"
    }

    close_client = False
    if client is None:
        client = httpx.Client(headers=HEADERS, timeout=20.0)
        close_client = True
    try:
        r = client.post(url, json=payload)
        r.raise_for_status()
        data = r.json()
        results = data.get("results", [])
        return {
            "award_id": award_id_piid,
            "total_transactions": len(results),
            "page": page,
            "transactions": results
        }
    except Exception as e:
        return {
            "award_id": award_id_piid,
            "error": str(e),
            "total_transactions": 0,
            "transactions": []
        }
    finally:
        if close_client:
            client.close()


def poll_contract_modifications(
    award_piid: str,
    known_mod_numbers: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Poll an award and detect any newly published modifications compared to known state.
    """
    known_set = set(known_mod_numbers or [])
    tx_data = fetch_award_transactions(award_piid, limit=100)
    if "error" in tx_data and tx_data.get("error"):
        return {"award_id": award_piid, "status": "ERROR", "error": tx_data["error"], "new_mods": []}

    transactions = tx_data.get("transactions", [])
    new_mods = []
    total_obligated = 0.0
    latest_end_date = None

    for tx in transactions:
        mod_num = str(tx.get("Modification Number") or tx.get("Award ID", "0"))
        ob_amount = float(tx.get("Federal Action Obligation") or tx.get("Award Amount") or 0.0)
        total_obligated += ob_amount
        end_date = tx.get("Period of Performance Current End Date")
        if end_date and (not latest_end_date or end_date > latest_end_date):
            latest_end_date = end_date

        if mod_num not in known_set:
            new_mods.append({
                "modification_number": mod_num,
                "action_date": tx.get("Action Date"),
                "obligation_delta": ob_amount,
                "description": tx.get("Description", ""),
                "end_date": end_date,
                "awarding_sub_agency": tx.get("Awarding Sub Agency", "")
            })

    return {
        "award_id": award_piid,
        "status": "OK",
        "has_new_mods": len(new_mods) > 0,
        "new_mods_count": len(new_mods),
        "new_mods": new_mods,
        "cumulative_obligations": total_obligated,
        "period_of_performance_end": latest_end_date,
        "poll_timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }
