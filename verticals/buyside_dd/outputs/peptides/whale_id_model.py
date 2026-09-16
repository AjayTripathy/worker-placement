"""whale_id_model — Bayesian identification of Stevanato's undisclosed GLP-1 "whale" customer.

Question: is the CONSTRAINED GLP-1 capacity book (the "sold-out 2027" bull thesis) anchored by
GROWING Eli Lilly or DECELERATING Novo Nordisk? Stevanato discloses two customers at 14.0% + 11.3%
of revenue but never names them. We infer from 6 physical/structural evidence channels (gathered
2026-06-25, whale_evidence.json). Each channel is a likelihood ratio over {Lilly, Novo, Other}.

Posterior = prior x product(LRs), normalized. We also run robustness: leave-one-out, and a
"Denmark-discounted" scenario that weakens the customs channel (US bills-of-lading cannot see Novo's
Denmark fill-finish, so absence-of-Novo is only weakly informative — we must not over-rely on it).
"""
from __future__ import annotations
import math

H = ["Lilly", "Novo", "Other"]
PRIOR = {"Lilly": 0.34, "Novo": 0.33, "Other": 0.33}   # ~agnostic between the two GLP-1 giants + a real "Other" (Amgen/Sanofi/Regeneron also ship via Ompi)

# Each evidence item: per-hypothesis likelihood ratio (relative; posterior normalizes).
# Strength encoded in magnitude: HIGH ~3-5x, MED ~1.8-2.3x, LOW ~1.3-1.4x, none = 1.0.
EVIDENCE = [
    {"id": "customs_bol", "lean": "Lilly", "strength": "HIGH",
     "lr": {"Lilly": 5.0, "Novo": 0.6, "Other": 1.0},
     "why": "Nuova Ompi SRL (Stevanato's US shipper) BOLs: Eli Lilly dominant consignee of "
            "'EZ-FILL NEXA 1ML' (the NAMED GLP-1 surge SKU); Novo absent. Novo penalty only 0.6 "
            "(not lower) because Novo fills US pens in Denmark -> invisible to US customs.",
     "source": "importinfo / importgenius (Ompi shipper + Lilly importer, bidirectional)"},
    {"id": "co_location", "lean": "Lilly", "strength": "MED",
     "lr": {"Lilly": 2.2, "Novo": 0.85, "Other": 0.9},
     "why": "Stevanato's only US glass plant (Fishers IN) ~20mi from Lilly HQ / ~30mi from Lilly's "
            "$9B Lebanon LEAP tirzepatide campus.", "source": "company + Lilly facility maps"},
    {"id": "disclosed_agreements", "lean": "Ambiguous", "strength": "LOW",
     "lr": {"Lilly": 1.0, "Novo": 1.0, "Other": 1.0},
     "why": "No named GLP-1 supply deal with either; named deals are BARDA/CEPI (vaccine vials). "
            "Non-discriminating.", "source": "STVN PRs / 20-F"},
    {"id": "container_format", "lean": "Lilly", "strength": "MED",
     "lr": {"Lilly": 2.0, "Novo": 0.9, "Other": 0.95},
     "why": "Named surge driver = Nexa 1mL PREFILLED SYRINGE = Lilly single-dose Zepbound/Mounjaro. "
            "Novo uses 3mL multi-dose CARTRIDGES (a separate, secondary book).",
     "source": "STVN transcript + product presentations"},
    {"id": "revenue_geography", "lean": "Lilly", "strength": "LOW",
     "lr": {"Lilly": 1.35, "Novo": 0.9, "Other": 1.0},
     "why": "FY25 NA 30.5% (+17.2% YoY, fastest region) fits a US (Lilly) ramp; EMEA majority is "
            "structural (Italian co.), not a Novo tell.", "source": "STVN FY25 20-F"},
    {"id": "destock_correlation", "lean": "Novo", "strength": "MED",   # the dissent
     "lr": {"Lilly": 0.8, "Novo": 2.2, "Other": 1.0},
     "why": "Mgmt: a whale is 'managing inventories' (destock), GLP-1 guide halved. A destocking "
            "customer maps to DECELERATING Novo, not Lilly's +28% growth. The load-bearing dissent.",
     "source": "STVN Q1'26 transcript + our NVO diligence"},
]


def posterior(prior, evidence):
    logp = {h: math.log(prior[h]) for h in prior}
    for e in evidence:
        for h in logp:
            logp[h] += math.log(max(e["lr"][h], 1e-9))
    mx = max(logp.values())
    un = {h: math.exp(logp[h] - mx) for h in logp}
    z = sum(un.values())
    return {h: round(un[h] / z, 3) for h in logp}


def fmt(p):
    return " | ".join(f"{h} {p[h]:.0%}" for h in H)


if __name__ == "__main__":
    base = posterior(PRIOR, EVIDENCE)
    print("=== WHALE IDENTITY — posterior for the CONSTRAINED GLP-1 book ===")
    print("Prior:    ", fmt(PRIOR))
    print("Base:     ", fmt(base))

    print("\n-- Leave-one-out robustness (drop each channel) --")
    for e in EVIDENCE:
        loo = posterior(PRIOR, [x for x in EVIDENCE if x is not e])
        print(f"  drop {e['id']:22} -> {fmt(loo)}")

    # Denmark-discounted: soften the customs channel (BOL can't see Novo's Denmark fill)
    disc = [dict(x) for x in EVIDENCE]
    for x in disc:
        if x["id"] == "customs_bol":
            x["lr"] = {"Lilly": 3.0, "Novo": 0.9, "Other": 1.0}
    print("\n-- Denmark-discounted (customs softened to Lilly3.0/Novo0.9) --")
    print("  ", fmt(posterior(PRIOR, disc)))

    # decision read
    print("\n=== READ ===")
    lo = min(posterior(PRIOR, [x for x in EVIDENCE if x["id"] != "customs_bol"])["Novo"],
             posterior(PRIOR, disc)["Novo"])
    hi = max(base["Novo"],
             posterior(PRIOR, [x for x in EVIDENCE if x["id"] != "customs_bol"])["Novo"])
    print(f"Constrained GLP-1 book is LILLY-anchored across all scenarios (Lilly {base['Lilly']:.0%} "
          f"base; >=67% even dropping customs).")
    print(f"Residual NOVO probability on that book: {base['Novo']:.0%} base, up to "
          f"~{hi:.0%} in the customs-discounted case = the bear tail.")
