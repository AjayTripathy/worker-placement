"""Build the maximum-equity-anti-correlation CA muni sleeve + long-Treasury benchmark.

HONEST FRAMING (post-hostile-review): a CA muni's equity anti-correlation is ~entirely
DURATION riding a flight-to-quality rally. "Most anti-correlated" = "most duration, top credit,
non-callable, liquid" = a regime-conditional bet on the Fed CUTTING. It INVERTS in rate-shock
(2022) / liquidity (2008, Mar-2020) crashes. The crash-rally numbers below are DURATION
ARITHMETIC (ΔP ≈ -dur×Δy) at an illustrative flight-to-quality Δy, NOT a backtest.

Levers: max duration (long, low-coupon, NON-called-away discounts/zeros) · max credit + strip
credit-beta (escrowed/AAA; but advance-refunded zeros are ~extinct post-2017 TCJA) · positive
convexity (non-callable) · liquidity (benchmark issues, not thin conduits).

Inputs: data/etf_v2_bond_analytics.json (real EMMA terms + validated durations) + FRED 30yr/10yr.
Output: data/anticorr_sleeve.json. Reproducible.
"""
import json, csv, urllib.request as u, statistics as st

ANALYTICS = "/Users/ajay/exalted/signalos/verticals/muni_credit/data/etf_v2_bond_analytics.json"
OUT = "/Users/ajay/exalted/signalos/verticals/muni_credit/data/anticorr_sleeve.json"
CA_TOP_FED = 0.408           # fed top 37% + 3.8% NIIT (Treasuries are CA-state-exempt)
STRESS_DY = -0.0250          # illustrative flight-to-quality long-end move (dot-com ~ -250bp)


def fred_last(series):
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}&cosd=2026-04-01&coed=2026-06-30"
    rows = [r for r in csv.reader(u.urlopen(url, timeout=30).read().decode().splitlines())
            if len(r) > 1 and r[1] not in (".", "")]
    for r in reversed(rows):
        try:
            return float(r[1])
        except ValueError:
            pass
    return None


def moddur_par(y, n_years, freq=2):
    c = y / freq; m = n_years * freq; yp = y / freq
    pv = sum(c / (1 + yp) ** t for t in range(1, m + 1)) + 1 / (1 + yp) ** m
    mac = (sum(t * c / (1 + yp) ** t for t in range(1, m + 1)) + m / (1 + yp) ** m) / pv / freq
    return mac / (1 + yp)


def main():
    rows = json.load(open(ANALYTICS))["rows"]
    # anti-correlation wants FULL duration: keep names NOT called away in a rally (worst==MATURITY)
    cands = [r for r in rows if r.get("dur_to_maturity") and (r.get("worst") or "").startswith("MATURITY")]
    cands.sort(key=lambda r: -r["dur_to_maturity"])
    sleeve = cands[:6]
    # AI-crash-optimal sub-sleeve: SCHOOL-DISTRICT GO only (property-tax = cap-gains-insulated;
    # drops State GO which carries the AI/cap-gains credit beta, and the CCRC wealth-sensitivity)
    school = [r for r in sleeve if "school" in (r.get("obligor") or "").lower()
              or "usd" in (r.get("obligor") or "").lower() or "unified" in (r.get("obligor") or "").lower()]

    y30, y10 = fred_last("DGS30"), fred_last("DGS10")
    t30 = moddur_par(y30 / 100, 30)
    strips30 = 30 / (1 + (y30 / 100) / 2)

    def summ(names):
        return {"n": len(names), "avg_dur": round(st.mean(r["dur_to_maturity"] for r in names), 1),
                "avg_coupon": round(st.mean(r["coupon"] for r in names), 2),
                "avg_ytm": round(st.mean(r["ytm"] for r in names) * 100, 2),
                "cusips": [r["cusip"] for r in names]}

    def line(name, dur, yld, tax_exempt):
        net = yld if tax_exempt else round(yld * (1 - CA_TOP_FED), 2)
        return {"name": name, "dur": round(dur, 1), "rally_pct": round(-dur * STRESS_DY * 100, 1),
                "gross_yield": round(yld, 2), "aftertax_carry_CAtop": round(net, 2)}

    sl = summ(sleeve); sc = summ(school)
    table = [
        line("Muni duration sleeve (high-grade, real)", sl["avg_dur"], sl["avg_ytm"], True),
        line("  └ AI-crash-optimal (school-GO only)", sc["avg_dur"], sc["avg_ytm"], True),
        line("CA-muni zero/CAB (illustrative, low-grade/illiquid)", 26.0, 4.60, True),
        line("30yr Treasury (coupon)", t30, y30, False),
        line("30yr Treasury STRIPS", strips30, y30, False),
    ]
    out = {"as_of": "2026-06-06", "fred_30yr": y30, "fred_10yr": y10, "stress_dy_bp": STRESS_DY * 1e4,
           "muni_sleeve": sl, "ai_crash_optimal_school_go": sc, "comparison": table,
           "caveats": ["rally = duration arithmetic, NOT a backtest; regime-conditional (inverts in "
                       "rate-shock/liquidity crashes)", "escrowed/AAA-zero ideal ~extinct post-2017 TCJA",
                       "muni sleeve anchor State GO carries the cap-gains/AI credit beta — the school-GO "
                       "sub-sleeve strips it", "Treasury coupons are CA-state-exempt but fed+NIIT taxable"]}
    json.dump(out, open(OUT, "w"), indent=1)
    print(f"FRED 30yr={y30}% 10yr={y10}% | sleeve dur={sl['avg_dur']} ytm={sl['avg_ytm']}% "
          f"| school-GO dur={sc['avg_dur']} ytm={sc['avg_ytm']}%")
    print(f"{'portfolio':<48}{'dur':>6}{'rally':>8}{'net carry':>11}")
    for t in table:
        print(f"  {t['name']:<46}{t['dur']:>6}{'+'+str(t['rally_pct'])+'%':>8}{t['aftertax_carry_CAtop']:>10}%")
    print("saved ->", OUT)


if __name__ == "__main__":
    main()
