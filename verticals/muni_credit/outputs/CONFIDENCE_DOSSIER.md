# Portfolio Confidence Dossier — CA Muni HTM Book (24 names)

As of 2026-06-20. Book: 24 DD-confirmed BUY names, 8.25% after-tax TEY, ~11.8y duration, fully
diversified (worst single fault-zone 17%, 0 high-fire, 0 Ss≥2.0). This dossier covers the three
portfolio-level confidence checks beyond the per-bond DD: stress, base rate, and execution.

---
## 1. Stress test — the tail is DOWNGRADE + mark-to-market, NOT default

| Scenario | Book exposure | Mechanism | Impact |
|---|---|---|---|
| **Major earthquake** (Bay/LA M7) | Worst single zone = 17% (LA 4 / Bay 3 / SD 2 / IE 2 names) | Unlimited ad-valorem levy RISES to offset a damaged AV base; SB-222 lien + Teeter | Downgrade (cf. Paradise post–Camp Fire), **not default** |
| **Rate shock +100/200/300 bps** | Duration ~11.8y | Price falls, but each rung matures at par | **MTM ~−12% / −24% / −35%** if you SELL; **0 realized** held to maturity |
| **AI / tech crash** (the thesis) | **0 / 24** names exposed to the State-GF cap-gains channel (AI insulation 99) | School GO = local property tax, insulated from state revenue | Dot-com precedent: State GO −4–5 notches; **this book untouched** |
| **Recession / AV decline −20%** | Prop 13 (AV resets only on sale; 2008-09 CA AV fell low-single-digits) | Unlimited levy rate rises ~25% to hold debt service constant | Coverage maintained; **no default channel** |
| **Single-taxpayer (idiosyncratic AV)** | 2 names >10% of AV: **Anaheim/Disney 19.6%**, Palo Verde/Blythe 13.5% | If the big taxpayer's AV falls, levy rate rises on the rest | Mitigated (un-relocatable Disneyland / power plant); the book's main idiosyncratic watch-items |

**Read:** every modeled scenario produces a *downgrade* or a *paper* (mark-to-market) drawdown, not an
impairment of the cash flows to maturity. The unlimited-tax pledge + statutory lien + Teeter convert
base/hazard risk into a *rate* the bondholder is senior to. The only scenario that hurts a true
hold-to-maturity investor is an actual default — addressed next.

## 2. Base rate — how safe is this class, historically?

(Moody's "US Municipal Bond Defaults and Recoveries, 1970–2022")
- **Investment-grade muni 10-yr cumulative default rate: 0.042%** (vs all-rated corporate ~10%).
- **GO is the safest muni sector**: of ~71 muni defaults over 41 years, **only 5 were GO**, and rated-GO
  **recovery is ~100%**. Our book is ~Aa2/Aa3 (above the all-IG average, so default odds are lower still).
- **CA unlimited ad-valorem school GO**: no modern default on record. Stress episodes resolved as
  downgrades, not defaults — Paradise USD kept paying through the 2018 Camp Fire; the City of Stockton's
  2012 Chapter 9 never touched the separate school-district GOs.

**Read:** the one tail the stress test can't fully rule out — an outright default — has a historical base
rate of effectively **zero** for this exact security class. Confidence on *credit* is high.

## 3. Execution — the real remaining gap (paper price ≠ fillable price)

We've priced off the EMMA trade tape; IBKR's muni feed is close-only (no live bid/ask). **13 of the 24
names trade <60×/yr** — modeled ≠ executable for those. This is the one leg NOT yet validated.

→ **`outputs/RFQ_BOOK_24.md`** stages the bid-wanted sheet for the desk: per-name two-sided market,
can-you-source-the-offer, all-in cost vs our target, and a buy-one-test-fill-then-rest-limits plan.
Running it converts the book from a paper portfolio to a deployable one.

---
## Bottom line for building this
- **Credit / tail: HIGH confidence.** Per-bond DD + a ~0 historical default base rate + a stress profile
  that is downgrade/MTM, not default. The thesis exposure (AI/state-GF) is screened to 0.
- **Genuine open risks (not credit):** (1) **execution** of the 13 thin names — pending the desk RFQ;
  (2) **rate MTM** if you might sell before maturity (−24% at +200 bps; immaterial if truly HTM);
  (3) the **2 single-taxpayer concentrations** (Disney, Blythe) — monitor; (4) the **legislative
  assumption** — the after-tax math assumes the muni exemption + CA top bracket persist.
- **Next step:** run the RFQ with the desk and score the answers; that closes the last leg.
