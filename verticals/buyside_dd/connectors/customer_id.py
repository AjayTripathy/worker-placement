"""customer_id — identify a company's UNDISCLOSED top customer(s) ("whales") by triangulating
physical/structural evidence and aggregating Bayesianly. Promoted to the brain from the Stevanato
(STVN) GLP-1 whale-ID, 2026-06-25.

When a diligence finds MATERIAL customer concentration ("top customer = N% of revenue") but the
company won't NAME the customer, this resolves who it most likely is — the swing factor for any
single-customer-dependent thesis. The method:

  1. resolve_shipping_entities(company) — companies ship on customs bills-of-lading under their
     OPERATING/legal subsidiary, NOT the brand. THE LESSON: Stevanato ships as "Nuova Ompi SRL";
     querying the brand returns nothing. Resolve the real shipper first. (Seed registry below;
     extend as the brain learns each one.)
  2. customs_consignees(shipper) — free US bill-of-lading aggregators (importinfo / importgenius
     public tiers; importyeti is Cloudflare-blocked) give shipper->consignee. BLIND SPOT: foreign
     fill-finish bypasses US customs (Novo fills in Denmark) -> "customer absent" is weakly
     informative, never dispositive. Down-weight absence, don't zero it.
  3. bayesian_customer_id(candidates, evidence) — each evidence channel is a likelihood ratio over
     the candidate set; posterior = prior x product(LRs), plus leave-one-out robustness so we see
     how much the answer leans on any single channel.

Evidence channels (the reusable template): customs_bol, co_location, disclosed_agreements,
product_format, revenue_geography, demand_trend_correlation.
"""

from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py) — added 2026-07-29 gap-close.
APPLIES_TO = {
    "kind": 'm_source',
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ['imports_physical_goods', 'undisclosed_top_customer', 'customer_concentration_above_10pct'],
    "asset_classes": ['corporate_ipo_dd'],
    "applies_universally": False,
    "summary": 'Customs-BOL shipper-alias triangulation of undisclosed top customers. Physical-goods importers.',
}

import math
import os
import re
from typing import Optional

import requests

from .base import (BaseConnector, ConnectorObservation, ConnectorRequest,
                   ConnectorResult, ErrorKind)

# Companies whose customs-BOL shipper name differs from the brand (the Nuova Ompi lesson).
# Extend as discovered — this is the brain accumulating entity-resolution knowledge.
SHIPPING_ALIASES: dict[str, list[str]] = {
    "stevanato": ["Nuova Ompi", "Ompi", "Ompi of America"],
    # Added 2026-07-11 (trade-data sweep). WST = the strongest NEW whale: unnamed single customer
    # ACCELERATING 10.9%->12.3%->15.8% ($485.9M FY25) as GLP-1 pen/autoinjector HVP ramps. KEY
    # REFINEMENT: West ships one HOP removed — its EU plants ship to a CDMO FILLER (Patheon), not the
    # brand, so you must bucket consignees {brand-owned US plant vs CDMO intermediary} and run a 2nd hop
    # (which CDMO fills for which brand). importyeti already shows West<->Novo (~4,982 recs) + West<->Patheon.
    "west pharmaceutical": ["West Pharmaceutical Services", "West Pharma Services Ireland",
                            "West Pharmaceutical Services Deutschland", "Daikyo", "Patheon"],
    # Gerresheimer: strongest READ-THROUGH signal (illiquid Frankfurt/OTC ADR GRRMY, not clean US equity);
    # live BOLs already show a Novo consignee; active Morpheus Research short on GLP-1 exposure — resolve
    # the US consignee list to adjudicate the bull-vs-Morpheus GLP-1 debate.
    "gerresheimer": ["Gerresheimer Bunde", "Gerresheimer Glas", "Gerresheimer Moulded Glass",
                     "Gerresheimer Peachtree City"],
    # SUPPLIER-SIDE INVERSION (resolve the hidden ASIAN VENDOR, not a customer): furniture importers that
    # disclose a dominant unnamed supplier % — query as the CONSIGNEE and reverse-resolve the top shipper.
    # This is a demand-nowcast / private-supplier-discovery edge, NOT a hidden-Fortune-500-customer re-rate.
    "restoration hardware": ["RH", "Restoration Hardware"],   # ~12% of purchase $ from one unnamed vendor; 72% Asia
    # Kokusai Co., Ltd. (7722.T): Japanese balancing machine & tire uniformity tester maker; ships via US subsidiary and Shanghai entity
    "kokusai": ["Kokusai Co", "Kokusai Incorporated", "Kokusai America", "Kokusai Europe", "高技国際計測器", "Kokusai Measurement"],
}

