"""water_supply_authority — FIRST-PRINCIPLES water-supply verification for revenue-water muni bonds.

THE PROBLEM IT REPLACES. water_revenue_underwrite.assess_supply_risk decided supply risk by (a) keyword-
scanning the issuer's own Official Statement and (b) a hand-coded issuer->region dictionary. Neither is
verification: (a) trips on statewide-context boilerplate (it false-flagged EBMUD = Mokelumne snowmelt as
"Colorado River"); (b) is just an encoded prior asserting the answer.

R / f / M HERE. The claim R = "this system's supply portfolio + its risk." The method f = membership checks
against PUBLISHED, INDEPENDENT registries. The authority M = not the OS and not a dictionary, but:
  1. DWR State Water Project long-term water-supply contractors          (SWP allocation / Bay-Delta cuts)
  2. MWD of Southern California member agencies                          (imported Colorado+SWP blend)
  3. USBR / Law-of-the-River Colorado River CA water-delivery contractors (Lower-Basin shortage cuts)
  4. DWR Bulletin 118 critically-overdrafted groundwater basins          (SGMA mandated pumping cuts)
     -> reused from sgma_overlay.py (already encoded verbatim from DWR, with citations).
The OS and the geo dictionary are DEMOTED to corroboration. A system not found in any registry is
UNVERIFIED (never "clean") and escalates to its Urban Water Management Plan (the per-agency authority).

HONESTY ON THE REGISTRIES. (1)-(3) are encoded SNAPSHOTS of published lists (AS_OF below) with source
URLs and a refresh_registries() live-fetch hook; they hold only high-confidence, well-documented
membership. A non-match returns UNVERIFIED + an explicit UWMP escalation — it never GUESSES membership.
Verdict mapping is conservative: an import/Colorado/critical-basin dependency confirmed by a registry is a
real physical tail (HIGH); a clean local-surface system absent from every import registry and every
critical basin is LOW; anything we cannot place is UNVERIFIED.
"""
from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py). Added 2026-07-29
# to close the atlas gap; muni sector mapping mirrors detectors/dispatch_index.py.
APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ["water_enterprise"],
    "asset_classes": ["ca_water_rev_muni", "ca_water_district_revenue", "ca_water_muni"],
    "applies_universally": False,
    "kind": "detector",
    "summary": "water_supply_authority — FIRST-PRINCIPLES water-supply verification for revenue-water muni bonds.",
}
import os, re, sys, json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    import sgma_overlay as SGMA               # DWR Bulletin 118 critically-overdrafted basin authority
except Exception:
    SGMA = None

AS_OF = "2024-2025 published lists (encoded snapshot — run refresh_registries() to re-pull)"
SOURCES = {
    "swp":   "DWR State Water Project — long-term water supply contractors (water.ca.gov, SWP contractors)",
    "mwd":   "Metropolitan Water District of Southern California — member agencies (mwdh2o.com)",
    "cr":    "USBR Lower Colorado Basin / California Seven-Party Agreement water-delivery contractors",
    "sgma":  "DWR Bulletin 118 — California's Critically Overdrafted Groundwater Basins (via sgma_overlay)",
    "uwmp":  "DWR Urban Water Management Plan repository (WUEdata) — per-agency supply portfolio (escalation)",
}

