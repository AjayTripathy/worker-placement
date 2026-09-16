# SUJA — consumer demand read (search trend + retail reviews)

**Run 2026-08-15 · first live output of the consumer-products lane · tape $6.48 (5d +3.5%, 21d −31.0%)**

Both benches closed the SUJA record with the same complaint: every real-time channel that could
resolve the back half early was unusable — hiring contaminated by wrong-entity postings, customs
empty, sponsor buy too small to read. This is the third channel they did not have: what the
consumer is actually doing with the brand, from sources the company does not control.

---

## Headline

**The demand tape does not corroborate a brand collapse. It flags the Emerging Brands (Slice) leg
instead of the core.**

Suja brand search interest is **flat year-over-year (+6.6%)** against the same four calendar weeks
of 2025, and is tracking its own category. The scary-looking number — **−30.3% versus the trailing
90 days** — is seasonal and cohort-wide: every one of the 13 brands in the lane printed DECAYING or
FLAT on that same metric this week, and the *category* term "cold pressed juice" fell −28.5% over
the identical window. Read the seasonal control, not the raw direction.

The genuine negative is elsewhere: **"Slice soda" search is −65% year-over-year** and sits at 0.31×
its own 12-month peak. The launch wave that the Emerging Brands spend bought has fully faded.

---

## 1. Search demand — Suja brand

Google Trends, US, weekly, 0–100 relative scale (each request is normalized independently, so
compare within a series, never across them).

| measure | value | reading |
|---|---|---|
| recent 4 weeks vs trailing 90 days | 40.5 vs 58.1 = **−30.3%** | DECAYING — but see the control below |
| slope across the recent window | **−6.9% / week** | still falling week to week |
| **vs the same 4 weeks of 2025** (anchor Aug 10, 2025) | 40.5 vs 38.0 = **+6.6%** | **FLAT year-over-year** |
| latest week vs 12-month peak | **0.35×** | the peak is the January cleanse season, not a lost level |

**The seasonal control is the whole point.** Juice/cleanse search peaks in January and again in
early summer; running any consumer screen in mid-August produces a wall of red. Confirmation that
this is calendar and not company: all 13 tracked brands read DECAYING or FLAT this week, including
Chipotle, Domino's and Dave & Buster's.

**Category control.** Over the identical 90-day window, "cold pressed juice" ran −28.5% and is
+2.3% year-over-year. Suja: −30.3% and +6.6%. **The brand is moving with its category, not below
it.** That is an independent, non-company data point consistent with management's stated cause —
channel shift, not share loss — and it is the first corroboration of that claim in the record from
a source that is not the company or its Nielsen slide. It is corroboration, not proof: search
interest is attention, not shipments.

One mix caveat: the **"wellness shot" category is −7.9% year-over-year** — the sub-category behind
Suja's single largest reviewed retail SKU.

## 2. The Emerging Brands leg — Slice

| measure | value |
|---|---|
| recent 4 weeks vs trailing 90 days | 32.0 vs 46.5 = **−31.1%** |
| **vs the same 4 weeks of 2025** | **−64.8%** |
| latest week vs 12-month peak | **0.31×** |

Slice's search interest is lapping the Jan-2025 relaunch and the 2025 Cola/Ginger-Ale expansion
waves, and has given all of it back. This cuts in **both** directions, which is why it matters to
the adjudication rather than to one bench:

- **For the blue bench's rehabilitation:** the launch wave is over, so launch-intensity spend
  plausibly does not recur — the "$(26)M Emerging Brands drag laps out" arithmetic is consistent
  with what the demand tape shows.
- **Against the guide's revenue half:** if Q4'26 has to print $98–107M, and Emerging Brands is the
  growth leg, the tape says Slice consumer pull is at a one-year low. The back half then depends on
  **core distribution wins**, not brand momentum — an execution claim, not a demand claim.

## 3. Retail shelf and reviews

Walmart, via the text proxy (Amazon, Target and Trustpilot are bot-walled from this egress and are
labelled as such in the output — they are not silently dropped).

| SKU | rating | ratings | 1–2★ share |
|---|---|---|---|
| Organic Immunity Turmeric Pineapple Wellness Shots 4-pk | 4.6 | **2,670** | 7% |
| Essentials Fuel Fruit & Vegetable Juice 12oz | 5.0 | 3 | 0% |
| Essentials Mighty Juice 12oz | 3.3 | 3 | 33% |
| Energy Wellness Shot 2oz | 4.0 | 2 | 0% |
| Organic Citrus Immunity Juice 12oz | 2.0 | 1 | 100% |

