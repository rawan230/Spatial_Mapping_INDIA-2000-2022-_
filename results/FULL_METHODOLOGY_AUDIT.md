# Full Methodology Audit: Spatial Mapping of Forest Fire in India using CDR-PINO Models

**Audit dates:** 2026-09-24 to 2026-09-25. **Scope:** Phases 0–57 of the audit brief, executed in
the brief's 32-step order. **Rule of evidence:** every number here was recalculated from raw data,
or reproduced by re-running the project's own code, in this audit. Historical values are shown only
next to their recalculated value. Biswas et al. (2025) values come only from the PDF (see
`biswas_reference/BISWAS_REFERENCE_AUDIT.md`).

All paths are relative to `results/`.

---

## 0. Bottom line

1. **The data pipeline reproduces.** Recalculated independently from the raw files, the fire labels (541,545 points, an
   identical set), FLDAS, land cover, NDVI, LST, terrain and accessibility features all match their
   historical rasters (86 checked items, `audit/NUMERICAL_RECALCULATION_AUDIT.csv`). Every
   historical CDR-PINO number (Track A 0.9398; B1 0.7510 ± 0.0182; B2 0.6187 ± 0.0680; B3 0.8960)
   and the RF/MaxEnt headlines (0.9704 / 0.9598; spatial CV 0.9459/0.9527/0.9508) reproduce **bit-exactly**.
2. **Several methods behind those numbers are defective**:
   - Half-pixel label misregistration: 74.9% of points are displaced.
   - Degenerate climate "anomaly-mean" features.
   - Mann–Kendall applied to seasonal or autocorrelated series.
   - A Moran's I dominated by filled synthetic cells.
   - An in-window 2020 land-cover map.
   - A leaky B3 terminal label.
   - Mismatched evaluation populations.

   A corrected feature set (v2) and corrected protocols were built. **None of the fixes changes AUC by
   more than 0.012.** The label fix *raises* AUC. The historical classical numbers were valid in magnitude
   but rested on invalid intermediate statistics.
3. **The CDR-PINO physics is not supported by controlled evidence.** Under one validated protocol with 3 seeds:
   - **Physics terms vs no physics:** every physics configuration is *worse* than the same network
     without physics on the random split and on unseen years. On spatial and regional hold-out the
     difference is indistinguishable from zero (§23).
   - **Classical models on identical inputs:** on CDR-PINO's own cells, splits and covariates, a
     Random Forest beats it on every track, with 0.980 / 0.974 / 0.959 vs 0.939 / 0.719 / 0.570 on A/B1/B2 (§32).
   - **Unseen years:** CDR-PINO's result (0.893) is below a covariate-free persistence baseline
     (0.908, and 0.930 for the seasonal version).
   - **Physical consistency:** the trained field is effectively static in time and does not
     satisfy its own PDE (residual 74–616 × |∂u/∂t|).
4. **Relative to Biswas et al.:**
   - **Protocol reimplementation:** a Biswas-style reimplementation on this project's data (0.25°,
     15 levels, 2020 presences, MaxEnt) reaches test AUC 0.893 ± 0.009, of the same order as their
     0.879. Their top permutation-importance variables (NDVI, air temperature, LST) are
     reproduced; specific humidity's dominance is not.
   - **This study's pixel-level results** (RF 0.975 all pixels / 0.897 forest pixels) are **not
     directly comparable** to Biswas's AUC.
   - **Genuine methodological extensions:** spatial, regional and temporal validation, leakage
     control, a forest-only evaluation population, and a reproducible numerical chain.

---

## Step 1 — Repository audit (Phase 0)

- **Repository structure:** nine git repositories, all clean at audit time (commits in
  `audit/DATA_PROVENANCE.md` §3). Every audit output lives under `results/` and no historical file was modified.
- **Source documents:**
  - `STUDY_METHODOLOGY_AND_GAPS.md` was placed at the root on 2026-09-24 and audited as the gap inventory.
  - `CDR_PINO_TGRS.pdf` does not exist; per the user's instruction the `.tex` manuscripts were not
    audited. The Markdown drafts (`CDR_PINN_Full_Paper_Draft.md`, `CDR_PINN_Methodology_Section.md`,
    `Complete_Methodology_Section.md`) were audited instead.
- **Dependency graph:** `audit/DATA_PROVENANCE.md` §2.
- **Environments:**
  - All CDR-PINO training uses `cdr_pinn_env` (torch 2.11 + CUDA 12.8), which is undocumented in CLAUDE.md.
  - The base env's torch is CPU-only.
  - The Step 6 kernelspec is `wildfire_env`, not `firerisk-anaconda3` as CLAUDE.md states.