EVIDENCE_CHANNELS = ["customs_bol", "co_location", "disclosed_agreements",
                     "product_format", "revenue_geography", "demand_trend_correlation"]


def resolve_shipping_entities(company: str) -> list[str]:
    """Likely customs-BOL shipper names for a company (brand + known subsidiary aliases)."""
    key = (company or "").strip().lower()
    out = [company]
    for k, aliases in SHIPPING_ALIASES.items():
        if k in key or key in k:
            out.extend(aliases)
    return list(dict.fromkeys(out))


# ─────────────────────────────────────────────────────────────────────────────
# Census trade-flow — the AIR-FREIGHT-INCLUSIVE complement to ocean-only BOL.
# Closes the documented blind spot: ocean bills-of-lading miss air-shipped goods
# (high-value/low-mass pharma, semis). US Census int'l-trade data breaks imports
# down by HS code x country x MODE (air vs vessel), monthly (~5wk lag). Aggregate
# (not per-consignee) but mode-resolved — use it to measure an import-velocity
# surge a single company's ocean-BOL absence can't reveal. Free; needs a Census key
# in ~/.census_key or env CENSUS_KEY.
# ─────────────────────────────────────────────────────────────────────────────
from pathlib import Path as _Path

_CENSUS = "https://api.census.gov/data/timeseries/intltrade/imports/hs"
CTY_CODES = {"south korea": "5800", "korea": "5800", "china": "5700", "germany": "4280",
             "japan": "5880", "india": "5330", "switzerland": "4419", "italy": "4759",
             "france": "4279", "ireland": "4190", "mexico": "2010", "canada": "1220"}


def _census_key() -> Optional[str]:
    k = os.environ.get("CENSUS_KEY", "").strip()
    if k:
        return k
    f = _Path.home() / ".census_key"
    try:
        return f.read_text().strip() if f.exists() else None
    except OSError:
        return None


