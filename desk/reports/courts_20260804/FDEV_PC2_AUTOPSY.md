# FDEV — THE PLANET COASTER 2 AUTOPSY × PLANET ZOO 2 PRE-LAUNCH DIFFERENTIAL
### Bear-refutation test, 2026-08-04 (T−70 to the 13-Oct-2026 PZ2 launch)

Companion to `FDEV.md` (DE-RATE 6/10) and `FDEV_TELEMETRY.md`. Tests the red team's bear
(p=0.35, 305p): *"PZ2 repeats Planet Coaster 2."*

**Doctrine.** Sizing and confidence only. The frozen call `FDEV | 2026-09-30 · nil dev-intangible
impairment · our_p 0.80` and the T2 post-launch evidence gate are **UNTOUCHED**. No shared-store
writes were made; the weight change below is a recommendation to route, not an applied edit.

**Price basis.** The court's same-day spot, **427.5p** (04-Aug-2026). Not re-pulled — this is a
weight-adjustment analysis, not a fresh valuation. Re-pull IBKR before any order.

**Evidence rule.** Every count below is labelled either **[CORPUS]** (measured from a primary Steam
API pull, 04-Aug-2026) or **[INFERENCE]** (my judgment on top of it). Regex-coded category counts
are **mechanical keyword prevalence**, non-exclusive, corroborated against a verbatim read of the
top-25 most-helpful reviews.

---

## 0. LEAD FINDING (Mode B) — the sentiment channels are worthless here, and I can now prove it

The strongest result of this pass is not about PZ2. It is that **the pre-launch channels the
telemetry note leaned on have zero demonstrated discriminating power for this franchise**, because
they all fired positive before Planet Coaster 2 — and I tested them in-sample rather than assuming.

The compensating finding: **both of PC2's top-two grievances were fully visible pre-launch on the
Steam store and announcement feed.** Not in sentiment — in *structure*. Frontier told everyone
exactly what it was going to do, in its own 12-Sep-2024 pre-order post, 55 days before launch. The
readable signal was the **shape of the offer**, not the temperature of the crowd.

That inverts the whole test. The refutable fraction of the bear is the **structural** fraction, and
it grades bear-refuting. The sentiment fraction is non-evidence. The execution fraction is
unresolvable until 13-Oct.

---

## 1. THE AUTOPSY — what actually killed Planet Coaster 2

**[CORPUS]** Pulled every PC2 negative review to launch day by chronological paging (`filter=recent`
— note `filter=all` is silently capped at a 365-day window and returns *nothing* from 2024):
**3,712 all-time negatives**, earliest 06-Nov-2024. Launch window (06-Nov → 31-Dec-2024):
**2,359 negatives = 63.6% of every negative review the game has ever received.** The verdict was
delivered in eight weeks. Median playtime at review in that window: **6.4 hours** — these are not
drive-bys, and not review-bombers either.

Language mix of the launch-window negatives: english 1,466 · german 265 · schinese 229 · french 152
· dutch 51 · korean 47 · spanish 31 · japanese 26. Coding below is on the **1,466 English**.

### Ranked flop causes

Two rankings. **Prevalence** = share of negative reviews mentioning it. **Weighted** = share of
community helpfulness votes (`votes_up`+1) attaching to reviews that mention it — i.e. what the
*audience* endorsed as the reason, which is the better read of what set the score.

| rank (weighted) | cause | weighted | prevalence |
|---|---|---|---|
| **1** | **UI / console-first design** — menus, click-count, controller-shaped interface | **52.2%** | 37.3% |
| **2** | **Monetization** — day-one and pre-order-exclusive paid content | **45.8%** | 28.1% |
| **3** | **Bugs / performance / "unfinished, stealth early access"** | **41.8%** | **49.4%** |
| **4** | **Missing content vs Planet Coaster 1** — themes, rides, stalls, night, hotels | **35.0%** | 27.0% |
| 5 | Pathing / building-tool regression | 30.6% | 25.7% |
| 6 | Water-slide physics — the flagship new feature — thin | 29.9% | 22.7% |
| 7 | Price / value, "wait for a sale", refund | 19.8% | 22.2% |
| 8 | Graphics / repeated textures | 13.6% | 13.7% |
| 9 | Management & career depth (energy, work zones, untaught systems) | 13.6% | 23.0% |
| 10 | Console-driven caps — 6,000-guest cap, small sandbox map | 11.3% | 3.8% |
| 11 | Multiplayer misrepresented — "co-op" is save-passing | 7.6% | 3.8% |
| 12 | Steam Workshop removed for Frontier Workshop | 7.2% | 7.2% |

