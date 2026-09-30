# Spatial Mapping of Forest Fire in India (2000–2022): Current, Corrected Study — Step-by-Step Documentation

**Written:** 2026-09-30. **Status:** reflects the full audit of 2026-09-24/25 and the current manuscript (`Manuscript_TGRS/main.tex`).
**Sources used (every number below comes from these, nothing is estimated):**
`results/FULL_METHODOLOGY_AUDIT.md`, `results/FINAL_MANUSCRIPT_NUMBERS.md`, `results/METHODOLOGY_CHANGELOG.md`,
`results/BISWAS_VS_CURRENT_COMPARISON.md`, `results/final/FINAL_MODEL_CONFIGURATION.json`, `Manuscript_TGRS/main.tex`.

> **If you read only one thing:** the study is no longer "CDR-PINO beats the baselines". It is now
> **"Does a governing equation help? A controlled evaluation."** The honest answer, under controlled
> conditions, is **no**. The best model in the study is a **Random Forest on 55 corrected predictors**.

---

## PART 0 — Why you are confused: old claims vs. current truth

Your older documents (`CDR_PINN_Full_Paper_Draft.md`, `CDR_PINN_Novelty_Comparison_Advantages.md`, `Step*_Audit_and_Documentation.md`, older slides, the pre-update sections of `CLAUDE.md`) describe the *v1 / historical* results. All historical numbers **reproduce bit-exactly**, but the *interpretation* and several *methods* behind them were defective. Use this table to translate.

| Topic | OLD statement (v1, do not cite) | CURRENT statement (v2, cite this) |
|---|---|---|
| Story of the paper | CDR-PINO is the novel, superior model | CDR-PINO physics gives **no** accuracy benefit; controlled negative result |
| Fire label | rounding rule `round((lat−f)/e)` | containing-pixel `floor` rule; **74.9 % of points (405,723 / 541,545) were displaced** in v1 |
| Label effect | — | corrected label **raises** RF AUC by +0.0055 (all) / +0.0114 (forest) |
| Feature count | 57 (v1 stack) / "55" / "58→55" mixed up | **v1 = 57, v2 = 55** |
| Climate/LST/NDVI "anomaly-mean" | used as predictors | **degenerate** (equals residue of the 26 out-of-baseline months); replaced by 2001–2020 climatological **levels** |
| Trend test | Mann–Kendall on seasonal / MA-smoothed series | **Seasonal Kendall + Sen slope + BH-FDR** (MA series had lag-1 autocorr. 0.975 → MK invalid) |
| Land-cover fractions | 2020 map (inside label window) | **2001** map |
| Moran's I (NDVI) | 0.8322 (67 % filled non-India cells) | **0.9456** (India cells only, 8×8 block means) |
| National forest cover | "~9.86–10.43 %" | **18.3–19.3 %** (old figure was over the download rectangle) |
| Headline RF AUC | 0.9704 (all pixels) | **0.975 all / 0.897 forest** (forest is the primary population) |
| Headline MaxEnt AUC | 0.9598 | **0.967 all / 0.866 forest** |
| Evaluation population | all India pixels | **forest pixels primary** (forest fraction alone gives AUC 0.91 over all pixels) |
| CDR-PINO number | 0.9398 (Track A), 0.7510 / 0.6187 / 0.8960 (B1/B2/B3) | **0.939 / 0.719 / 0.570 / 0.893** under one unified protocol, 3 seeds |
| Physics ablation | 0.602 → 0.924 → 0.940 "each term contributes" | **no physics 0.945 ≥ full CDR 0.939**; contradicted by the controlled ablation |
| "Temporal generalisation is CDR's advantage (0.8960)" | claimed strength | **withdrawn**: 0.893 is *below* persistence baselines (0.908 / 0.930) |
| RF vs CDR "0.950 vs 0.751 same folds" | apples-to-oranges | **same cells & covariates**: RF 0.980 / 0.974 / 0.959 vs CDR 0.939 / 0.719 / 0.570 |
| "Elevation dominance" | a driver finding for fire | artefact of CDR's 7-covariate model; with the full predictor set removing terrain changes AUC by **−0.0001** |
| "Beats Biswas (0.9576 vs 0.879)" | claimed | **not comparable** and not traceable; remove |
| "Fisher–KPP reaction" | in the design docs | **misnomer**: reaction acts on the logit, so ds/dt = ρ s²(1−s)² |
| Zero-shot super-resolution / resolution independence / fine-tuning | claimed | **never evaluated** → future work only |
| Physical consistency | "physics-informed" implied consistent | trained field is **static** and **violates its own PDE** (residual 74–616 × \|∂u/∂t\|) |

