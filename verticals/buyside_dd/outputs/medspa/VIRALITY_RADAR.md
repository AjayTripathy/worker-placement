# Cosmeceutical Virality Radar — Week of 2026-06-29

**Thesis (the edge):** a product going viral on TikTok / influencers shows up in a PUBLIC company's
earnings print ~1–2 quarters LATER. Most viral K-beauty / indie brands are PRIVATE, so the trade is
mapping the viral product to the listed beneficiary (brand owner | ODM | distributor) BEFORE the
market connects them — and only acting where the beneficiary is NOT yet discovered/priced.

**Method:** WebSearch virality scan (TikTok/Sephora/Ulta roundups + Glossy/WWD/BeautyMatter/KED/Reuters
trade press) → brand→vehicle map via `connectors/beauty_virality.py` (BRAND_TO_VEHICLE + resolve_odm_via_fda)
→ conditioning (how discovered already?). Detection date **2026-06-29** (weekly refresh).

**Conditioning-layer caveat (mandatory):** `discovery_state()` was attempted on every candidate; its live
connectors (StockTwits / Wikipedia / FINRA-SI / SEC-FTD and google_trends/gdelt) **time out / are
UNAVAILABLE on this egress** — consistent with the known cloud-IP limitation (`gtimeout` guard also absent
on this host). Regimes below are therefore conditioned from PUBLIC-DOMAIN proxies (YTD price move, 2026
forward P/E vs sector, institutional-ownership %, analyst count, press saturation), NOT the full automated
panel. **Treat regime confidence as MED.** All candidates are logged to
`/Users/ajay/exalted/signalos/outputs/latency_log.jsonl`.

**openFDA note (honesty):** `resolve_odm_via_fda()` returned `None` for every brand this run (brand_name
query rate-limited / not surfacing from this egress). So **NO new openFDA-confirmed ODM link this week.**
The Anua/BYOMA → Cosmecca SPF link below is the PRIOR-confirmed registry entry (Englewood Lab US sub),
unchanged. openFDA covers OTC-drug/SPF only — every non-SPF ODM link is **UNVERIFIABLE** and marked so.

---

## ⭐ THE SINGLE STRONGEST FRESH PAIR

