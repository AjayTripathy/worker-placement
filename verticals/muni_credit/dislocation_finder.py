"""dislocation_finder — INVERT the screen: buy the unlimited-GO bonds the market marked DOWN on a rating/
headline that does NOT reach the cash flows.

The standard underwrite EXCLUDES a NEGATIVE/QUALIFIED-cert or hazard-headline name. But for a HOLD-TO-
MATURITY holder of a CALIFORNIA UNLIMITED AD-VALOREM GO, those bonds are money-good to maturity (Moody's:
GO defaults 5 of ~71 historical muni defaults, ~100% recovery; zero modern CA school-GO defaults) because
the debt service is paid from a SEGREGATED county levy under the SB-222/§53515 statutory lien + Teeter,
ring-fenced from the operating fund. So a rating/headline-driven DISCOUNT is a BUY — the carry plus
price-recovery optionality if the cert/rating normalizes — not an exclusion. The gap between the market's
rating-driven price and the structural cash-flow safety IS the alpha.

BOUNDARY CONDITIONS (hard gates — buy-the-dip kills people without these):
  1. UNLIMITED ad-valorem GO ONLY (pledge=school). NOT revenue/COP/lease/limited-tax — those can impair.
  2. The distress must be RING-FENCED from the segregated debt-service levy. Operating-fund cert downgrade,
     enrollment/pension stress, fire/quake/flood/SGMA headline = INSULATED (the dislocation signal).
     Anything that reaches the SECURITY — SEC/disclosure fraud, bond-proceeds misuse, taxpayer/debt
     concentration that erodes the AV base, structural call traps, sub-90 AI insulation — is a REAL risk,
     NOT a dislocation buy.
  3. Output is BUY-PENDING-DD: every candidate needs a per-name DD confirming the levy/lien/Teeter
     insulation (is it truly unlimited? any lien gap or Teeter exclusion?). The finder QUEUES; the DD rules.

Output: outputs/DISLOCATION_CANDIDATES.{json,md}
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "outputs")

# Flags that signal a rating/headline dislocation but DON'T reach the segregated GO levy (the BUY signal):
INSULATED = ("fiscal:NEGATIVE", "fiscal:QUALIFIED", "enroll", "pension", "fire-review", "flood",
             "sgma", "subsidence", "EQ-elev", "EQ-veryhigh", "issuer-litig-review", "call-soon")
# Flags that reach the SECURITY / break the unlimited-GO thesis -> NOT a dislocation buy (a real risk):
SECURITY = ("issuer-litigation", "AV-conc", "debt/AV", "FIRE-high", "CC-uncovered", "CC-sanction",
            "unresolved", "near-par-call", "CAB", "AI<", "DSCR", "water-supply", "premium-call", "fire-unmatched")


def classify(flags):
    ins = [f for f in flags if f.split(":")[0].startswith(INSULATED) or any(f.startswith(p) for p in INSULATED)]
    sec = [f for f in flags if any(f.startswith(p) for p in SECURITY)]
    return ins, sec


def find(univ, px_max=99.0):
    """Dislocation candidates: unlimited-GO with a RATING/CERT DOWNGRADE (the primary signal — these are the
    names the standard screen HARD-FLAGS and excludes), NO other security-reaching flag, trading at a
    discount. A pure low-coupon discount on a POSITIVE-cert name is NOT a dislocation (just coupon math,
    already in the clean book) — the price has to be depressed by the RATING."""
    out = []
    for r in univ:
        if r.get("pledge") == "water": continue                      # gate 1: unlimited GO only
        px = r.get("px")
        if not px or not r.get("tey_aftertax") or not r.get("maturity"): continue
        cert = r.get("cert_status") or ""
        # PRIMARY SIGNAL: an operating fiscal-cert downgrade (NEGATIVE/QUALIFIED) — the rating dislocation.
        # (The cert is OPERATING stress; the GO levy is segregated, so it doesn't reach the cash flows.)
        if cert not in ("NEGATIVE", "QUALIFIED"): continue
        _, sec = classify(r.get("uw_flags") or [])
        if sec: continue                                             # any OTHER security-reaching flag = real risk, skip
        if px > px_max: continue                                     # the dislocation: trading at a discount
        ins = [f for f in (r.get("uw_flags") or []) if f.startswith("fiscal:")] + \
              [f for f in (r.get("uw_flags") or []) if "litig-review" in f or f.startswith(("enroll", "pension"))]
        score = (100 - px) + (r["tey_aftertax"] * 100 - 8) * 3 + 4   # deeper discount + higher carry = bigger dislocation
        out.append({**{k: r.get(k) for k in ("cusip", "issuer", "county", "coupon", "maturity", "px",
                                             "ytw", "tey_aftertax", "cert_status", "seismic_ss", "n365")},
                    "insulated_flags": ins, "discount_to_par": round(100 - px, 1),
                    "recovery_optionality_pts": round(100 - px, 1), "dislocation_score": round(score, 1),
                    "status": "BUY-PENDING-DD (confirm levy/lien/Teeter insulation per name)"})
    out.sort(key=lambda x: -x["dislocation_score"])
    return out


def main():
    m = json.load(open(os.path.join(OUT, "DILIGENCE_MASTER.json")))
    cand = find(m)
    json.dump(cand, open(os.path.join(OUT, "DISLOCATION_CANDIDATES.json"), "w"), indent=1, default=str)
    L = ["# Dislocation-Buy Candidates — marked down on rating/headline, structurally money-good", "",
         "_Unlimited ad-valorem CA school GO, flagged ONLY for cash-flow-insulated reasons (operating cert "
         "downgrade / enrollment / pension / hazard headline), trading at a discount = the market pricing the "
         "RATING, not the security. HTM money-good (GO default base rate ~0); discount = carry + recovery "
         "optionality. Each is BUY-PENDING-DD: the DD must confirm the levy/lien/Teeter insulation._", "",
         "| # | CUSIP | Issuer | County | Cpn | Mat | Px | TEY% | Cert | EQ | n/yr | Discount(pts) | Insulated flags |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for i, c in enumerate(cand, 1):
        L.append(f"| {i} | {c['cusip']} | {str(c.get('issuer'))[:22]} | {c.get('county')} | {c['coupon']} | "
                 f"{c['maturity'][:7]} | {c['px']} | {c['tey_aftertax']*100:.1f} | {c.get('cert_status')} | "
                 f"{c.get('seismic_ss')} | {c.get('n365')} | {c['discount_to_par']} | {';'.join(c['insulated_flags'])[:40]} |")
    open(os.path.join(OUT, "DISLOCATION_CANDIDATES.md"), "w").write("\n".join(L))
    print(f"DISLOCATION candidates: {len(cand)} (unlimited-GO, insulated-flag-only, at a discount)")
    for c in cand[:10]:
        print(f"  {c['cusip']} {str(c.get('issuer'))[:24]:24} px{c['px']} TEY{c['tey_aftertax']*100:.1f}% "
              f"{c.get('cert_status'):10} disc {c['discount_to_par']}pt | {';'.join(c['insulated_flags'])[:34]}")
    return cand


if __name__ == "__main__":
    main()