def census_trade_flow(hs_code: str, country: str, *, start: str = "2024-01",
                      end: str = "2026-12", mode: str = "air") -> dict:
    """Monthly US import value by HS x country x mode + velocity-surge detection.

    hs_code: 6-digit HS (e.g. '300249' botulinum toxin). country: name or Census CTY code.
    mode: 'air' | 'vessel' | 'total'. Returns {status, series:[{month,total_M,mode_M,mode_pct}],
    baseline_3mo_avg_M, recent_3mo_avg_M, velocity_vs_baseline, surge (bool), note}.
    """
    key = _census_key()
    if not key:
        return {"status": "NO_KEY", "note": "put a Census API key in ~/.census_key (free, instant)"}
    cty = CTY_CODES.get(country.strip().lower(), country)
    field = {"air": "AIR_VAL_MO", "vessel": "VES_VAL_MO", "total": "GEN_VAL_MO"}.get(mode, "AIR_VAL_MO")
    params = {"get": f"GEN_VAL_MO,{field}", "I_COMMODITY": hs_code, "CTY_CODE": cty,
              "COMM_LVL": "HS6", "time": f"from {start} to {end}", "key": key}
    try:
        r = requests.get(_CENSUS, params=params, timeout=40)
    except Exception as e:
        return {"status": "ERROR", "note": str(e)[:80]}
    if "Invalid Key" in r.text:
        return {"status": "INVALID_KEY", "note": "Census rejected the key (activate via the email link; "
                                                 "propagation can lag a few minutes)"}
    if r.status_code != 200 or not r.text.lstrip().startswith("["):
        return {"status": "BAD_RESPONSE", "note": r.text[:80]}
    rows = r.json(); h = rows[0]
    gi, mi, ti = h.index("GEN_VAL_MO"), h.index(field), h.index("time")
    ser = []
    for x in sorted((z for z in rows[1:] if z[gi]), key=lambda z: z[ti]):
        tot = int(x[gi] or 0); mv = int(x[mi] or 0)
        ser.append({"month": x[ti], "total_M": round(tot / 1e6, 2), "mode_M": round(mv / 1e6, 2),
                    "mode_pct": round(100 * mv / tot, 0) if tot else 0})
    if len(ser) < 6:
        return {"status": "THIN", "series": ser, "note": "too few months for a surge read"}
    vals = [s["mode_M"] for s in ser]
    baseline = sum(vals[:-3]) / max(len(vals) - 3, 1)
    recent = sum(vals[-3:]) / 3
    vel = round(recent / baseline, 2) if baseline else None
    return {"status": "OK", "hs": hs_code, "country": country, "mode": mode, "series": ser,
            "baseline_avg_M": round(baseline, 2), "recent_3mo_avg_M": round(recent, 2),
            "velocity_vs_baseline": vel,
            "surge": bool(vel and vel >= 1.25),
            "latest_month": ser[-1]["month"],
            "note": "aggregate (all importers of this HS from this country), mode-resolved, ~5wk lag"}


