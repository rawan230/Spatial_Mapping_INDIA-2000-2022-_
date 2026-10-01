# Full Methodology of the Current (Audited, v2) Study

**Title:** *Does a Governing Equation Help? A Controlled Evaluation of a Convection-Diffusion-Reaction Physics-Informed Neural Operator for Forest Fire Susceptibility Mapping in India*

**Written:** 2026-10-01. **Companion file:** `CURRENT_STUDY_STEPWISE_DOCUMENTATION.md` (old-vs-new table and results). This file is the *methods* reference: what was done, in what order, with which parameters, and why.

**Sources (all verified against files in this repository):** `results/FULL_METHODOLOGY_AUDIT.md`, `results/METHODOLOGY_CHANGELOG.md`, `results/FINAL_MANUSCRIPT_NUMBERS.md`, `results/final/FINAL_MODEL_CONFIGURATION.json`, `Manuscript_TGRS/main.tex`, and the code in `Physics_Informed_FireRisk_Model/cdr_pinn/` (`build_monthly_stacks.py`, `preprocessing.py`, `losses.py`, `run_unified_protocol.py`, `eval_utils.py`).

---

## 1. Study design in one page

**Question.** Does embedding a convection-diffusion-reaction (CDR) equation in a neural operator improve forest-fire susceptibility mapping for India, once everything else is held fixed?

**Design logic.** Three controls are added to the physics model, so any gain or loss can be attributed:

| Control | What it isolates |
|---|---|
| The *same network without the equation* | the effect of the physics terms |
| Classical models (RF, MaxEnt, logistic regression) on the *operator's own cells, partitions and covariates* | the effect of the model family |
| Baselines using *no covariates* (persistence) | whether temporal skill is real |

**Two model branches, two grids** (they are not interchangeable):

| Branch | Models | Grid | Purpose |
|---|---|---|---|
| Classical | RF, MaxEnt, LogReg | 1/120° (~0.93 km), 3,641 × 3,504 | best-performing national susceptibility map; 55 predictors |
| Operator | CDR-PINO (4 physics configs) | 256 × 256 (~12 km), 22,542 valid cells, 266 months | the physics test; 7 covariates |

A third small branch reimplements the reference study (Biswas et al., 2025) at 0.25° to place the work in context.

**Why the audit changed the method.** Before 2026-09-24 the pipeline had defects (half-pixel fire labels, degenerate anomaly features, invalid Mann–Kendall use, in-window land cover, mismatched evaluation protocols). The v2 pipeline described here corrects them. None of the corrections changed any AUC by more than 0.012, so the conclusions do not hinge on them, but the descriptive statistics that relied on the old choices were invalid.

---

## 2. Study area, period and common grid

- **Domain:** India, using the dissolved state-boundary polygon (`India_State_Boundary.shp`). The country-boundary file has ~60 degenerate sliver polygons near the Palk Strait and is not used. The shapefile ships without a usable CRS; raw coordinates are EPSG:3857 (Web Mercator, metres), set explicitly and reprojected to EPSG:4326.
- **Period:** 2000-11-01 to 2022-12-15 → **266 monthly steps**. Capped at 2022 because ESA-CCI/C3S land cover does not exist beyond it. Every step must use this exact window so `(year, month)` joins align.
- **Common grid:** EPSG:4326, **3,641 × 3,504 cells at 1/120° (~0.93 km)** (not 0.01°). It is established by the NDVI product and every other raster is reprojected onto it.
- **Populations:**
  - India-mask cells: 4,184,671; NDVI-valid cells: 4,161,009.
  - **Analysis population: 4,160,768 cells.**
  - **Forest population:** cells with 2001 forest fraction > 0 → **1,197,538 cells**.
  - Forest cover inside India is 18.3–19.3 % (the older "~10 %" figure was computed over the download rectangle and must not be cited).

---

## 3. Fire observations and the label

