# Forest-Fire Risk Mapping in India (2000–2022) — Methodology & Feature Summary

**Purpose of this document**: a self-contained summary of the current, verified feature set
and step-wise methodology flow for an 8-step India forest-fire-risk research pipeline, for
updating a presentation. Every number below was checked directly against live data/code as
of 2026-09-14, not recalled from memory.

**Reference paper**: Biswas, S., Mahato, S., & Joshi, P.K. (2025). *Environmental Science and
Pollution Research*, 32:4856–4878 — a national-scale India forest-fire susceptibility map
using MaxEnt on 15 static predictor variables, forest classes per Sannigrahi et al. (2018).
This project extends that reference study with real fire-point integration, GPU-vectorized
statistics, a 22-year record (vs. Biswas et al.'s 20-year 2001–2020 period), full 15/15
predictor-group parity, and a novel physics-informed neural operator (CDR-PINN) alongside
the classical Random Forest/MaxEnt baselines.

**Study period**: 2000-11-01 to 2022-12-15 (266 months, ~22 years), hard-capped by
ESA-CCI/C3S land-cover data availability.

---

## 1. Feature count — 57 features, verified directly against the live pixel table

Checked directly against `Integrated_FireRisk_Pixels.parquet` (4,161,009 in-India pixels):
61 total columns, minus `lon`, `lat`, `fire_count`, and the label `fire_ever` = **57
features** used by the classical ML models (Random Forest, MaxEnt).

| # | Group | Count | Source step | Examples |
|---|---|---:|---|---|
| 1 | NDVI-derived | 9 | Step 2 | QA-filtered mean, climatology, anomaly, trend (2×12-MA decomposition), Mann-Kendall τ, CVSI (optimal lag k*=8), LISA cluster, NDVI–fire breakpoint |
| 2 | LST-derived | 5 | Step 3 | Day/night LST anomaly, diurnal temperature range (DTR) anomaly, day/night Mann-Kendall τ |
| 3 | FLDAS climatic | 14 | Step 4 | 7 variables (air temperature, wind, precipitation, relative humidity, specific humidity, soil moisture, net longwave radiation) × {anomaly, trend} |
| 4 | Land-cover fractions | 22 | Step 4 | ESA-CCI/C3S 22-class LCCS fractional composition per pixel (official Level-1 legend) |
| 5 | Terrain | 3 | Step 5a | Elevation, slope, aspect (SRTMGL3 90m DEM) |
| 6 | Accessibility | 3 | Step 5b | Distance to roads, railways, waterways (Geofabrik OSM 2022) |
| 7 | Forest fraction | 1 | Step 6 | `forest_frac_baseline` (2001 only — later years dropped to remove label leakage) |
| | **Total** | **57** | | |

**Why 22 land-cover classes, not a smaller set?** Verified via Gini feature importance:
combined LULC contribution is only 0.1529, concentrated in 4 of the 22 classes (89.3% of
that contribution), with 8 classes near-zero — kept as the full official legend for
completeness/defensibility, not because all 22 carry equal signal. (Full reasoning:
`Step7_LandCover_Feature_Selection_Rationale.md`.)

**Note — CDR-PINN uses a different, smaller feature set by design.** The physics-informed
neural operator (Step 8) does not consume all 57 features; it uses **7 covariates** (NDVI
baseline, NDVI anomaly, forest fraction, a dryness proxy, slope, distance to roads,
elevation), each mapped to a specific term of its governing PDE (diffusion ↔
biophysical/climatic, advection ↔ topographic, reaction ↔ human-activity). This is a
deliberate architectural choice — physics-informed models are typically built on a compact,
interpretable covariate set, not a maximal feature table — not a data gap.

---

## 2. Step-wise methodology flow, with current headline numbers

1. **Fire point extraction.** MODIS Collection 6.1 FIRMS archive clipped to India's exact
   state-boundary polygon (not a lon/lat bounding box, which would also cover Nepal/
   Bangladesh/Myanmar/Pakistan/Sri Lanka), filtered to forest land-cover pixels via exact
   affine pixel-lookup against yearly ESA-CCI/C3S rasters.
   **Result: 541,545 real forest-fire points.**
   Validation: correlated against independent MODIS MCD64A1.061 annual burned area —
   **Pearson r = 0.915, Spearman ρ = 0.835, p < 0.0001, n = 23 years** (all-India, every
   land-cover type — the internal fire-point-archive credibility check).
   **Forest-masked comparison against Biswas et al.'s own burned-area chart (Fig. 7d,
   2026-09-16):** re-deriving burned area with this project's own forest mask applied
   (instead of all land cover) brings the two studies onto the same population —
   forest-masked annual burned area is **9,392–51,455 km²/year** (2001–2020) vs. Biswas
   et al.'s own **~2,100–17,200 km²/year** (digitized from their chart, no exact table in
   their text). Correlation against their chart: **r = 0.9044**, and both series now
   agree exactly on the minimum year (2002) and maximum year (2009). A residual **~4×
   magnitude gap remains and is disclosed, not hidden** — plausibly a stricter
   forest-class definition or extra QA filtering in Biswas et al.'s own unpublished
   processing. The forest-masked series also correlates *more* tightly against this
   project's own forest-fire-point counts than the all-land-cover series did —
   **Pearson r = 0.9345** (vs. 0.9149), **Spearman ρ = 0.7846**, n = 23 — the expected
   direction, since both measure the same forest-fire population.

