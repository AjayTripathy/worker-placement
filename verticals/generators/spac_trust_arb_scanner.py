"""spac_trust_arb_scanner — Stage 0b CARRY generator: SPACs trading BELOW trust value.

THE FLOOR IS THE EDGE. A pre-deal SPAC (blank-check "Acquisition Corp") holds shareholder cash
in a segregated trust — invested in T-bills/money-market — and every PUBLIC shareholder has a
statutory right to REDEEM their shares for the pro-rata trust value (cash + accrued interest) at
the merger vote, at any extension amendment, or if the SPAC liquidates. So the trust-per-share is
a near-guaranteed CASH FLOOR: buy below it and you capture (trust_ps − price) by tendering at the
deadline, PLUS free optionality on any deal / bump / warrant that closes above trust.

Institutions ignore these because the tickets are odd-lot / sub-threshold and the absolute $-edge
per name is tiny — exactly the office-thesis capacity edge (fee-replication CARRY, capacity-ceilinged).

v1 screens a SEED universe of active pre-deal SPAC tickers on the two things computable from PRIMARY
data — nothing fabricated:
  1. TRUST-PER-SHARE  = AssetsHeldInTrust (SEC XBRL companyconcept) / public redeemable shares
  2. PRICE            = live last close (yfinance)
  → discount_to_trust_pct = (trust_ps − price) / trust_ps ; annualized to the deadline if known.
The universe is a SEED to EXPAND + VERIFY; unresolvable tickers self-drop (reported, never silent).
Trust values are REAL XBRL only — any share-count approximation is FLAGGED in the row note.

    python3 verticals/generators/spac_trust_arb_scanner.py
Writes data/SPAC_TRUST_ARB.json. READ-ONLY. (A CARRY generator — never an order.)
"""
from __future__ import annotations

import datetime
import json
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "data" / "SPAC_TRUST_ARB.json"
HDRS = {"User-Agent": "signalos-research 4tripathy@gmail.com"}

TICKERS_MAP = "https://www.sec.gov/files/company_tickers.json"
CONCEPT = "https://data.sec.gov/api/xbrl/companyconcept/CIK{cik10}/us-gaap/{tag}.json"

# XBRL tags for the trust balance, most-common first. SPACs classify the trust as noncurrent early
# (>12mo to deadline) then reclassify to current as the deadline nears — try both + the base tag.
TRUST_TAGS = ["AssetsHeldInTrustNoncurrent", "AssetsHeldInTrustCurrent", "AssetsHeldInTrust"]
# public redeemable-share concepts (temporary/mezzanine equity — the shares that carry the redemption right).
# NOTE: SharesSubjectToMandatoryRedemptionSettlementTermsNumberOfShares is deliberately EXCLUDED — it is an
# IPO-terms disclosure (frozen at the offering count) that does NOT track redemptions, so dividing a
# post-redemption trust by it fabricates a garbage per-share (SPKL: stale 10M sh vs a 75%-redeemed trust).
SHARE_TAGS = [
    "TemporaryEquitySharesOutstanding",
    "TemporaryEquitySharesSubjectToPossibleRedemption",
]
# plausibility band for a computed trust-per-share ($); outside this = a stale/mismatched share count -> treat
# per-share as UNKNOWN rather than emit a fabricated discount. SPACs redeem at ~$10.00-$11.50 (par + accrued).
TRUST_PS_LO, TRUST_PS_HI = 9.0, 13.0

# SEED universe of ACTIVE pre-deal SPACs (blank-check "Acquisition Corp" not yet merged). ticker | name.
# A SEED to EXPAND — v2 auto-discovers via SIC 6770. Merged/liquidated/renamed tickers self-drop on
# resolve (reported in `dropped`, never silently omitted). NO financials hardcoded — all pulled live.
UNIVERSE = [
    ("AAC",   "Ares Acquisition Corp III"),
    ("CCIX",  "Churchill Capital Corp IX"),
    ("CEPF",  "Cantor Equity Partners IV"),
    ("CEPV",  "Cantor Equity Partners V"),
    ("CLBR",  "Colombier Acquisition Corp II"),
    ("DTSQ",  "DT Cloud Star Acquisition"),
    ("FGII",  "FG Imperii Acquisition Corp"),
    ("GSRF",  "GSR IV Acquisition Corp"),
    ("GSRV",  "GSR V Acquisition Corp"),
    ("HCIC",  "Hennessy Capital Investment Corp VIII"),
    ("HVII",  "Hennessy Capital Investment Corp VII"),
    ("IRHO",  "Iron Horse Acquisition II Corp"),
    ("LEGO",  "Legato Merger Corp IV"),
    ("MACI",  "Melar Acquisition Corp I"),
    ("MBAV",  "M3-Brigade Acquisition V"),
    ("MBVI",  "M3-Brigade Acquisition VI"),
    ("NPAC",  "New Providence Acquisition Corp III"),
    ("OACC",  "Oak Woods Acquisition"),
    ("PMTR",  "Perimeter Acquisition Corp I"),
    ("SPKL",  "Spark I Acquisition"),
    ("SVAC",  "Spring Valley Acquisition Corp III"),
    ("SVIV",  "Spring Valley Acquisition Corp IV"),
    ("VHCP",  "Vine Hill Capital Investment Corp II"),
]