**Anua + BYOMA → Cosmecca Korea (241710.KQ)** — the only CLEAN + openFDA-VERIFIED (SPF) viral→ODM pair
with residual latency. Both SPF lines map to Cosmecca's US sub (Englewood Lab). Anua/BYOMA still
ACCELERATING (Anua = #2 TikTok skincare, 9.3B views; Ulta rollout). Cosmecca Q1'26: revenue **+56.4%**
to ₩185.1B, OP **+78%** to ₩21.9B, **sun-care +173.6%**; trades **2026 P/E 12.7x vs sector 20.2x**.
Residual-latency catalyst = the **Q2 print (Aug 7)** that should carry the continued Anua/BYOMA + sun-care
ramp not yet in the multiple.

**HONEST CROWDING WARNING — this is the LAST week it reads pre-crowded.** Discovery is advancing fast:
the Q1 +78%-OP surprise is already public, Cosmecca is ~**45% institutional**, **12 analysts** cover it,
and the whole ODM/distributor complex has rallied with GIC/Morgan Stanley accumulating K-beauty names.
Regime = **DISCOVERING (trending toward CROWDED)**, not UNDISCOVERED. Surface it as the best clean pair,
but size with the window narrowing — the genuinely UNDISCOVERED fresh signals this week are all PRIVATE
(Dr. Melaxin, Mixsoon) and not tradeable today.

---

## WEEK-OVER-WEEK CHANGES (vs 2026-06-26)

**NEW ACCEL viral entrants (all resolve PRIVATE — no listed vehicle, IPO/M&A watch):**
- **Dr. Melaxin** — became the **#1 beauty brand on TikTok Shop** (~$46.3M Q1'26 rev); hero = Peel Shot
  Glow rice ampoule, "slow-aging" positioning. Parent **Brand501 Corp = PRIVATE**; Amazon lists mfr
  **BNB Korea Co** — NOT openFDA-confirmed (non-SPF) and BNB's listing status is unverified = **UNVERIFIABLE**.
- **Mixsoon** — **PDRN Collagen Tinted Moisturizer** = viral "skin-first makeup" debut. Parent **Parket Inc
  = PRIVATE**; ODM unconfirmed.
- **Medik8** — **Exo-PDRN Prismatic+** (triple-exosome + PDRN, "7-day revive"). UK, Inflexion PE-backed,
  private.
- **Rhode Caffeine Reset** (sculpt/tighten) — newly viral leg inside **ELF**; Rhode upgraded PEAK→ACCEL.

**FADES (decelerating = short-side latency tells):**
- **Sol de Janeiro → NEW FADE** — founder exit + fragrance-mist slowdown + sales stall. Owner **L'Occitane
  delisted (2024 take-private)** = no clean listed short.
- **Drunk Elephant → Shiseido (4911.T)** — still fading (unchanged); soft-print short tell persists.

**Momentum upgrades:** Tirtir PEAK→**ACCEL** (550% color-cosmetics growth H2'25); Rhode PEAK→**ACCEL**.

**Conditioning regime shifts (the big one):** the **K-beauty ODM/distributor complex got DISCOVERED.**
Cosmecca (+56.4% rev / +78% OP), Kolmar (OP +32%), Cosmax (record rev) all printed strong Q1; stocks
rallied (Cosmecca +12% on May 11); ~45% institutional; **GIC + Morgan Stanley accumulating K-beauty stocks**.
→ **Silicon2 reclassified DISCOVERING → DISCOVERED_CROWDED**; Cosmecca DISCOVERING-trending-crowded.
Latency on last week's #1 pair is being harvested in real time.

**Newly-CONFIRMED openFDA ODM links:** **NONE** (openFDA brand_name query returned nothing this run).

**PRIVATE brands worth an IPO/M&A watch (new + carried):** Dr. Melaxin (Brand501), Mixsoon (Parket),
Medik8, Biodance, Rejuran, Gudai Global house (Beauty of Joseon / Tirtir / Skin1004), Glow Recipe.

---

## RANKED RADAR (tradeable signal = viral velocity × clean public vehicle × residual latency)

| # | Viral product / brand | Hero ingredient / claim | Momentum | Driving influencer(s) | PUBLIC vehicle | Linkage | Conf | Regime | Tradeable read |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **Anua** (Heartleaf, Zero-Cast SPF) + **BYOMA** | heartleaf/centella, PDRN; tinted SPF; ceramide barrier | **ACCEL** — Anua #2 TikTok skincare (9.3B views), Ulta rollout | Skinfluencers; Ulta K-beauty zone | **Cosmecca Korea 241710.KQ** (Englewood Lab US sub, openFDA-confirmed SPF) | ODM | MED | **DISCOVERING → crowding** (P/E 12.7x vs 20.2x; ~45% inst, 12 analysts) | **Strongest clean+verified pair.** Residual latency = Q2 print (Aug 7); window narrowing. |
| 2 | **Beauty of Joseon** Relief Sun (18.5M units) + new **Revive** fermented-retinol | rice + prebiotic SPF50+; fermented retinol | **ACCEL** — Sephora; new launch may eclipse Relief Sun | Derm/skinfluencer sunscreen roundups | **Kolmar 161890.KS** (+Cosmax/Green Cos) | ODM | **LOW** | DISCOVERING (P/E 12.8x) | ODM link **industry-reported, NOT openFDA-confirmed = UNVERIFIABLE**; Kolmar diluted across many brands. |
| 3 | **K-beauty viral basket** (BoJ/Medicube/Biodance/Anua) | aggregated export demand | **ACCEL** (basket) | n/a — distributor read | **Silicon2 257720.KQ** (distributor) | distributor | MED | **DISCOVERED_CROWDED** (fwd P/E 10.15; GIC + Morgan Stanley accumulating) | Cheapest read but **now crowded** — institutions found it. Latency largely harvested. |
| 4 | **Rhode** Caffeine Reset + **Naturium** | caffeine sculpt/tighten; actives-forward | **ACCEL** (Naturium fastest-growing top-50; Rhode new viral SKU) | Hailey Bieber (Rhode); Bretman Rock (Naturium) | **e.l.f. Beauty ELF** | brand_owner | HIGH | DISCOVERING — Rhode leg ~discovered | Rhode largely in print; **Naturium = residual leg**. Large-cap dilutes single-SKU latency. |
| 5 | **Medicube** PDRN serum + AGE-R device | PDRN "salmon sperm", collagen | **PEAK (stock), product still selling** | TikTok PDRN wave (10.6B views); Kardashian-adjacent halo | **APR Corp 278470.KS** | brand_owner | HIGH | **DISCOVERED_CROWDED** | **SKIP / fade as a discovery trade.** Press + stock saturated; latency harvested. |
| 6 | **COSRX** / **Laneige** | snail mucin "glass skin"; lip sleeping mask | Durable-viral, maturing | Long-tail skinfluencer staple | **Amorepacific 090430.KS** | brand_owner | HIGH | DISCOVERING | Large-cap parent dilutes single-SKU latency. |
| 7 | **Drunk Elephant** | legacy actives | **FADE** | Past TikTok-teen wave cooling | **Shiseido 4911.T** | brand_owner | HIGH | DISCOVERING (negative) | **SHORT-side latency tell** — decelerating virality → soft print 1–2Q out. |
| 8 | **Dr. Melaxin** Peel Shot Glow rice ampoule | rice exfoliation, "slow-aging" | **ACCEL (NEW)** — #1 TikTok-Shop beauty (~$46.3M Q1'26) | Paid-creator engine; livestream scale | **— (Brand501, PRIVATE; mfr BNB Korea)** | private / ODM unverified | LOW | PRIVATE_NO_VEHICLE | **UNVERIFIABLE** ODM (non-SPF; BNB listing unconfirmed). Prime IPO/M&A watch. |
| 9 | **Mixsoon** PDRN Collagen Tinted Moisturizer | PDRN + 74% skin-active essence | **ACCEL (NEW)** — viral skin-first makeup debut | TikTok glass-skin; Amazon launch | **— (Parket Inc, PRIVATE)** | private | HIGH | PRIVATE_NO_VEHICLE | No listed vehicle; ODM unconfirmed. IPO/M&A watch. |
| 10 | **Medik8** Exo-PDRN Prismatic+ | triple exosome + PDRN, "7-day revive" | **ACCEL (NEW)** | Derm/editor launch | **— (UK, Inflexion PE-backed)** | private | HIGH | PRIVATE_NO_VEHICLE | Private; no clean listed vehicle. Watch. |
| 11 | **Tirtir** Mask Fit Red Cushion | wide-shade cushion (550% color-cosmetics growth) | **ACCEL** (up from PEAK) | Black beauty creators (shade-range) | **— (Gudai Global, PRIVATE)** | private/ODM unconfirmed | LOW | PRIVATE_NO_VEHICLE | UNVERIFIABLE ODM. Gudai Global IPO watch. |
| 12 | **Biodance** Bio-Collagen Real Deep Mask | "bio-collagen" overnight hydrogel | **ACCEL** | TikTok overnight-mask ritual | **— (private; ODM NFC/Seoul Cosmetics)** | private/ODM | LOW | PRIVATE_NO_VEHICLE | Brand + ODM private. Indirect read = Silicon2 (crowded, see #3). |
| 13 | **Skin1004** Centella ampoule | centella/madecassoside | ACCEL | K-beauty conversion staple | **— (Gudai Global, PRIVATE)** | private | LOW | PRIVATE_NO_VEHICLE | Same private parent as Tirtir/BoJ. |
| 14 | **Rejuran** Turnover Ampoule | PDRN, pharma-grade | ACCEL (category originator) | Kim Kardashian / Kris Jenner | **— (private)** | private | LOW | PRIVATE_NO_VEHICLE | UNVERIFIABLE vehicle. PDRN-category IPO/M&A watch. |
| 15 | **Sol de Janeiro** mist / jelly balm | fragrance body care | **FADE (NEW)** | founder exit; mist slowdown | **— (L'Occitane, delisted 2024)** | brand_owner (private) | HIGH | PRIVATE_NO_VEHICLE | Fade tell, but owner delisted = no clean listed short. |
| 16 | **Glow Recipe** | dewy / fruit actives | PEAK | TikTok | **— (private, VC-backed)** | private | HIGH | PRIVATE_NO_VEHICLE | No clean vehicle. |

---

## TOP "VIRAL → PUBLIC-BENEFICIARY" PAIRS TO WATCH

1. **Anua + BYOMA → Cosmecca Korea (241710.KQ)** — *the cleanest + only openFDA-verified pair.* ACCEL,
   12.7x vs 20.2x, residual latency into the Aug-7 Q2 print. **But discovery is advancing (Q1 +78% OP
   already public, ~45% inst, complex rallied) — DISCOVERING-trending-crowded, not undiscovered.**
2. **Naturium leg of ELF** — Rhode's latency largely spent; Naturium (fastest-growing top-50, Bretman Rock)
   is the residual under-discounted leg inside ELF.
3. **(Short-side)** **Drunk Elephant → Shiseido (4911.T)** — fading virality → soft print 1–2Q out.
4. **Beauty of Joseon → Kolmar (161890.KS)** — *conditional.* ACCEL into Sephora + new Revive launch, but
   ODM link is industry-press, **NOT openFDA-confirmed = UNVERIFIABLE**. Confirm before sizing.
5. **AVOID — already crowded:** Silicon2 (GIC/MS in), APR/Medicube (saturated). Skip as discovery trades.

## PRIVATE / NO-VEHICLE — the gap (IPO / M&A watch)

- **Dr. Melaxin (Brand501)** — *new this week,* #1 TikTok-Shop beauty brand; prime IPO/buyout candidate.
  ODM BNB Korea UNVERIFIABLE (non-SPF, listing unconfirmed).
- **Mixsoon (Parket Inc)** — *new,* viral PDRN tinted-moisturizer makeup debut.
- **Medik8** — *new,* Exo-PDRN; UK PE-backed.
- **Gudai Global** (Beauty of Joseon / Tirtir / Skin1004) — private house of three viral brands; single
  highest-value future K-beauty IPO/buyout in the radar.
- **Biodance, Rejuran, Glow Recipe** — viral, private, no clean listed vehicle.

## TOP INFLUENCERS DRIVING THE SIGNAL (the upstream)

- **Dr. Muneeb Shah (DermDoctor), Dr. Shereene Idriss, Dr. Whitney Bowe, Caroline Hirons** — derm/ingredient
  literacy → barrier, PDRN, exosomes, SPF, "skin longevity" framing.
- **Hailey Bieber (Rhode), Bretman Rock (Naturium)** — owner/ambassador drivers feeding ELF.
- **Kim Kardashian / Kris Jenner** — celebrity PDRN/salmon-sperm halo (Rejuran → cheaper Medicube/Anua).
- **Paid-creator scale engines** — Dr. Melaxin and Medicube's tens-of-thousands-creator livestream model is
  the new growth mechanic (WWD: heavy paid-content reliance).

## CURRENT INGREDIENT/TREND MAP (June 2026)

PDRN "salmon sperm" (Rejuran→Medicube/Anua/Mixsoon/INKEY) · **exosomes** (Medik8 Exo-PDRN) · polynucleotides ·
peptides · bio-collagen overnight masks (Biodance) · snail mucin / "glass skin" (COSRX) · centella/heartleaf
(Anua, Skin1004) · rice + prebiotic SPF + fermented retinol (Beauty of Joseon) · cushion-foundation revival
(Tirtir, Mixsoon, YSL) · "skin longevity" / barrier-first reframing · bakuchiol (gentle retinol alt).
NB: on Olive Young, **PDRN appears in 33 of the Top-50 skin-longevity products** (Oct'25–Mar'26).

---
*Files: radar → `/Users/ajay/exalted/signalos/verticals/buyside_dd/outputs/medspa/VIRALITY_RADAR.md`;
seed/scan → `/Users/ajay/exalted/signalos/verticals/buyside_dd/outputs/medspa/run_virality_scan.py`;
latency log → `/Users/ajay/exalted/signalos/outputs/latency_log.jsonl`. Sources: TikTok Shop/Sephora/Ulta
roundups, WWD, BeautyMatter, Glossy, KED Global, Seoul Economic Daily, Korea Biomed (KBR), Who What Wear,
PitchBook/CB Insights (ownership), stockanalysis.com (KOSDAQ valuations). discovery_state live connectors
UNAVAILABLE on egress → regimes from public proxies at MED confidence.*