### 3.1 Extraction (Step 1)
1. Source: MODIS Collection 6.1 FIRMS archive.
2. Clip to bounding box, then to the exact India polygon.
3. Remove duplicates by location and date.
4. Keep only detections that fall on a **forest class of the same year's land-cover map** (13 forest codes, ESA-CCI/C3S).
5. Record counts: 2,804,373 → 2,801,347 → 1,599,471 → 1,599,466 → **541,545 forest fire points**.

### 3.2 Filters examined, not applied
Confidence < 30 (4.29 % of points) and type ≠ 0 (0.21 %) were *kept*, because excluding them changes RF AUC by less than 0.001 (−0.0003/−0.0005 for confidence; +0.0000/+0.0002 for type; all/forest).

### 3.3 External validation of the points
Annual counts versus those implied by the published shares in Biswas et al.: +0.5 % to +2.4 % higher, r = 0.99996 (2001–2020). Forest-masked MODIS MCD64A1 burned area versus annual fire counts: Pearson r ≈ 0.93 (recomputed from saved series; raw burned-area rasters were not re-extracted).

### 3.4 Rasterisation (the key correction)
Each point is assigned to the pixel that **contains** it:

`col = floor((lon − x0)/Δx)`, `row = floor((lat − y0)/Δy)` with (x0, y0) the **outer pixel edge** and Δy < 0.

The historical `round()` rule measured against the edge (not the pixel centre) and displaced **405,723 of 541,545 points (74.9 %)** by one pixel. The same containing-pixel rule is used in the 12 km operator grid; points outside the grid are dropped, not clipped onto edge cells. `round` is correct only when reference coordinates are pixel centres (e.g. the LCCS NetCDF lat/lon arrays in the forest filter).

### 3.5 Label definition
- **1 km classical label:** a cell is positive if it contains ≥ 1 forest fire point in the whole period → **268,411 positive cells**; prevalence **6.45 % (all cells)**, **22.4 % (forest cells)**.
- **12 km operator labels:** (a) a binary **monthly fire indicator** per cell-month; (b) a "ever burned" terminal label (`fire_ever_frac`, positive if > 0). Track-A cell prevalence is 42 %; B3 cell-month prevalence is 2.46 %.
- **Effect of the correction:** RF AUC +0.0055 (all) and +0.0114 (forest) on the same split.

---

## 4. Predictor engineering (55 features, 1 km)

### 4.1 Group summary

| Group | n | Source | Features |
|---|---|---|---|
| Vegetation | 6 | MOD13A3.061, 1 km monthly | QA-masked mean NDVI; climatological June NDVI; Seasonal Kendall τ; seasonal Sen slope; CVSI at k\* = 8; LISA cluster class |
| Surface temperature | 6 | MOD11A2.061, 1 km 8-day | 2001–2020 climatological level + Seasonal Kendall τ of day LST, night LST, DTR |
| Climate | 14 | FLDAS Noah, 0.1° monthly | level + Seasonal Kendall τ of air temperature, specific humidity, relative humidity (derived), wind, precipitation, net longwave radiation, soil moisture |
| Terrain | 4 | SRTMGL3 90 m | elevation, Horn slope, sin(aspect), cos(aspect) |
| Accessibility | 3 | OSM 2022 (Geofabrik) | distance to roads, railways, waterways |
| Land cover | 22 | ESA-CCI/C3S 2001 | 21 class fractions + forest fraction |
| **Total** | **55** | | |

All 15 variable groups of Biswas et al. are represented. The v1 stack had 57 features; v2 has 55.

