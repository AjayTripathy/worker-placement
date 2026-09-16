"""SPV-conduit awareness for Form D verification.

A venture round is frequently funded through one or more single-purpose
vehicles (SPVs) rather than direct checks to the operating company. On EDGAR
each SPV files its OWN Form D as a "Pooled Investment Fund", and the issuer
entityName encodes the operating company it feeds, e.g.:

    "American Housing Corp Jan 2025 a Series of CGF2021 LLC"   (Sydecar series)

So a naive `raise_amount == form_d.totalAmountSold` check is structurally wrong
on these deals:
  * a single SPV's `totalAmountSold` is one SLICE of the round, never the whole;
  * a loose issuer-name search also returns UNRELATED pooled funds that merely
    share a token (e.g. an "Antler Brasil Management" fund matching "Antler").

This module:
  1. recognises an SPV-conduit Form D and the administrator behind it
     (Sydecar / AngelList / Carta / Assure / ...),
  2. ATTRIBUTES a conduit to an operating company by issuer-name prefix,
  3. FILTERS OUT funds that merely name-collide,
  4. sums attributable conduit `totalAmountSold` and reconciles it against the
     headline raise as a SUBSET (Σconduits <= headline is consistent; a
     material excess is the only divergence).

Both the comparator (verdict) and the tearsheet (rendering) import this so the
"this is a Sydecar SPV conduit for AHC" judgement is computed in exactly one
place.
"""
from __future__ import annotations

import re
from typing import Optional

# Fund-administration platforms that appear as a relatedPerson (often as a
# Director / Manager) on SPV Form Ds. Used only as a corroborating signal — the
# issuer-name "a Series of" pattern is the primary detector.
KNOWN_SPV_ADMINS = (
    "sydecar", "angellist", "assure", "carta", "belltower", "flow inc",
    "roll up vehicles", "ruv", "glassboard", "odin", "vauban",
)

# Issuer-name tokens that mark a series/SPV conduit rather than an operating co.
_SERIES_MARKERS = ("a series of", "series of", " spv", "spv ", "investments llc",
                    "investors llc", "co-invest", "coinvest")

# Generic corporate suffixes stripped when extracting an operating-company core.
_SUFFIX_TOKENS = frozenset({
    "the", "inc", "inc.", "incorporated", "corp", "corp.", "corporation",
    "co", "co.", "company", "llc", "l.l.c.", "lp", "l.p.", "ltd", "limited",
    "holdings", "labs", "technologies", "technology", "inc/de",
})


def normalize(s: Optional[str]) -> str:
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def operating_core(name: Optional[str]) -> str:
    """Drop trailing corporate-suffix tokens to get the distinctive name core.

    'American Housing Corp' -> 'american housing'
    'The American Housing Corporation' -> 'american housing'
    """
    toks = normalize(name).split()
    while toks and toks[-1] in _SUFFIX_TOKENS:
        toks.pop()
    while toks and toks[0] in _SUFFIX_TOKENS:
        toks.pop(0)
    return " ".join(toks)


def is_pooled_fund(form_d: dict) -> bool:
    igt = (form_d.get("industryGroupType") or "")
    return "pooled investment" in igt.lower()


def conduit_admin(form_d: dict) -> Optional[str]:
    """Return the fund-admin platform name if a known one appears as a related
    person, else None."""
    for rp in (form_d.get("relatedPersons") or []):
        blob = normalize(f"{rp.get('firstName','')} {rp.get('lastName','')}")
        for admin in KNOWN_SPV_ADMINS:
            if admin in blob:
                return admin
    return None


def issuer_names(form_d: dict) -> list[str]:
    return [i.get("entityName") for i in (form_d.get("issuers") or []) if i.get("entityName")]


def looks_like_series_vehicle(form_d: dict) -> bool:
    for nm in issuer_names(form_d):
        low = nm.lower()
        if any(m in low for m in _SERIES_MARKERS):
            return True
    return False


def attributable_to(form_d: dict, operating_name: str) -> bool:
    """True iff this Form D's issuer is a conduit FEEDING `operating_name`.

    The issuer entityName of an SPV begins with the operating company's name
    core, e.g. 'American Housing Corp Jan 2025 a Series of CGF2021 LLC' begins
    with 'american housing'. We require the issuer-name normalization to START
    WITH the operating core (not merely contain a shared token) so that an
    unrelated 'Antler Brasil Management' fund does NOT attribute to 'Antler'.
    """
    core = operating_core(operating_name)
    if not core or len(core) < 3:
        return False
    for nm in issuer_names(form_d):
        n = normalize(nm)
        if n.startswith(core + " ") or n == core:
            return True
    return False