DISCOUNT_FLOOR = 0.0        # any positive discount (price < trust) is a candidate — the floor is the edge


def _get_json(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=HDRS), timeout=25) as r:
            return json.load(r)
    except Exception:
        return None


def _ticker_cik_map():
    """{TICKER: cik10} from the SEC master file."""
    d = _get_json(TICKERS_MAP)
    out = {}
    if isinstance(d, dict):
        for row in d.values():
            try:
                out[str(row["ticker"]).upper()] = str(int(row["cik_str"])).zfill(10)
            except Exception:
                continue
    return out


def _latest_concept(cik10, tag):
    """Latest reported value of a us-gaap concept for a CIK. Returns (value, end_date) or (None, None)."""
    d = _get_json(CONCEPT.format(cik10=cik10, tag=tag))
    if not isinstance(d, dict):
        return None, None
    best_val, best_end = None, None
    for unit_rows in (d.get("units") or {}).values():
        for f in unit_rows:
            end = f.get("end")
            val = f.get("val")
            if val is None or end is None:
                continue
            if best_end is None or end > best_end:
                best_end, best_val = end, val
    return best_val, best_end


def _trust_and_shares(cik10):
    """(trust_usd, trust_end, shares, shares_end, shares_tag) — best available from XBRL. shares may be None."""
    trust, trust_end = None, None
    for tag in TRUST_TAGS:
        trust, trust_end = _latest_concept(cik10, tag)
        if trust:
            break
    shares, shares_end, shares_tag = None, None, None
    for tag in SHARE_TAGS:
        shares, shares_end = _latest_concept(cik10, tag)
        if shares:
            shares_tag = tag
            break
    return trust, trust_end, shares, shares_end, shares_tag


def _price(ticker):
    """Live last close via yfinance. Returns float or None (self-prune on failure)."""
    import yfinance as yf
    try:
        tk = yf.Ticker(ticker)
        fi = getattr(tk, "fast_info", {}) or {}
        px = fi.get("last_price") or fi.get("lastPrice")
        if px:
            return float(px)
        hist = tk.history(period="5d")
        if len(hist):
            return float(hist["Close"].dropna().iloc[-1])
    except Exception:
        return None
    return None


