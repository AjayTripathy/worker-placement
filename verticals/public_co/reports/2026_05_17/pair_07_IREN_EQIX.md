# SHORT **IREN** / LONG **EQIX** — AI-DC / crypto-pivot

**Tier:** TIER2   ·   **Composite (short):** 1.17   ·   **Flags (short):** 0R / 1S / 5M

**Long-leg composite:** 0.00 (in-cohort cleanest follow)

**Short-leg filing analyzed:** `0001878848-26-000026_10-Q.txt (FY26 Q3 10-Q, period ending 2026-03-31, filed 2026-05-08); cross-referenced with 0001878848-25-000063_10-K.txt (FY25 10-K, period ending 2025-06-30)`

---

## Thesis

Tier 2 (lower-conviction, MOD-pattern): composite 0.60–1.20 with ≥2 MODERATE findings and no RED_FLAG. The thesis is a **disclosure-quality re-rating** — the market eventually penalizes the multiple applied to filings where claims don't independently verify. Holding period typically 6–12 months; basket sizing preferred over single-name conviction.

---

## Evidence (R / F(M) / M)

#### 🟠 SEVERE — `C6`
- **R (claim):** >$7B fresh capital (debt + equity) raised in <18 months: $3.69B convertibles outstanding at Mar 31 2026 + $3.0B 2031 Convert issued May 14 2026 + $635M ATM equity through Aug 2025.
- **F (M-source check):** Distress / dilution fingerprint (Heuristic 10). Repeated large convertible issuance + active ATM equity at thin balance sheet is a distress marker.
- **M (observed):** Capital raise pace: $440M (Dec 2024) + $550M (Jun 2025) + $1.0B (Oct 2025) + $2.3B (Dec 2025) + $3.0B (May 2026) = $7.3B in convertible debt over 17 months, plus $635M+ ATM equity, plus $3.6B GS/JPM committed (not closed) for Microsoft GPU financing, plus $625M Mirantis acquisition almost entirely in stock, plus EUR 165M Nostrum.
- **Why this severity:** Funding cadence is consistent with a company racing to fund a capex commitment that exceeds current cash flow capacity. Capped call + prepaid forward structures on each convertible tranche reduce dilution mechanics but also signal management acutely concerned about share-price-sensitive dilution. Convertible-debt levels ($7.3B principal) now substantially exceed market cap-implied operating cash flow. SEVERE per Heuristic 10 — heavy reliance on convertible debt + dilutive equity is a classic AI-DC pivot funding pattern that becomes acutely problematic if the Microsoft tranches slip, GS/JPM fac

#### 🟡 MOD — `C1`
- **R (claim):** Microsoft Agreement: $9.7B TCV over ~5 years, signed Nov 2 2025, dedicated GPU services at Childress; zero tranches delivered/accepted as of Mar 31 2026; no Microsoft RPO recognized.
- **F (M-source check):** Counterparty disclosure threshold (Layer 3 Rule 7). A $9.7B contract is multi-$100M-per-year recurring AI hosting capex and is material to Microsoft's data center capex commentary. Microsoft's 10-Ks/10-Qs filed since November 2, 2025 (FY26 Q1 10-Q filed Oct 2025, FY26 Q2 10-Q filed January 2026) sho
- **M (observed):** Microsoft EDGAR filings: 0 mentions of 'IREN', 0 of 'Iris Energy', 0 of 'Childress' as of 2026-05-16. HARD CONTRADICTION per Calibration Heuristic 7.
- **Why this severity:** CRITICAL: IREN claims a $9.7B 5-year dedicated GPU services contract with Microsoft, yet zero corroboration in Microsoft's EDGAR filings. Combined with the fact that zero tranches have been delivered/accepted, no Microsoft consideration is in RPO, the related $3.6B GS/JPM financing remains a non-binding commitment letter, and Microsoft contract value is essentially a TCV announcement booked entirely as future opportunity. This is the textbook AI-DC TCV-vs-recognized-revenue conflation pattern flagged by Heuristic 9, AND a counterparty-disclosure failure per Rule 7. Stage ladder: term sheet / d
- **Audit:** originally `RED_FLAG_NEGATIVE` — adjusted by rescoring.

#### 🟡 MOD — `C2`
- **R (claim):** 4,510MW grid-connected power capacity claim with new 1,600MW Oklahoma site added since FY25 year-end.
- **F (M-source check):** Stage-ladder discipline (Heuristic 3). The 'executed grid connection agreements, letters of agreement or equivalents' headline lumps together executed and LOA-stage interconnections. Oklahoma site connection-right amortization begins Q4 FY28, implying energization is not imminent.
- **M (observed):** No third-party EDGAR corroboration of IREN's Oklahoma site (no utility filings, no partner announcements indexed); however the 10-Q financial-statement note showing a $112M asset acquisition with capitalized connection rights is a substantive, auditable disclosure that is internally consistent.
- **Why this severity:** The 4,510MW headline conflates: 810MW operating + 75MW Childress Horizon 1 under construction + 1,400MW Sweetwater 1 substation under construction + ~2,225MW that is at LOA / connection-agreement-signed / development stage including the new 1,600MW Oklahoma site whose connection rights amortization doesn't even begin until FY28. Marketing-tier number is real on paper but only ~18% is operating MW today. Score MODERATE per Heuristic 3 (planned vs operational conflation in headline).