---

## PART 1 — Big picture and manuscript flow

**Working title:** *Does a Governing Equation Help? A Controlled Evaluation of a Convection-Diffusion-Reaction Physics-Informed Neural Operator for Forest Fire Susceptibility Mapping in India* (IEEE TGRS target).

### 1.1 Manuscript section order (as in `main.tex`)

| § | Section | What it says |
|---|---|---|
| Abstract | — | Hypothesis (physics helps) → 3 controls → negative result → corrected pipeline → RF is best |
| I | Introduction | Biswas et al. (2025) context; Indian regional ML literature; PINN/FNO background; **4 research questions**; 4 contributions |
| II | Study area & data | Domain, period, grid; fire label + rasterisation equation; predictor table (55 features); Figs. fire density, land cover |
| III | Methods | Workflow figure → trend/spatial statistics → classical models → CDR operator (equation, architecture, losses, training algorithm) → controlled evaluation design → physical-consistency diagnostic → Biswas reimplementation |
| IV | Results | National patterns → classical 1 km models → **RQ1** ablation → **RQ2** same-cell classical vs CDR → **RQ3** held-out years vs nulls → **RQ4** does the field solve its PDE → contribution decomposition → Biswas comparison → national map |
| V | Discussion | Why the equation did not help (4 reasons); implications & minimum reporting standard; pipeline lessons; limitations |
| VI | Conclusion | Negative result stated plainly; RF best; recommendation of controlled design |
| App. | Supplement | Biswas importance figure, MaxEnt sample-size sensitivity, sensitivity table |

### 1.2 The four research questions and their answers

| RQ | Question | Answer |
|---|---|---|
| RQ1 | Do diffusion / advection / reaction terms beat the *same network without them* under random, spatial, regional, temporal splits? | **No.** Physics is worse on random split and unseen years; indistinguishable from zero on spatial/regional |
| RQ2 | How does the operator compare with classical models on the *same cells, partitions, covariates*? | **Worse on every track** (RF +0.041 / +0.26 / +0.39) |
| RQ3 | On held-out years does it beat *covariate-free* baselines? | **No** (0.893 < 0.908 / 0.930) |
| RQ4 | Does the trained operator satisfy its own equation? | **No** (static field, residual 74–616 × its rate of change) |

### 1.3 Four contributions (as framed now)