def scan() -> dict:
    today = datetime.date.today()
    cikmap = _ticker_cik_map()
    resolved, dropped, rows = 0, [], []

    for ticker, name in UNIVERSE:
        t = ticker.upper()
        cik10 = cikmap.get(t)
        if not cik10:
            dropped.append({"ticker": ticker, "why": "no SEC CIK (bad/merged/renamed ticker)"})
            continue

        trust, trust_end, shares, shares_end, shares_tag = _trust_and_shares(cik10)
        if not trust:
            dropped.append({"ticker": ticker, "why": "no AssetsHeldInTrust in XBRL (not a live SPAC trust?)"})
            continue

        price = _price(ticker)
        if not price:
            dropped.append({"ticker": ticker, "why": "no live price (yfinance unresolved)"})
            continue

        resolved += 1
        note_bits = []
        trust_ps = None
        # trust-per-share from REAL XBRL share count where available; else FLAG per-share UNKNOWN.
        if shares and shares > 0:
            cand = trust / shares
            if TRUST_PS_LO <= cand <= TRUST_PS_HI:
                trust_ps = cand
                stale = "" if (shares_end and trust_end and abs((datetime.date.fromisoformat(shares_end)
                          - datetime.date.fromisoformat(trust_end)).days) <= 100) else " [share/trust periods differ >100d — verify]"
                note_bits.append(f"trust {trust_end} / {shares:,.0f} redeemable sh ({shares_tag} {shares_end}){stale}")
            else:
                # implausible per-share => the share count is stale or mismatched (e.g. pre-redemption).
                # Do NOT emit a fabricated discount; leave per-share NULL and flag it.
                note_bits.append(f"trust ${trust/1e6:,.1f}M {trust_end}; share count {shares:,.0f} ({shares_tag} "
                                 f"{shares_end}) implies ${cand:,.2f}/sh — OUTSIDE ${TRUST_PS_LO:.0f}-${TRUST_PS_HI:.0f} "
                                 f"band (stale/pre-redemption) -> per-share UNKNOWN (FLAG)")
        else:
            note_bits.append(f"trust ${trust/1e6:,.1f}M {trust_end} but NO redeemable-share XBRL concept — "
                             f"per-share UNKNOWN, approximate at the ~$10.00-$11.50 SPAC redemption par (FLAG)")

        row = {
            "ticker": ticker, "name": name, "cik": cik10,
            "trust_usd": round(trust),
            "trust_per_share": round(trust_ps, 4) if trust_ps else None,
            "price": round(price, 2),
            "discount_pct": None,
            "deadline": None,          # best-effort deadline not parsed in v1 (see caveats)
            "days_to_deadline": None,
            "annualized_yield": None,
            "note": "; ".join(note_bits),
        }
        if trust_ps:
            disc = (trust_ps - price) / trust_ps
            row["discount_pct"] = round(disc * 100, 2)
        rows.append(row)

    # candidates = price strictly below a KNOWN trust-per-share (the floor). Sort by discount desc.
    cands = [r for r in rows if r["discount_pct"] is not None and r["discount_pct"] > DISCOUNT_FLOOR * 100]
    cands.sort(key=lambda r: -r["discount_pct"])

    priced = [r for r in rows if r["discount_pct"] is not None]
    above = [r for r in priced if r["discount_pct"] <= 0]
    approx = [r for r in rows if r["trust_per_share"] is None]

    return {
        "asof": today.isoformat(),
        "n_universe": len(UNIVERSE),
        "n_resolved": resolved,
        "candidates": cands,
        "all_priced": sorted(priced, key=lambda r: -(r["discount_pct"] or -99)),
        "approx_no_pershare": [r["ticker"] for r in approx],
        "dropped": dropped,
        "distribution": {
            "n_priced": len(priced),
            "n_below_trust": len(cands),
            "n_at_or_above_trust": len(above),
            "median_discount_pct": round(sorted(r["discount_pct"] for r in priced)[len(priced)//2], 2) if priced else None,
        },
        "caveats": [
            "REDEMPTION IS A TENDER: you only capture the trust floor by tendering shares by the "
            "redemption deadline (at the merger vote, an extension amendment, or liquidation) — you do "
            "NOT auto-receive it by holding. Miss the window and you own the post-deal equity at market.",
            "You receive TRUST + ACCRUED INTEREST pro-rata; the per-share value grows as T-bill interest "
            "accrues, so trust_ps rises over time (a small positive carry even absent a discount).",
            "EXTENSION AMENDMENTS can erode the floor: sponsors sometimes fund extensions FROM the trust, "
            "or holders who don't redeem get diluted — read the latest 8-K/proxy for the current per-share.",
            "WARRANTS are SEPARATE optionality (usually a different ticker, e.g. .WS) and are NOT redeemable "
            "for trust — do not conflate the common's floor with warrant value.",
            "A DEAL CLOSING ABOVE TRUST also realizes the discount (the common re-rates), so the edge is "
            "(floor from redemption) OR (upside from a deal) — a heads-you-win structure, capacity-limited.",
            "Trust values are the LATEST XBRL filing (may be a quarter stale); the live per-share can differ "
            "after redemptions/extensions. Share counts use temporary-equity XBRL where present; names with "
            "no clean redeemable-share concept are listed in approx_no_pershare with per-share left NULL (never fabricated).",
        ],
        "note": "CARRY class — SPACs BELOW trust offer a near-guaranteed cash floor (redeem for pro-rata "
                "trust+interest) plus free deal/extension optionality. Institutions skip them (odd-lot / "
                "sub-threshold) = the office capacity edge. Trust-per-share from PRIMARY SEC XBRL "
                "(AssetsHeldInTrust / redeemable shares); price live from yfinance. Seed universe of ~23 "
                "active pre-deal SPACs — EXPAND (v2: auto-discover via SIC 6770). Deadlines not yet parsed "
                "from 8-Ks (annualized_yield null until then). Below-trust ≠ free money: verify the current "
                "per-share and deadline in the latest proxy before sizing.",
    }


def main():
    res = scan()
    OUT.write_text(json.dumps(res, indent=1))
    d = res["distribution"]
    print(f"=== SPAC TRUST-ARB SCANNER  {res['asof']}  "
          f"({res['n_resolved']}/{res['n_universe']} resolved, {d['n_below_trust']} below trust) ===")
    print(f"  distribution: {d['n_priced']} priced | {d['n_below_trust']} BELOW trust | "
          f"{d['n_at_or_above_trust']} at/above | median disc {d['median_discount_pct']}%")
    if res["candidates"]:
        print("  BELOW-TRUST CANDIDATES (buy the floor; verify current per-share + deadline in the proxy):")
        for r in res["candidates"][:15]:
            print(f"    {r['ticker']:6} {r['name'][:30]:30} px ${r['price']:6.2f}  trust ${r['trust_per_share']:7.4f}  "
                  f"{r['discount_pct']:+5.2f}% disc")
    else:
        print("  no below-trust names this run (SPACs commonly trade a hair ABOVE trust — normal).")
        print("  tightest to trust (top of all_priced):")
        for r in res["all_priced"][:8]:
            ps = f"${r['trust_per_share']:.4f}" if r["trust_per_share"] else "n/a"
            print(f"    {r['ticker']:6} {r['name'][:30]:30} px ${r['price']:6.2f}  trust {ps:9}  {r['discount_pct']:+5.2f}% disc")
    if res["approx_no_pershare"]:
        print(f"  no redeemable-share XBRL (per-share NULL, FLAGGED): {res['approx_no_pershare']}")
    if res["dropped"]:
        print(f"  dropped (unresolved, {len(res['dropped'])}): {[x['ticker'] for x in res['dropped']]}")
    print(f"[-> {OUT.name}]")


if __name__ == "__main__":
    main()