#### 🟡 MOD — `C3`
- **R (claim):** Childress Horizon 1-4 liquid-cooled AI data centers under construction; Horizon 1 (~50-75MW) targeted CY2025 energization to support the Microsoft Agreement.
- **F (M-source check):** Stage-ladder discipline (Heuristic 3) + counterparty corroboration (Rule 7) for Microsoft tranche delivery.
- **M (observed):** No Microsoft EDGAR mentions of Horizon, Childress, or IREN; IREN's own 10-Q reveals zero accepted tranches under the Microsoft contract.
- **Why this severity:** 10-K target was Horizon 1 energization by end of CY2025 to begin AI hosting deliveries. As of the 10-Q reporting date 2026-03-31, no Microsoft tranches have been delivered or accepted — implying the Horizon 1 facility has slipped or is not yet generating Microsoft revenue. The Horizons 2-4 facilities are referenced only as planned in MD&A capex commentary. This is a stage-ladder failure: 'planned/under construction' is being marketed in service of the headline Microsoft contract but commissioning + energization + revenue milestones have not been hit. MODERATE since the company does disclose 'n

#### 🟡 MOD — `C5`
- **R (claim):** Q3 FY26 revenue $144.8M (flat YoY), net loss $(247.8)M, Adj EBITDA $59.5M (down from $83.1M); Microsoft contribution = $0 (nil tranches delivered).
- **F (M-source check):** AI-DC revenue-recognition pattern check (Heuristic 11). Legacy BTC mining revenue is volatile; if AI pivot marketing is loud but recognized revenue is still mostly BTC, score MODERATE.
- **M (observed):** Revenue is exactly flat YoY ($144.8M each period) — implying the AI Cloud Services growth offsets BTC declines or vice versa but no net AI lift visible yet. Net loss expanded materially ($(16.1)M → $(247.8)M) likely driven by interest expense from $3.3B of new convertible notes plus operating costs from AI/GPU buildout WITHOUT corresponding AI revenue.
- **Why this severity:** Per Heuristic 11, revenue mix has not yet shifted to AI Cloud Services despite the company's pivot narrative and $9.7B Microsoft contract. Headline 'AI Cloud provider' branding is not yet supported by recognized revenue. Quarter shows widening losses and Adj EBITDA contraction. MODERATE — disclosure-quality issue: the gap between marketing tier (AI pivot) and recognized-revenue tier (still flat, mostly BTC) is significant.

#### 🟡 MOD — `C7`
- **R (claim):** Two M&A transactions in the four days immediately preceding the May 11-14 2026 $3B convertible offering: Mirantis ($625M ~90% stock) on May 4 and Ingenostrum/Nostrum Group (~EUR 165M) on May 7.
- **F (M-source check):** Investment vs operating distinction (Heuristic 4) + counterparty corroboration. Acquisitions targets are private (Mirantis private cloud software co; Ingenostrum private Spanish DC developer) so absence from external EDGAR is expected.
- **M (observed):** No external corroboration is achievable for private acquisition targets. Both transactions are disclosed in IREN's own 10-Q subsequent events / Item 5 Other Information.
- **Why this severity:** Two acquisitions announced in four days, immediately followed by a $3B convertible raise on May 11-14, suggests a deliberate sequencing of news flow ahead of a capital raise. Mirantis is paid ~90% in IREN stock (price-sensitive), Ingenostrum is 65% cash / 35% stock. The Spanish DC pipeline (490MW) adds to the marketing-tier MW number but is brand new with no operating MW. MODERATE — disclosure-quality issue around the cadence of news flow and capital raise.

---

## Execution

### Shortability
- **Tier:** `SHORTABLE`
- Price: $52.94
- Market cap: $18.89B
- Daily $ volume: $2067.31M
- Short float: 18.0%

### IBKR borrow
- **Latest fee:** **0.44%** annualized (2026-05-15)
- Shares available: 8.6M
- 30-day avg: 0.40%
- 30-day max: 0.88%
- Trend: **stable**

### Hedge ratio
- **Beta-neutral:** **4.24×** (short β=4.20, long β=0.99)
- _Method: beta-neutral (short_beta / long_beta)_
- For every $1 long EQIX, short $4.24 of IREN.

### Notional cap (5% daily $ vol)
- Short daily $ vol: $2067.31M → cap $103.37M
- Long daily $ vol: $636.96M → cap $31.85M
- **Binding leg: long**
- **Max long-leg notional:** $31.85M

### Suggested conservative entry (30% of cap)
- Long EQIX: **$9.55M**
- Short IREN: **$40.53M**
- Annualized borrow carry on short: **$177,294/yr** (0.4374% × $40.53M)

---

## Risk + falsification

- **Falsification window:** 12 months from cutoff (2026-05-16). Pair survives if either leg moves >50% against the thesis OR the divergence claim is corroborated post-cutoff and the pair returns ~0.
- **Suggested exit rule:** close on +20% adverse move on the short leg, OR 6 months without confirming evidence, whichever comes first.
- **Hedge ratio reliability:** if either β was missing (default 1:1 fallback), the hedge is approximate. Watch correlation drift quarterly.

## Pair metadata
- Theme: AI-DC / crypto-pivot
- Generated: 2026-05-17 from frozen position_sizing.json + borrow_rates.json