1. A controlled test of a physics-informed operator (4 physics configs × 4 tracks × 3 seeds, paired tests, same-cell classical comparison, persistence baselines). Negative for RQ1–3.
2. A physical-consistency diagnostic (term magnitudes + equation residual).
3. A reproducible, audited national pipeline (541,545 points, 55 predictors, corrected label, Seasonal Kendall, India-only Moran's I, 2001 land cover, forest-primary evaluation).
4. A reimplementation of the Biswas et al. MaxEnt protocol on this data, with clear statements of what is and is not comparable.

---

## PART 2 — The pipeline, step by step (data → features → models → evaluation)

Common conventions (unchanged by the audit): study period **2000-11-01 → 2022-12-15** (266 months; capped by ESA-CCI/C3S land cover); dissolved `India_State_Boundary.shp` (raw coords EPSG:3857 → EPSG:4326); common grid **EPSG:4326, 3,641 × 3,504, 1/120° ≈ 0.93 km** (not 0.01°).

### Step 1 — Forest fire points (label source)
- **Data:** MODIS Collection 6.1 FIRMS archive.
- **Method:** clip to bounding box → clip to India polygon → drop duplicates (location + date) → keep only points on a **forest LULC class of the same year** (13 forest codes, ESA-CCI/C3S).
- **Counts (verified):** 2,804,373 → 2,801,347 → 1,599,471 → 1,599,466 → **541,545 forest fire points**.
- **Filters tested, not applied:** confidence < 30 (4.29 % of points) and type ≠ 0 (0.21 %); removing either changes AUC by < 0.001 → null result, points retained.
- **Validation:** annual counts vs. Biswas-derived counts **+0.5 % to +2.4 %, r = 0.99996** (2001–2020). MCD64A1 burned area vs. forest-fire counts: Pearson r ≈ 0.93 (forest-masked series; recomputed from saved series, raw not re-extracted).
- **Corrected rasterisation (the most important fix):** `col = floor((lon − x0)/Δx)`, `row = floor((lat − y0)/Δy)` where (x0, y0) is the **outer pixel edge**. The old `round` rule measured against the edge and shifted 74.9 % of points by one pixel.
- **Label:** a pixel is positive if it contains ≥ 1 forest fire point in the period → **268,411 positive pixels**; prevalence **6.45 % (all pixels)**, **22.4 % (forest pixels)**.

### Step 2 — NDVI features (MOD13A3.061, 1 km monthly)
- **Kept (v2):** QA-masked mean NDVI; climatological June NDVI; **Seasonal Kendall τ**; seasonal **Sen slope**; **CVSI** at lag **k\* = 8** (re-selected on training labels only, still 8); **LISA** cluster class.
- **Dropped (v2):** F3 anomaly-mean (degenerate), F5 residual-mean (≈ 0), F4 (≈ F1, r = 0.99994), θ\* breakpoint indicator (redundant step function of mean NDVI).
- **Corrected statistics:** Seasonal Kendall + BH-FDR → **3,552,278 greening / 72,305 browning pixels**, median Sen slope **+0.0026 yr⁻¹** (old MK: 3,731,210 / 147,206 — direction robust, counts not). Global **Moran's I = 0.9456** (z = 494.2, p = 0.001).
- **Data gap disclosed:** 2007-03/04 lack a pixel-reliability layer (handled with VI_Quality MODLAND bits; effect on F1 r = 0.999996).
- **Sensitivity:** Good-only vs Good+Marginal QA changes F1 by r = 0.989 but loses 39.7 % (vs 8.2 %) of pixel-months → Good+Marginal kept.

### Step 3 — Land surface temperature (MOD11A2.061, 1 km, 8-day)
- **Kept (v2, 6 features):** climatological level + Seasonal Kendall τ for **day LST, night LST, DTR**.
- **Corrected trends:** Day **cooling** 2,435,163 px (−0.050 °C/yr); Night **warming** 2,080,747 px (+0.024 °C/yr); DTR **narrowing** 3,273,301 px (−0.077 °C/yr). The old MK counts understated significant pixels by ~6.7× (day) to ~117× (night).
- **Product caveat:** Biswas used MOD11C3 (0.05°). At 0.05°, 98.5–99.4 % of level variance is retained and AUC changes ≈ 0.
- **Gaps disclosed:** two incomplete composites (2001-06-26, 2016-02-18).

### Step 4 — FLDAS climate + ESA-CCI land cover
- **Variables (14 features):** level + Seasonal Kendall τ for air temperature, specific humidity, relative humidity (derived), wind, precipitation, net longwave radiation, soil moisture. Source: FLDAS Noah (0.1°, CHIRPS-forced) → reprojected to the 1/120° grid.
- **Humidity clarification:** specific humidity **is** a per-pixel predictor (same FLDAS source as Biswas); relative humidity is an *additional* predictor. The old gap document's claim that humidity was only a national scalar was wrong.
- **Trend result:** air temperature significantly changing at 9,988 / 29,056 pixels (7,620 decreasing) — **reverses** the older "air-temp trend is noise" statement. Specific humidity increasing at 26,373 / 29,056 pixels.
- **Land cover (22 features):** 21 class fractions + forest fraction, from the **2001** map (v1 used 2020, inside the label window; measured leakage mechanism is weak: forest change +0.019 at fire pixels vs +0.018 at non-fire forest pixels).

### Step 5 — Terrain and accessibility
- **Terrain (4):** elevation (SRTMGL3 90 m), Horn slope, **sin(aspect), cos(aspect)** (aspect in degrees has a 0/360 discontinuity).
- **Accessibility (3):** distance to roads / railways / waterways (Geofabrik OSM 2022, GPU Euclidean distance transform). Validated against exact geodesic distances (n = 3,000): RMSE **0.31 / 0.65 / 0.32 km**.
- **Checks:** Horn vs Zevenbergen–Thorne slope r = 0.9998, ΔAUC 0.0000. A 0.25° DEM gives slopes ~20× smaller (so Biswas's "slope" is a different quantity).
- **Disclosed:** the OSM source sits outside the project folder.

### Step 6 — Integrated feature table (v2)
- **File:** `results/recalculated/FEATURE_TABLE_v2.parquet` — 4,160,768 analysis pixels × 60 columns, **55 features** (v1 stack: 57).
- **Group counts:** Vegetation 6, Surface temperature 6, Climate 14, Terrain 4, Access 3, Land cover 22 = **55**.
- **Forest population:** 1,197,538 pixels with `forest_frac_2001 > 0`.
- **Leakage controls in v2:** 2001 land cover; median imputation fitted on training rows only; θ\* dropped; CVSI k\* chosen on training labels (ΔAUC 0.0000). Remaining disclosed items: transductive covariates for the operator (covariates only, never labels) and forest-definitional coupling (non-forest pixels can never be positive → forest population is primary).
- **All 15 Biswas et al. variable groups** are represented (group-level parity in v1; variable-level parity — levels, not just anomaly-means — only in v2).

### Step 7 — Classical models (RF and MaxEnt) — corrected results
**Configuration (`FINAL_MODEL_CONFIGURATION.json`):**
- **Random Forest:** 200 trees, max_depth 25, min_samples_leaf 3, class_weight balanced, max_features sqrt, random_state 42 (validated on a validation split, not chosen on test).
- **MaxEnt (elapid 1.0.4):** linear + hinge + product (v2 model), β multiplier 4.0 (validation-tuned; grid essentially flat: val AUC 0.9589–0.9592), 150k training rows, cloglog output.
- **Protocol:** stratified **65/15/20** split by the *corrected* label; thresholds (max-F1) from validation; **test touched once**. Also fitted on the 15 Biswas-equivalent predictors to separate "model family" from "predictor set".

**Track A results (1 km, random split; prevalence 6.45 % all / 22.4 % forest):**

| Model | ROC-AUC all | ROC-AUC forest | AP all | AP forest |
|---|---|---|---|---|
| **RF, 55 features** | **0.975** | **0.897** | 0.720 | 0.721 |
| MaxEnt, 55 features | 0.967 | 0.866 | 0.663 | 0.664 |
| RF, Biswas-15 predictors | 0.970 | 0.885 | 0.692 | 0.698 |

**Harder splits (RF, 55 features):**

| Track | Definition | AUC all | AUC forest |
|---|---|---|---|
| B1 | 2° spatial blocks, 3 folds (block-carved validation) | 0.959 | 0.838 |
| B1, MaxEnt | same | 0.956 | 0.828 |
| B2 | leave-one-region-out (6 k-means regions) | 0.935 | 0.782 |
| B3 | unseen years (2000, 2008, 2009, 2015) | 0.965 | 0.872 |
| B3 null | persistence baseline | 0.807 | 0.744 |

Fold SDs: B1 0.014 / 0.039 (RF), 0.012 / 0.029 (MaxEnt); B2 0.036 / 0.034 (RF).

**Reading:** spatial transfer costs ~0.06 (forest AUC 0.897 → 0.838) and regional transfer ~0.115 (→ 0.782). The historical GroupKFold spatial CV (0.9459 / 0.9527 / 0.9508) reproduces exactly but used a *different* fold geometry and is not the same as CDR's B1.

**MaxEnt sample size (is the RF–MaxEnt gap a subsampling artefact? No):**

| Rows | AUC all / forest | Fit time |
|---|---|---|
| 50k | 0.9640 / 0.855 | 150 s |
| 100k | 0.9663 / 0.863 | 510 s |
| 150k (used) | 0.9672 / 0.867 | 1,130 s |
| 300k | 0.9680 / 0.870 | 3,411 s |
| 500k | 0.9685 / 0.872 | 7,303 s |

Seed SD ≤ 0.0004; gain from 150k → 500k is +0.0015 / +0.006; fit time ~ n^1.6, so 1M and the full 2.7M rows were not run.

**Calibration:** RF v2 ECE 0.064 (all) / 0.219 (forest); MaxEnt v2 ECE 0.015 / 0.054. Hence the RF output is a **relative score, not a probability**. No calibrated uncertainty estimate was established.

### Step 8 — The CDR-PINO (physics-informed neural operator)

**8a. Governing equation (as implemented).** Latent logit field u, susceptibility s = σ(u):

∂u/∂t = D(x,t) ∇²u − v(x)·∇u + ρ(x,t) σ(u)(1−σ(u)), with u(x,0)=0 and a zero-flux boundary.

- **Diffusion** D = softplus( f_D(NDVI, forest fraction) − softplus(w)·NDVI′ ) — biophysical/climatic.
- **Advection** v = softplus(c)·∇E — upslope transport from elevation.
- **Reaction** ρ = softplus( f_ρ(dryness Q, NDVI, slope S, road distance R) ) — ignition pressure/human activity.
- f_D: MLP 2-12-12-1 (tanh); f_ρ: MLP 4-12-12-1 (tanh); w, c scalars.
- Analytical properties (bounded, parabolic, Lipschitz reaction → global existence/uniqueness) concern the **equation only**; RQ4 tests the *trained network*.

**8b. Architecture (FNO2d, 1,054,613 parameters).** Input 8 channels on a 256 × 256 grid (~12 km, **22,542 valid cells**, 266 months): state u_t + 7 covariates (mean NDVI, NDVI anomaly, forest fraction, monthly dryness, slope, distance to roads, elevation). Lift 8→32, **4 Fourier layers** (16 × 16 modes + 1×1 skip, GELU), projection 32→32→1. Output u_{t+1} = 𝒢_θ(u_t, a_t).

**8c. Residual and loss.** r = (u_{t+1}−u_t) − D∇²ū + v·∇ū − ρσ(ū)(1−σ(ū)), ū = midpoint state, spherical spectral derivatives on a symmetric extension. Loss = data (class-weighted BCE + pooled terminal BCE) + PDE MSE + boundary |∇u|² + IC; weights adapted by gradient-norm balancing every 5 windows. Training windows of 24 months (truncated BPTT).

**8d. What differs between the manuscript text and the code (disclosed in the audit):**
- "Fisher–KPP" label is mathematically wrong (reaction on the logit).
- Boundary loss penalises |∇u|², not ∂u/∂n.
- **IC loss is identically 0** (u₀ = 0 is imposed exactly).
- The loss-weight formula in the older text differs from the code (the manuscript now uses the code's rule).
- "Size-matched negative sampling" in old text does not exist in the code.
- The diffusion form is non-conservative.

**8e. One unified protocol (v2).** AdamW, lr 1e-3, weight decay 0 (validation-selected), ReduceLROnPlateau (factor 0.5, patience 2 checks), up to 80 epochs, early stopping on **validation AUC** every 5 epochs (patience 4 checks), best-checkpoint restore. **Seeds 42, 43, 44.** Validation is block-carved for B1/B2 and year-carved for B3. **102 runs** in total. Environment: `cdr_pinn_env` (torch 2.11.0 + CUDA 12.8, RTX PRO 4500 Blackwell).

**8f. Why this was necessary.** Historically, Track A and B1/B2/B3 were *separately trained models under different protocols* (different optimiser, schedule, epoch budget, validation scheme), and the ablation's full-CDR checkpoint had been overwritten by the Track A checkpoint (`cdr_pinn_full_cdr.pt` is byte-identical to `…_standard_protocol.pt`). The historical values were therefore not comparable across tracks.

### Step 9 — Controlled evaluation design (the study's core)

| Control | Purpose |
|---|---|
| Same network **without physics** (none) | isolates the effect of the equation (RQ1) |
| Physics ladder: none / D / D+A / D+A+R(full) | which term, if any, helps |
| Classical RF, MaxEnt, LogReg on **CDR's own 12 km cells, partitions and 7 covariates** | isolates model family (RQ2) |
| Same, with 12 km aggregates of the 55 predictors | isolates predictor set |
| Persistence nulls: per-cell training-year frequency; same-calendar-month frequency | interpretability of temporal skill (RQ3) |
| Term magnitudes + residual of trained checkpoints | physical consistency (RQ4) |
| DeLong (tracks A, B3); spatial block bootstrap (123 blocks, 300 resamples) for B1/B2 | paired significance |

**Tracks:** A = random 65/15/20 cells (prevalence 42 %); B1 = 2° blocks, 3 folds; B2 = 6 k-means regions held out; B3 = held-out years 2000/2008/2009/2015 (validation 2001/2012/2013/2020), cell-month level (prevalence 2.46 %), terminal label rebuilt from training months only (the old pooled label leaked test years; effect only +0.0006).

---

## PART 3 — Results with the corrected numbers

### 3.1 RQ1 — Physics vs. no physics (mean of 3 seeds, 12 km, all cells)

| Track | No physics | Diffusion | Diff + Adv | Full CDR | Full − none (paired) |
|---|---|---|---|---|---|
| A random | **0.945** ± 0.002 | 0.924 | 0.939 | 0.939 ± 0.002 | −0.005 / −0.007 / −0.006 (DeLong p < 0.02, every seed) |
| B1 spatial blocks | 0.724 | 0.642 | **0.730** | 0.718 | CIs include 0 (all seeds) |
| B2 regions | **0.614** | n/a | n/a | 0.570 | CIs include 0 (p ≈ 0.06–0.87) |
| B3 unseen years | **0.904** | 0.886 | 0.894 | 0.893 | −0.010 / −0.009 / −0.014 (replicated) |

- Forest-cell ordering is the same (A: 0.910 none vs 0.898 full; B3: 0.848 vs 0.833).
- Diffusion alone is the weakest wherever trained; advection recovers most of the loss.
- **Cost:** physics raises training time 2.3–2.4×.
- **No physics configuration beats no physics.**

### 3.2 RQ2 — Classical models on CDR's own cells and covariates (all / forest cells)

| Track | CDR full | CDR none | LogReg | MaxEnt | **RF** |
|---|---|---|---|---|---|
| A | 0.939 / 0.897 | 0.945 / 0.910 | 0.924 / 0.874 | 0.958 / 0.927 | **0.980 / 0.950** |
| B1 | 0.719 / 0.701 | 0.724 / 0.702 | 0.919 / 0.869 | 0.950 / 0.917 | **0.974 / 0.936** |
| B2 | 0.570 / 0.569 | 0.614 / 0.635 | 0.872 / 0.835 | 0.845 / 0.824 | **0.959 / 0.916** |

- RF beats CDR by **0.041 (A), 0.26 (B1), 0.39 (B2)**; even logistic regression beats it by 0.20 (B1) and 0.30 (B2).
- Using 12 km aggregates of all 55 predictors changes classical scores by ≤ 0.01 (RF 0.981 / 0.976 / 0.953) → the covariate set is **not** what limits spatial transfer; the operator's spatial transfer is the weakness.

### 3.3 RQ3 — Unseen years vs. covariate-free baselines (cell-months, prevalence 2.46 %)

| Model | AUC (all) | AUC (forest) |
|---|---|---|
| Per-cell training-year frequency (null) | 0.908 | 0.857 |
| Same-calendar-month frequency (null) | **0.930** | 0.920 |
| CDR-PINO, no physics | 0.904 | — |
| CDR-PINO, full | 0.893 | — |
| RF on monthly covariates | 0.902 | — |
| RF on monthly covariates + month | **0.972** | — |

The operator's temporal skill is *below what location and season already give*. The "temporal generalisation is CDR-PINO's advantage" claim is **withdrawn**.

### 3.4 RQ4 — Physical consistency of the trained field (track A, seed 42)

| Config | Median \|∂ₜu\| (month⁻¹) | Share adv. | Share react. | Share diff. | Residual ratio |
|---|---|---|---|---|---|
| None | 0.0016 | 0.98 | 0.02 | 0.003 | 616 |
| D | 0.0003 | 0.83 | 0.16 | 0.002 | 224 |
| D+A | 0.0002 | 0.83 | 0.17 | 0.0004 | 74 |
| D+A+R | 0.0003 | 0.91 | 0.09 | 0.0004 | 78 |

The field is **effectively static** despite strongly seasonal fire; diffusion is ≤ 0.3 % of the right-hand side; advection mostly routes elevation. The optimiser meets the data loss with a near-static map and leaves the residual unresolved.

### 3.5 Where do the accuracy differences come from? (paired ΔAUC, all / forest)

| Source | Effect |
|---|---|
| Model family: RF − MaxEnt (Biswas-15) | +0.025 / +0.067 |
| Model family: RF − MaxEnt (55 features) | +0.008 / +0.031 |
| 55 features − Biswas-15 (RF) | +0.005 / +0.012 |
| 55 features − Biswas-15 (MaxEnt) | +0.022 / +0.048 |
| 55 features − CDR's 5 static covariates (RF) | +0.017 / +0.071 |
| Trend group (Seasonal Kendall/Sen) | +0.001 / +0.006 |
| Land-cover group | +0.003 / +0.008 |
| Terrain group | −0.0001 / −0.0006 (redundant) |
| Physics terms (full − none) | −0.006 (A); n.s. (B1, B2); −0.011 (B3) |
| CDR-PINO − RF, same cells & covariates | −0.041 (A) |

**Attribution:** accuracy differences come from the **model family** and the **predictor set**, not from physics or operator structure.

### 3.6 Comparison with Biswas et al. (2025)

| Result | Biswas et al. | This study | Comparability |
|---|---|---|---|
| Test AUC under Biswas-style protocol (0.25°, 15 predictors, 2020 presences, MaxEnt, 10 random 75/25 splits) | 0.879 | **0.893 ± 0.009** (range 0.877–0.912); train 0.902 ± 0.003 vs their 0.894 | Moderate (5 data sources differ; their 2,439 presences unexplained — we get 1,292 unique cells) |
| Pixel-level RF (1 km) | not reported | 0.975 all / 0.897 forest | **Not comparable** |
| NDVI importance | 22.3 % | 19.0 % | reproduced |
| Air temperature | 13.1 % | 13.2 % | reproduced |
| LST night / day | 10.1 / 9.6 % | 14.3 / 8.1 % | roughly |
| Slope | 5.6 % | 5.8 % | limited (scale-dependent) |
| Specific humidity | 13.0 % | 3.1 % | **not reproduced** |
| Elevation | 2.4 % | 10.7 % | not reproduced |
| r(NDVI, fire density) | 0.43 | 0.456 | agrees |
| r(wind, fire density) | −0.32 | −0.363 | agrees |
| r(slope, fire density) | 0.40 | 0.223 | weaker |

Also noted from their paper: the text says 70/30 but the counts (1,830/609) imply 75/25; their group totals (33.9/26.1/10.8/9.7 %) are permutation importances though labelled contributions. Ranking differences are mostly a **model-family** effect (Biswas-15 MaxEnt ordering — NDVI ≫ LST night > LST day > elevation > specific humidity — is the closest to theirs).

**Recommended sentence:** *"Under a Biswas-style protocol reimplemented with this study's data, test ROC-AUC was 0.893 ± 0.009, compared with 0.879 reported by Biswas et al. (2025) under their own data. The pixel-level ROC-AUCs of this study (0.975 over all pixels; 0.897 over forest pixels) are not comparable with Biswas et al.'s presence–background AUC."*

**Genuine extensions over Biswas et al.:** longer record (2000–2022), corrected fire label, valid trend statistics, spatial/regional/temporal validation, leakage audit, forest-only evaluation, calibration reporting, a reproducible numerical chain, and the controlled physics test.

### 3.7 Sensitivity analyses (all null unless stated)
FIRMS confidence/type filters (|ΔAUC| ≤ 0.0006), NDVI QA level, LST at 0.05°, slope algorithm, slope from a 0.25° DEM, B3 label leakage (+0.0006): null. MaxEnt sample size: small monotone effect. **Not tested:** CDR loss weights and spectral modes, alternative climate sources. **Not testable / not done:** resolution independence, zero-shot super-resolution, instance-wise fine-tuning (future work).

### 3.8 National susceptibility map
RF v2 (55 features) score at 1/120°, tagged **"relative score, not a calibrated probability"** (mean 0.135 vs prevalence 0.065). Five classes by forest-pixel quantile breaks **0.043 / 0.210 / 0.582 / 0.893**. High classes: northeast, central Indian highlands, Eastern Ghats, Himalayan foothills. Files: `results/final/maps/Susceptibility_RF_v2_score.tif` and `…_5class_quantile.tif`. Fire points lie on steeper terrain than the national mean (12.35° vs 5.72°) and are 38.9 % closer to roads and 64.4 % closer to waterways.

---

## PART 4 — Why the equation did not help (the manuscript's explanation)

1. **Static target vs dynamic equation.** Susceptibility is a long-run property of a place; the data loss rewards a stable ranking, so the simplest optimum is a near-static field, for which the PDE's right-hand side would have to vanish — nothing in the data enforces that.
2. **Wrong process scale.** The terms describe spread; monthly detections at 12 km record where fires occur, not how they move (diffusion's share is ≤ 0.3 %).
3. **Advection = elevation channel.** It carries 83–98 % of the right-hand side, yet terrain adds nothing once the full predictor set is available.
4. **Spatial transfer is an operator weakness.** With identical inputs even a linear model transfers far better; a global Fourier representation on a single domain can tie distant regions together. The no-physics network shares this weakness, so physics neither causes nor cures it.

**Minimum reporting standard proposed:** (i) same network without the equation, (ii) classical models on identical cells/covariates, (iii) covariate-free persistence baselines for any temporal claim, (iv) a consistency check of the trained field against its equation.

---

## PART 5 — Limitations (state them honestly)

- Only one operator family (FNO) and one equation were tested; local operators or equations fitted to spread data are not excluded.
- Loss weights, modes and window length were not tuned beyond weight decay and early stopping (a larger search could narrow, but is unlikely to reverse, a 0.26–0.39 spatial gap).
- The FNO sees test cells' *covariates* (never labels) and dryness is z-scored over all months — both would favour the operator.
- Operator runs at 12 km, classical at 1 km → every operator comparison is on the operator's own cells.
- Label = detected fire, not burned area/severity (forest-masked burned area vs counts r ≈ 0.93).
- RF map is a relative score with no calibrated uncertainty.
- SHAP not computed (`shap` fails to import with the NumPy version installed); permutation importance and partial dependence used instead.
- Three items in the audit were not fully re-derived from raw data: MCD64A1 burned area, the historical Jackknife (not re-run), fire-coincidence anomaly statistics.
- The manuscript's title-page author fields are still placeholders.

---

## PART 6 — What is still stale in the repository (fix before you write from it)

Per `METHODOLOGY_CHANGELOG.md`, these are **outside `results/` and have not been changed without your approval**:

1. `CLAUDE.md` — the old `round()` rasterisation rule is already annotated as corrected, but check environment table wording.
2. `STUDY_METHODOLOGY_AND_GAPS.md` — entries A1 and C4 are wrong (humidity, etc.).
3. Root Markdown drafts (`CDR_PINN_Full_Paper_Draft.md`, `CDR_PINN_Novelty_Comparison_Advantages.md`, `CDR_PINN_Study_Clarifications_QA.md`, `Step*_Audit_and_Documentation.md`, older slides) — carry the v1 story (CDR superiority, 0.9398, "temporal advantage", "elevation dominance"). Pre-update copies are in `_Archive_Unwanted_2026-09-25/pre_audit_document_snapshots/`.
4. Any figure not regenerated: the audit's 8 figures (Fig A–H) are new; other historical figures should not be reused for physics claims.

---

## PART 7 — Where every number lives (for checking)

| Need | File |
|---|---|
| Paper numbers (only source to cite) | `results/FINAL_MANUSCRIPT_NUMBERS.md` |
| Full audit narrative (32 steps) | `results/FULL_METHODOLOGY_AUDIT.md` |
| v1 → v2 change log (21 changes with measured effects) | `results/METHODOLOGY_CHANGELOG.md` |
| Biswas comparison and Table X | `results/BISWAS_VS_CURRENT_COMPARISON.md` |
| Claim-by-claim number audit | `results/audit/MANUSCRIPT_NUMBER_AUDIT.csv`, `BISWAS_CLAIM_AUDIT.csv` |
| Equation vs code audit (25 checks) | `results/audit/EQUATION_CODE_AUDIT.csv` |
| All metrics, seeds, ablation, decomposition | `results/final/*.csv` |
| Model hyperparameters | `results/final/FINAL_MODEL_CONFIGURATION.json` |
| v2 feature table / feature dictionary | `results/recalculated/FEATURE_TABLE_v2.parquet`, `results/final/FINAL_FEATURE_DICTIONARY.csv` |
| Reproduction run order | `results/REPRODUCIBILITY_REPORT.md` |
| Current manuscript | `Manuscript_TGRS/main.tex` (PDF: `main.pdf`) |

**Compute to refit from scratch:** ≈ 16 CPU-hours (Step 7) and ≈ 4.5 GPU-hours (Step 8); by default notebooks load the audit's verified result files instead.