def summarize_conduits(form_d_dicts: list[dict], operating_name: str) -> dict:
    """Partition Form D filings into attributable SPV conduits vs name-collisions.

    Returns:
      {
        "operating_core": str,
        "attributable": [ {issuer, cik, admin, sold, accession, xml_url} ],
        "total_sold": float,             # Σ attributable totalAmountSold
        "admins": [str],                 # distinct admins on attributable conduits
        "unrelated_pooled": [ {issuer, sold} ],  # pooled funds that name-collided
      }
    """
    attributable, unrelated = [], []
    for fd in form_d_dicts:
        if not isinstance(fd, dict):
            continue
        names = issuer_names(fd)
        rec = {
            "issuer": names[0] if names else None,
            "cik": (fd.get("issuers") or [{}])[0].get("cik") if fd.get("issuers") else None,
            "admin": conduit_admin(fd),
            "sold": fd.get("totalAmountSold"),
            "offering": fd.get("totalOfferingAmount"),
            "accession": fd.get("accession"),
            "xml_url": fd.get("xml_url"),
        }
        if attributable_to(fd, operating_name):
            attributable.append(rec)
        elif is_pooled_fund(fd):
            unrelated.append({"issuer": rec["issuer"], "sold": rec["sold"]})
    total = sum(float(r["sold"]) for r in attributable
                if isinstance(r["sold"], (int, float)))
    admins = sorted({r["admin"] for r in attributable if r["admin"]})
    return {
        "operating_core": operating_core(operating_name),
        "attributable": attributable,
        "total_sold": total,
        "admins": admins,
        "unrelated_pooled": unrelated,
    }


# Verdict labels mirror comparator.Severity names so callers can map directly.
def assess_raise_via_conduits(operating_name: str, headline_raise,
                              form_d_dicts: list[dict]) -> Optional[dict]:
    """Reconcile a headline raise against attributable SPV conduits.

    Returns None when there is no SPV-conduit structure to reason about (caller
    should fall back to the plain numeric rule). Otherwise returns:
      {severity, divergence_pct, summary, note}
    where severity is one of PASS / MODERATE / SEVERE / UNVERIFIABLE.
    """
    summ = summarize_conduits(form_d_dicts, operating_name)
    has_pooled = summ["attributable"] or summ["unrelated_pooled"]
    if not has_pooled:
        return None  # not an SPV situation; let the numeric rule run

    try:
        headline = float(headline_raise)
    except (TypeError, ValueError):
        headline = None

    n = len(summ["attributable"])
    admins = ", ".join(a.title() for a in summ["admins"]) or "an unnamed administrator"
    total = summ["total_sold"]

    if n == 0:
        # Only unrelated pooled funds name-collided — no conduit actually
        # attributable to this issuer. Honest verdict: unconfirmed, NOT refuted.
        names = "; ".join(u["issuer"] or "?" for u in summ["unrelated_pooled"][:3])
        return {
            "severity": "UNVERIFIABLE",
            "divergence_pct": None,
            "summary": summ,
            "note": (f"Form D search returned only pooled funds that do NOT attribute to "
                     f"'{summ['operating_core']}' (name collisions: {names}). No SPV conduit "
                     f"for this issuer was confirmed — open gap, not a refutation."),
        }

    conduit_desc = (f"{n} SPV conduit{'s' if n != 1 else ''} attributable to "
                    f"'{summ['operating_core']}' via {admins}, totaling "
                    f"${total:,.0f} sold")
    if headline is None:
        return {"severity": "PASS", "divergence_pct": 0.0, "summary": summ,
                "note": f"Cap-table structure corroborated: {conduit_desc}."}

    # A conduit total is a SUBSET of the round (direct checks + other SPVs exist),
    # so Σconduits <= headline is CONSISTENT. Only a material EXCESS is a problem.
    if total <= headline * 1.05:
        pct = (headline - total) / headline if headline else 0.0
        return {
            "severity": "PASS",
            "divergence_pct": 0.0,
            "summary": summ,
            "note": (f"Cap-table structure corroborated: {conduit_desc}, consistent with "
                     f"(a subset of) the ${headline:,.0f} headline raise "
                     f"({pct*100:.0f}% of the round is direct or via other vehicles)."),
        }
    # Conduits sold MORE than the headline round — a genuine discrepancy.
    excess = (total - headline) / headline
    sev = "SEVERE" if excess > 0.30 else "MODERATE"
    return {
        "severity": sev,
        "divergence_pct": excess,
        "summary": summ,
        "note": (f"SPV conduits attributable to '{summ['operating_core']}' sold ${total:,.0f}, "
                 f"{excess*100:.0f}% MORE than the ${headline:,.0f} headline raise — "
                 f"reconcile the round size."),
    }