*Caveat: categories are non-exclusive and two regexes are loose (cause 5 catches "snap"; cause 6
catches bare "pool"/"slides"). Ordering of the top four is robust to that; 5–6 should be read as a
band, not a rank.*

**Verbatim, the four that carried the votes** [CORPUS]:

- **#2 weighted, and the single most-upvoted review of the game (1,973 votes):** *"There are coasters
  & rides in the game, visible within the build menus, that send you to purchase DLC when you try to
  build them… I wanted to build a 'powered rotating ride', but it's locked behind a pre-order
  exclusive DLC I can't buy even if I wanted to! The ride isn't some minor cosmetic difference — it
  has unique functions, not available on any other track ride!"*
- **#1 weighted (939 votes):** *"The interface was clearly designed with a controller in mind and is
  not intuitive to use with a keyboard and mouse. Everything takes way more clicks than the original."*
- **#4 weighted (616 votes):** *"A themepark game without themes like western and space deserves a
  negative review… Planet Coaster 1 had those themes, they removed those to possibly sell them as DLC."*
- **#11 (547 votes):** *"'Co-op' is just save sharing, you can't actually play together. Absolute let
  down and labelling it as multiplayer is a scam tactic."*

### The score was set in 48 hours and never recovered

**[CORPUS]** Full positive corpus pulled to launch day (10,455) and merged with the negatives:

| day | cumulative reviews | positive rate |
|---|---|---|
| 0 | 735 | **61.8%** |
| 1 | 1,831 | 64.8% |
| 7 | 3,826 | 64.6% |
| 14 | 4,499 | 64.4% |
| 30 | 5,790 | 67.9% |
| 90 | 7,551 | 65.9% |
| 365 | 11,268 | 71.2% |

**The day-zero score was the score.** A full year of free updates bought 9pp. The English weekly
rollup shows a second collapse to **32.7% positive in the week of 11-Dec-2024** — the week Frontier
shipped the £7.99 Thrill-Seekers Ride Pack alongside a save-breaking update, five weeks after launch.

### Frontier's own launch-quality ladder — a clean in-sample separator

**[CORPUS]** English review-histogram rollups, launch month or launch week:

| title | launch window positive rate | outcome |
|---|---|---|
| Planet Coaster 1 (Nov-2016) | **94.6%** | success (90.5% lifetime) |
| Planet Zoo (Nov-2019) | **87.8%** | success (90.1% lifetime) |
| AoS: Realms of Ruin (Nov-2023) | **67.1%** | flop (56.4% lifetime) |
| Planet Coaster 2 (Nov-2024) | **59.3%** | flop (69.9% lifetime) |

Successes ≥87.8%, flops ≤67.1%, with a **20pp dead zone between them**. Four points is four points —
but it is monotone, in-family, and it reads within a week of launch. This is the instrument.

---

## 2. THE DIFFERENTIAL — each flop cause mapped onto PZ2's disclosed state

Sources: PZ2 Steam store page and `appdetails` (04-Aug-2026), the 23 Steam announcements from
28-May-2026, PC2's 22 pre-launch announcements from 11-Jul-2024, Google News RSS trade pickup.

