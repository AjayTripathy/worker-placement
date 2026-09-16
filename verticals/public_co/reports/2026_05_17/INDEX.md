# Signal OS — Trade Book Index (2026-05-17)

Curated point-in-time report folder.

## Top-level documents
- [TRADE_BOOK.md](TRADE_BOOK.md) — executability-focused report (the headline read)
- [POSITION_SIZING.md](POSITION_SIZING.md) — two-tier sized sheet for all 12 pairs
- [PAIR_TRADES.md](PAIR_TRADES.md) — full emit list (15 pairs across 12 cohorts)
- `borrow_rates.json` — frozen IBKR borrow snapshot

## Per-pair reports
Each file: cohort + tier + composite + R/F(M)/M evidence + shortability + IBKR borrow + hedge ratio + notional cap + suggested entry + carry cost + falsification rules.

### Tier 1 (high-conviction, factual-revision thesis)

- [MVST / ALB](./pair_01_MVST_ALB.md) — Solid-state battery, comp **1.57**, borrow 0.48%, cap $0.31M, shortability `BORROW_AT_PREMIUM`
- [SES / ALB](./pair_02_SES_ALB.md) — Solid-state battery, comp **1.50**, borrow 0.79%, cap $0.52M, shortability `BORROW_AT_PREMIUM`
- [KSCP / TER](./pair_03_KSCP_TER.md) — Robotics / autonomy, comp **1.44**, borrow n/a, cap $0.08M, shortability `HARD_TO_BORROW_OR_RETAIL_RESTRICTED`
- [BLDP / LIN](./pair_04_BLDP_LIN.md) — Hydrogen / fuel-cell, comp **1.22**, borrow 0.52%, cap $1.07M, shortability `BORROW_AT_PREMIUM`
- [FCEL / LIN](./pair_05_FCEL_LIN.md) — Hydrogen / fuel-cell, comp **1.00**, borrow 0.68%, cap $4.72M, shortability `SHORTABLE`
- [AIRO / KTOS](./pair_06_AIRO_KTOS.md) — Defense-tech, comp **0.75**, borrow 1.10%, cap $0.18M, shortability `SHORTABLE`

### Tier 2 (MOD-pattern, disclosure-quality re-rating)

- [IREN / EQIX](./pair_07_IREN_EQIX.md) — AI-DC / crypto-pivot, comp **1.17**, borrow 0.44%, cap $31.85M, shortability `SHORTABLE`
- [CIFR / EQIX](./pair_08_CIFR_EQIX.md) — AI-DC / crypto-pivot, comp **0.83**, borrow 0.25%, cap $31.85M, shortability `BORROW_AT_PREMIUM`
- [AEVA / INVZ](./pair_09_AEVA_INVZ.md) — Lidar / ADAS, comp **0.75**, borrow 0.43%, cap $0.00M, shortability `BORROW_AT_PREMIUM`
- [RDW / IRDM](./pair_10_RDW_IRDM.md) — Space / satcom, comp **0.71**, borrow 0.42%, cap $4.72M, shortability `SHORTABLE`
- [OUST / INVZ](./pair_11_OUST_INVZ.md) — Lidar / ADAS, comp **0.67**, borrow 0.27%, cap $0.00M, shortability `BORROW_AT_PREMIUM`
- [AFRM / COF](./pair_12_AFRM_COF.md) — Fintech lending / BNPL, comp **0.67**, borrow 0.25%, cap $18.63M, shortability `SHORTABLE`

## Notes
- These reports are generated from `data/_pair_trades/{pairs,position_sizing,borrow_rates}.json` plus the per-ticker `data/_local/<TK>.{plan,queries,scores}.json` files. Re-run the pipeline (`pair_trades` → `position_sizing` → `build_pair_reports`) to refresh.
- The data/_pair_trades/ source-of-truth files remain in place; this folder is a curated read-only artifact for a specific point in time.