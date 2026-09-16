"""entitlement_control_mismatch — fires when a real-estate/development offering's claims diverge
from the public entitlement record (the masking mechanism caught on AHC "Sun Valley").

THE SIGNAL. A sponsor markets "we are developing this $X, N-unit, for-sale project" — but the
city's site-plan record names a DIFFERENT applicant/owner (often the master developer), a
DIFFERENT unit count, and/or a DIFFERENT product type (e.g., entitled apartments vs. marketed
for-sale rowhouses). The offering re-presents someone else's entitlement, on land the sponsor may
not own, as its own project. This is invisible to a deck-internal read; it only surfaces against
the primary entitlement record — which the laserfiche_weblink connector now supplies (M-side).

THE KILLER CONDITION (severity HIGH): the marketed sponsor/developer appears NOWHERE in the
entitlement's applicant / owner / representative — i.e., per the public record the sponsor is not
a party to the approval at all.

VALIDATED 2026-06-17 on AHC Sun Valley / Blackwood Groves Block 9 (City file 24635): marketed as
American Housing Corp's 33-unit for-sale rowhouse project; the record shows Bridger Land Group /
Blackwood Land Fund LLC as applicant+owner (AHC absent), 30 apartment units.

CONTRACT: evaluate(offering, record) -> {fires, reason, severity, evidence}. Same shape as the
muni/public_co detectors. Consumes the laserfiche_weblink connector's parsed entitlement record.
"""
from __future__ import annotations
import re


def _norm(s: str) -> str:
    s = (s or "").lower()
    s = re.sub(r"\b(llc|inc|corp|corporation|company|co|lp|llp|ltd|group|holdings|fund|partners)\b", " ", s)
    return re.sub(r"[^a-z0-9 ]", " ", s).strip()


def _name_in(claimed: str, parties: list[str]) -> bool:
    """True if the claimed developer matches any entitlement party (token-overlap, suffix-stripped)."""
    c = set(_norm(claimed).split())
    if not c:
        return False
    for p in parties:
        pt = set(_norm(p).split())
        if not pt:
            continue
        overlap = c & pt
        if overlap and (len(overlap) >= min(2, len(c)) or len(overlap) / len(c) >= 0.5):
            return True
    return False


_SALE = ("for-sale", "for sale", "condominium", "condo", "rowhouse", "row house", "townhome",
         "town home", "townhouse", "for-sale rowhouse")
_RENT = ("apartment", "rental", "multifamily", "multi-family", "for-rent", "for rent", "lease")


def _product_class(s: str) -> str | None:
    t = (s or "").lower()
    if any(k in t for k in _RENT): return "rental"
    if any(k in t for k in _SALE): return "for_sale"
    return None


def evaluate(offering: dict, record: dict) -> dict:
    """
    offering = {
      "developer": str,          # the sponsor marketing the deal
      "units": int|None,         # marketed unit count
      "product": str|None,       # "for-sale rowhouses" / "townhomes" / etc.
      "claims_owns_land": bool,  # does the offering present the land as owned/controlled?
    }
    record = parsed entitlement (from laserfiche_weblink): {
      "applicant": str, "property_owner": str, "representative": str,
      "units": int|None, "description"/"project_type": str (product), "owner_is_sponsor": bool|None
    }
    """
    parties = [record.get(k, "") for k in ("applicant", "property_owner", "representative")]
    parties = [p for p in parties if p]
    dev = offering.get("developer", "")
    flags, ev = [], {"entitlement_parties": parties}

    sponsor_absent = bool(dev) and bool(parties) and not _name_in(dev, parties)
    if sponsor_absent:
        flags.append("SPONSOR_NOT_PARTY_TO_ENTITLEMENT")
        ev["sponsor"] = dev

    cu, ru = offering.get("units"), record.get("units")
    if isinstance(cu, int) and isinstance(ru, int) and cu != ru:
        flags.append("UNIT_COUNT_MISMATCH")
        ev["units_claimed_vs_record"] = [cu, ru]

    pc_off = _product_class(offering.get("product", ""))
    pc_rec = _product_class(record.get("description") or record.get("project_type") or "")
    if pc_off and pc_rec and pc_off != pc_rec:
        flags.append("PRODUCT_TYPE_MISMATCH")
        ev["product_claimed_vs_record"] = [pc_off, pc_rec]

    if offering.get("claims_owns_land") and record.get("owner_is_sponsor") is False:
        flags.append("LAND_OWNERSHIP_MISMATCH")

    if not flags:
        return {"fires": False, "reason": "ENTITLEMENT_CONSISTENT_WITH_OFFERING", "evidence": ev}

    severity = "HIGH" if "SPONSOR_NOT_PARTY_TO_ENTITLEMENT" in flags else (
        "REVIEW" if len(flags) >= 2 else "LOW")
    if severity != "HIGH" and "LAND_OWNERSHIP_MISMATCH" in flags:
        severity = "REVIEW"
    interp = ("The marketing sponsor does not appear in the entitlement's applicant/owner/"
              "representative — per the public record the sponsor is not a party to the approval; "
              "the offering re-presents another entity's entitlement as its own."
              if "SPONSOR_NOT_PARTY_TO_ENTITLEMENT" in flags else
              "The offering's claims diverge from the entitlement record on " + ", ".join(flags) + ".")
    ev["interpretation"] = interp
    return {"fires": True, "reason": flags[0], "severity": severity,
            "evidence": {**ev, "all_flags": flags}}


# APPLIES_TO contract — dispatch index keys on this (see feedback_kg_dispatch_index_pattern)
APPLIES_TO = {
    "asset_classes": ["real_estate_development", "private_re_credit", "land_secured"],
    "must_have_feature": "development_offering",          # a deck/PPM for a specific RE project
    "requires_sources": ["laserfiche_weblink"],            # needs the entitlement record (M-side)
    "fires_on": "claimed sponsor/units/product vs. city entitlement record divergence",
}


if __name__ == "__main__":
    # AHC Sun Valley demo (R from the offering deck, M from the laserfiche_weblink connector)
    off = {"developer": "American Housing Corp", "units": 33,
           "product": "for-sale rowhouses at $2.5-2.9M", "claims_owns_land": True}
    rec = {"applicant": "Bridger Land Group", "property_owner": "Blackwood Land Fund LLC",
           "representative": "Bridger Land Group", "units": 30,
           "description": "3 residential apartment buildings, 10 units each", "owner_is_sponsor": False}
    r = evaluate(off, rec)
    print("fires:", r["fires"], "| severity:", r.get("severity"), "| reason:", r["reason"])
    print(" flags:", r["evidence"].get("all_flags"))
    print(" ", r["evidence"].get("interpretation"))
    # control: a deal where the sponsor IS the applicant and everything matches
    ok = evaluate({"developer": "Bridger Land Group", "units": 30, "product": "apartments"},
                  {"applicant": "Bridger Land Group", "property_owner": "Bridger Land Group",
                   "representative": "Bridger Land Group", "units": 30, "description": "apartment buildings"})
    print("control fires:", ok["fires"], "(should be False)")