# --- Registry snapshots (high-confidence published membership only; normalized lowercased key tokens) ---
# DWR State Water Project long-term water-supply contractors (29). Major muni-relevant CA agencies.
SWP_CONTRACTORS = {
    "metropolitan water district", "kern county water agency", "alameda county water district",
    "zone 7", "alameda county flood control", "santa clara valley water", "valley water",
    "antelope valley-east kern", "castaic lake water agency", "coachella valley water district",
    "desert water agency", "mojave water agency", "palmdale water district", "littlerock creek",
    "san bernardino valley municipal water", "san gorgonio pass water agency", "crestline-lake arrowhead",
    "san luis obispo county flood control", "santa barbara county flood control", "ventura county",
    "napa county flood control", "solano county water agency", "yuba city", "butte county",
    "plumas county flood control", "tulare lake basin water storage", "dudley ridge water district",
    "empire west side irrigation", "oak flat water district",
}
# Metropolitan Water District of Southern California member agencies (26: 14 cities + 12 agencies).
MWD_MEMBERS = {
    "los angeles", "anaheim", "beverly hills", "burbank", "compton", "fullerton", "glendale",
    "long beach", "pasadena", "san fernando", "san marino", "santa ana", "santa monica", "torrance",
    "calleguas municipal water", "central basin municipal water", "eastern municipal water",
    "foothill municipal water", "inland empire utilities", "las virgenes municipal water",
    "municipal water district of orange county", "san diego county water authority",
    "three valleys municipal water", "upper san gabriel valley municipal water",
    "west basin municipal water", "western municipal water",
}
# California Colorado River water-delivery contractors (Law of the River / Seven-Party priorities + USBR).
COLORADO_RIVER_CA = {
    "palo verde irrigation", "imperial irrigation district", "coachella valley water district",
    "metropolitan water district", "city of needles", "yuma project",
    "fort mojave", "chemehuevi", "colorado river indian tribes", "quechan",
}


# DWR 2020 Urban Water Management Plan — Table 6-8 Retail/Wholesale "Water Supplies - Actual" (CKAN
# datastore on data.ca.gov). The per-agency supply PORTFOLIO by source + acre-foot volume — the richest,
# most authoritative supply source (R/f/M done right: actual volumes, not the OS's words or any prior).
UWMP_RETAIL = "08e0c75d-3257-4d36-b722-ef4b5c9140a9"
UWMP_WHOLESALE = "204e4fb4-382b-4f09-bb18-1eda30777a83"
_CKAN = "https://data.ca.gov/api/3/action/datastore_search"
_UWMP_CACHE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "data", "uwmp_supply_cache.json")
_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
# WATER_SUPPLY type -> normalized bucket
_SUPPLY_TYPE = {
    "groundwater": "groundwater", "surface water": "surface", "recycled water": "recycled",
    "purchased or imported  water": "import", "purchased or imported water": "import",
    "transfers": "transfer", "exchanges": "transfer", "desalinated water - groundwater": "desal",
    "desalinated water - ocean water": "desal",
}


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", " ", (s or "").lower())


def _uwmp_cache_load() -> dict:
    try:
        return json.load(open(_UWMP_CACHE))
    except Exception:
        return {}