Review-weighted lifetime rating **4.60** across 2,679 ratings — but that number is one SKU. **The
mass-channel shelf is thin: four of the five juice SKUs carry three or fewer ratings between them.**
That is exactly the shape you would expect from a brand disclosed as ~⅓ grocery vs ~12% mass, and
it means the mass-channel expansion the back half needs **has not yet shown up as buyer volume at
the largest mass retailer.** This is the most useful forward tripwire in the read.

**Rating trajectory: BASELINE_ONLY, by design.** The exact recent-cohort-versus-lifetime delta is
computed from consecutive snapshots — (R₁N₁ − R₀N₀)/(N₁ − N₀) is the precise mean of the reviews
added in between — and today's run *is* the first snapshot. Snapshots are stored; the first real
delta is available from **2026-08-18** and weekly thereafter. Nothing is claimed before then.

## 4. Social and retail rank

- **Reddit / ApeWisdom: ABSENT** from the top pages. A −46% single-session IPO break did not
  generate durable retail chatter — low attention, consistent with an undiscovered/uncrowded name,
  and it means no squeeze fuel is being priced.
- **Amazon Best-Sellers (Grocery): not ranked** in the parsed top-30. Present in the category,
  absent from the demand-velocity leaders.
- **Composite heat score: 26.4 / 100** (full three-channel read, confidence 1.0) — 4th coldest of
  the 13 tracked brands. Read as a *velocity* score against the brand's own trailing 90 days, with
  the seasonal caveat above.

## 5. Provenance and one honest gap

Every number above is a live pull on 2026-08-15 (UTC 21:47–22:11). The **stored** heatmap JSON shows
an empty "vs LY" column for the whole lane: after the bounded pass plus these SUJA-specific pulls,
Google Trends rate-limited this egress (~20 requests/hour), and the connector returns RATE_LIMIT with
no points rather than a fabricated series. The YoY figures quoted here therefore come from the
successful pulls listed above, each with its anchor date stated; the heatmap's own column fills on the
next scheduled daily pass. That is the degraded-loud contract working as designed, not a data gap
being papered over.

## 6. What this read cannot say

- Search interest and retailer review counts are **attention and one retailer's buyer volume**, not
  shipments, not sell-through, not the grocery channel where most of Suja's mix sits. Whole Foods,
  Costco and Kroger have no free public review or rank surface.
- The 0–100 Trends scale is renormalized per request; only within-series comparisons are valid.
- The exact review cohort delta needs the second snapshot (from 8/18).
- Amazon is bot-walled here; the escalation is the Product Advertising API or a logged-in browser.

## 7. Bearing on the pending adjudication

It does not flip either bench. It **removes one "unresolvable"** from the record and adds dated
tripwires:

1. **The demand-collapse premise behind the −46% session is not visible in the consumer tape.**
   Brand search is flat YoY and in line with its category. The de-rate looks like multiple and
   float mechanics, not a consumer walking away — which is the direction the blue bench took.
2. **The soft spot is Emerging Brands, not core.** That is a partial *support* for blue's
   base-effect argument on margin (launch spend has no wave left to fund) and a partial *warning*
   on red's side of the ledger for revenue (Q4 must come from distribution, not from Slice pull).
3. **Mass-channel penetration is unproven in the data we can see** — the thin Walmart shelf is the
   cheapest available early read on the channel-shift story, and it now has a weekly monitor.

**Tripwires (now monitored daily by the `consumer_heat` watch):**

| trip | meaning | first read |
|---|---|---|
| Suja YoY search turns ≤ −12% while the category holds | genuine share loss, not channel shift → re-court | daily |
| New Suja SKUs appear at Walmart / review velocity accelerates | the mass-channel ramp the Q4 guide needs is real | from 8/18 |
| Recent-cohort rating falls ≥0.15 below lifetime | product reception deteriorating ahead of the print | from 8/18 |
| Slice YoY improves off −65% | Emerging Brands re-accelerating without new launch spend | daily |

Next scheduled reads land well before the ~11/03 lockup and the ~11/10 print.

---

*Sources: Google Trends widget JSON (search) · ApeWisdom/Reddit (social) · Amazon Best-Sellers and
Walmart product pages via the r.jina.ai text proxy (retail). Generated by
`verticals/buyside_dd/connectors/consumer_product_heat.py` and `…/consumer_product_reviews.py`;
stored at `verticals/buyside_dd/outputs/consumer_heat/CONSUMER_HEAT.json`; rendered at
`desk/ui/static/consumer_heat.html` (the "consumer" tab). Every degraded source is named in the
output rather than scored as zero.*