| # | cause | wt | PZ2's disclosed pre-launch state | grade |
|---|---|---|---|---|
| **1** | Console-first UI | 52.2% | **PZ2 is a day-one PC + PS5 + Xbox Series release** (Gematsu, Tech Times, Xbox Wire, all 28-May-2026) — the *franchise's first console release*, into an installed base that has been 100% mouse-and-keyboard for 6.9 years. Store page declares full Xbox and PS5 controller support. The exact structural setup that produced PC2's #1 grievance. | **SAME — bear-confirming, and it is the heaviest axis** |
| **2** | Monetization | 45.8% | **Materially different, and this is verified from both companies' own store pages.** PC2: Deluxe = **ten vintage rides**; *every* pre-order = **three more rides** including the *'FD Vision' rotating ride* — the exact item behind the 1,973-vote review — plus **£19.98 of separately-listed launch-day DLC** (Vintage Funfair £15.99 on 06-Nov, Bonus Ride Collection £3.99 on 06-Nov). PZ2: Deluxe = **6 animal species + animal signs**; pre-purchase bonus = **Toucan Eat Shop, 3 donation bins, a Tiger photo stand-in** — *decoration only, zero functional units*; and **zero separately-listed DLC exists at T−70**. | **DIFFERENT — the strongest bear-refuting finding** |
| **3** | Bugs / unfinished | 41.8% | Unobservable pre-launch by construction. But the *process* tell is readable: **PZ2 has no playtest, demo or beta at T−70** (store page: zero). PZ1 ran a public beta with a full press hands-on cycle ~5–6 weeks pre-launch (PC Gamer 26-Sep-2019, PCWorld 28-Sep, TheSixthAxis 01-Oct); PC1 ran the Early Bird Alpha. PC2 ran neither — and its reviewers said so explicitly: *"For PC1, players were involved in Alpha and Beta testing. For PC2, the players were left out."* **Honest limit: Realms of Ruin DID run an open beta (Jul-2023) and still flopped**, so a public build is not sufficient — 2 successes with, 1 flop with, 1 flop without. Weak, one-directional tell only. | **UNKNOWN on outcome; process tell = SAME as PC2** |
| **4** | Missing content vs predecessor | 35.0% | **PZ2 ships nine themes at launch — four new plus five returning from Planet Zoo 1** (store page, verbatim). PC2's store page *today* also claims nine themes "from returning classics like Pirate and Western" — but its launch reviews say it shipped with three and no Western; **PC2 needed ~20 months of free updates to reach the number PZ2 claims on day one.** Career, Franchise and Sandbox are all present at launch (PZ1 parity). | **DIFFERENT — bear-refuting** |
| 5 | Pathing / build tools | 30.6% | Same Cobra engine, same tool lineage; store page markets "easy-to-use pathing systems", scaling, flexi-colour, foliage and terrain brushes — i.e. PC2's toolchain iterated. Inherits the risk; unresolvable on marketing copy. | **UNKNOWN** |
| 6 | Flagship feature thin | 29.9% | PZ2's flagship trio — aquariums, fully flying birds, Wildlife Reserves — is the *same risk shape* as PC2's water slides: a brand-new physics/traversal domain shipping v1. Marketed hard (Feature Focus: Awesome Aquatics, Behind the Scenes: Going Underwater). | **SAME risk shape, UNKNOWN magnitude** |
| 7 | Price / value | 19.8% | Identical to PC2: **£39.99 / $49.99** standard, **£54.99 / $64.99** Deluxe. No escalation, no premium ask. | **SAME — neutral** |
| 9 | Management depth | 13.6% | Career (FEN), Franchise and Sandbox all at launch. Dev on the record against simplification: *"We don't want to simplify it and make it easy, that's not where we're at"* (GamesRadar+, 08-Jun-2026). | **DIFFERENT — modestly bear-refuting** |
| 10 | Console-driven caps | 11.3% | **Not disclosed.** No guest cap or map size anywhere on the store page — exactly as PC2 failed to disclose its 6,000-guest cap. Unread, not clean. | **UNKNOWN — and demand it** |
| **11** | Multiplayer misrepresented | 7.6% | PZ2 markets only *"trade animals with other players in Franchise mode"* — PZ1's existing asynchronous mode, accurately described. **No co-op or multiplayer claim anywhere** in 23 announcements. | **DIFFERENT — bear-refuting** |
| **12** | Steam Workshop removed | 7.2% | **PZ2 = Frontier Workshop, zero Steam Workshop** — while **PZ1 has Steam Workshop**. PZ2 therefore imports the regression into an audience that has never suffered it, on a creative game where user-generated content is the retention engine. | **SAME — bear-confirming** |

**Was PZ2 ever delayed? [CORPUS] NO — verified from the announcement history.** PZ2 was teased
05-Nov-2025, announced *with* its 13-Oct-2026 date on 28-May-2026, and has held that date across all
23 announcements through 04-Aug-2026. So the delay-to-polish quality signal is **absent — no credit
either way.** For symmetry: PC2 was announced 11-Jul-2024 for "Fall 2024", dated 06-Nov on
12-Sep-2024, and also held. **Holding a date is not a quality signal in this family.**

*One honest two-sided note:* PZ2 having **zero listed DLC at T−70** is bear-refuting on cause 2 and
simultaneously bear-confirming on FY27 revenue — it compounds the PZ1 PDLC air-gap the telemetry
note found. The same fact cuts both ways and I am not going to spend it twice.

---

## 3. THE PRE-LAUNCH SKEPTICISM CONTROL — decisive, and it goes against us

