# FDEV — GAMES-TELEMETRY SENTIMENT PASS · 2026-08-04 (T−70 to PZ2 launch)

Companion to `FDEV.md` (DE-RATE 6/10) and `edge_classifications/FDEV.json` (bear .35 / base .45 /
bull .20, E[FV] 483p vs 427.5p). **Doctrine: this is a nowcast. It adjusts sizing and confidence
only. The frozen call `FDEV | 2026-09-30 · nil dev-intangible impairment · our_p 0.80` and the T2
evidence gate are UNTOUCHED.**

**Channels used / blocked.** Worked: Steam storefront pages, Steam appreviews API (all languages —
strictly better than the English-only store-page count), Steam appdetails API, Steam news API,
Steam's server-rendered most-wishlisted list (`/search/results/?filter=popularwishlist`, the JS
`/charts/mostwishlisted` page returns an empty shell), Steam concurrent-players API, YouTube search
JSON, Google News RSS. **Blocked and therefore reported as unread, not clean:** steamdb.info returns
403 on every path (so *follower counts and all-time-peak-concurrents history are unavailable* —
this matters, see §4); reddit.com returns the HTML shell on `.json`, `old.reddit`, `api.reddit` and
via WebFetch, so **no subreddit size or thread-level engagement was obtainable by any route.**

---

## 1. IS PLANET ZOO GOOD — the quality corpus

| metric (Steam, all languages, 04-Aug-2026) | Planet Zoo (app 703080) | Planet Coaster 2 (2688950) | Planet Coaster 1 (493340) |
|---|---|---|---|
| Release | 05-Nov-2019 (PC-only) | 06-Nov-2024 | 17-Nov-2016 |
| All-time reviews | **97,075 · 91.0% · Very Positive** | 14,166 · 73.8% · Mostly Positive | 72,058 · 91.3% · Very Positive |
| Recent (30d, store page) | 84% of 1,308 (English) | 84% of 365 | — |
| Review velocity (from newest-100 timestamps) | **22.8/day ≈ 684/30d** | 12.3/day ≈ 369/30d | — |
| **Live concurrents** | **4,620** | 2,067 | **634** |

**The decisive number is the last row.** Planet Coaster 1 — eight years old when its sequel shipped —
holds 634 concurrent players today. Planet Zoo, six years and nine months old and ten weeks from its
sequel, holds **4,620, i.e. 7.3× PC1's live base**, and is still generating ~684 reviews a month at
91% lifetime positive. PC2 inherited a dead installed base; PZ2 inherits a living one. That is the
single strongest disconfirmation of the naive "PZ2 = PC2 repeat" bear, and it is measured, not argued.

**The DLC engine — the court's economics leg (PDLC = 43% of the £143m franchise) — is HIGH-QUALITY
BUT CURRENTLY DARK.** All 22 PZ1 DLC packs pulled and reviewed individually:

- **Quality held throughout.** The first-wave packs are the *weakest* (Deluxe Upgrade 72.8%, Arctic
  75.4%, South America 71.3%, Australia 76.7%); every pack from Dec-2022 onward scores 78–95%
  (Grasslands 94.7%, Oceania 94.0%, Asia 94.1%, Conservation 95.8%). Frontier got *better* at PDLC
  over the run. This is a genuine positive and it corroborates the court's PDLC-annuity premise.
- **But the audience thinned hard.** Reviews per pack fell 394 (Apr-2020) → 262 → 178 → 143 → 116 →
  52 → **34 (Asia, Jun-2025)**, a ~91% decline. Some of that is structural DLC review fatigue; the
  magnitude is larger than fatigue alone explains.
- **NEW FINDING, NOT IN THE COURT — the PZ1 PDLC engine has been off for 13+ months.** Last paid
  pack: **Asia Animal Pack, 25-Jun-2025.** Last content update of any kind: **1.20.2, 28-May-2026**
  (free scenery, shipped the same day as the PZ2 date announcement). The Steam news feed for app
  703080 from 28-May-2026 onward is *entirely PZ2 cross-promotion*. Cadence went ~3 packs/yr
  (2020–23) → 2 (2024) → 1 (2025) → **0 (2026 YTD)**. FY27 therefore carries a **PDLC air-gap**: no
  PZ1 packs, and PZ2's own DLC will not begin monetising until FY28. This cuts bearish on the FY27
  revenue line *independently of whether PZ2's launch succeeds* and it is not priced into the court's
  base case, which assumes £108–115m FY27 revenue.