def customs_consignees(shipper: str, *, limit: int = 25) -> dict:
    """Best-effort free US bill-of-lading consignee lookup for a shipper entity. Returns
    {ok, consignees:[{name,count}], source, note}. Degrades gracefully (these aggregators rate-
    limit / Cloudflare-block datacenter IPs — when blocked, returns ok=False for agent/manual use)."""
    # importinfo + importgenius public tiers worked in the STVN run; both are scrape-fragile.
    # We attempt importyeti's search JSON first (often blocked), then signal degradation.
    try:
        r = requests.get("https://www.importyeti.com/api/search",
                         params={"q": shipper, "type": "supplier"},
                         headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        if r.status_code == 200 and "json" in r.headers.get("content-type", ""):
            data = r.json()
            cons = [{"name": c.get("name"), "count": c.get("count")}
                    for c in (data.get("consignees") or [])][:limit]
            if cons:
                return {"ok": True, "consignees": cons, "source": "importyeti"}
    except Exception:
        pass
    return {"ok": False, "consignees": [], "source": None,
            "note": "free BOL aggregators block this egress (Cloudflare/403). Run via an agent "
                    "(importinfo/importgenius public tiers) or a paid Panjiva drill. Resolve the "
                    "SHIPPER alias first: " + ", ".join(resolve_shipping_entities(shipper))}


def bayesian_customer_id(candidates: list[str], evidence: list[dict],
                         prior: Optional[dict] = None) -> dict:
    """Posterior over candidate customer identities + leave-one-out robustness.

    candidates: e.g. ["Lilly","Novo","Other"]. evidence: [{id, lr:{cand->likelihood ratio},
    lean, strength, why, source}, ...]. prior: optional dict (defaults to uniform).
    Returns {posterior, leave_one_out, prior, n_evidence}.
    """
    if not candidates:
        return {"error": "no candidates"}
    prior = prior or {c: 1.0 / len(candidates) for c in candidates}

    def _post(ev):
        logp = {c: math.log(max(prior.get(c, 1e-9), 1e-9)) for c in candidates}
        for e in ev:
            lr = e.get("lr", {})
            for c in candidates:
                logp[c] += math.log(max(lr.get(c, 1.0), 1e-9))
        mx = max(logp.values())
        un = {c: math.exp(logp[c] - mx) for c in candidates}
        z = sum(un.values())
        return {c: round(un[c] / z, 3) for c in candidates}

    post = _post(evidence)
    loo = {e.get("id", f"ev{i}"): _post([x for j, x in enumerate(evidence) if j != i])
           for i, e in enumerate(evidence)}
    top = max(post, key=post.get)
    # robustness: worst-case (max) probability of each candidate across leave-one-out
    worst = {c: max([post[c]] + [loo[k][c] for k in loo]) for c in candidates}
    return {"posterior": post, "top": top, "top_prob": post[top],
            "leave_one_out": loo, "robust_range": {c: [min([post[c]] + [loo[k][c] for k in loo]),
                                                        worst[c]] for c in candidates},
            "prior": prior, "n_evidence": len(evidence)}


class CustomerIdConnector(BaseConnector):
    source_id = "customer_id"

    def query(self, request: ConnectorRequest) -> ConnectorResult:
        company = request.entity_name or request.extra.get("company")
        if not company:
            return self._fail(request, ErrorKind.UNSUPPORTED, "customer_id needs entity_name (the company)")
        ex = request.extra or {}
        obs: list[ConnectorObservation] = []

        # 1) shipping-entity resolution (always available — the durable lesson)
        shippers = resolve_shipping_entities(company)
        obs.append(ConnectorObservation(attribute="shipping_entities", value=shippers,
                   extra={"note": "query customs BOLs under these, not the brand (Nuova Ompi lesson)"}))

        # 2) customs consignees (best-effort)
        cust = customs_consignees(shippers[-1] if len(shippers) > 1 else company)
        obs.append(ConnectorObservation(attribute="customs_consignees", value=cust.get("consignees"),
                   confidence=0.9 if cust["ok"] else 0.2,
                   extra={"ok": cust["ok"], "source": cust.get("source"), "note": cust.get("note")}))

        # 3) Bayesian identification if the caller supplied candidates + evidence
        cands, evidence = ex.get("candidates"), ex.get("evidence")
        if cands and evidence:
            res = bayesian_customer_id(cands, evidence, ex.get("prior"))
            obs.append(ConnectorObservation(attribute="customer_identity_posterior",
                       value=res["posterior"], confidence=0.7,
                       extra={"top": res["top"], "top_prob": res["top_prob"],
                              "robust_range": res["robust_range"], "leave_one_out": res["leave_one_out"],
                              "n_evidence": res["n_evidence"]}))
        else:
            obs.append(ConnectorObservation(attribute="customer_identity_posterior", value=None,
                       extra={"status": "needs candidates + evidence channels",
                              "channels": EVIDENCE_CHANNELS,
                              "how": "gather the 6 channels (customs/co-location/agreements/format/"
                                     "geography/demand-trend), assign per-candidate likelihood ratios, "
                                     "then call bayesian_customer_id()"}))
        return self._ok(request, obs)


if __name__ == "__main__":
    # Reproduce the STVN whale-ID through the generic API (validation).
    EV = [
        {"id": "customs_bol", "lr": {"Lilly": 5.0, "Novo": 0.6, "Other": 1.0}},
        {"id": "co_location", "lr": {"Lilly": 2.2, "Novo": 0.85, "Other": 0.9}},
        {"id": "disclosed_agreements", "lr": {"Lilly": 1.0, "Novo": 1.0, "Other": 1.0}},
        {"id": "product_format", "lr": {"Lilly": 2.0, "Novo": 0.9, "Other": 0.95}},
        {"id": "revenue_geography", "lr": {"Lilly": 1.35, "Novo": 0.9, "Other": 1.0}},
        {"id": "demand_trend_correlation", "lr": {"Lilly": 0.8, "Novo": 2.2, "Other": 1.0}},
    ]
    r = bayesian_customer_id(["Lilly", "Novo", "Other"], EV,
                             prior={"Lilly": 0.34, "Novo": 0.33, "Other": 0.33})
    print("STVN reproduce -> posterior:", r["posterior"], "| top:", r["top"])
    print("robust range Novo:", r["robust_range"]["Novo"])
    print("shipping entities for 'Stevanato Group':", resolve_shipping_entities("Stevanato Group"))