- **Checkpoint provenance:** `cdr_pinn_full_cdr.pt` is **byte-identical** to
  `cdr_pinn_full_cdr_standard_protocol.pt`. The term-ablation's full-CDR checkpoint was overwritten,
  so the historical ablation row cannot be traced to a checkpoint (`final/FINAL_CHECKPOINT_MANIFEST.csv`).

## Step 2 — Biswas et al. reference audit (Phase 2)

`biswas_reference/BISWAS_REFERENCE_AUDIT.md` gives the 26-item specification with page citations,
and lists every item Biswas et al. do not report. Findings from their own text:

- **Train/test split:** the text says 70/30, but the counts (1,830/609) give 75/25.
- **Sample definition:** "10% of 2020 fires" does not match 2,439 presences.
- **Importance labels:** the group totals (33.9/26.1/10.8/9.7%) are **permutation importance**,
  although the paper labels them as contribution.

## Step 3 — Data provenance (Phase 0/1)

See `audit/DATA_PROVENANCE.md`. Undisclosed data gaps found:

- **NDVI:** 2007-03/04 have no pixel-reliability layer. Step 2 used them unfiltered; the CDR stack
  dropped them entirely.
- **LST:** two composites are incomplete (2001-06-26, 2016-02-18).
- **OSM:** the source data sits outside the project folder.

## Step 4 — Feature parity (Phases 3–6)

`biswas_reference/BISWAS_FEATURE_PARITY.csv`, `BISWAS_DATA_SOURCE_COMPARISON.csv`.

- **Parity:** all 15 Biswas variables are represented at the group level.
- **Variable form in v1:** the climate and LST variables enter only as degenerate anomaly-means plus
  MK trends, so the variable *levels* Biswas used are absent. v2 restores them as 2001–2020
  climatological levels.
- **Source differences:** five of the 15 come from different products: LST (MOD11A2 vs MOD11C3),
  NDVI (MOD13A3 vs MOD13C2), precipitation (FLDAS/CHIRPS vs GPM IMERG), and soil moisture and net LW
  (FLDAS vs GLDAS). The DEM and the distance algorithm are **not reported by Biswas et al.**
- **Humidity (Phase 6):** specific humidity (FLDAS Qair, the same source Biswas used) **is** a
  per-pixel predictor in v1 and v2. The gap document's claim that it is only a national scalar is
  incorrect, and its proposed "fix" would introduce an error. Derived relative humidity is an
  *additional* predictor.

## Step 5 — Numerical recalculation (Phase 1)

86 items; 60 reproduce exactly, and the remainder are explained. See
`audit/NUMERICAL_RECALCULATION_AUDIT.csv` and `audit/EQUATION_CODE_AUDIT.csv` (25 equation/code checks).

## Step 6 — Fire labels (Phase 11)

- **Reproduction:** the stage counts, the point set and the Biswas annual-count comparison
  (+0.5 to +2.4%, r = 0.99996) all reproduce.
- **Filter sensitivities:** confidence ≥ 30 changes AUC by −0.0003/−0.0005 (all/forest), type = 0 by
  +0.0000/+0.0002, and both by −0.0003/−0.0006. These are null results.
- **Rasterization defect:** the historical rule `round((lat − f)/e)` against the top edge displaces
  **405,723 / 541,545 points**, and the corrected label raises RF AUC by +0.0055 (all) and +0.0114
  (forest) on the same split. The rule is prescribed in CLAUDE.md and must be corrected there.
- **Boundary sensitivity:** point counts under the state, country and GADM polygons are in
  `recalculated/R1_fire_labels/R1_report.json`.
- **Forest cover:** the "national forest cover 9.86–10.43%" figure is computed over the download
  rectangle; for India alone it is **18.3–19.3%**.

## Step 7 — NDVI (Phase 12)

- **Reproduction:** F1, F2, F3, F4 and F7 are exact. F5 is identically about 0 (degenerate, since the
  seasonal component is not centred). F4 ≈ F1 (r = 0.99994).
- **k\* = 8** holds under historical, corrected and training-only labels (MI 0.01253 vs documented
  0.01257).