### 4.2 Vegetation (NDVI) – details
- QA filter: Good + Marginal pixel reliability. For 2007-03/04, where the reliability layer is missing, the VI_Quality MODLAND bits (bits 0–1 in {0,1} and bit 14 "possible snow/ice" = 0) reproduce the reliability mask exactly (100 % pixel agreement on a month where both exist).
- **CVSI** lag k\* = 8, selected by mutual information against *training* labels only (MI 0.01253; identical under historical, corrected and training-only labels).
- **Trend:** Seasonal Kendall (tie-corrected, ≥ 30 comparable pairs) + seasonal Sen slope + Benjamini–Hochberg FDR at q < 0.05.
- **Spatial statistics:** global Moran's I and LISA on **8 × 8 block means restricted to India cells**, 999 permutations (Moran's I = 0.9456, z = 494.2, p = 0.001).
- **Dropped:** anomaly mean (degenerate), residual mean (≈ 0), F4 (≈ F1, r = 0.99994), and the θ\* breakpoint indicator (redundant step function of mean NDVI).

### 4.3 Surface temperature, climate
- Climatological level = mean over **2001–2020**. The historical "anomaly mean" against that baseline equals the residue of the 26 months outside the baseline divided by n, so it carries almost no spatial information (the spatial SD of each level is 40–431 × that of its anomaly mean).
- Trend = Seasonal Kendall τ (Mann–Kendall is invalid on seasonal series).
- FLDAS provides specific humidity per pixel (same source as Biswas et al.); relative humidity is derived and added.
- Product differences versus Biswas et al., disclosed: LST (MOD11A2 vs MOD11C3), NDVI (MOD13A3 vs MOD13C2), precipitation (FLDAS/CHIRPS vs GPM IMERG), soil moisture and net LW (FLDAS vs GLDAS). Their DEM and distance algorithm are unreported.

### 4.4 Land cover
22-class ESA-CCI/C3S Level-1 LCCS legend. Fractions come from the **2001 map**, which precedes almost the whole label window. The 2020 map used in v1 lay inside it. The measured post-fire-reclassification mechanism is weak (forest change 2001→2020: +0.019 at fire pixels versus +0.018 at non-fire forest pixels). The static land cover against dynamic climate is a temporal-resolution mismatch, documented but not leakage.

### 4.5 Terrain and accessibility
- Slope by Horn's method (GPU). Aspect expanded to sin/cos because degrees have a 0/360 discontinuity.
- Distances by a GPU Euclidean distance transform on rasterised OSM roads, railways and waterways. Validated against exact geodesic distances at 3,000 random points: bias −0.15 / −0.22 / −0.14 km, RMSE **0.31 / 0.65 / 0.32 km**.
- A −46.9 m minimum elevation is at the Neyveli open-cast lignite mines (likely a real excavation).

### 4.6 Assembly (Step 6) and leakage controls
Output: `results/recalculated/FEATURE_TABLE_v2.parquet` (4,160,768 × 60 columns, 55 features).