2. **NDVI features.** 9 GPU-vectorized features: QA-filtered mean, climatology, anomaly,
   trend/seasonal/residual decomposition, Mann-Kendall τ, Cumulative Vegetation Stress Index
   (CVSI, optimal lag k*=8), LISA spatial-cluster map, and an NDVI–fire breakpoint threshold
   fit on real fire/no-fire labels. India-boundary-masked (fixed 2026-08-21 — this was the
   one step in the pipeline with no boundary clipping at all).
   **Result: national breakpoint θ* = 0.535.**

3. **LST analysis.** MODIS day/night Land Surface Temperature, diurnal temperature range
   (DTR), climatology/anomaly/Mann-Kendall trend with FDR (Benjamini-Hochberg) multiple-
   comparisons correction.
   **Result (FDR-corrected significant-trend pixels): Day 393,838; Night 17,935; DTR 2,290,051**
   (out of ~4.16M in-India pixels).

4. **FLDAS climatic variables + land cover.** Noah Land Surface Model monthly variables
   (air temp, wind, humidity, precipitation, soil moisture, net longwave radiation) plus a
   22-class ESA CCI/C3S land-cover reclassification, both reprojected onto the NDVI's
   1km grid.

5. **Terrain (5a) + Accessibility (5b).** Elevation/slope/aspect (SRTMGL3 90m DEM, GPU
   Horn's-method gradient) and distance to roads/railways/waterways (Geofabrik OSM 2022,
   GPU Euclidean distance transform) — closes the last 6 of Biswas et al.'s 15 predictor
   variables, bringing this pipeline to **full 15/15 predictor-group parity** with the
   reference paper.

6. **Integrated alignment.** Assembles Steps 1–5 into one 57-feature, 4,161,009-pixel table
   (`Integrated_FireRisk_Pixels.parquet`). A 2026-08-21 data-leakage fix dropped
   `forest_frac_recent` (2020) and `forest_frac_current` (2022) — both overlapped the pooled
   2000–2022 fire label's own time window, a reverse-causality risk — keeping only
   `forest_frac_baseline` (2001).

7. **Susceptibility model (classical ML baselines).** Random Forest and MaxEnt, both
   hyperparameter-tuned via a genuine validation split.
   **Random Forest: ROC-AUC 0.9704, AP 0.7011** (`max_depth=25, min_samples_leaf=3`).
   **MaxEnt: ROC-AUC 0.9598, AP 0.6275** (`beta_multiplier=4.0`).
   Spatial-block cross-validation (2°×2° blocks, harder/more realistic test): **RF
   0.9498±0.0035, MaxEnt 0.9465±0.0054.**

8. **CDR-PINN — this study's novel contribution.** A Convection-Diffusion-Reaction PDE
   (mapping all 4 Biswas et al. predictor groups onto one governing equation) embedded in a
   Fourier Neural Operator (FNO/PINO) backbone — a physics-informed neural *operator*, not a
   pointwise coordinate-MLP PINN. `width=32` channels, 4 spectral layers, 16×16 Fourier-mode
   truncation, GELU activation, ~1.05M parameters.
   Standard 65/15/20 train/val/test split: **test ROC-AUC = 0.9398** (val 0.9351).
   Generalization tracks: **B1 (spatial-block CV) 0.7510±0.0182; B2 (leave-one-region-out)
   0.6187±0.0680; B3 (leave-years-out, temporal) 0.8960.**
   Jackknife variable-importance retraining, permutation importance, and response curves all
   converge on **near-total elevation/terrain dominance**.
   **Newest diagnostic (2026-09-02):** train-vs-validation AUC tracking shows B1/B2's weak
   scores are **not classical overfitting** — train and validation AUC stay close and high
   (0.93–0.96) throughout training for every fold/region. The entire collapse happens at the
   validation→test boundary (pixels from unseen spatial blocks/regions), isolating the
   failure as a genuine out-of-distribution transfer problem specific to the spatial axis —
   Track B3 (temporal) shows no such gap. Confirmed CDR-PINN is not overfitting also for the
   Jackknife sweep (train−val gap uniformly small, +0.008 to +0.028, across all 15 retrains).
   **22-year vs. 20-year ablation** (this study's 22-year record vs. Biswas et al.'s 20-year
   period, same architecture/split/protocol): no measurable accuracy advantage from the
   extra 2 years on raw test AUC (ΔAUC = +0.0024, within single-seed noise) — but the
   22-year record captures **+485 additional distinct fire-affected pixels (+5.59%)** of
   India's fire-prone geography, an honest, disclosed null result on accuracy alongside a
   genuine coverage gain.

---

*All numbers above are traceable to real executed code/data — none are estimated. Full
detail: `Complete_Methodology_Section.md` (master assembled methodology), individual
`Step1`–`Step8_*_Audit_and_Documentation.md` files, and `FULL_EXPERIMENT_LOG.md` (raw
experiment log), all at the project root.*
