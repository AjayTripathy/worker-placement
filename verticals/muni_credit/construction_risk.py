"""construction_risk — project / completion risk.

For a tax-secured GO this is essentially N/A: the unlimited ad-valorem pledge stands whether or not the
financed school is ever built — a structural strength of GO over lease-revenue / certificates of
participation (COP). It applies to REVENUE and LEASE/COP bonds: a NEW-MONEY construction project that
must be completed and then generate revenue (or, for lease bonds, be occupied — abatement risk if not)
carries completion / cost-overrun risk; a REFUNDING of an existing, operating system does not.

Classifies use-of-proceeds from the OS text. Output flags are soft (REVIEW) — completion risk is a
real but rarely-fatal concern, and it's the right lens only on the non-GO sleeve.
"""
import re

_LEASE = re.compile(r"\b(lease|abatement|certificates? of participation|\bcops?\b)\b", re.I)
_REFUND = re.compile(r"\brefund", re.I)
_NEWMONEY = re.compile(r"\b(construct|acquir\w+ and construct|the project|new\s+\w+\s+(plant|facilit|treatment)|"
                       r"expansion|design and build|finance the (acquisition|construction))", re.I)


def construction_risk(pledge=None, security=None, os_text=None):
    sec = (security or "").lower()
    is_revenue = pledge in ("water", "revenue") or "revenue" in sec or _LEASE.search(sec or "")
    if not is_revenue:
        return {"construction_risk": "N/A-GO",
                "project_type": "tax-GO — pledge stands regardless of project completion"}, []
    flags = []
    # The security TITLE is authoritative for refunding; lease/COP only if the TITLE says so (a 300-page OS
    # mentions "lease" incidentally everywhere). New-money is read from a FOCUSED use-of-proceeds scan
    # (cover + plan-of-finance, first ~6000 chars), not the whole document.
    title_refunding = bool(_REFUND.search(sec))
    title_lease = bool(_LEASE.search(sec))
    head = (os_text or "")[:6000]
    newmoney = bool(re.search(r"finance the (acquisition|construction|design)|"
                              r"proceeds[^.]{0,60}(to construct|to acquire and construct|the construction of)|"
                              r"new[- ](money|project)", head, re.I))
    if not os_text:
        ptype = "use-of-proceeds UNVERIFIABLE (OS not parsed)"; flags.append("construction-UNVERIFIABLE")
    elif title_refunding and not newmoney:
        ptype = "refunding of an existing, operating system (low completion risk)"
    elif newmoney and not title_refunding:
        ptype = "new-money construction (completion / cost-overrun risk)"; flags.append("construction-new-money")
    elif newmoney and title_refunding:
        ptype = "refunding + some new-money (partial completion risk)"; flags.append("construction-partial")
    else:
        ptype = "existing system, no new-money in use-of-proceeds (low completion risk)"
    if title_lease:
        flags.append("lease/COP-abatement-risk")     # non-completion -> abatement of lease payments
    return {"construction_risk": "flagged" if flags else "low", "project_type": ptype}, flags