| Leakage item | v2 treatment |
|---|---|
| `forest_frac_recent/current`, forest-loss feature | absent (removed 2026-08-21) |
| 2020 land-cover fractions | replaced by 2001 |
| Label-fitted θ\* and CVSI lag | θ\* dropped; k\* re-selected on training labels (= 8) |
| Median imputation | fitted on **training rows only** |
| B3 terminal label | rebuilt from training months only |
| Transductive covariates in the operator (it sees test cells' covariates; dryness z-scored over all months) | disclosed; covariates only, never labels |
| Forest-definitional coupling (non-forest cells can never be positive) | not leakage, but inflates all-pixel AUC → **forest cells are the primary population** |

---

## 5. Classical susceptibility models (1 km)

### 5.1 Models and hyperparameters
- **Random Forest:** 200 trees, `max_depth` 25, `min_samples_leaf` 3, `class_weight='balanced'`, `max_features='sqrt'`, `random_state` 42. Depth/leaf were chosen on a validation split (beat the literature default 20/5).
- **MaxEnt** (elapid 1.0.4): linear + hinge + product features, `beta_multiplier` 4.0 (selected from {0.5, 1, 1.5, 2.5, 4} on validation AUC; the grid was essentially flat, val AUC 0.9589–0.9592), class weight 100, cloglog output, **150,000 training rows** (sensitivity 50k–500k reported).
- **Logistic regression** (used in the same-cell comparison).
- Variants: each learner also fitted on the 15 Biswas-equivalent predictors (levels) and on CDR's 5 static covariates, to separate predictor-set effects from model-family effects.

### 5.2 Splits (all produce test sets touched once)
| Track | Construction |
|---|---|
| A | stratified **65/15/20** train/val/test by the corrected label, `random_state` 42 |
| B1 | 2° × 2° blocks, 3 folds, using the CDR-PINO block permutation (origin 68.2°E/6.75°N, seed 42); validation carved as whole blocks from the training region |
| B2 | 6 k-means regions on 12 km valid cells, one held out at a time; 1 km pixels assigned by nearest centroid |
| B3 | held-out years 2000, 2008, 2009, 2015 (validation 2001, 2012, 2013, 2020); scored per cell-month |

Decision thresholds are chosen by maximum F1 on validation. Imputation uses training rows only.

### 5.3 Metrics
ROC-AUC, average precision, Brier score, expected calibration error (10 bins), sensitivity/specificity/precision/F1 at the validation threshold, and stratified-bootstrap CIs. **Every metric is reported for all cells and for forest cells, with the prevalence and grid stated beside each AUC.**

### 5.4 Interpretability
Permutation importance (per feature and per group) and partial dependence on the Track-A models. SHAP was not computed (the `shap` package fails to import against the installed NumPy).

---

## 6. The CDR-PINO operator (12 km)

### 6.1 Input stack (`build_monthly_stacks.py`)
- Target grid: **256 × 256**, lon 68.20–97.40, lat 6.75–37.09, EPSG:4326, built by `Resampling.average` (continuous-field aggregation, not block decimation).
- 266 monthly steps. Valid cells = those with NDVI (22,542). NaNs in covariates are set to 0 (≈ 0.38 % of valid cells lack DEM; a few lack FLDAS), covariates are not otherwise standardised.
- **Seven covariates** (channel order is fixed): mean NDVI, monthly NDVI anomaly, forest fraction (2001), monthly **dryness**, slope, distance to roads, elevation. Plus the state u_t as the 8th channel. Elevation gradients (∂E/∂x, ∂E/∂y) feed the advection head.
- **Dryness proxy:** (z[air-temp anomaly] − z[relative-humidity anomaly] − z[surface soil-moisture anomaly] − z[precipitation anomaly]) / 4, with FLDAS monthly anomalies against the 2001–2020 monthly climatology, each z-scored over the whole stack. This normalisation is transductive but label-free (disclosed).
- Monthly precipitation uses the exact number of days per month.
- **Provenance note:** the published audit numbers used the stack built *before* three minor fixes (2007-03/04 NDVI handling, exact-day precipitation, native-transform indexing; e.g. 9,170 vs 9,161 ever-burned cells). Rebuilding it would require re-running all CDR-PINO results; to reproduce the published numbers use the original stack (SHA-256 `ea7828a5…a85d`).

### 6.2 Governing equation
Latent logit field u(x,t), susceptibility s = σ(u):

∂u/∂t = D(x,t) ∇²u − v(x)·∇u + ρ(x,t) σ(u)(1 − σ(u)),  u(x,0) = 0,  ∂u/∂n = 0 on ∂Ω.

| Term | Definition | Physical role |
|---|---|---|
| Diffusion D | softplus( f_D(NDVI, forest fraction) − softplus(w)·NDVI′ ), f_D = MLP 2-12-12-1 (tanh) | biophysical/climatic spread |
| Advection v | softplus(c)·∇E, c scalar | upslope (topographic) transport |
| Reaction ρ | softplus( f_ρ(dryness Q, NDVI, slope S, road distance R) ), f_ρ = MLP 4-12-12-1 (tanh) | ignition pressure / human activity |

Honest caveats: the reaction acts on the logit, so in s it is ds/dt = ρ s²(1−s)²; it is **not** Fisher–KPP. The proven properties (bounded coefficients, uniform parabolicity, Gårding inequality, Lipschitz reaction → global existence and uniqueness) concern the *equation*, not the trained network.

### 6.3 Architecture (1,054,613 parameters)
FNO2d: pointwise lift 8 → 32; four Fourier layers, each `GELU( irFFT2( R_ℓ · rFFT2(z) ) + W_ℓ z )` with complex weights R_ℓ on the lowest **16 × 16** modes and a 1×1 skip W_ℓ; projection 32 → 32 → 1 with GELU in between. One forward pass maps (u_t, a_t) → u_{t+1}; the model is rolled out month by month from u_0 = 0.

### 6.4 Residual and derivatives
Residual with a one-month forward difference and midpoint ū = (u_t + u_{t+1})/2:

`r = (u_{t+1} − u_t) − D ∇²ū + v·∇ū − ρ σ(ū)(1 − σ(ū))`

Spatial derivatives use **spherical spectral operators** on a whole-sample-symmetric (Neumann) extension of the grid. The diffusion form is non-conservative. The four physics configurations differ only in which terms enter the residual.

### 6.5 Loss
`L = Σ_k w_k L_k` over data, PDE, BC and IC:
- **Data:** class-weighted BCE on all training cells of each month, `pos_weight = (1−p)/p` (p = training positive rate, ≈ 2.3 % monthly). *No size-matched negative sampling exists in the code.* The last window adds a 0.5/0.5 mix with a **log-sum-exp-pooled (τ = 5) terminal BCE** against the "ever burned" label.
- **PDE:** mean r² over valid cells.
- **BC:** mean |∇u|² on the 1-cell boundary ring (1,253 cells) – a proxy that also penalises the tangential derivative, stricter than ∂u/∂n = 0.
- **IC:** identically 0, because u_0 = 0 is imposed exactly.
- **Adaptive weights:** every 5 windows, `w_k ← 0.9 w_k + 0.1 · mean_norm / norm_k` (gradient-norm balancing).
- **No-physics configuration:** data + IC only.

### 6.6 Training protocol (identical for every track and configuration)
- Optimiser AdamW, lr 1e-3, **weight decay 0** (the validated winner of a weight-decay search).
- `ReduceLROnPlateau` on validation loss (factor 0.5, patience 2 checks).
- Up to **80 epochs**; validation AUC checked every 5 epochs; **early stopping with patience 4 checks**; best checkpoint restored.
- Truncated backpropagation over **24-month windows**, state detached between windows.
- Seeds **42, 43, 44** vary only initialisation and training noise; fold, region and year assignments are fixed (`SPLIT_SEED` 42).
- Hardware/software: `cdr_pinn_env`, torch 2.11.0+cu128, NVIDIA RTX PRO 4500 (Blackwell). **102 runs** in total. Every run saves test predictions and its checkpoint.

### 6.7 Why the protocol was unified
Historically, Track A and B1/B2/B3 were separately trained models with different optimisers, schedules, budgets and validation schemes, B1/B2 validation was random pixels (in-distribution), single seeds were used, and the ablation's full-CDR checkpoint was overwritten. The unified runner fixes all of these. Effect on the numbers: B1 0.7510 → 0.7185 and B2 0.6187 → 0.5701 for the full model.

---

## 7. Controlled evaluation design

### 7.1 Physics configurations
none (data + IC) | D (diffusion) | D + A (+ advection) | D + A + R (full CDR). Same network, data, budget and protocol; 4 configurations × 4 tracks × 3 seeds (B2 only for none and full).

### 7.2 Evaluation tracks for the operator (12 km)
| Track | Held-out unit | Notes |
|---|---|---|
| A | random cells (65/15/20) | cell-level, prevalence 42 % |
| B1 | 2° blocks, 3 folds | block-carved validation |
| B2 | 6 k-means regions | one region at a time |
| B3 | years 2000/2008/2009/2015 | cell-month scoring; terminal label from training months only; the leaky original ("B3orig") re-run for comparison only (effect +0.0006) |

### 7.3 Same-cell controls ("bridge")
RF, MaxEnt and LogReg are fitted on the operator's **own 12 km cells, partitions and 7 covariates**. A second set uses 12 km aggregates of all 55 predictors. For B3 two covariate-free baselines are scored: (i) each cell's fire frequency over the training years, (ii) its frequency in the same calendar month. A random forest on monthly covariates, with and without the month as an input, is also reported.

### 7.4 Statistics
- **DeLong** paired test on identical test units (tracks A and B3).
- **Spatial block bootstrap** for paired differences on B1/B2 (123 blocks, 300 resamples) because test cells are spatially clustered.
- Stratified bootstrap CIs for single AUC/AP values.
- Brier score and ECE for calibration.

### 7.5 Physical-consistency diagnostic (RQ4)
For trained Track-A seed-42 checkpoints of every configuration, over all valid cells and months: median |∂u/∂t|; mean magnitude of each right-hand-side term (as a share of their sum); and RMS residual divided by mean |∂u/∂t|. A field that solves its equation should have a residual small relative to its own rate of change *and* a clearly non-zero rate of change, since fire in India is strongly seasonal.

---

## 8. Reference-study reimplementation (Biswas et al., 2025)

- 0.25° grid, 4,630 cells, 15 predictors as levels, presences = cells with 2020 forest fires (**1,292**; their 2,439 is unexplained), MaxEnt with linear + quadratic + hinge + product features, β = 1, background = all valid cells (< 10,000), **10 random 75/25 presence splits**.
- The paper's text says 70/30, but its counts (1,830 train / 609 test) imply 75/25.
- Result: test AUC 0.893 ± 0.009 (0.877–0.912), train 0.902 ± 0.003 (reported by them: 0.879 / 0.894). This is a *reimplementation*, not their result, and comparability is "moderate".
- Their group totals (33.9/26.1/10.8/9.7 %) are permutation importances though labelled contributions.

---

## 9. National susceptibility map

- RF v2 (55 features) score on the 1/120° grid (`results/final/maps/Susceptibility_RF_v2_score.tif`), plus a 5-class map by **quantile breaks over forest cells: 0.043 / 0.210 / 0.582 / 0.893**.
- GeoTIFF tags state "relative score, not a calibrated probability" (mean 0.135 vs prevalence 0.065). No calibrated uncertainty was established.

---

## 10. Sensitivity analyses

| Analysis | Outcome |
|---|---|
| FIRMS confidence / type filters | null (|ΔAUC| ≤ 0.0006) |
| NDVI QA level (Good vs Good+Marginal) | F1 r = 0.989; Good-only loses 39.7 % of pixel-months |
| LST at 0.05° (MOD11C3-like) | 98.5–99.4 % variance retained; ΔAUC ≈ 0 |
| Slope algorithm (Horn vs Zevenbergen–Thorne) | r = 0.9998; ΔAUC 0.0000 |
| Slope from 0.25° DEM | ~20× smaller, r = 0.70 (different quantity) |
| B3 terminal-label leakage | +0.0006 |
| MaxEnt training rows 50k–500k | small monotone effect (+0.0015 / +0.006 at 500k); SD ≤ 0.0004 |
| Not tested | CDR loss weights/modes beyond weight decay; alternative climate sources |
| Not done | resolution independence, zero-shot super-resolution, instance-wise fine-tuning |

---

## 11. Methodological corrections v1 → v2 (changelog summary)

| # | Component | v1 → v2 | Measured effect |
|---|---|---|---|
| 1 | Fire rasterisation | `round` against edge → containing-pixel `floor` | RF +0.0055 / +0.0114 |
| 2 | Anomaly-mean features | dropped → climatological levels | −0.0004 / −0.001 (whole set) |
| 3 | Trend test | Mann–Kendall → Seasonal Kendall (+ Sen, BH-FDR) | trend group +0.0013 / +0.0056 |
| 4 | DTR trend | not in stack → in stack | part of #3 |
| 5 | Land cover | 2020 → 2001 | weak mechanism |
| 6 | Label-fitted NDVI features | θ\* dropped; k\* on training labels | 0.0000 |
| 7 | Degenerate features | dropped | — |
| 8 | Aspect | degrees → sin, cos | within #2 |
| 9 | NDVI QA gap 2007-03/04 | unfiltered/dropped → VI_Quality bits | r = 0.999996 |
| 10 | Moran's I / LISA | 67 % filled cells → India-only block means | 0.8322 → 0.9456 |
| 11 | Imputation | all rows → training rows | minor |
| 12 | Evaluation population | all pixels → forest primary | RF 0.975 → 0.897 |
| 13 | Classical split | mixed 80/20 and 65/15/20 → single 65/15/20 | — |
| 14 | Spatial CV (classical) | 0°-anchored GroupKFold → CDR block permutation | identical partitions across models |
| 15 | CDR-PINO protocol | per-track protocols → one protocol | B1 −0.033, B2 −0.049 |
| 16 | B3 terminal label | pooled over all years → training months | +0.0006 |
| 17 | Ablation | single seed, no no-physics arm → 4 configs × 3 seeds, paired tests | no physics beats no physics |
| 18 | B3 baselines | none → two persistence nulls | nulls exceed CDR-PINO |
| 19 | CDR vs classical | different grids → same-cell bridge | RF +0.041 / +0.25 / +0.39 |
| 20 | Final map | v1 probabilities → relative score + quantile classes | — |
| 21 | MaxEnt training size | undisclosed 150k → disclosed + sensitivity | +0.0015 / +0.006 |

**Unchanged:** study period, boundary, forest codes, FIRMS filtering (none applied), NDVI QA level, CDR-PINO architecture/losses/covariates/12 km grid, RF and MaxEnt hyperparameters.

---

## 12. Reproducibility

- **Historical numbers:** all reproduce bit-exactly (e.g. 0.9398, 0.7510 ± 0.0182, 0.6187 ± 0.0680, 0.8960; RF 0.9704, MaxEnt 0.9598). Independent raw-data recalculation matched 86 checked items (60 exact, remainder explained).
- **Code:** audit scripts in `results/code/`; operator code in `Physics_Informed_FireRisk_Model/cdr_pinn/`; canonical entry `run_unified_protocol.py`.
- **Environments:** Steps 1–3 and 6: `wildfire_env` (Python 3.10); Steps 4, 5, 7 notebooks and audit scripts: `firerisk-anaconda3` (Python 3.12, CPU-only torch); **all CDR-PINO training: `cdr_pinn_env`** (Python 3.11, torch 2.11.0+cu128).
- **Compute to refit from scratch:** ≈ 16 CPU-hours (Step 7) and ≈ 4.5 GPU-hours (Step 8). Notebooks load verified result files by default.
- **Run order, hashes, checkpoint manifest:** `results/REPRODUCIBILITY_REPORT.md`, `results/final/FINAL_CHECKPOINT_MANIFEST.csv`.

---

## 13. Known limitations of the methodology

1. One operator family (FNO) and one equation; local operators or equations fitted to spread data are not excluded.
2. CDR loss weights, modes and window length were not tuned beyond weight decay and early stopping.
3. The operator sees test cells' covariates (never labels) and dryness is z-scored over all months; both favour the operator.
4. Different grids (12 km vs 1 km): all operator comparisons are made on the operator's cells.
5. The label is detected fire, not burned area or severity.
6. The RF map is a relative score with no calibrated uncertainty.
7. SHAP not computed.
8. Not re-derived from raw data: MCD64A1 burned area, the historical Jackknife, fire-coincidence anomaly statistics.
9. The Biswas comparison is a reimplementation with five different data sources and an unexplained presence count.