**r/PlanetZoo:** UNOBTAINABLE — every Reddit endpoint blocked (see channels note). Substituted with a
direct read of the 200 newest English PZ1 reviews as a community-sentiment proxy: **86% positive**,
and on sequel sentiment specifically, **"Planet Zoo 2" / "PZ2" / "sequel" appear 9 times, all 9 in
POSITIVE reviews, zero in negative reviews.** There is no detectable "abandoned us for the sequel"
backlash — the failure mode that usually precedes a sequel launching into a hostile base is absent.

> **Verdict, one line: Planet Zoo is genuinely good and still alive — 91% lifetime over 97k reviews,
> 7.3× Planet Coaster 1's live player base at the equivalent pre-sequel moment, DLC quality rising
> across its run — but its paid-DLC engine has been switched off for 13 months, so FY27 revenue leans
> on PZ2 harder than the court's slate description implies.**

---

## 2. PZ2 PRE-LAUNCH HEAT, BENCHMARKED

**Wishlist rank — the industry-standard pre-launch demand indicator.** Read from Steam's own
server-rendered most-wishlisted ordering, 04-Aug-2026, paged to depth 600 of 5,204 unreleased entries:

> **Planet Zoo 2 (app 3219030) = RANK 158.**

Context from the same pull: Total War: WARHAMMER 40,000 #7 · Dawn of War IV #17 · Warhammer 40,000:
Dark Heresy #30 · **Jurassic Park: Survival #128** (a *competitor's* dinosaur-park game, ahead of
PZ2) · **Prison Architect 2 #96** (the closest management-sim-sequel comparable, ahead of PZ2) ·
Warhammer 40,000: Chaos Gate – Deathwatch **#379**.

