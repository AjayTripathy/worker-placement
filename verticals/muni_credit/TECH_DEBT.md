# muni_credit — Tech Debt

## TD-1 — Proprietary rating-action data (Moody's / S&P / Fitch) [BLOCKING for middle-tier validation]

**Gap.** The β-CapGains AI-crash rating's **cross-sectional validation (Test C)** can only be
hardened to bucket/extremes level, not to per-sector 8-way precision, because the underlying
*per-issuer rating-action counts* (downgrades, notch magnitudes, upgrades, by CA muni sector by
crisis) are **not in any free/public source**.

**What we proved (don't re-investigate — it's settled):**
- The commonly-cited CDIAC `…/cdiac/default-draw/issuename.asp` URL is a **404**.
- The real CDIAC data (DebtWatch API, `cdiac_draws.py`) **exists and is scriptable, 1991–2026**,
  but is **~89% Mello-Roos/CFD land-secured draws** — it tracks *defaults & reserve draws*, NOT
  *rating actions*. The GO / school-GO / hospital / CCRC / water / county sectors appear 0–3×
  each, because their credit stress manifests as **downgrades**, which CDIAC does not record.
- Rating-action histories therefore live **only** in the agencies' proprietary databases.

**What a license would unlock:**
- Replace the *structural* channel-elasticities in `capgains_beta.py` with **empirical betas**
  (regress each sector's rating migrations on CA capital-gains receipts).
- Harden Test C's middle-tier Spearman ρ (currently 0.80 count-based / 0.90 judgment-based, with
  the middle sectors collapsing to ties on documented events).
- Confirm/refute the model-v2 refinement (TAB/hospital/CCRC are property/operational-channel, not
  income — `capgains_beta.py` likely over-rates them for the cap-gains channel).

**Options (in cost order):**
1. **Moody's CreditView / Data Reports** or **S&P Capital IQ Pro** muni rating-transition feeds —
   the authoritative source; ~$tens of k/yr seat/API. Decision needed: is the middle-tier
   precision worth it, given the rating is already validated at the extremes + bucket level and
   the AI-crash use case only needs the cap-gains-regime ordering (ρ=0.90)?
2. **MSRB EMMA** rating-change disclosures (free) — partial: only post-2009, only what issuers
   filed, no clean sector aggregation. A scraping project, not a clean feed. Possible half-measure.
3. **Municipal Market Analytics (MMA)** default/impairment data — better default coverage than
   CDIAC but still not full rating-transition; subscription.

**Current workaround (acceptable, documented):** blinded sector-level agent research for the
outcome rankings (Test C) + CDIAC for the land-secured sector. The limitation is disclosed in
`CA_MUNI_EQUITY_HEDGE_REPORT.md` §5.3.1 and the methodology tearsheet §7.4.

**Owner:** unassigned. **Priority:** LOW (does not block the rating's primary use; only the
middle-tier precision). Revisit only if the rating is productized for non-CA states or sold.

---

## TD-2 — CUSIP-level muni pricing feed [BLOCKING for scaling the portfolio past the demo universe]

**Gap.** Building a real, diversified ≥20-name portfolio with *current* per-bond stats (YTW/YTM/
duration) requires CUSIP-level market data for names beyond the 20-name research universe. Verified
2026-06-07 that **free public sources cannot supply this reliably:**
1. **EMMA** encrypts per-maturity CUSIPs in the free scale (`cusip9_enc` ciphertext; zero plaintext
   on issue pages) — no clean issuer→CUSIP path. *And* EMMA **rate-limits/blocks** scraping volume
   (a batch of `search_issues` calls that worked began returning 0 results mid-session).
2. **CDIAC DebtWatch `issues`** dataset is *issue-level* (issuer, par, sale date, TIC/NIC, S&P/
   Moody's/Fitch ratings, final maturity) — **no CUSIPs, no per-bond yields.** Good for ratings, not
   pricing.
3. **OS PDFs** list CUSIPs in plaintext (the maturity schedule), but automated parsing is **brittle**
   across issuers (term vs serial bonds, split coupons, base-CUSIP-in-header vs full-per-row), and it
   still needs the per-CUSIP trade tape (spotty for specific maturities) for a *current* mark.

**What works (proven):** the per-bond pipeline `compute_bond_analytics.fetch_security(cusip)` +
`analyze()` → current coupon/maturity/call + EMMA trade YTW + computed YTM/duration → `channel_scoring_v2`
score. Demonstrated on the 11-name basket and the El Camino/Stanford OS covenant verification. **Given a
CUSIP list, scoring any number of names to 20+ with full stats is straightforward.**

**Fix:** plug in a muni data feed — **ICE Data Services (muni)**, **Bloomberg**, **Refinitiv/MMD-TM3**,
or a **broker-dealer's CA-muni inventory + CUSIP-level pricing**. Any of these supplies the CUSIP +
current evals the free path can't. Wire its CUSIP list into the existing per-bond pipeline.

**Owner:** unassigned. **Priority:** MEDIUM (blocks productizing the 20-name portfolio; the methodology,
engine, and 11-name demo are complete without it). Same theme as TD-1: free data → framework + demo;
production → paid feed.

---
*Logged 2026-06-06. See: `capgains_beta.py`, `cdiac_draws.py`, `testC_*.py`,
`outputs/MUNI_AI_CRASH_RATING_METHODOLOGY.html`.*