- **θ\*** = 0.5348 (historical), 0.5239 (corrected) and 0.5370 (training only).
- **Mann–Kendall** was run on the 2×12-MA trend series, whose lag-1 autocorrelation is 0.975, so the
  test is invalid. Seasonal Kendall with BH-FDR gives 3,552,278 greening / 72,305 browning pixels
  (historical 3,731,210 / 147,206). The direction is robust; the counts are not.
- **Moran's I:** the historical 0.8322 reproduces, but 67% of its cells are filled non-India cells.
  With India cells only (8×8 block means), I = 0.9456.
- **QA sensitivity:** Good-only vs Good+Marginal gives F1 correlation r = 0.989, but loses 39.7% of
  pixel-months (vs 8.2%).
- **NDVI ablation:** not run as a dedicated group ablation. NDVI is the top permutation-importance
  variable in the Biswas-15 models.

## Step 8 — LST (Phase 13)

- **Reproduction:** MK τ is exact. The anomaly means reproduce once the historical composite-weighted
  climatology is used (r = 1.000000).
- **Corrected trends:** Seasonal Kendall gives Day **cooling** (2,435,163 FDR-significant pixels;
  Sen −0.050 °C/yr), Night **warming** (2,080,747; +0.024 °C/yr) and DTR **narrowing** (3,273,301;
  −0.077 °C/yr). The directions match the historical text, but the historical counts understated the
  number of significant pixels by roughly 6.7× (day) to 117× (night).
- **MOD11A2 vs MOD11C3:** at 0.05°, 98.5–99.4% of the level variance is retained and model AUC
  changes by about 0. The product difference (8-day vs monthly CMG) remains a disclosed caveat.
- **DTR gap (Phase 14):** resolved with option A. The Seasonal-Kendall DTR trend is part of v2.

## Step 9 — Climate and land cover (Phases 15–16)

- **FLDAS:** all 14 historical features are exact.
- **Anomaly means:** the identity is proven for all 7 variables. The spatial std of each level is
  40–431× that of its anomaly mean.
- **Trends:** the "air-temperature trend is noise" conclusion reverses. Under Seasonal Kendall,
  9,988/29,056 pixels are FDR-significant.
- **Land cover:** the 2020 fractions are exact, and the 2001 fractions were built for v2.
- **Leakage mechanism:** forest change 2001→2020 is +0.019 at fire pixels vs +0.018 at non-fire
  forest pixels, so the post-fire reclassification signal is weak.
- **Temporal mismatch:** static land cover vs dynamic climate is a temporal-resolution mismatch,
  documented as such. It is not leakage.

## Step 10 — Terrain and accessibility (Phase 17)

- **Reproduction:** terrain and all three distances match (r ≥ 0.9986 for aspect, which is
  wrap-limited; 0.99999 or better for the rest).
- **Slope algorithm:** Horn vs Zevenbergen–Thorne gives r = 0.9998 and ΔAUC 0.0000.
- **Slope scale:** a 0.25° DEM gives slopes about 20× smaller (mean 0.29° vs 5.72°, r = 0.70), so Biswas's "slope" is a different quantity.
- **Distance accuracy:** against exact geodesic distances (n = 3,000), the biases are −0.15, −0.22 and
  −0.14 km (RMSE 0.31/0.65/0.32 km), uniform across latitude.
- **The −46.9 m minimum** is at the Neyveli open-cast lignite mines, most likely a real excavation surface.

## Step 11 — Common grid (Phase 18)

- **Grid:** EPSG:4326, 3,641 × 3,504, **1/120° (not 0.01°)**.
- **Pixels:** 4,184,671 India-mask pixels, 4,161,009 NDVI-valid; the analysis population is 4,160,768.
- **Features:** 57 in v1 (not 55) and 55 in v2.
- **CDR-PINO grid:** 256 × 256, about 12 km, with 22,542 valid cells and 266 months.

## Step 12 — Leakage (Phase 19)