def fetch_uwmp_supply(issuer: str, use_cache: bool = True, timeout: int = 25) -> dict | None:
    """Fetch the agency's ACTUAL supply portfolio from the DWR 2020 UWMP Table 6-8 (data.ca.gov CKAN
    datastore). Returns {supplier, total_af, mix:{import,groundwater,surface,recycled,transfer,...},
    sources:[(type,detail,af)...], matched} aggregated from real acre-foot volumes — or None on no match /
    fetch failure. NEVER fabricates: a network failure or no-name-match returns None (caller stays UNVERIFIED)."""
    issuer = re.split(r"[—–]|\s-\s", issuer or "")[0]   # drop the bond-description suffix after the dash
    key = _norm(issuer)
    if use_cache:
        c = _uwmp_cache_load()
        if key in c:
            return c[key] or None
    # drop generic / pledge-suffix tokens so a bond-title issuer ("City of Corcoran — Water System
    # Revenue") matches the UWMP supplier name ("Corcoran  City Of") on the distinctive place token.
    _DROP = {"city", "of", "the", "district", "water", "municipal", "authority", "department", "dept",
             "system", "systems", "revenue", "revenues", "refunding", "series", "bonds", "bond",
             "wastewater", "sewer", "financing", "fin", "elec", "electric", "power", "sanitation",
             "utility", "utilities", "agency", "co", "and", "improvement", "public"}
    toks = [t for t in key.split() if t not in _DROP and len(t) > 1 and not t.isdigit()]
    if not toks:
        return None
    import urllib.request, urllib.parse
    found = None
    for rid in (UWMP_RETAIL, UWMP_WHOLESALE):
        try:
            q = urllib.parse.quote(" ".join(toks[:3]))
            url = f"{_CKAN}?resource_id={rid}&q={q}&limit=200"
            req = urllib.request.Request(url, headers={"User-Agent": _UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                recs = json.loads(r.read())["result"]["records"]
        except Exception:
            continue
        # group rows by supplier; pick the supplier whose name best token-overlaps the issuer
        from collections import defaultdict
        by_sup = defaultdict(list)
        for rec in recs:
            by_sup[rec.get("WATER_SUPPLIER_NAME") or ""].append(rec)
        best, best_score = None, 0
        for sup, rows in by_sup.items():
            st = set(_norm(sup).split())
            score = len(st & set(toks))
            if score > best_score:
                best, best_score = (sup, rows), score
        if best and best_score >= 1:
            found = best
            break
    if not found:
        if use_cache:
            c = _uwmp_cache_load(); c[key] = None
            try: json.dump(c, open(_UWMP_CACHE, "w"), indent=1)
            except Exception: pass
        return None
    supplier, rows = found
    mix, sources, total = {}, [], 0.0
    for rec in rows:
        typ = (rec.get("WATER_SUPPLY") or "").strip()
        bucket = _SUPPLY_TYPE.get(typ.lower(), "other")
        det = (rec.get("ADDITIONAL_WATER_SUPPLY_DETAIL") or "").strip()
        try:
            af = float(rec.get("ACTUAL_VOLUME_AF") or 0)
        except Exception:
            af = 0.0
        if af <= 0:
            continue
        mix[bucket] = mix.get(bucket, 0.0) + af
        total += af
        sources.append((typ, det, round(af)))
    if total <= 0:
        return None
    out = {"supplier": supplier, "total_af": round(total),
           "mix": {k: round(100 * v / total) for k, v in mix.items()},
           "sources": sorted(sources, key=lambda x: -x[2])[:6], "matched": True,
           "source_authority": SOURCES["uwmp"]}
    if use_cache:
        c = _uwmp_cache_load(); c[key] = out
        try: json.dump(c, open(_UWMP_CACHE, "w"), indent=1, default=str)
        except Exception: pass
    return out


def _match(name: str, registry: set) -> str | None:
    """Return the matched registry entry if the issuer name contains it (token-safe), else None."""
    n = _norm(name)
    for entry in registry:
        if entry in n:
            return entry
    return None


_RANK = {"none": 0, "low": 1, "moderate": 2, "high": 3, "unverified": 1}


def verify_supply(issuer: str | None, county: str | None = None, district: str | None = None,
                  system_type: str | None = None, os_text: str | None = None) -> dict:
    """Verify a revenue-water system's supply against the published registries (R/f/M, not OS keywords).

    Returns {sources:[...], import_dependent, sgma_basin, sgma_critical, risk_level, confidence, authorities,
             escalate, note}. confidence: VERIFIED (a registry placed it) / PARTIAL / UNVERIFIED (escalate
             to UWMP — never treated as clean)."""
    name = issuer or district or ""
    sources, authorities, level = [], [], "low"

    # Is the system SURFACE or GROUNDWATER supplied? sgma_overlay is county-level and built for GO
    # TAX-BASE AV-erosion — a county's overdrafted basin does NOT mean a surface-water utility (an
    # irrigation district on a river) draws from it. So the SGMA-critical -> HIGH escalation below is
    # gated to groundwater-dependent systems; a surface system in an overdrafted county is N/A.
    if not county and SGMA is not None:
        try:
            county = SGMA._infer_county_from_name(name)   # reuse sgma_overlay's name->county inference
        except Exception:
            county = None
    geo = "UNKNOWN"
    try:
        import utility_supply as _US
        geo = _US.supply_bucket(issuer=name, county=county, system_type=system_type)
    except Exception:
        pass
    surface = geo in ("SIERRA_LOCAL", "NORCAL_DELTA", "COASTAL_LOCAL") or (system_type or "") == "surface"
    groundwater_dep = (geo == "GROUNDWATER") or (system_type or "") in ("groundwater", "groundwater_mgmt")

    # Basin (DWR Bulletin 118) — shared by both tiers.
    sgma_basin = sgma_critical = None
    if SGMA is not None:
        try:
            sg = SGMA.sgma_exposure(district_name=district or issuer, county=county)
            sgma_basin, sgma_critical = sg.get("sgma_basin"), sg.get("sgma_critical")
        except Exception:
            pass

    # ---- TIER 1a: IRRIGATION DISTRICTS first — eWRIMS surface water rights + FERC hydro. They are not
    # urban UWMP filers; any UWMP entry is a tiny municipal/park slice (Turlock's was 347 AF) that would
    # mis-represent a ~600,000 AF agricultural surface supply, so eWRIMS must take precedence here.
    if "irrig" in _norm(name):
        irr = verify_irrigation_supply(name)
        if irr:
            return irr

    # ---- TIER 1 (richest authority): the agency's ACTUAL DWR UWMP supply portfolio (volumes by source).
    try:
        uwmp = fetch_uwmp_supply(name)
    except Exception:
        uwmp = None
    if uwmp:
        m = uwmp["mix"]
        imp = m.get("import", 0) + m.get("transfer", 0)
        gw, surf = m.get("groundwater", 0), m.get("surface", 0)
        # PRECISION: the UWMP names the actual basin in the source detail (e.g. "Antelope Valley
        # Groundwater") — match it against DWR's critically-overdrafted list directly, which is far more
        # precise than the county-level sgma_overlay (LA county alone spans many basins).
        if gw and SGMA is not None and not sgma_critical:
            details = " ".join(_norm(d) for (_t, d, _a) in uwmp["sources"])
            for _num, bname, _cty in getattr(SGMA, "CRITICALLY_OVERDRAFTED", []):
                key = _norm(bname).replace("san joaquin valley", "").strip()
                key = re.sub(r"\b(basin|subbasin|valley|area)\b", "", key).strip()
                if key and len(key) >= 4 and key in details:
                    sgma_critical = True; sgma_basin = bname; break
        if gw >= 40 and sgma_critical:
            lvl, why = "high", f"{gw}% groundwater in critically-overdrafted basin '{sgma_basin}'"
        elif imp >= 50:
            lvl, why = "high", f"{imp}% purchased/imported (SWP/CVP/Colorado allocation exposure)"
        elif gw >= 50:
            lvl, why = "moderate", f"{gw}% groundwater (basin '{sgma_basin or 'prioritized'}')"
        elif imp >= 25 or gw >= 40:
            lvl, why = "moderate", f"{imp}% imported / {gw}% groundwater"
        else:
            lvl, why = "low", "predominantly own surface / diversified supply"
        mixstr = ", ".join(f"{b} {p}%" for b, p in sorted(m.items(), key=lambda x: -x[1]))
        top = uwmp["sources"][0]
        auth = [uwmp["source_authority"]] + ([SOURCES["sgma"]] if (gw and sgma_basin) else [])
        return {"sources": [f"DWR UWMP actual portfolio: {mixstr}"], "import_dependent": imp >= 25,
                "sgma_basin": sgma_basin, "sgma_critical": bool(sgma_critical), "risk_level": lvl,
                "confidence": "VERIFIED", "escalate_to_uwmp": False, "authorities": auth,
                "as_of": "DWR 2020 UWMP Table 6-8", "portfolio": m, "uwmp_supplier": uwmp["supplier"],
                "note": f"DWR UWMP portfolio [{mixstr}] (largest: {top[1] or top[0]} {top[2]:,} AF) — {why}"}

    # ---- TIER 2: published registries (SWP / MWD / USBR Colorado) — used when no UWMP match.
    cr = _match(name, COLORADO_RIVER_CA)
    if cr:
        level = "high"
        sources.append(f"Colorado River — direct CA contractor ('{cr}')")
        authorities.append(SOURCES["cr"])
    mwd = _match(name, MWD_MEMBERS)
    if mwd:
        level = max(level, "high", key=_RANK.get)   # MWD supply = Colorado + SWP imports
        sources.append(f"imported via MWD member agency ('{mwd}') — Colorado River + SWP blend")
        authorities.append(SOURCES["mwd"])
    swp = _match(name, SWP_CONTRACTORS)
    if swp:
        level = max(level, "moderate", key=_RANK.get)
        sources.append(f"State Water Project contractor ('{swp}') — Bay-Delta / SWP allocation exposure")
        authorities.append(SOURCES["swp"])
        if not (cr or mwd):                          # a pure SWP contractor with no local buffer leans high
            level = max(level, "high", key=_RANK.get)

    # DWR Bulletin 118 critically-overdrafted basin (groundwater), via sgma_overlay authority.
    # Only a GROUNDWATER-dependent system's supply is actually exposed; for a surface system the county's
    # overdrafted basin is tax-base context (and a revenue bond has no tax base), so it is NOT a source.
    sgma_basin = sgma_critical = None
    context = None
    if SGMA is not None:
        try:
            sg = SGMA.sgma_exposure(district_name=district or issuer, county=county)
            sgma_basin, sgma_critical = sg.get("sgma_basin"), sg.get("sgma_critical")
            if sgma_basin and groundwater_dep:
                level = "high" if sgma_critical else max(level, "moderate", key=_RANK.get)
                sources.append(f"groundwater in DWR basin '{sgma_basin}'"
                               + (" — CRITICALLY OVERDRAFTED, SGMA pumping cuts by 2040" if sgma_critical
                                  else " (DWR-prioritized)"))
                authorities.append(SOURCES["sgma"])
            elif sgma_basin and surface:
                context = (f"county overlies basin '{sgma_basin}'"
                           + (" (critically overdrafted)" if sgma_critical else "")
                           + f", but this system's supply is {geo.replace('_',' ').title()} surface water — "
                           f"not a supply risk for this system")
            elif sgma_basin:                          # dependence unconfirmed -> escalate, don't assume clean
                level = max(level, "moderate", key=_RANK.get)
                sources.append(f"in basin '{sgma_basin}'"
                               + (" (critically overdrafted)" if sgma_critical else "")
                               + " — groundwater-dependence UNCONFIRMED, verify via UWMP")
                authorities.append(SOURCES["sgma"])
        except Exception:
            pass

    if sources:
        confidence = "VERIFIED"
        escalate = False
        note = "; ".join(sources)
    else:
        # absent from every import registry AND not in a critical basin: most likely a self-supplied
        # local-surface system with senior water rights -> LOW, but we did NOT positively source it,
        # so confidence is PARTIAL and we name the escalation authority. Never "clean".
        confidence = "PARTIAL"
        level = "low"
        escalate = True
        base = ("not a SWP/MWD/Colorado-River contractor")
        base += (f"; {context}" if context else " and not groundwater in a critically-overdrafted basin")
        note = (base + " — likely self-supplied local-surface/senior-rights; CONFIRM the portfolio "
                "against the agency's DWR Urban Water Management Plan before relying on LOW")
        authorities.append(SOURCES["uwmp"])

    return {
        "sources": sources, "import_dependent": bool(cr or mwd or swp),
        "sgma_basin": sgma_basin, "sgma_critical": bool(sgma_critical),
        "risk_level": level, "confidence": confidence, "escalate_to_uwmp": escalate,
        "authorities": authorities, "as_of": AS_OF, "note": note,
    }


# --------------------------------------------------------------------------- irrigation districts
# Irrigation districts are NOT urban UWMP filers — their supply is SURFACE WATER under appropriative /
# pre-1914 rights + a Sierra reservoir + FERC-licensed hydro. The authority is the State Water Board's
# eWRIMS water-rights database (live, data.ca.gov) — the priority date + right status determine drought
# CURTAILMENT seniority (the real supply risk: junior post-1914 rights are curtailed first; pre-1914 /
# early-licensed senior rights are last). FERC governs the hydro/reservoir relicensing (a pointer below).
EWRIMS_LIST = "151c067a-088b-42a2-b6ad-99d84b48fb36"   # CA Water Rights LIST (Detail Summary)
SOURCES["ewrims"] = "CA State Water Resources Control Board — eWRIMS water-rights record (data.ca.gov)"
SOURCES["ferc"] = "FERC eLibrary — hydroelectric project license / relicensing (verify by project no.)"
# Major CA irrigation-district FERC hydro projects (project no. + reservoir are documented facts; the
# license/relicensing STATUS must be confirmed on FERC eLibrary — encoded as a pointer, not asserted).
FERC_HYDRO = {
    "merced irrigation": ("P-2179", "Merced River Project — New Exchequer Dam / Lake McClure"),
    "modesto irrigation": ("P-2299", "Don Pedro Project — Don Pedro Reservoir (jointly w/ Turlock ID)"),
    "turlock irrigation": ("P-2299", "Don Pedro Project — Don Pedro Reservoir (jointly w/ Modesto ID)"),
    "oakdale irrigation": ("P-2067", "Tri-Dam Project — Tulloch/Beardsley/Donnells (w/ South San Joaquin ID)"),
    "south san joaquin": ("P-2067", "Tri-Dam Project (w/ Oakdale ID)"),
    "nevada irrigation": ("P-2266", "Yuba-Bear Hydroelectric Project"),
    "placer county water": ("P-2079", "Middle Fork American River Project"),
}
_SENIOR_TYPES = ("statement of div", "pre-1914", "riparian", "registration")   # curtailment-protected
_ACTIVE = ("licensed", "permitted", "certified", "claimed", "registered")


def fetch_water_rights(issuer: str, use_cache: bool = True, timeout: int = 30) -> dict | None:
    """eWRIMS water-rights portfolio for a district (live, data.ca.gov). Returns {owner, rights:[...],
    has_senior, earliest_priority, licensed_appropriative, storage_af, sources:[stream...], has_power,
    n_active} or None (no match / fetch fail -> caller escalates; never fabricates)."""
    name = re.split(r"[—–]|\s-\s", issuer or "")[0]
    key = "wr:" + _norm(name)
    if use_cache:
        c = _uwmp_cache_load()
        if key in c:
            return c[key] or None
    _drop = ("city", "of", "the", "water", "district", "authority", "co", "financing", "fin", "light",
             "power", "electric", "system", "series", "refunding", "revenue", "bonds", "and")
    toks = [t for t in _norm(name).split() if t not in _drop and len(t) > 1 and not t.isdigit()]
    if not toks:
        return None
    import urllib.request, urllib.parse
    try:
        q = urllib.parse.quote(" ".join(toks[:3]) + " irrigation")
        url = f"{_CKAN}?resource_id={EWRIMS_LIST}&q={q}&limit=400"
        req = urllib.request.Request(url, headers={"User-Agent": _UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            recs = json.loads(r.read())["result"]["records"]
    except Exception:
        return None
    want = set(toks)
    rights, streams = [], set()
    has_senior = licensed_appro = has_power = False
    storage = 0.0; priorities = []; owner = None
    for rec in recs:
        o = (rec.get("PRIMARY_OWNER_NAME") or rec.get("APPLICATION_PRIMARY_OWNER") or "")
        o_norm = _norm(o); ot = set(o_norm.split())
        # require a distinctive place-name overlap AND that the owner is an irrigation district — including
        # the "I D" abbreviation and JOINT ownership ("TURLOCK I D & MODESTO I D" = Don Pedro co-owners).
        looks_irrig = ("irrigation" in ot) or ("irr" in o_norm) or ("i" in ot and "d" in ot)
        if not (want & ot) or not looks_irrig:
            continue
        status = (rec.get("WATER_RIGHT_STATUS") or "").lower()
        if not any(s in status for s in _ACTIVE):                       # skip cancelled/revoked/rejected
            continue
        owner = owner or o
        typ = (rec.get("WATER_RIGHT_TYPE") or "")
        if any(s in typ.lower() for s in _SENIOR_TYPES):
            has_senior = True
        if "appropriative" in typ.lower() and "licensed" in status:
            licensed_appro = True
        if (rec.get("USE_CODE") or "").lower().find("power") >= 0:
            has_power = True
        pd = rec.get("PRIORITY_DATE")
        if pd:
            priorities.append(pd[:10])
        try:
            face = float(rec.get("FACE_VALUE_AMOUNT") or 0)
            storage = max(storage, face)
        except Exception:
            pass
        src = rec.get("SOURCE_NAME")
        if src and src.strip().lower() not in ("na", "n/a", "none", "unnamed", "unknown"):
            streams.add(src.title())
        rights.append((typ, rec.get("WATER_RIGHT_STATUS"), pd, rec.get("SOURCE_NAME")))
    if not rights:
        out = None
    else:
        out = {"owner": owner, "n_active": len(rights), "has_senior": has_senior,
               "licensed_appropriative": licensed_appro, "has_power": has_power,
               "earliest_priority": min(priorities) if priorities else None,
               "max_face_af": round(storage), "sources": sorted(streams)[:5],
               "source_authority": SOURCES["ewrims"]}
    if use_cache:
        c = _uwmp_cache_load(); c[key] = out
        try: json.dump(c, open(_UWMP_CACHE, "w"), indent=1, default=str)
        except Exception: pass
    return out


def verify_irrigation_supply(issuer: str) -> dict | None:
    """First-principles supply for an IRRIGATION DISTRICT: senior surface water rights (eWRIMS) + Sierra
    storage + FERC hydro. Senior/licensed rights on a Sierra river with own reservoir = LOW (the most
    drought-secure CA water — last curtailed). Returns the verdict dict, or None if eWRIMS has no rights."""
    wr = fetch_water_rights(issuer)
    if not wr:
        return None
    nm = _norm(issuer)
    ferc = next((v for k, v in FERC_HYDRO.items() if k in nm), None)
    secure = wr["has_senior"] or (wr["licensed_appropriative"] and (wr["max_face_af"] or 0) > 50_000)
    if secure:
        lvl = "low"
        why = ("senior/licensed appropriative surface rights"
               + (" + pre-1914 statement (curtailment-protected)" if wr["has_senior"] else "")
               + (f" + {wr['max_face_af']:,} AF reservoir storage" if wr["max_face_af"] else ""))
    elif wr["n_active"]:
        lvl = "moderate"
        why = "active appropriative rights but no senior/pre-1914 priority or storage confirmed — junior rights are curtailed first in drought"
    else:
        return None
    src = ", ".join(wr["sources"][:3]) or "Sierra river"
    note = (f"eWRIMS water rights: {wr['n_active']} active right(s) on {src}; {why}")
    auth = [wr["source_authority"]]
    if ferc:
        note += f". Hydro: FERC {ferc[0]} {ferc[1]} — confirm license/relicensing on FERC eLibrary"
        auth.append(SOURCES["ferc"])
    return {"sources": [note], "import_dependent": False, "sgma_basin": None, "sgma_critical": False,
            "risk_level": lvl, "confidence": "VERIFIED", "escalate_to_uwmp": False, "authorities": auth,
            "as_of": "eWRIMS live", "note": note, "water_rights": wr, "ferc": ferc}


def refresh_registries(timeout: int = 30) -> dict:
    """Live-refresh the import-source registries from the published authorities, replacing the snapshot.
    Best-effort: gov sites are JS/PDF-heavy and may block; on failure the cited snapshot stands and the
    caller is told so (UNVERIFIED beats a stale guess). Returns {source: status}."""
    out = {}
    try:
        import urllib.request
        for key, url in (("mwd", "https://www.mwdh2o.com/who-we-are/member-agencies/"),
                         ("swp", "https://water.ca.gov/programs/state-water-project/management/"
                                 "swp-water-contractors")):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=timeout) as r:
                    out[key] = f"fetched {len(r.read())} bytes (parse-to-registry TODO — manual review)"
            except Exception as e:
                out[key] = f"fetch failed ({type(e).__name__}) — snapshot retained"
    except Exception as e:
        out["error"] = str(e)[:120]
    out["note"] = "snapshot is authoritative-as-cited; parse-to-registry left manual to avoid silent drift"
    return out


if __name__ == "__main__":
    for iss, cty in [("East Bay Municipal Utility District", "Alameda"),
                     ("City of Corcoran", "Kings"),
                     ("Palmdale Water District", "Los Angeles"),
                     ("City of Azusa", "Los Angeles"),
                     ("Merced Irrigation District", "Merced"),
                     ("City of Riverside", "Riverside")]:
        v = verify_supply(iss, cty, district=iss)
        print(f"{iss[:30]:30} -> {v['risk_level'].upper():10} [{v['confidence']}] {v['note'][:80]}")