The question: was PC2's fanbase skeptical before launch, or blindsided? If blindsided, the
telemetry's "9 sequel mentions, 9 positive, 0 negative" on PZ1 carries less weight.

**I ran the exact mirror of that test on PC1 in PC2's pre-launch window. [CORPUS]**

Planet Coaster 1 English reviews, 11-Jul-2024 (PC2 announce) → 05-Nov-2024 (day before launch):
**n = 1,048.** Reviews mentioning the sequel: **64 — of which 60 in POSITIVE reviews, 4 in negative
= 93.8% positive.** Base rate for positive reviews in that same window: **93.1%.**

> **Sequel-mention positivity was 93.8% against a 93.1% base rate. The signal carried exactly zero
> information.** And the content was not lukewarm — *"Hyped for Planet Coaster 2"*, *"My preorder is
> now in"*, *"Can't wait"*, *"super excited… only a few days away"* (30-Oct-2024, seven days out).

**The fanbase was blindsided, not skeptical.** Applying the same normalization to PZ2: 9/9 against
PZ1's 86% recent-review base rate has an expected value of 7.7/9 — a one-sided binomial p ≈ 0.27.
Not significant at n=9, and the higher-n version of the identical signal preceded the flop.

**Stated as plainly as the record deserves: the 9/9 positive sequel-mention finding carries no
refutation weight. I am withdrawing it as evidence.**

**Two further controls, same direction:**

1. **Press previews.** PC2 ran a coordinated hands-on preview embargo on **12-Sep-2024 (T−55)** and
   the tone was uniformly glowing [CORPUS, Google News RSS]: *"Frontier's best park sim yet?"*
   (GameSpew) · *"solidify it as the ultimate theme park builder"* (ggrecon) · *"Revamped Management
   Sim Mechanics That Make A Big Splash"* (ScreenRant) · *"More Thrills Than Ever Before"*
   (ScreenRant) · IGN, TheGamer, Metro, Twinfinite, TheSixthAxis, GameRant all positive. TheGamer even
   ran *"How Planet Coaster 2 Devs Used Community Feedback To Build A Stronger Sequel"* on 17-Oct-2024,
   three weeks before a 59.3% launch. **Preview-embargo tone was uniformly positive ahead of the
   flop.** This directly refutes the hypothesis in the brief that preview tone is the strongest
   pre-launch quality signal for sims — for this family it is not a signal at all. PZ2's preview tone
   is likewise positive (Gamereactor *"An ambitious sequel that elevates the Planet formula"*,
   TheSixthAxis, DualShockers, Shacknews, PC Gamer cover feature) and should be given **no weight**.
2. **Campaign density.** **[CORPUS — this corrects the telemetry note.]** PC2 did *not* run a thin
   campaign. It ran **22 pre-launch Steam announcements** from 11-Jul to 05-Nov-2024, including four
   gameplay Deep Dives (one dedicated to management), four speedbuilds, a Building 101 series and
   multiple Steam-exclusive livestreams. PZ2 has 23 in ten weeks with ten weeks still to run — denser
   in cadence, but the telemetry's "8 substantive beats vs PC2's 3" understated PC2 because it counted
   YouTube trailers only. **Campaign density has no discriminating power.**

**What the control does *not* wash away.** Three bear-reducing facts survive because none of them is
a sentiment reading: PZ1's live concurrent base is **7.3× PC1's** at the equivalent pre-sequel moment
(4,620 vs 634); the **monetization structure** is verified different from both companies' own store
pages; and the **nine-themes-at-launch** content posture is a falsifiable disclosure, not a mood.

---

## 4. THE PC2 MECHANISM WAS PRE-LAUNCH-VISIBLE — the honesty read

The autopsy's top-two grievances were both fully disclosed by Frontier before launch. [CORPUS]

- **Monetization.** The 12-Sep-2024 pre-order announcement, verbatim: *"The Deluxe Edition… comes with
  the enchanting Vintage Funfair Ride Pack, which gives you TEN vintage rides… PLUS, all pre-orders
  will get an EXTRA three bonus rides… includes an 'Outamax' water coaster, 'The Cube' thrill ride and
  an **'FD Vision' rotating ride**."* The most-upvoted negative review in the game's history is about
  that rotating ride. **The mechanism was on the store page 55 days early.**
- **Multiplayer.** The 11-Jul-2024 announcement said *"Build with other players – **one park manager
  at a time** –"* and *"Friendship fuels the fun!"*; Deep Dive 4 (31-Oct) said *"play and build with
  friends **(one at a time)**"*. The limitation was disclosed — **in a parenthetical, under framing
  that pointed the other way.** Technically accurate, marketed takeaway divergent. Outcome: a
  547-vote review calling it *"a scam tactic"*.