| Item | Status |
|---|---|
| `forest_frac_recent/current`, forest loss (removed 2026-08-21) | verified absent from v1 |
| 22 land-cover fractions from the **2020** map | present in v1; replaced by 2001 in v2; measured effect small |
| θ\* indicator and CVSI k\* chosen with labels | ΔAUC 0.0000; k\* unchanged with training-only labels |
| Median imputation fitted on all rows (v1) | v2 fits on training rows |
| B3 terminal label pooled over held-out years | effect +0.0006; fixed in unified runs |
| Transductive covariates (FNO sees test cells' covariates; dryness z-scored over all months) | disclosed; covariates only, no labels |
| Forest-definitional coupling (non-forest pixels are never positive) | not leakage, but it dominates all-pixel AUC → forest population is primary |

## Step 13 — Feature stack (Phase 18/52)

See `recalculated/FEATURE_TABLE_v2.parquet`, `recalculated/FEATURE_SETS.json` and
`final/FINAL_FEATURE_DICTIONARY.csv`.

## Step 14 — Biswas-style baseline (Phase 9)

`biswas_reference/BISWAS_STYLE_BASELINE.json`: a **reimplementation, not Biswas's result**.

- **Protocol:** 0.25° grid, 4,630 cells, 1,292 unique cells with 2020 forest fires (their 2,439 is
  unexplained). MaxEnt L+Q+H+P with β = 1 and 10 random 75/25 presence splits.
- **Performance:** test AUC **0.893 ± 0.009** (range 0.877–0.912), train 0.902. Biswas reported 0.879 / 0.894.
- **Permutation importance:** NDVI 19.0% (their 22.3), LST night 14.3 (10.1), air temperature 13.2
  (13.1), elevation 10.7 (2.4), LST day 8.1 (9.6), slope 5.8 (5.6), specific humidity 3.1 (13.0).
- **Fig. 11 correlations:** NDVI 0.456 (their 0.43) and wind −0.363 (−0.32) agree; slope 0.223 (0.40)
  is weaker; soil moisture 0.389 and net LW 0.361 (0.27/0.28) differ, consistent with the different
  source models.

## Step 15 — RF / MaxEnt (Phase 20)

**Track A** (v2 split 65/15/20, test touched once):

| Model | All India AUC / AP | Forest AUC / AP |
|---|---|---|
| RF v2 | **0.9750** / 0.720 | **0.8971** / 0.721 |
| MaxEnt v2 | 0.9670 / 0.663 | 0.8657 / 0.664 |

Prevalence is 6.45% (all) and 22.4% (forest). Confidence intervals, calibration and threshold metrics
are in `baseline/CLASSICAL_METRICS.csv` and `final/FINAL_METRICS.csv`.

**B1** (CDR fold geometry at 1 km):

| Model | All India AUC | Forest AUC |
|---|---|---|
| RF v2 | 0.959 | 0.838 |
| RF Biswas-15 | 0.946 | 0.808 |
| MaxEnt v2 | 0.956 | 0.828 |

**B2:** RF v2 0.935 (all) / 0.782 (forest).

**Historical GroupKFold** spatial CV reproduces exactly (0.9459 / 0.9527 / 0.9508).

## Step 16 — MaxEnt sample size (Phase 21)

| Training rows | AUC, all / forest | Fit time |
|---|---|---|
| 50k | 0.9640 / 0.855 | 150 s |
| 100k | 0.9663 / 0.863 | 510 s |
| 150k | 0.9672 / 0.867 | 1,130 s |
| 300k | 0.9680 / 0.870 | 3,411 s |
| 500k | 0.9685 / 0.872 | 7,303 s |

- **Stability:** seed SD ≤ 0.0004.
- **Scaling:** fit time grows as about n^1.6, so 1M rows (about 5–6 h) and the full 2.7M were not run.
- **Conclusion:** the RF–MaxEnt gap is not a subsampling artefact. The size was not selected on AUC;
  150k is kept for comparability.

## Steps 17–19 — CDR-PINO mathematics, architecture, training and checkpoints (Phases 23–28)

- **Implemented residual:** `r = (u_{t+1} − u_t) − D∇²u_mid + v·∇u_mid − ρσ(u_mid)(1 − σ(u_mid))`.
  Signs match the manuscript, but the diffusion is non-conservative.
- **Discrepancies between the text and the code:**
  - The "Fisher–KPP" label is mathematically incorrect: the reaction acts on the logit.
  - The loss-weight formula in the text differs from the code.
  - The text describes "size-matched negative sampling", which does not exist in the code.
  - The BC term penalises |∇u|², not ∂u/∂n.
  - The IC loss is identically 0.

  See `audit/EQUATION_CODE_AUDIT.csv` E14–E25.
- **Architecture:** as documented, 1,054,613 parameters.
- **Track A vs B1/B2/B3:** these are **separate models trained under different protocols**, not one
  checkpoint. The unified runner therefore applies one protocol (AdamW, validated WD = 0,
  ReduceLROnPlateau, early stopping on validation AUC) to every track, with 3 seeds and
  block-carved validation for spatial tracks.

## Steps 20–23 — Validation tracks, multi-seed and physics ablation (Phases 27, 29, 30)

`final/ABLATION_RESULTS.csv`, `final/SEED_LEVEL_RESULTS.csv`, `ablation/PAIRED_physics_vs_nophys.csv`.
Mean of 3 seeds, all 12 km cells:

| Track | No physics | Diffusion | Diff + adv | Full CDR | Full − no physics (paired) |
|---|---|---|---|---|---|
| A (random) | **0.9450** | 0.9242 | 0.9394 | 0.9388 | −0.005 / −0.007 / −0.006 (DeLong p < 0.02, every seed) |
| B1 (spatial blocks) | 0.7235 | 0.6421 | **0.7298** | 0.7185 | block-bootstrap CIs include 0 (all seeds) |
| B2 (regions) | **0.6144** | — | — | 0.5701 | CIs include 0 (p ≈ 0.06–0.87) |
| B3 (unseen years, leak-free) | **0.9044** | 0.8855 | 0.8941 | 0.8934 | −0.010 / −0.009 / −0.014 (replicated) |
| B3, original leaky label | 0.9045 | — | — | 0.8941 | leakage effect +0.0006 |

- **Forest-cell AUCs** follow the same ordering (Track A: 0.910 without physics vs 0.898 full).
- **Cost:** physics raises training time by 2.3–2.4×.
- **Physical consistency** (`cdr_pino/term_magnitudes_*.json`):
  - Every trained configuration yields an **effectively static field** (median |∂u/∂t| ≤ 0.002 per month).
  - None satisfies the full CDR equation (RMS residual 74–616 × |∂u/∂t|).
  - Diffusion is ≤ 0.3% of the RHS magnitude.

## Step 24 — Contribution decomposition (Phases 10, 31)

`final/CONTRIBUTION_DECOMPOSITION.csv`. Paired ΔAUC is given as all / forest pixels.

| Source of difference | Effect |
|---|---|
| Model family: RF − MaxEnt (Biswas-15 predictors) | +0.025 / +0.067 |
| Model family: RF − MaxEnt (v2 predictors) | +0.008 / +0.031 |
| Added predictors and engineering: v2 − Biswas-15 (RF) | +0.005 / +0.012 |
| Added predictors: v2 − Biswas-15 (MaxEnt) | +0.022 / +0.048 |
| Predictor restriction: v2 − CDR's 5 static covariates (RF) | +0.017 / +0.071 |
| Trend group (Seasonal Kendall/Sen) | +0.001 / +0.006 |
| Land-cover group | +0.003 / +0.008 |
| Terrain group | −0.0001 / −0.0006 (redundant) |
| Physics terms in CDR-PINO (full − no physics) | −0.006 (A), CI incl. 0 (B1/B2), −0.011 (B3) |
| Model structure: full CDR-PINO − RF, same cells and covariates | −0.041 (A) |

**Attribution:** accuracy differences come from the model family and the predictor set, not
from physics or the operator structure.

## Step 25 — Quantitative comparison with Biswas (Phases 7, 8, 37–39)

See `BISWAS_VS_CURRENT_COMPARISON.md`, `biswas_reference/BISWAS_RESULT_COMPARISON.csv` and
`audit/BISWAS_CLAIM_AUDIT.csv` (12 claims): 2 supported (one of them as a methodological
extension), 3 partially supported, 5 not supported, 2 not directly comparable.

## Step 26 — Sensitivity (Phase 41)

`final/SENSITIVITY_RESULTS.csv`:

- **Null results:** FIRMS confidence and type filters, the NDVI QA level, LST resolution (0.05°),
  the slope algorithm, slope from a 0.25° DEM, and the B3 label leakage.
- **MaxEnt sample size:** a small, monotone effect.
- **Not tested:** CDR loss weights and spectral modes (historical scale-up only), and alternative
  climate sources.
- **Not testable:** resolution independence and zero-shot super-resolution (Phases 42–43) → future
  work. Instance-wise fine-tuning (Phase 44) is not implemented → future work.

## Step 27 — Interpretability (Phases 36–37)

`baseline/importance__trackA__*.json` contains permutation importance per feature and per group, plus
partial-dependence curves. SHAP was **not computed**: the `shap` package fails to import (its numba
build needs NumPy ≤ 2.0; the env has 2.5).

- **RF v2:** forest fraction ≫ NDVI > LST day > NDVI June > wind.
- **MaxEnt v2:** forest fraction ≫ air temperature > elevation > NDVI > specific humidity.
- **Biswas-15 MaxEnt:** NDVI ≫ LST night > LST day > elevation > specific humidity.

This last ordering is closest to Biswas's; the ranking differences are largely a **model-family**
effect. The historical claim of CDR-PINO "elevation dominance" is specific to its 7-covariate model:
with the full predictor set, removing terrain changes AUC by −0.0001.

## Step 28 — Final map (Phase 46)

- **Historical maps** (`Integrated_Analysis/Model_Outputs/*.tif`): EPSG:4326, 1/120°, NaN nodata,
  4,161,009 pixels, with no metadata tags.
  - The RF map is **not a calibrated probability**: mean 0.135 vs prevalence 0.065.
  - The MaxEnt map is a cloglog relative suitability.
  - CDR-PINO has only a PNG map.
- **New maps:** `final/maps/Susceptibility_RF_v2_score.tif` and `…_5class_quantile.tif` (breaks
  0.043/0.210/0.582/0.893 over forest pixels), with provenance tags stating "relative score, not a
  calibrated probability".
- **Uncertainty (Phase 45):** Brier and ECE are reported (RF v2 ECE 0.064 all / 0.219 forest;
  MaxEnt v2 0.015 / 0.054). **No calibrated uncertainty estimate was established.**

## Step 29 — Manuscript numbers (Phases 47–48)

`audit/MANUSCRIPT_NUMBER_AUDIT.csv` (55 numbers; see `FINAL_MANUSCRIPT_NUMBERS.md` for replacements)
and `audit/BISWAS_CLAIM_AUDIT.csv`.

## Step 30 — Figures and tables (Phase 49)

`final/figures/FigA`–`FigH` are regenerated from result files, with the plotted data in
`final/FIGURE_DATA/`. No figure mixes grids, populations or metrics on one axis. The tables are in
`final/` and `final/TABLE_DATA/`.

## Step 31 — Reproducibility

See `REPRODUCIBILITY_REPORT.md`.

## Step 32 — Final scientific quality control (Phase 57)

| # | Question | Answer |
|---|---|---|
| 1 | Every number recalculated? | Yes, with three stated exceptions: MCD64A1 burned area (correlations recomputed from saved series; raw not re-extracted), the historical Jackknife (not re-run), and fire-coincidence anomaly statistics (N32) |
| 2 | Every equation verified? | Yes: 25 checks in EQUATION_CODE_AUDIT.csv; 11 partial or non-matching, all documented |
| 3 | Every feature traceable? | Yes (FINAL_FEATURE_DICTIONARY.csv) |
| 4 | Every data source verified? | Yes; the OSM location outside the project is flagged |
| 5 | Every Biswas comparison verified? | Yes (PDF-verified, with page numbers) |
| 6 | 15/15 parity achieved? | At group level yes; in variable form only in v2 |
| 7 | Differences from Biswas documented? | Yes |
| 8 | LST product difference documented? | Yes, and its resolution effect was tested |
| 9 | Precipitation-source difference documented? | Yes |
| 10 | Humidity correctly described? | Yes: specific humidity is per-pixel, RH is additional; the gap document was wrong |
| 11 | Feature count verified? | v1 57, v2 55 |
| 12 | Any leakage? | v1 had four sources, all quantified (small); v2 removes them. Forest-definitional coupling is handled with the forest population |
| 13 | Fire labels defensible? | Yes, after the rasterization fix; the filters are immaterial |
| 14 | MaxEnt comparison fair? | Yes, with the sample-size sensitivity; same split and features as RF |
| 15 | Comparable populations? | Yes: 1 km classical models on identical pixels; CDR-PINO vs classical on identical 12 km cells (bridge) |
| 16 | CDR-PINO mathematically identical to the code? | The equation signs are; five text details are not (E15, E19–E22) |
| 17 | Checkpoints consistent? | No historically (different protocols; one overwritten); fixed in the unified runs |
| 18–21 | Ablation, spatial, temporal and regional results reproducible? | The historical ones reproduce bit-exactly; the unified ones have 3 seeds each |
| 22 | Biswas comparisons valid? | Only as labelled in BISWAS_CLAIM_AUDIT.csv |
| 23 | Manuscript numbers correct? | No: see MANUSCRIPT_NUMBER_AUDIT.csv for 20+ required changes |
| 24 | Figures regenerated? | Yes (8 audit figures); the manuscript's own figures have not been redrawn |
| 25 | Can another researcher reproduce this? | Yes, given the raw data; the full run order is in REPRODUCIBILITY_REPORT.md |
