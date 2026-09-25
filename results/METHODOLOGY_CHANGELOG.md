# Methodology Changelog (v1 → v2, 2026-09-24/25 audit)

Nothing changed silently. Each change lists the reason, the evidence, and its measured effect
(paired DeLong on identical test pixels unless stated). v1 is kept intact: the historical files are
untouched, and every v1 number is reproduced in `results/`.

| # | Component | v1 (historical) | v2 (audit) | Reason | Measured effect |
|---|---|---|---|---|---|
| 1 | Fire rasterisation | `round((lat−f)/e)` against the top-left edge | containing pixel, `floor` against the edge | 74.9% of points displaced by one pixel | RF +0.0055 (all) / +0.0114 (forest) on the same split |
| 2 | Climate/LST/NDVI "anomaly-mean" features | time mean of anomalies (2001–2020 baseline) | dropped; replaced by 2001–2020 climatological levels | identity: equals the 26 out-of-baseline months' anomalies ÷ n | v1 vs v2 −0.0004 / −0.001 (whole feature set) |
| 3 | Trend features | MK τ on raw monthly series (LST, FLDAS) or on the MA trend (NDVI) | Seasonal Kendall τ (+ Sen slope for NDVI); BH-FDR for significance maps | MK assumes no seasonality or serial dependence | trend group +0.0013 / +0.0056 |
| 4 | DTR trend | computed, not in stack | Seasonal-Kendall DTR τ in stack | Phase 14 option A | part of #3 |
| 5 | Land-cover fractions | 2020 map (inside label window) | 2001 map | temporal leakage in principle | measured mechanism weak (+0.019 vs +0.018 forest change) |
| 6 | Label-fitted NDVI features | θ\* indicator (fitted on all labels); CVSI lag by MI on all labels | θ\* indicator dropped (redundant step function of NDVI mean); CVSI k\* re-selected on training labels (= 8) | label use in feature construction | 0.0000 |
| 7 | Degenerate features | F5 residual mean (≈0), LC140 (constant), F4 (≈F1) | dropped | no information / redundant | — |
| 8 | Aspect | degrees (0/360 discontinuity) | sin, cos | circular variable | within #2 |
| 9 | NDVI QA gap 2007-03/04 | unfiltered (Step 2), dropped (CDR stack) | VI_Quality MODLAND bits | missing reliability layer | F1 r = 0.999996 |
| 10 | Moran's I / LISA | stride-8 subsample; non-India cells row-mean filled (67%) | 8×8 block mean; India cells only (`w_subset`) | synthetic cells dominated the statistic | I 0.8322 → 0.9456 |
| 11 | Imputation | median over all rows before split | median over training rows | minor leakage | — |
| 12 | Evaluation population | all India pixels | forest pixels primary; all pixels secondary | forest fraction alone gives AUC 0.91 | RF v2 0.975 → 0.897 |
| 13 | Classical random split | 80/20 (headline) / 65/15/20 (tuning) | 65/15/20 stratified by the corrected label; test touched once; thresholds from validation | single protocol | — |
| 14 | Spatial CV (classical) | GroupKFold on 0°-anchored 2° blocks | CDR-PINO block permutation (68.2E/6.75N origin), block-carved validation | identical partitions across all models | — |
| 15 | CDR-PINO protocol | Track A: AdamW + ReduceLROnPlateau, 80 epochs; B1/B2/B3: Adam + cosine, 50/80 epochs, random-pixel validation | one protocol for every track; block-carved validation for B1/B2; year-carved for B3 | tracks were not comparable | B1 0.7510 → 0.7185; B2 0.6187 → 0.5701 |
| 16 | CDR-PINO B3 terminal label | pooled 2000–2022 (includes held-out years) | training months only | label leakage | +0.0006 (negligible) |
| 17 | CDR-PINO ablation | single seed, no no-physics arm, fixed budget | 4 configurations × 3 seeds, identical protocol, paired tests | controlled evidence | no physics configuration beats no physics |
| 18 | Baselines for B3 | none | covariate-free persistence and seasonal-frequency nulls | interpretability of temporal skill | nulls 0.908 / 0.930 > CDR-PINO 0.893 |
| 19 | CDR-PINO vs classical | different grids, labels and folds | bridge: classical models on CDR-PINO's cells, covariates and partitions | fair comparison | RF +0.041 (A), +0.25 (B1), +0.39 (B2) |
| 20 | Final map | RF v1 probabilities, no metadata | RF v2 relative score + 5 forest-quantile classes, with provenance tags | calibration and provenance | — |
| 21 | MaxEnt training size | 150k, undisclosed | 150k kept; sensitivity 50k–500k reported | disclosure | +0.0015 / +0.006 at 500k |

Items **not** changed: study period, boundary, forest codes, FIRMS filtering (no filter; the
sensitivity is null), NDVI QA level (Good + Marginal), the CDR-PINO architecture, losses, covariates
and 12 km grid, and the RF and MaxEnt hyperparameters (historical validated values).

Items that need changing **outside `results/`** (not done without approval):

- CLAUDE.md's rasterization rule.
- The environment table in CLAUDE.md (`cdr_pinn_env`).
- The gap document's A1 and C4 entries.
- Every manuscript number listed in `FINAL_MANUSCRIPT_NUMBERS.md`.