That is the house pattern exactly: **takeaway-vs-data divergence, not datum suppression.** And it is
the reason this channel is worth reading at all. Applying the same lens to PZ2's 23 announcements and
store page, I find **no equivalent divergence**: no co-op or multiplayer claim to overrun, a
cosmetic-only pre-order bonus, a Deluxe pack continuous with PZ1's own precedent, and a specific,
checkable content claim (nine themes, five of them returning). **On the one axis where Frontier's
pre-launch honesty was previously readable and previously failed, PZ2 currently reads clean.**

One live asymmetry to watch: PC2's store page declares *"Requires 3rd-Party Account: Frontier
Account"*; **PZ2's does not** — despite marketing the Frontier Workshop, which requires one. Either
the metadata is incomplete pre-release, or the requirement changed. Unread, not clean → tripwire 3.

---

## 5. THE TELEMETRY TRIPWIRE IS FALSIFIED IN-SAMPLE — and must be replaced

`FDEV_TELEMETRY.md` tripwire #5 reads: *"≥3,500–4,500 reviews @ 2wk = on >600k-unit pace; <2,000 = a
PC2-repeat warning."*

**[CORPUS] Planet Coaster 2 had 4,499 reviews at day 14.** The tripwire would have scored the
reference flop at the **top of its "on pace" band**.

It is not arithmetically wrong — PC2 *did* sell ~600k units. It measures the wrong variable. PC2's
failure was never volume; it was a 59.3% launch score that capped the tail, left FY25 revenue flat,
and is the entire content of the bear. **A count gate cannot detect a quality failure.**

The same defect sits in the court's **kill-trigger #2** ("PZ2 fails to exceed 600,000 units → exit").
PC2 hit roughly that number *and was the flop the bear is named after*, so clearing it is a very low
bar. Flagged as a calibration observation for the parent court — **not** an edit; the T2 gate is frozen.

**Replacement instrument — the launch-window positive rate**, against the four-point Frontier ladder
in §1, readable from a free endpoint within 48 hours:

`store.steampowered.com/appreviews/3219030?json=1&language=english&purchase_type=all`
and `store.steampowered.com/appreviewhistogram/3219030?l=english`

| PZ2 English positive rate at T+48h (15-Oct-2026) and T+7d (20-Oct-2026) | read |
|---|---|
| **≥ 85%** | PZ1/PC1-class launch. Bear substantially refuted; T2 evidence gate satisfied on quality. |
| **78 – 85%** | Base case intact. |
| **70 – 78%** | Warning band — below every Frontier success, above both flops. Hold T2. |
| **≤ 67%** | **PC2 / Realms-of-Ruin repeat. Bear confirmed.** Kill-path, do not deploy T2. |

Keep the ~50× units-per-review multiplier for the units question — it is independently verified — but
subordinate it. **Score first, units second.**

---

## 6. VERDICT

**What is refutable NOW, and how it grades.**

| fraction of the bear | axes | weight of PC2's failure | grade |
|---|---|---|---|
| **Structural — refutable now** | monetization (2), content-at-launch (4), multiplayer honesty (11), management depth (9) | **~68% of helpfulness-weighted grievance** | **REFUTED / DIFFERENT** |
| **Structural — refutable now, against us** | console-first UI (1), Steam Workshop removal (12), no public build (3, process) | **~59%** | **CONFIRMED / SAME** |
| **Execution — only on 13-Oct** | bugs & polish (3), build tools (5), flagship-feature depth (6), console caps (10) | **~85%** | **UNKNOWN** |
| **Sentiment — not evidence at all** | community warmth, preview tone, campaign density, wishlist heat | n/a | **NON-DISCRIMINATING (proven in-sample)** |

*Weights sum past 100% because categories are non-exclusive; read them as severity, not shares.*

**Roughly a third of the bear is genuinely refutable pre-launch, and that third grades bear-refuting
on net — but it is not a clean win, because the single heaviest axis (console-first UI, 52.2%) grades
SAME, and the heaviest *unresolvable* axes are unresolvable precisely because they are execution.**

The PZ2 pre-launch state is **not** a re-run of PC2's setup: the offer structure is clean where PC2's
was predatory, the content posture is forward where PC2's was a regression, there is no marketing
overpromise to be caught on, and the installed base is alive rather than dead. But PZ2 goes into a
day-one triple-platform launch with a controller-shaped UI risk, no Steam Workshop, and no public
build — and PC2 proves Frontier can execute all three of those badly at once.