Rank 158 is the **top 3% of unreleased Steam titles — solid, not elite.** It has had nine months to
accumulate (PZ2 was first teased 05-Nov-2025 on PZ1's sixth anniversary; dated 28-May-2026), and it
still sits behind both its nearest genre comparable and a direct thematic competitor.

**Base rates — flagged honestly as PLAUSIBLE PUBLIC PRIORS, not our calibration (ours is n=0).** The
widely-cited public rules of thumb are: top-10 most-wishlisted ≈ 1m+ wishlists; top-50 ≈ 200–400k;
top-100 ≈ 150–250k; **top-200 ≈ 80–150k**; and wishlist→purchase conversion ≈ 8–12% in the launch
week, ~20% over the first year, with wide dispersion. Applied to rank 158 that implies on the order
of **~10–18k launch-week Steam units from the wishlist channel alone** — a number that is nearly
meaningless for a sequel, because the existing 97k-review PZ1 owner base buys without wishlisting and
the PS5/XSX SKUs (PZ2 is the franchise's first console release) are entirely off this channel.
**Treat the rank as an ordinal signal about launch-window PC momentum, not as a units forecast.**

**Steam followers:** UNOBTAINABLE. The Steam store page exposes no follower count and steamdb.info
403s on every path including via the Wayback snapshot. Reported as unread.

**Trailer view velocity — Frontier's own channel, and this is the encouraging half of the read.**

| video | views | age | implied /day |
|---|---|---|---|
| Announce Trailer | 455,611 | ~2 mo | — |
| Gameplay Trailer | 599,813 | ~1 mo | — |
| Official Zoo Tour (35 min) | 309,283 | ~1 mo | — |
| Feature Focus – Awesome Aquatics | 166,025 | 2 wk | ~11.9k |
| Feature Focus – Awe-inspiring Animals | 148,068 | 4 wk | ~5.3k |
| Animal Spotlight – African leopard | 85,659 | 2 wk | ~6.1k |
| Wildlife Reserves Sneak Peek | 94,218 | 7 d | ~13.5k |
| **Animal Spotlight – Leopard Shark** | **87,778** | **5 d** | **~17.6k** |

**Velocity is accelerating into launch, not decaying** — the five-day-old beat is out-pacing the
fourteen-day-old beat ~2.9:1 per day. Aggregate own-channel campaign engagement ≈ **1.95m views in
ten weeks**. Cadence is extremely dense: **20 Steam announcements between 29-May and 04-Aug**, ~2/week
(Zoopedia drops, Feature Focus, Behind the Scenes, Animal Spotlights, PC Gaming Show, Wholesome
Direct). Coverage tone from Google News RSS (100 items) is **uniformly positive-to-neutral trade
pickup with no negative angle** — though most of it is press-release-derivative, so it evidences that
the campaign is *landing*, not that the game is *good*.

**The head-to-head that cuts the other way:** PC2's own-channel Announcement Trailer has **1,110,876
lifetime views** vs PZ2's Announce Trailer at 455,611 after two months. Trailer views front-load
heavily, so PC2 was probably ahead of PZ2 at the equivalent point on that single cleanest comparable.
PZ2 is ahead on *campaign breadth* (8 substantive beats vs PC2's 3) and on the gameplay trailer
(599k @1mo vs PC2's Pre-Order Trailer at 270k lifetime). **Honest net: comparable to modestly better
than PC2, not a step-change.**

### THE COMPARISON THAT MATTERS

Planet Coaster 2 went into launch with strong wishlists and a well-received announce trailer, and it
still landed at ~600k units and **73.8% "Mostly Positive"** — because it shipped *content-thin*, and
the damage showed up in the review score and therefore in the tail, not in the launch window.

- **Pre-launch heat CAN predict:** the launch-window number — first-week/first-month units, peak
  concurrents, initial sell-in. Wishlists and trailer velocity are attention metrics and attention is
  what converts in week one.
- **Pre-launch heat CANNOT predict:** the review-driven tail — the 6-to-24-month sales curve, the
  attach rate on paid DLC, and whether the title becomes a catalogue annuity. That is set by product
  quality *after* people play it, which is exactly the variable no pre-launch channel observes. PC2 is
  the proof: its pre-launch signal was fine and its post-launch signal was the failure.

**Which one does FDEV's FY27 guide actually need? The tail.** The court's base case is FY27 revenue
£108–115m and adjusted operating profit £19–21m across a **full twelve months from an October launch**,
plus the PDLC annuity thesis, plus (per §1) a PZ1 PDLC air-gap that PZ2's own tail has to fill. A big
October and a mediocre 74%-positive score would produce something close to the *bear*, not the base.
**Therefore the pre-launch read, however good it gets, cannot resolve the load-bearing uncertainty —
which is precisely why the red team was right to re-gate T2 to post-launch evidence.**

**A calibrated instrument for that post-launch gate — and it fills a real hole, because SteamDB
(the source the T2 gate names) is 403-blocked to us.** Both FDEV-disclosed unit numbers can be
reconciled to Steam review counts at a single multiplier:

- Planet Zoo: **5,000,000+ units** (company-disclosed to 01-Sep-2025, PC-only — verified: appdetails
  shows Windows-only, no console SKU) ÷ **97,075 reviews** = **51.5 units per review.**
- Planet Coaster 2: **~600,000 units at 10 months** (the court's PC2 benchmark) ÷ 14,166 reviews at
  21 months; back-casting the review count to the 10-month mark implies **~50 units per review.**

**A ~50× units-per-Steam-review multiplier reproduces both company-disclosed figures independently.**
That converts kill-trigger #2 from a datum we must wait until ~mid-Jan-2027 for into something
readable daily from a free API:

- **10-month gate (by ~13-Aug-2027): PZ2 must reach ~12,000 Steam reviews to clear 600k units.**
- **2-week gate (~27-Oct-2026, the red team's re-gated T2 checkpoint): ≥3,500–4,500 reviews puts PZ2
  on a >600k pace; <2,000 is a PC2-repeat warning.** *These two-week thresholds are derived from
  typical launch front-loading (~25–35% of year-one reviews in month one), not verified — the ~50×
  multiplier is verified, the front-loading split is a judgment. Console units sit outside this
  channel and will bias the estimate low.*

---

## 3. WARHAMMER LINKAGE — RESOLVED, NOT ASSUMED

**What FDEV actually holds today, from primary Steam metadata:**

| title | app | dev / pub | status | Steam evidence |
|---|---|---|---|---|
| Warhammer Age of Sigmar: Realms of Ruin | 1844380 | **Frontier / Frontier** | released 17-Nov-2023 | **3,124 reviews · 52.0% · "Mixed"**; **7 live concurrents**; ~25 reviews/30d at **39% positive**; no recent-reviews box (<10/30d on the store page); last DLC 2024 |
| Warhammer 40,000: Chaos Gate – Daemonhunters | 1611910 | Complex Games (FDEV-owned) / — | released 2022 | 14,643 reviews · 76.6% · Mostly Positive; 350 concurrents |
| Warhammer 40,000: Chaos Gate – Deathwatch | 3010270 | **Complex Games / Frontier Developments** | **"Coming soon" — NO DATE** | **wishlist rank #379**; only **3 announcements ever** (21-May, 29-May, 26-Jun-2026); footer: "© 2026 Games Workshop Limited … used under licence" |

So the linkage is real but small and cold. Frontier does hold a live Games Workshop licence and does
have a Warhammer title in the FY27 slate. But **Realms of Ruin is a verified flop** — at the ~50×
multiplier, 3,124 reviews ≈ **~155k units** on a £59.99 title, with a 52% Mixed score and seven
people playing it. And **Deathwatch has no release date on its own store page**, which is a direct
caveat on the court's line that "FY27's slate is heavier than FY26's": the Planet Zoo 2 leg is dated
and marketed hard; the Warhammer leg is undated, 379th in wishlist demand, and has been marketed
three times in ten weeks. Its predecessor's 14,643 reviews ≈ ~730k units is the realistic ceiling,
and 76.6% is a merely-decent score.

**Meanwhile, where is the Warhammer heat?** It is in the top 30 of the wishlist chart — and **none of
it is Frontier's**: Total War: WARHAMMER 40,000 (#7, Creative Assembly/SEGA), Dawn of War IV (#17),
Warhammer 40,000: Dark Heresy (#30), Warhammer Survivors (#135), Boltgun 2 (#198). Frontier's entry
is #379, behind all five.

> **Stated exactly as requested: the Warhammer heat is real — it is one of the strongest franchise
> signals visible anywhere on the Steam wishlist chart right now — but it attaches to Games Workshop
> and to OTHER studios' titles, not to FDEV. Frontier is a marginal, licence-fee-paying participant
> in the Warhammer cycle, and its one shipped Warhammer game was a flop. Do not underwrite any part
> of FDEV on Warhammer sentiment.**
>
> *One-line redirect, not a court:* the pure-play carrier of that feeling is **Games Workshop
> (GAW.L)** — it collects a royalty on every one of those top-30 titles regardless of which studio
> ships them. That is a separate name requiring its own court; nothing here underwrites it.

---

## 4. IMPACT ON THE FDEV RECORD — DOCTRINE-BOUNDED

**What the pre-launch read establishes.** Two-sided, and the sides roughly cancel:

*Bear-reducing (weight toward base/bull):* PZ1's live base is **7.3× PC1's** at the equivalent
pre-sequel moment — the mechanical reason PC2 disappointed is largely absent here; PZ1 DLC *quality*
rose across the run (last five packs 78–95%), so the PDLC annuity premise is sound as a product
matter; sequel sentiment in the base is **9 positive mentions / 0 negative**; marketing velocity is
**accelerating** into launch (17.6k views/day on the newest beat) with dense 2×/week cadence and
uniformly positive trade coverage; and PZ2's announced feature set (aquariums, aviaries, Wildlife
Reserves, nine themes, and Career/Franchise/Sandbox all present at launch) is additive-heavy against
exactly the content-thinness that killed PC2.

*Bear-preserving (weight toward bear):* wishlist rank **158 is solid, not elite** — nine months of
accumulation and still behind Prison Architect 2 (#96) and Jurassic Park: Survival (#128); the
cleanest single head-to-head, own-channel announce trailer, **favours PC2** (1.11m vs 455k @2mo); the
**PZ1 PDLC air-gap of 13+ months** is a new FY27 revenue drag the court did not model; PZ1's marginal
DLC audience thinned ~91% across the run; **Deathwatch is undated** so the second FY27 leg is softer
than the court's slate table implies; and Realms of Ruin proves Frontier can ship a dud (2 of the last
3 original launches underperformed — RoR 2023, PC2 2024 — against JWE3 2025 working).

**Does it move the weights enough to matter for T1? NO.** The most the evidence would justify is
trimming bear 0.35 → 0.32 into base:

| | bear 305p | base 530p | bull 690p | **E[FV]** | edge vs 427.5p |
|---|---|---|---|---|---|
| court (frozen) | 0.35 | 0.45 | 0.20 | **483p** | +13.0pp |
| telemetry-adjusted | 0.32 | 0.48 | 0.20 | **490p** | +14.6pp |

**Δ E[FV] = +6.75p (+1.6pp of edge).** That is inside the noise of a three-point scenario grid and far
below any threshold that would change a **0.375% starter**. **RECOMMENDATION: no change. T1 stays
0.375% (~$12.4k, ~2,150 sh) GTC ≤435p. T2 stays gated on post-launch evidence, chase-cap 530p. The
frozen 0.80 impairment call and the 10-Sep-2026 audited-accounts gate are untouched.** The honest
summary is that the pre-launch channels confirm the base case is *plausible* and confirm that PZ2 is
*not* obviously walking into PC2's grave — they do not, and structurally cannot, resolve the tail.

**Two items that DO belong in the record independent of sizing** (route to the next FDEV update, not
to a shared store): (a) the **PZ1 PDLC air-gap** — it strengthens kill-trigger #3 (FY27 guidance cut
below £104.8m / £19.0m) because FY27 must absorb a full year with no PZ1 pack revenue; (b) **Deathwatch
has no release date**, so the court's "FY27 slate heavier than FY26" claim should be downgraded from
CONFIRMED to PARTIALLY CONFIRMED pending a dated announcement.

### Pre-launch tripwires, 04-Aug-2026 → 13-Oct-2026

| # | tripwire | reading | threshold |
|---|---|---|---|
| 1 | **PZ2 wishlist rank, weekly** (`store.steampowered.com/search/results/?filter=popularwishlist`, page to depth 300) | **158 @ T−70** | **Top-60 by 30-Sep = UPGRADE signal** (rank rises mechanically into launch as released titles fall off; failing to climb is failing to convert). **>200 at any weekly read, or outside top-100 at T−7 (06-Oct) = WARNING** — trim T2 intent. *n=0 calibration; these are judgment thresholds.* |
| 2 | Trailer beat velocity | ~17.6k views/day on newest beat; 2 beats/week | Per-day velocity on the newest beat falling below ~5k for two consecutive beats = campaign fatigue |
| 3 | Deathwatch gets a dated release before the 10-Sep FY26 results | undated, wishlist #379 | Still undated at 10-Sep = FY27 second leg soft; flag against kill #3 |
| 4 | Any new PZ1 paid DLC announcement | none since 25-Jun-2025 | Would close the PDLC air-gap — bullish surprise for FY27 |
| 5 | **Post-launch (arms 27-Oct-2026):** PZ2 Steam review count via `store.steampowered.com/appreviews/3219030?json=1&language=all` | n/a pre-launch | **≥3,500–4,500 @ 2wk = on >600k-unit pace; <2,000 = PC2-repeat warning.** 10-month hard gate: **~12,000 reviews by 13-Aug-2027** = the 600k kill-trigger, made observable ~7 months before FDEV discloses it |

---

## 5. DETECTOR SPEC

**`games_prelaunch_telemetry`** — for issuers whose revenue turns on dated software/entertainment
releases, read pre-launch demand from the free leading channels (Steam most-wishlisted **ordinal rank**
and its weekly trajectory, store-page follower velocity where reachable, publisher-channel trailer
**views-per-day on the newest beat**, announcement cadence, and community sentiment sampled from the
predecessor title's recent reviews) ahead of the revenue print; pair it at launch with the
**units ≈ ~50 × Steam review count** conversion, calibrated here against two independently
company-disclosed unit figures, to read the outcome months before the issuer discloses it.
*Direct analogue of the beauty-virality radar: the attention channel leads the print by one to two
quarters, and the trade is the latency.* **APPLIES_TO:** games/entertainment issuers with a dated
release inside the forecast period, where one title is a material share of guided revenue.

**Honest limits.** (1) Attention instruments are **sector-conditional** — the house record is luxury
~0.45, apparel NULL, **games UNTESTED, n=0** — so nothing here is alpha until backtested across a
cohort of dated releases. (2) The channel measures **launch-window demand only**; the review-driven
tail, which is what most guides actually need, is structurally invisible pre-launch (PC2 is the
in-sample proof). (3) Console and Game Pass units sit entirely outside Steam, biasing both the
wishlist read and the review-multiplier low for multi-platform titles. (4) Wishlist rank is **ordinal**
— a rank change is not proportional to a wishlist-count change. (5) SteamDB, the richest source for
followers and peak-concurrents history, **403s us**, so the follower leg of this detector is currently
unimplemented and any gate written against SteamDB metrics (including the court's own T2 wording)
needs the review-count substitute above. (6) Reddit is fully blocked on every endpoint tried; the
community leg is presently served only by predecessor-title review sampling.

*No shared-store writes were made. Evidence rule observed throughout: every number above is from a
primary Steam/YouTube/Google-News endpoint pulled 04-Aug-2026, or is flagged as a public prior or a
derived judgment.*