### Recommended weight adjustment — doctrine-bounded, sizing/confidence only

| | bear 305p | base 530p | bull 690p | E[FV] | edge vs 427.5p |
|---|---|---|---|---|---|
| court (frozen) | 0.35 | 0.45 | 0.20 | 483p | +13.0pp |
| **this pass** | **0.32** | **0.48** | **0.20** | **490p** | **+14.6pp** |

**I land on the same 0.32 the telemetry note proposed — but on entirely different evidence, and that
is the point worth recording.** The telemetry reached 0.32 via community warmth, campaign cadence and
trade tone; §3 shows all three preceded the flop and carry no information. Those supports are
withdrawn. Replacing them are three verified structural findings — the monetization-structure
differential, nine-themes-at-launch, and the absence of a marketing overpromise — which are sturdier
than what they replace. **The number survives; the reasoning behind it did not.**

**Δ E[FV] = +6.75p (+1.6pp).** Still far inside the noise of a three-point grid and nowhere near a
threshold that would change a 0.375% starter.

**RECOMMENDATION: no sizing change.** T1 stays 0.375% (~$12.4k, ~2,150 sh) GTC ≤435p. T2 stays gated
on post-launch evidence, chase-cap 530p. The frozen 0.80 impairment call and the 10-Sep-2026
audited-accounts gate are untouched.

### New pre-launch tripwires (dated)

| # | tripwire | window | reading now | threshold |
|---|---|---|---|---|
| **1** | **Launch positive rate** (supersedes telemetry #5) | **15-Oct-2026 (T+48h)**, re-read 20-Oct | n/a | **≥85% bull · 78–85% base · 70–78% warn · ≤67% bear confirmed.** The count gate is demoted. |
| **2** | Any **separately-listed paid PZ2 DLC** appearing on the store page before launch — the exact PC2 mechanism | weekly to 13-Oct-2026 | **zero listed** | Any functional (non-cosmetic) paid pack listed pre-launch = cause-2 differential collapses → bear back to 0.35+ |
| **3** | *"Requires 3rd-Party Account: Frontier Account"* appearing on the PZ2 store page | weekly to 13-Oct-2026 | **absent** (PC2 has it) | Appearance = workshop/account grievance confirmed; minor bear-confirming |
| **4** | **Guest cap / map size disclosure** — PC2's 6,000-guest console cap was never disclosed pre-launch | by **06-Oct-2026 (T−7)** | **not disclosed** | Still undisclosed at T−7 = unread-not-clean, carry as a live console-parity risk into launch |
| **5** | **Public beta / playtest announcement** — PZ1's ran ~T−40, announced ~T−47 | by **01-Sep-2026** | **none** | No public build announced by 01-Sep = PZ2 has broken from PZ1's own launch process → hold bear at 0.35. *Weak instrument: Realms of Ruin had a beta and flopped.* |
| **6** | Review-embargo tone, T−2d | **11-Oct-2026** | n/a | **Log only, do not size on it** — PC2's preview cycle was uniformly glowing and non-predictive, and tripwire 1 supersedes it four days later. |

### Corrections to the record (route to the parent court, not to a shared store)

1. **Telemetry tripwire #5 is falsified in-sample** — PC2 cleared it at day 14. Replace with §5.
2. **"9/9 positive sequel mentions" is withdrawn as evidence** — PC1 produced 60/64 at base rate ten
   weeks before the flop.
3. **"PZ2 campaign breadth 8 beats vs PC2's 3" is wrong** — PC2 ran 22 pre-launch Steam announcements
   including four Deep Dives. The YouTube-only count understated it.
4. **Kill-trigger #2 (600k units) is a weak discriminator** — PC2 hit ~600k and is the flop the bear
   is named after. Flagged for the parent's calibration; the frozen gate is untouched.

---

*All counts pulled 04-Aug-2026 from `store.steampowered.com/appreviews`, `/appreviewhistogram`,
`/api/appdetails`, `api.steampowered.com/ISteamNews`, the PZ1/PZ2/PC1/PC2 store pages, and
`news.google.com` RSS. Wayback returned 429 on the archived PC2 launch store page, so PC2's launch-era
store copy is reported as unread; Frontier's own pre-launch announcements were used instead and are
strictly better primary evidence. No shared-store writes.*
