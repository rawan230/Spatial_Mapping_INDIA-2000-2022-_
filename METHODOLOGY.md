# Methodology & Statistical Reference — India Forest-Fire-Risk Pipeline

This document consolidates the exact statistical/mathematical methodology used in
every step of the pipeline, extracted directly from the executed code (not from
memory or prior summaries), together with literature justification for each method
and every discrepancy found during this audit. It is written for direct use in a
paper's Methods section and Supplementary Material.

**How citations are marked in this document:**
- **[cite-confirmed]** — the citation is well-established, foundational literature I
  can state with high confidence (author/year/venue verified against reliable recall).
- **[cite-verify]** — my best recollection of the correct citation, but specific
  enough (exact volume/page/co-author list) that it should be independently checked
  against the publisher/DOI before it goes into the paper. Flagged rather than
  presented as fact, because a wrong citation in a submission is worse than a
  flagged gap.
- **[not cited in-notebook]** — the notebook itself contains no literature citation
  for this method; a citation is supplied here from general knowledge, but the
  in-repo code gives no independent confirmation.

---

## Step 1 — Fire Point Extraction

**Notebook:** `Forest fire Extraction in INDIA(2000-2022)/FOREST_FIRE_POINTS_EXTRACTION(INDIA).ipynb`

### Boundary clipping

Exact point-in-polygon test: `shapely.contains_xy(INDIA_POLYGON, lon, lat)`, applied
*after* a cheap bounding-box pre-filter (68.0–97.5°E, 6.5–37.5°N). The polygon itself
is `India_State_Boundary.shp` (37 state/UT polygons, dissolved to one via
`union_all()`), reprojected EPSG:3857→EPSG:4326. The state boundary is used instead
of the country boundary because the latter has ~60 degenerate near-zero-area sliver
polygons near the Palk Strait (79–79.5°E, 9–9.3°N).

Result: 2,804,373 raw rows → 2,801,347 (bbox) → 1,599,471 (exact polygon, excluding
1,201,876 points outside India's real border) → 1,599,466 (after deduplication).

### Forest classification

Binary forest mask from ESA-CCI/C3S LULC (LCCS classification), forest codes:
`FOREST_CODES = {50, 60, 61, 62, 70, 71, 72, 80, 81, 82, 90, 100, 110}` (13 codes).
In-code citation: *"Sannigrahi et al. (2018), cited in Biswas et al. (2025), p.
4863."* No independent citation detail (journal/volume) exists in the notebook.

**RESOLVED 2026-08-10**: Step 6 (Integrated Feature Alignment — see below;
FLDAS/land-cover is Step 4, renumbered 2026-08-17)'s LULC
forest-fraction feature (`forest_frac_*`) previously used an **11-code** set —
`{50,60,61,62,70,71,72,80,81,82,90}` — excluding 100 (mosaic_tree_and_shrub) and 110
(mosaic_herbaceous) that Step 1 includes, meaning two different operational
definitions of "forest" coexisted in this pipeline. Fixed by reconciling Step 6 to
Step 1's 13-code set (which carries a literature citation trail via Sannigrahi et
al.; the 11-code set had none) — both the fire-point ground-truth label and the
forest-fraction predictor feature now share one consistent definition.

### Rasterization (affine pixel lookup)

```
row = round((lat − lat₀) / Δlat),  col = round((lon − lon₀) / Δlon)
```
where `(lat₀, lon₀)` is the grid's own first coordinate and `(Δlat, Δlon)` its own
step size, read directly from each year's LULC NetCDF coordinate arrays (not
supplied as separate affine coefficients). Mathematically equivalent to the classical
affine-transform pixel lookup; both indices are clamped to valid array bounds.

### Deduplication

Exact-key dedup: `drop_duplicates(subset=["longitude","latitude","acq_date"])` — no
coordinate rounding, no confidence-field filtering. **⚠ Note**: an earlier internal
validation checklist for this step assumed rounding-based dedup and a confidence
threshold; neither exists in the actual code. If the paper's methods text describes
either, correct it to match what's actually implemented.

### Citations

| Method/product | Citation | Status |
|---|---|---|
| MODIS FIRMS Collection 6.1 active-fire product | Giglio, L., Schroeder, W., & Justice, C.O. (2016). *The Collection 6 MODIS active fire detection algorithm and fire products.* Remote Sensing of Environment, 178, 31–41. DOI: 10.1016/j.rse.2016.02.054. | [cite-confirmed] |
| ESA-CCI/C3S LULC forest classes | Sannigrahi, S. et al. (2018) — cited via Biswas et al. (2025), p. 4863 | [cite-verify — a dedicated search pass could not confirm which 2018 Sannigrahi paper this is; check Biswas et al.'s own bibliography directly, see Reference List entry] |
| Overall pipeline methodology | Biswas, U., Mahato, S., & Joshi, P.K. (2025). *Spatial prediction of forest fires in India: a machine learning approach for improved risk assessment and early warning systems.* Environ. Sci. Pollut. Res., 32(8), 4856–4878. DOI: 10.1007/s11356-025-35982-8. | [cite-confirmed] |
| Secondary reference | Uthappa, A.R., Das, B., Raizada, A., Kumar, P., Jha, P., & Prasad, P.V.V. (2025). *Forest fire susceptibility mapping using multi-criteria decision making and machine learning models in the Western Ghats of India.* J. Environmental Management, 379, 124777. DOI: 10.1016/j.jenvman.2025.124777. | [cite-confirmed] |

---

## Step 2 — NDVI Feature Engineering (9 features)

**Notebook:** `NDVI_DATA_INDIA_/NDVI_ANALYSIS_WITH_FFP.ipynb` (generated by `build_ndvi_notebook.py`)
**Grid:** 3641×3504, EPSG:4326, T=266 months (Nov 2000–Dec 2022), MOD13A3.061 monthly 1km NDVI.

### F1 — QA-filtered NDVI mean

Reliability filter keeps `pixel_reliability ∈ {0 (Good), 1 (Marginal)}`, drops
Snow/Ice/Cloudy/Fill. `F1ᵢⱼ = (1/n) Σₜ NDVI(t,i,j)` over valid months only
(`np.nanmean`).

**Citation for NDVI itself [not cited in-notebook]**: Rouse, J.W., Haas, R.H.,
Schell, J.A., & Deering, D.W. (1974). *Monitoring vegetation systems in the Great
Plains with ERTS.* NASA SP-351, 3010–3017. **[cite-confirmed]**

### F2 — Climatology

Baseline 2001–2020 inclusive (*"unchanged from Biswas et al. convention"*, per
in-code comment). Per-pixel, per-calendar-month mean:
`μ̄ᵢⱼ⁽ᵐ⁾ = mean{NDVI(y,m,i,j) : y ∈ [2001,2020]}`. F2 excludes 2021–2022 because
those years fall outside this baseline window, not due to a bug (independently
verified earlier in this project).

### F3 — Anomaly

`δ(t,i,j) = NDVI(t,i,j) − μ̄ᵢⱼ⁽ᵐ⁽ᵗ⁾⁾` — a raw departure from climatology, **not
z-scored** (no division by standard deviation). Matched by calendar month.

### F4/F5 — Trend & Residual (classical 2×12-MA additive decomposition)

Classical centered 2×12 moving-average trend-cycle estimator (13-tap symmetric
window, half-weight at both ends: `[0.5,1,1,1,1,1,1,1,1,1,1,1,0.5]`):
`Trend(t) = Σₖ wₖ·x(t+k) / Σₖ wₖ`, k=−6..6, NaN-adaptive normalization. Undefined
for the first/last 6 months (254/266 valid).

Detrend → seasonal (mean of detrended series per calendar month, across the *full*
series, not baseline-restricted) → residual: `NDVI = Trend + Seasonal + Residual`
(classical additive decomposition). F4 = time-mean of Trend; F5 = time-mean of
Residual.

**Citation [not cited in-notebook]**: this is the textbook centered moving-average
decomposition method, standard in time-series analysis. General reference:
Cleveland, R.B., Cleveland, W.S., McRae, J.E., & Terpenning, I. (1990). *STL: A
Seasonal-Trend Decomposition Procedure Based on Loess.* Journal of Official
Statistics, 6(1), 3–73. **[cite-verify]** — note this project uses the simpler
classical 2×12-MA method, not STL/loess itself; cite Cleveland et al. as the general
decomposition-family reference, or a classical time-series textbook (e.g., Kendall &
Stuart) if a more exact match is wanted for the *specific* centered-MA method.

### F6 — Mann-Kendall trend τ

Applied to the **trend component** (F4's underlying series), not raw NDVI, over
T=266 months. Classical Mann-Kendall S-statistic via full pairwise lag sweep:
`S = Σᵢ₌₁^{T−1} Σⱼ sign(x_{i+lag} − x_i}`, `τ = S / [n(n−1)/2]` using each pixel's own
valid-count `n` (requires n≥10). Significance via **normal approximation**:
`Var(S) = n(n−1)(2n+5)/18`, `z = (S∓1)/√Var(S)`, two-sided p-value via `erf`.
Threshold `p<0.05` applied to both directions:
`browning_sig = (p<0.05) & (τ<0)`, `greening_sig = (p<0.05) & (τ>0)`.
Result: 150,108 significant browning pixels, 3,748,043 significant greening pixels
(both p<0.05, independently confirmed earlier in this project).

**RESOLVED 2026-08-10**: Step 3 (LST) and Step 4 (FLDAS) now compute the identical
normal-approximation significance test (same `erf`-based two-sided p-value formula)
on the *same* S/τ computation described above — added without changing any existing
τ/anomaly values (verified byte-identical pre/post-fix). Step 3's three Mann-Kendall
runs (Day/Night/DTR) can be reported as statistically significant or not, exactly like
NDVI's browning/greening figures: LST Day 1,063,120 significant pixels (37,812
warming, 1,025,308 cooling), LST Night 234,318 (234,164 warming, 154 cooling), DTR
2,545,287 (19,004 widening, 2,526,283 narrowing) — all p<0.05. Full breakdown in
`LST_Outputs/LST_trend_summary.csv`.

**Citations [cite-confirmed]**: Mann, H.B. (1945). *Nonparametric tests against
trend.* Econometrica, 13(3), 245–259. Kendall, M.G. (1975). *Rank Correlation
Methods.* Griffin, London.

### F7 — CVSI (Cumulative Vegetation Stress Index)

`CVSI(t,k) = Σ_{lag=1}^{k} max(−δ_{t−lag}, 0)` — accumulated pre-fire NDVI anomaly
deficit over a trailing k-month window (requires ≥⌈k/2⌉ valid months in-window).
**This is a project-specific, unpublished index** — no literature precedent exists
for it; it is a genuine methodological contribution of this work, not an adaptation
of a named method.

**Optimal-lag selection**: mutual information between quantile-binned (10 bins) CVSI
values and real fire/no-fire pixel-month labels (from Step 1, restricted to a
random, size-matched, `RandomState(seed=42)` case-control sample of never-burned
background pixels), swept k=1..12 (extended from an original k=1..6 range on
2026-08-10). Selected `k* = argmax_k I(Y; CVSI_k)`.

**RESOLVED 2026-08-10 — now a confirmed interior optimum**: MI rises monotonically
k=1..8 (peak 0.01246 at **k\*=8**) then falls for k=9..12 (0.01057, 0.00949, 0.00853,
0.00761) — no longer an unverified boundary result. Exported feature file renamed
`F7_CVSI_k6.tif` → `F7_CVSI_k8.tif`; any downstream step referencing the old
filename/column name (`ndvi_cvsi_k6`) needs updating to `k8`.

**Citation for the general mutual-information selection framework [cite-confirmed]**:
Cover, T.M., & Thomas, J.A. (2006). *Elements of Information Theory* (2nd ed.).
Wiley. — standard reference for mutual information as a dependence measure; not a
citation for CVSI itself, which has none.

### F8 — LISA cluster map

Spatial weights: queen contiguity (`libpysal.weights.lat2W(rook=False)`), row-
standardized, on an 8×-coarsened grid (1km→8km, 456×438 cells) for tractability.
Global Moran's I (`permutations=0`, analytical normal approximation): I=0.8925,
z=795.86, p≈0. Local Moran's I / LISA (`esda.Moran_Local`, 199 conditional
permutations, `seed=42`): standard quadrant codes (1=HH, 2=LH, 3=LL, 4=HL), filtered
to `p_sim<0.05`. Counts (of 199,728 coarse cells): HH 6.8%, LL 4.8%, LH 0.1%, HL
0.0%, not-significant 21.0%, ocean/no-data 67.2%.

**Citations [cite-confirmed]**: Moran, P.A.P. (1950). *Notes on continuous
stochastic phenomena.* Biometrika, 37(1/2), 17–23. Anselin, L. (1995). *Local
Indicators of Spatial Association — LISA.* Geographical Analysis, 27(2), 93–115.

### F9 — NDVI–fire breakpoint threshold

**Exact method**: a piecewise (two-regime) logistic regression fit by maximum
likelihood — **not** a ROC/Youden's-J cut, **not** a decision-tree split:
```
P(fire=1 | NDVI=x) = σ(a₁+b₁x)  if x ≤ θ
                    = σ(a₂+b₂x)  if x > θ
```
fit by minimizing binary cross-entropy jointly over `(a₁,b₁,a₂,b₂,θ)` via
Nelder-Mead, multi-started over a 25-point grid spanning the 10th–90th percentile of
sampled NDVI (to avoid local optima), on a balanced case-control subsample (up to
100k positive + 100k negative, `seed=42`), both nationally and per biogeographic
zone (rectangular approximations of Rodgers & Panwar 1988 zones).

Results (corrected 2026-08-10): All-India θ*=0.529; Western Ghats 0.482; Northeast
0.668; Central India 0.504; Deccan 0.497; **Himalayan −0.001**.

**RESOLVED 2026-08-10**: the Himalayan zone previously returned θ*=−0.613, outside
the physically valid NDVI range. Root cause, confirmed by direct investigation: not
sample size (falsified — the zone's fire-positive sample, n=27,030, was mid-pack
across zones, larger than Western Ghats' or Deccan's) and not weak signal (the
zone's fire/no-fire NDVI separation was cleanly significant, Mann-Whitney p≈0).
The actual cause was **MLE non-identifiability**: the unbounded multi-start
Nelder-Mead search let θ drift onto a flat, non-identifiable NLL plateau
(numerically flat from θ=−2.0 to −0.16 to 6 decimal places) once the winning
solution emptied one regime entirely (`n_below=0`, collapsing the piecewise model to
a single logistic where θ carries no information). Fixed by (a) bounding θ to the
physically valid NDVI range in the optimizer, and (b) rejecting any multi-start
winner whose solution has `n_below`/`n_above` < 1% of the sample as a non-identifiable
regime-collapse result rather than a genuine threshold (zones where every start
degenerates this way now report `NaN` with an explicit "no stable interior
breakpoint" message, not a fabricated number). All 5 other zones are numerically
unchanged after the fix, confirming it altered only optimizer robustness, not the
underlying data or method.

**Citations**: Rodgers, W.A., & Panwar, H.S. (1988). *Planning a Wildlife Protected
Area Network in India.* Wildlife Institute of India, Dehradun. **[cite-verify]** —
zone boundaries here are rectangular approximations of this scheme, not the original
polygons. The piecewise-logistic MLE method itself has no specific citation in the
notebook; general reference for piecewise/segmented regression: Muggeo, V.M.R.
(2003). *Estimating regression models with unknown break-points.* Statistics in
Medicine, 22(19), 3055–3071. **[cite-verify]**

---

## Step 3 — LST Analysis (5 features)

**Notebook:** `LST_analysis/LST_DAY_NIGHT.ipynb`. Product: MOD11A2.061 (8-day
composite, 1km), bands `LST_Day_1km`/`LST_Night_1km` + QC bands.

Climatology (2001–2020, same convention as Step 2), anomaly, and Mann-Kendall use
**identical formulas to Step 2/4** (see above) — same streaming-accumulator
climatology, same anomaly-vs-calendar-month formula, same full-lag-sweep MK
S/τ computation. **DTR = LST_Day − LST_Night**, with its own independently-computed
anomaly and Mann-Kendall trend (not derived by differencing the day/night τ values).
Measured: DTR τ mean=−0.104 (narrowing trend), stronger than either Day (−0.041) or
Night (+0.043) alone, consistent with simultaneous day-cooling/night-warming.

**RESOLVED 2026-08-10, as noted under F6 above**: Step 3 computes the same
normal-approximation p-value/significance test as Step 2 for all three Mann-Kendall
runs (Day/Night/DTR). Significant-pixel counts: Day 1,063,120 (37,812 warming,
1,025,308 cooling), Night 234,318 (234,164 warming, 154 cooling), DTR 2,545,287
(19,004 widening, 2,526,283 narrowing) — all at p<0.05.

**Citations**:
- MOD11 LST algorithm **[not cited in-notebook; cite-confirmed]**: Wan, Z. (2014).
  *New refinements and validation of the collection-6 MODIS land-surface
  temperature/emissivity product.* Remote Sensing of Environment, 140, 36–45.
  DOI: 10.1016/j.rse.2013.08.027. (Verified 2026-08-09 as the correct
  Collection-6-specific paper.)
- DTR as a fire-risk indicator **[not cited in-notebook]**: general wildfire-weather
  literature links high DTR to low fuel moisture/high evaporative demand; a specific
  citation should be sourced from the fire-weather literature the paper is
  positioning against (e.g., work using the Haines Index or similar dryness
  indicators) — none is currently in-repo.
- Mann-Kendall: as cited under Step 2, F6.

---

## Step 4 — FLDAS Climatic Variables + Land Cover

> **Renumbered 2026-08-17**: this was "Step 6" before — moved to Step 4 since it
> genuinely runs before the assembly/training steps (the old numbering had it
> running *before* the step numbered lower than it, which was never the real
> dependency order, just a historical artifact of when it was added to the
> project). No content, code, or data flow changed — only the label.

**Notebook:** `FLDAS Noah Land Surface Model.../Land Surface Model Variables Analysis.ipynb`
**Product:** FLDAS_NOAH01_C_GL_M.001 (Noah LSM, MERRA-2 + CHIRPS forced), 0.1°, monthly.

### Variables and transforms

| Feature | Source variable | Transform |
|---|---|---|
| Wind speed | `Wind_f_tavg` | m/s, as-is |
| Air temperature | `Tair_f_tavg` | K, as-is |
| Precipitation | `Rainf_f_tavg` | kg/m²/s → mm/month (× days_in_month × 86400) |
| Soil moisture (surface) | `SoilMoi00_10cm_tavg` | volumetric → kg/m² (× 0.10m × 1000) |
| Net LW radiation | `Lwnet_tavg` | W/m², as-is |
| Relative humidity (derived) | `Qair_f_tavg`, `Tair_f_tavg`, `Psurf_f_tavg` | Magnus/Tetens formula, see below |

**RH formula** (labeled "Clausius-Clapeyron" in-code; more precisely the **Magnus
formula**, a Clausius-Clapeyron-derived empirical approximation):
```
es(hPa) = 6.112 · exp[17.67·Tc / (Tc+243.5)]     (Tc in °C)
e(hPa)  = q·p / (0.622+0.378·q)
RH(%)   = 100 · e / es,  clipped to [0,100]
```
**Citation [cite-verify]**: Tetens, O. (1930). *Über einige meteorologische
Begriffe.* Zeitschrift für Geophysik, 6, 297–309. (Original Magnus-type formula;
verify exact constants used match this vs. a later refinement, e.g. Murray 1967.)

Six variables get the full climatology/anomaly/Mann-Kendall treatment (same formulas
as Steps 2/3, baseline 2001–2020, explicitly *"same baseline window as Step 3"*
in-code); three (raw precip rate, specific humidity, total-profile soil moisture) are
exported as monthly means only.

### 22-class land-cover reclassification

**Resolved 2026-08-09 (was flagged as unconfirmed inference, now verified)**: the
notebook's own code comment described this as *"the standard ESA CCI level-1 legend
and the most likely match for a paper citing '22 classes'"* — an educated guess, not
a confirmed citation, at the time it was written. A web-search verification pass
against ESA CCI's own documentation confirms this guess was exactly correct: ESA
CCI's LCCS legend is officially structured in two tiers — a **"Level 1" legend of
exactly 22 global classes**, expressed by the tens-value codes (10, 20, 30, ...,
220), defined via the UN FAO Land Cover Classification System (LCCS); and a finer
**"Level 2" legend** of regional sub-variants (11, 12, 61, 62, ...) that refine
those same 22 parent classes where more detailed regional information is available.
`base_code = (raw_code // 10) * 10` — collapsing Level-2 sub-variants to their
Level-1 parent — is therefore the **correct, standard operation**, not a
project-specific reinterpretation. Citable as: *"the Level 1 legend (22 global
classes) of the ESA CCI/C3S Land Cover Classification System (LCCS), following the
UN FAO LCCS scheme."* Source: ESA Climate Change Initiative Land Cover
documentation (climate.esa.int/en/projects/land-cover/) and Digital Earth Africa's
CCI Land Cover specification
(docs.digitalearthafrica.org/en/latest/data_specs/CCI_Landcover_specs.html), both
confirming the Level 1 (10/20/30-coded) vs. Level 2 (11/12/61/62-coded) structure.
Method: each of the 22 classes is reprojected 300m→~1km via `Resampling.average`
(fractional cover per class per pixel).

### Reprojection

Two directions, both explicit and deliberate: FLDAS variables (0.1°→~0.01°,
**upsampling**) use `Resampling.bilinear`; land cover (300m→~1km, **downsampling**,
fractional/categorical) uses `Resampling.average` — the correct resampling choice for
each direction (bilinear for continuous-field interpolation, area-averaging for
fractional-cover aggregation).

### Citations

| Product | Citation | Status |
|---|---|---|
| FLDAS | McNally, A. et al. (2017). *A land data assimilation system for sub-Saharan Africa food and water security applications.* Scientific Data, 4, 170012. | [cite-verify — not confirmed in-notebook, source independently] |
| ESA CCI/C3S land cover | (no specific external citation found; the 22-class reclassification is this project's own inference, see caveat above) | — |

**Corrected 2026-08-18** (was previously miscounted as "10 of 11" — that framing was
wrong and has been replaced project-wide): Biswas et al.'s actual Table 3 lists **15**
MaxEnt predictor variables, verified by direct extraction from the user's own copy of
the paper — burned area is **not** one of the 15 (it appears in their Table 2 as a
dataset used elsewhere, not as a Table 3 predictor, so it was never actually a gap
relative to their predictor set in the first place). The genuinely missing groups,
confirmed against Table 3, are:
- **Distance to roads / railways / waterways** (OpenStreetMap, 2022 vintage; combined
  10.8% contribution in their model).
- **Slope / aspect / elevation** (DEM-derived; combined 9.7% contribution).

**Closed 2026-08-18, numbered 2026-08-19, split into two repos 2026-08-19**: all six
built as Step 5a (`Terrain_Elevation_Slope_Aspect_Analysis/`,
`Step5a_Terrain_Elevation_Slope_Aspect.ipynb`) and Step 5b
(`Distance_Roads_Railways_Waterways_Analysis/`,
`Step5b_Accessibility_Distance_Analysis.ipynb`), run alongside this step (Step 4) and
feeding Step 6 (Integration, renumbered from Step 5 to make room). Full results,
methodology, and fire-coincidence findings in each repo's own README. This pipeline now
covers all 15 of Biswas et al.'s real predictor variables (was 9 before this step
existed). Not yet wired into Step 6's integrated pixel table or Step 7's retrained
model — that's the remaining task before a direct full-parity comparison is possible.

A related but separate addition, in the Step 1 repo, not a Table 3 predictor: a
burned-area-vs-fire-count validation analysis
(`Forest fire Extraction in INDIA(2000-2022)/Forest_Fire_Outputs/
Annual_BurnedArea_vs_FireCount.csv`) replicating Biswas et al.'s Fig. 7 trend comparison
with the same MODIS MCD64A1.061 product, plus a direct correlation (Pearson r=0.915,
Spearman ρ=0.835, p<0.0001, n=23 years, full Jan–Dec coverage as of the 2026-08-20
re-run — an earlier Mar-Dec-restricted version of this figure, r=0.824, was superseded
once the previously-missing Jan/Feb source months downloaded) they didn't attempt, and
a year-by-year cross-check against their own reported annual fire counts (this
project's counts run 0.5–2.4% higher across every
overlapping year 2001–2020, a consistent small offset, not a discrepancy).

---

## Step 5 — Terrain & Accessibility Analysis

> **Added 2026-08-18, numbered 2026-08-19, split into two repos 2026-08-19.** Runs
> alongside Step 4 (FLDAS), feeds Step 6 (Integration, bumped from Step 5 to make room
> for this step). Two independent repos, both still Step 5a/5b:
> `Terrain_Elevation_Slope_Aspect_Analysis/` (Step 5a) and
> `Distance_Roads_Railways_Waterways_Analysis/` (Step 5b) — full detail in each repo's
> own `README.md`.

**Notebooks:** `Step5a_Terrain_Elevation_Slope_Aspect.ipynb`,
`Step5b_Accessibility_Distance_Analysis.ipynb`

Closes the six Biswas et al. (2025) predictor variables this pipeline had zero coverage
of before this step existed (see the corrected Step 4 note above — their real predictor
set is 15 variables, not the 11 previously claimed):

- **Elevation, slope, aspect** — SRTMGL3 (90m) DEM, mosaicked from four
  OpenTopography latitude-band requests (a single full-India request exceeds even the
  90m product's 4,050,000 km² area cap). Horn's-method gradient computed at native 90m
  *before* resampling to the shared NDVI grid, GPU-vectorized, latitude-corrected pixel
  spacing.
- **Distance to roads, railways, waterways** — Geofabrik OpenStreetMap extracts, 2022
  vintage (matching Biswas et al.'s own stated source), clipped to this project's own
  `India_State_Boundary.shp`, GPU/CPU Euclidean distance transform in a custom
  India-centred equidistant conic projection (a flat degree×111km conversion is wrong
  by >19% across India's latitude range).

**Fire-coincidence validation** (541,545 real Step 1 fire points): fires sit at 12.3°
mean slope vs. 5.7° nationally (+115%), directly corroborating Biswas et al.'s own
finding that slope is their second-most-important variable (16.7% contribution).
Distance-to-road/waterway also show strong, literature-consistent enrichment (fires
40% closer to roads, 65% closer to waterways than the national average).

**Infrastructure note worth knowing**: `geopandas.clip()` never finished against the
raw boundary shapefile's 422,929 vertices, even given a 6-hour timeout — fixed with a
simplified 13,451-vertex mask and vectorized `shapely.covered_by`/`intersection`
(~160 seconds once corrected). Two full notebook executions failed before a clean run:
one from a GPU conflict with a concurrently-running job (the documented
`cudaErrorAlreadyMapped` fragility — never run two GPU-heavy kernels against the same
GPU at once), one from an undersized 1-hour cell timeout on the boundary-clip step
before that fix landed.

Not yet wired into Step 6's integrated pixel table or Step 7's retrained model — the
remaining task before a direct 15/15-variable-parity comparison against Biswas et al.
is possible.

---

## Step 6 — Integrated Feature Alignment

> **Renumbered twice.** On 2026-08-17: this was "Step 4" before — moved to Step 5,
> after FLDAS (Step 4), since it depends on FLDAS's output and always ran after it
> regardless of the old numbering. On 2026-08-19: moved again to Step 6 to make room
> for the new Step 5 (Terrain & Accessibility Analysis) inserted between FLDAS and
> this step.

**Notebook:** `Integrated_Analysis/Step6_Integrated_FireRisk_Analysis.ipynb`
(renamed from `Step5_...ipynb` 2026-08-19, `Step4_...ipynb` before that)

### LULC forest-fraction construction

Binary 300m forest mask (13-code set, reconciled with Step 1 on 2026-08-10 — see
Step 1's discrepancy note above) → `rasterio.warp.reproject(...,
resampling=Resampling.average)` onto the NDVI grid — an area-weighted mean of
source sub-pixels per destination cell, producing a continuous [0,1]
fractional-forest-cover value per pixel (not a coarse category). Years:
baseline=2001, recent=2020, current=2022 (chosen to bracket the 2001–2020 NDVI/LST
climatology baseline plus a most-recent snapshot).
`forest_loss_baseline_to_recent = forest_frac_baseline − forest_frac_recent` — a
simple pixelwise difference, **not** a change-detection/transition analysis;
positive values mean net loss. National mean forest cover (NDVI grid), post the
2026-08-10 forest-class reconciliation: 2001=10.2%, 2020=10.5%, 2022=10.7% (was
7.8%/7.9%/8.0% under the previous 11-code definition).

**2026-08-21 data-leakage fix, superseding this subsection's original output
columns**: `forest_frac_recent` (2020), `forest_frac_current` (2022), and
`forest_loss_baseline_to_recent` were all **dropped** from the final feature stack
— both non-baseline years fall inside the pooled 2000–2022 fire label's own time
window, a real reverse-causality risk (published literature on post-fire land-cover
change documents burned forest commonly gets reclassified to shrubland/agriculture
in later LULC products, meaning these features could partly encode the *outcome* of
fire rather than a pre-fire condition). Only `forest_frac_baseline` (2001) survives
as the forest-fraction feature going forward. The underlying computation described
above (reproject/average-resample for all three years) is unchanged — only the
recent/current/loss columns' presence in the final parquet/stack changed.

### Grid alignment

Every other source (NDVI/LST/FLDAS/land-cover/fire) is loaded with a **hard
shape-equality assertion** against the reference grid (`ValueError` on mismatch) —
this step does not itself reproject these; each upstream step is responsible for
delivering an already-aligned raster. The only reprojection performed here is the
LULC forest-fraction block described above.

### NaN handling

Only filter applied: `valid = india_mask & ~isnan(ndvi_mean)`. Other feature columns
(LST/FLDAS/land-cover) are **not** independently checked for NaN at this stage —
they can still contain NaN in the retained 4,161,009-row table; no imputation is
performed here (left to Step 7's median-fill).

**Citations**: none in-notebook for the reprojection approach or forest-fraction
method; these are standard GIS raster-resampling operations (`rasterio`/GDAL average
resampling) rather than a citable statistical method per se.

---

## Step 7 — Random Forest Susceptibility Model

> **Renumbered twice.** On 2026-08-17: this was "Step 5" before — moved to Step 6, the
> genuinely last step in the actual execution order (training happens after every
> preprocessing step, not in the middle of the numbering). On 2026-08-19: moved again
> to Step 7 to make room for the new Step 5 (Terrain & Accessibility Analysis).

**Notebook:** `Integrated_Analysis/Step7_FireRisk_Susceptibility_Model.ipynb`
(renamed from `Step6_...ipynb` 2026-08-19, `Step5_...ipynb` before that)

### Model & hyperparameters

```
RandomForestClassifier(n_estimators=200, max_depth=20, min_samples_leaf=5,
                        class_weight="balanced", n_jobs=-1, random_state=42)
```
In-notebook rationale (only for the *algorithm* choice, not individual hyperparameter
values): *"robust to the very different scales/units across NDVI, LST, and LULC
features (no scaling needed), gives feature importances for free, parallelizes
cleanly."* `class_weight="balanced"` is explicitly tied to the ~6.5% positive-class
prevalence.

**RESOLVED 2026-08-10**: the 5-fold CV re-fit previously used `n_estimators=100`
(half the main model's 200), undocumented. Now uses identical hyperparameters to
the reported model — a true apples-to-apples cross-validation.

### Split & evaluation

80/20 stratified split (`stratify=fire_ever`, `random_state=42`) — *"so the ~6-7%
fire-affected pixels are represented proportionally in both sets."* ROC-AUC and
Average Precision reported *"instead of raw accuracy, which would be misleading at
this [class] imbalance."* AP is reported against its no-skill baseline (`y.mean()` =
0.0649) explicitly.

5-fold `StratifiedKFold(shuffle=True, random_state=42)` on the **full** dataset
(re-split independently of the 80/20 train/test split) — *"to confirm the AUC
doesn't depend on which 20% of pixels happened to land in the test set."* Informal
stability bar: `std(cv_scores) < 0.02` → "stable." Current measured (post-2026-08-10
CV fix and forest-class/CVSI reconciliation, both below): mean 0.9670, std 0.0002.

**Current headline results** (as of the 2026-08-10 forest-class reconciliation and
CVSI k8 rename — see Step 6 section above): ROC-AUC 0.9674 (was 0.9676 pre-fix — a
<0.001 shift, not a red flag), AP 0.6761 (was 0.6765). `forest_frac_recent`/
`forest_frac_current`/`forest_frac_baseline` moved from mid-pack into the **top 3**
Gini-importance features (0.160, 0.141, 0.112), ahead of `ndvi_mean` (0.094) —
consistent with the corrected 13-code forest definition capturing more fire-relevant
area than the previous 11-code version.

**Superseded 2026-08-21/22** (`forest_frac_recent`/`current` dropped as a data-
leakage fix, see the LULC subsection above; RF/MaxEnt hyperparameters also
genuinely tuned via a validation split for the first time, plus a new spatial-block
CV added): current headline is **ROC-AUC 0.9701** (tuned RF, 55-feature set,
`max_depth=25, min_samples_leaf=3`), AP 0.6961. `forest_frac_baseline` alone is now
the single top Gini-importance feature (0.2066). New: RF's own spatial-block CV
(2°×2°, matching CDR-PINN's Track B1) scores 0.9497±0.0033 — this pipeline's
first-ever spatial-generalization number for its classical baseline. Full
before/after numbers: `Integrated_Analysis/Model_Outputs/rf_hp_search_result.json`,
`Integrated_Analysis/Model_Outputs/Model_Comparison_SpatialBlockCV.csv`.

### Reproducibility check

Retrain with identical hyperparameters/seed, compare `predict_proba` via
`np.array_equal` (exact) and `np.allclose(atol=1e-9)` (tolerance). Measured
max-diff 7.77e-16, attributed explicitly in-code to floating-point summation-order
noise from `n_jobs=-1` multi-threaded vote aggregation (non-associativity of
float64 addition), not a seed failure. No `n_jobs=1` control run exists to isolate
this — a reviewer-facing methods section could strengthen this claim by adding one.

### Citations

| Method | Citation | Status |
|---|---|---|
| Random Forest | Breiman, L. (2001). *Random forests.* Machine Learning, 45(1), 5–32. | [cite-confirmed] |
| ROC-AUC vs. Average Precision for imbalanced classification | Davis, J., & Goadrich, M. (2006). *The relationship between Precision-Recall and ROC curves.* ICML '06, 233–240. | [cite-confirmed] |
| K-fold cross-validation | Kohavi, R. (1995). *A study of cross-validation and bootstrap for accuracy estimation and model selection.* IJCAI, 1137–1143. | [cite-confirmed] |
| Class-imbalance handling | He, H., & Garcia, E.A. (2009). *Learning from imbalanced data.* IEEE Trans. Knowledge and Data Engineering, 21(9), 1263–1284. | [cite-confirmed] |

**IN PROGRESS 2026-08-16**: a real, trained MaxEnt baseline (`elapid` package) is
being added directly to this notebook specifically to close the gap noted below —
trained on a ~450k-row stratified subsample of the training portion (MaxEnt's own
textbook presence-background training convention, not a compute shortcut), evaluated
on the full test set for a fair comparison against RF. Results pending as of this
writing; update this section once that run completes.

**Gap being closed**: no comparison or citation previously existed anywhere in this
project to Biswas et al.'s own MaxEnt methodology, despite this pipeline explicitly
extending that paper — see "IN PROGRESS" note directly above.

---

## Step 8 / 8b — PINN Comparison Ladder & Statistical Testing

> **Renumbered 2026-08-19**: was Step 7/7b before — moved to Step 8/8b to make room
> for the new Step 5 (Terrain & Accessibility Analysis). Already built with real
> results (run 2026-08-08/09), before this project started tracking it as a numbered
> step at all — the renumbering is a label-only change.

**Notebooks:** `Physics_Informed_FireRisk_Model/Step8_PINN_FireRisk_Model.ipynb`,
`Step8b_PINN_Seed_Robustness_Check.ipynb`

### Model ladder

| Model | Method | Citation |
|---|---|---|
| Logistic Regression | `class_weight="balanced"`, L-BFGS | standard; no single citable origin paper |
| Random Forest | as Step 7 | Breiman (2001), as above |
| XGBoost | `tree_method="hist"`, early stopping | Chen, T., & Guestrin, C. (2016). *XGBoost: A scalable tree boosting system.* KDD '16, 785–794. **[cite-confirmed]** |
| Plain MLP | LayerNorm+ReLU+Dropout, `BCEWithLogitsLoss`, Adam | see below |
| PINN | Plain MLP + physics-informed loss penalty | Raissi, M., Perdikaris, P., & Karniadakis, G.E. (2019). *Physics-informed neural networks: A deep learning framework for solving forward and inverse problems involving nonlinear partial differential equations.* J. Comput. Phys., 378, 686–707. **[cite-confirmed]** |

Component citations: Adam optimizer — Kingma, D.P., & Ba, J. (2015). *Adam: A method
for stochastic optimization.* ICLR. **[cite-confirmed]**. Layer normalization — Ba,
J.L., Kiros, J.R., & Hinton, G.E. (2016). *Layer normalization.* arXiv:1607.06450.
**[cite-confirmed]**. Dropout — Srivastava, N. et al. (2014). *Dropout: A simple way
to prevent neural networks from overfitting.* JMLR, 15(1), 1929–1958.
**[cite-confirmed]**.

### The physics constraint (as tested — superseded going forward)

Grounded in: Dahal, A., & Lombardo, L. (2025). *Towards physics-informed neural
networks for landslide prediction.* Engineering Geology, 344, 107852.
DOI: 10.1016/j.enggeo.2024.107852. **[cite-confirmed — corrected 2026-08-09: the
arXiv preprint (2407.06785)'s own journal-ref metadata was stale/wrong, pointing to
JGR: Machine Learning and Computation, which is actually a different Dahal/Lombardo
paper. The real published venue is Engineering Geology, verified via Crossref.]** —
architecture precedent for a static-tabular hazard-susceptibility PINN. Rodrigues,
M., Resco de Dios, V., Sil, Â., Cunill Camprubí, À., & Fernandes, P.M. (2024). *VPD-
based models of dead fine fuel moisture provide best estimates in a global dataset.*
Agricultural and Forest Meteorology, 346, 109868. DOI: 10.1016/j.agrformet.2023.109868.
**[cite-confirmed]**

**Note for the paper**: multi-seed statistical testing (below) found this specific
physics formulation produced **no significant improvement** over a same-capacity
plain MLP on any of three evaluation tracks (all 95% bootstrap CIs on the AUC delta
included zero). This is now superseded by the user's own CDR-PINN diffusion-equation
design (`CDR_PINN_Diffusion_Design.md`, rigor-audited and extended in
`CDR_PINN_Diffusion_Design_v2.md` — domain bounds reconciled against verified grid
data, a spherical-metric correction added for the Laplacian, a formal well-posedness
proof completed per Evans 2010, and a two-timescale time-varying diffusivity
D(x,y,t) locked in — structural NDVI baseline modulated by NDVI anomaly, citing
Rothermel 1972 for the qualitative moisture-spread direction) — report the Step 8/8b
result as a disclosed negative finding for the *soft monotonicity-penalty* approach
specifically, not as a statement about physics-informed methods in general.

### Statistical testing methodology

- **Spatial block cross-validation**: 2°×2° lon/lat grid blocks, `GroupKFold`.
  **Citation [cite-confirmed]**: Roberts, D.R. et al. (2017). *Cross-validation
  strategies for data with temporal, spatial, hierarchical, or phylogenetic
  structure.* Ecography, 40(8), 913–929. — the standard reference for why random
  splits overstate accuracy under spatial autocorrelation, and for block/grouped CV
  as the correction.
- **Leave-one-region-out**: states clustered into KMeans regions (no `.dbf`/state
  names exist in the shapefile, confirmed empirically) — standard sklearn KMeans,
  Lloyd, S. (1982). *Least squares quantization in PCM.* IEEE Trans. Information
  Theory, 28(2), 129–137. **[cite-confirmed]**
- **Bootstrap confidence intervals** on the seed-level PINN-minus-MLP AUC delta (5
  seeds for Track A/B1, 3 for Track B2; 10,000 resamples, percentile method).
  **Citations [cite-confirmed]**: Efron, B. (1979). *Bootstrap methods: Another look
  at the jackknife.* Annals of Statistics, 7(1), 1–26. Efron, B., & Tibshirani, R.J.
  (1993). *An Introduction to the Bootstrap.* Chapman & Hall.

### Results summary (for direct paper use)

Track A (random split, full budget): LR 0.9460, RF 0.9676, XGBoost 0.9678, plain
MLP 0.9614, PINN 0.9613. Track B1 (3-fold spatial block CV, mean): LR 0.9396, RF
0.9459, XGBoost 0.9492, plain MLP 0.9499, PINN 0.9494. Track B2 (6-region
leave-one-region-out, mean): RF 0.8721, plain MLP 0.8896, PINN 0.8870.
Seed-robustness bootstrap 95% CIs on (PINN−MLP): Track A [−0.00015,+0.00005], Track
B1 [−0.00036,+0.00049], Track B2 [−0.00566,+0.00372] — all include zero, no
significant difference on any track. The one finding that *does* hold up: both
neural architectures generalize better than Random Forest under spatial CV/
leave-one-region-out (~+1.5–1.8 AUC points), an architecture-level (not
physics-specific) result.

---

## CDR-PINN — Physics-Informed Neural Operator Redesign (supersedes Step 8's PINN for the paper's actual novel contribution)

> **Design work completed 2026-08-19/20**, in a separate track of documents, not
> hand-authored notebooks — this section is a summary and citation cross-reference,
> not a duplicate of the full derivations. Full detail, including every proof, lives
> in four files in the project root: `CDR_PINN_Diffusion_Design.md` (v1, researcher's
> own original physics formulation), `CDR_PINN_Diffusion_Design_v2.md` (rigor pass —
> domain reconciliation, exact spherical Laplacian, formal well-posedness proof),
> `CDR_PINN_Advection_Design.md`, `CDR_PINN_Reaction_Design.md`, and
> `CDR_PINN_Final_Design_STEP_D.md` (the consolidated final design). Step 8 above
> (the soft-monotonicity-penalty PINN, a plain coordinate-MLP) is kept as-is in this
> document as a real, honestly-reported result — a disclosed negative finding for
> *that specific* physics formulation — but it is **not** the physics-informed model
> this project is carrying forward into the paper's headline contribution. The
> CDR-PINN design below is.

**Physical formulation** — a convection-diffusion-reaction (CDR) PDE, each term
designed to correspond to one of Biswas et al. (2025)'s four non-trivial predictor
groups, closing the loop between this pipeline's variable-parity work (Step 5) and
its modeling contribution:

```
∂u/∂t = D(x,y,t)·∇²u  −  v(x,y)·∇u  +  ρ(x,y,t)·σ(u)·(1−σ(u))
```

- **Diffusion** `D(x,y,t)` — biophysical/climatic group. Two-timescale construction:
  structural NDVI baseline + LULC forest-fraction (`D_net([NDVI_F1, forest_frac])`)
  modulated by NDVI anomaly, `softplus`-bounded. Researcher-originated (see
  `CDR_PINN_Diffusion_Design.md`'s own provenance note).
- **Advection** `v(x,y)` — topographic group. Terrain-driven, `c_adv·∇E(x,y)`,
  points upslope by construction (`softplus`-constrained sign), grounded in
  Rothermel (1972)'s upslope fire-acceleration finding.
- **Reaction** `ρ(x,y,t)·σ(u)(1−σ(u))` — human-activity group. Fisher–KPP logistic
  form, learned ignition-rate coefficient over dryness/NDVI/slope/distance-to-roads.

**Architecture** — physics-informed neural *operator* (PINO), not a pointwise
coordinate-MLP PINN: FNO backbone (Fourier layers, spectral differentiation for the
PDE residual, Fourier-continuation zero-padding for the non-periodic India domain),
following Li, Zheng, Kovachki et al. (2023). Per-month one-step-ahead operator
`G_θ: (u_t, a_t)→u_{t+1}`, with a hybrid data-supervision scheme (sparse monthly
fire-point signal + a smooth-max terminal-aggregate anchor against the already-
validated `fire_ever` label) chosen specifically because a dense monthly ground-truth
susceptibility field doesn't exist — see `CDR_PINN_Final_Design_STEP_D.md` §3.

**Well-posedness** — existence and uniqueness of a **global-in-time** weak solution
proven for the full assembled equation (not just the diffusion term Step 8's design
originally covered), via Galerkin approximation, an explicit Gårding's inequality
with a data-derived drift bound (advection document, §6), and a Gronwall argument
exploiting the Fisher–KPP reaction term's global boundedness (reaction document,
§5.2) — every constant in these proofs is derived from this project's own verified
data extremes (NDVI range, measured maximum slope 77.31°), not asserted abstractly.

**Loss function and validation** — one combined PDE residual (not three
per-mechanism residuals) plus data/BC/IC terms, adaptively balanced by gradient-norm
rescaling (Wang, Teng & Perdikaris 2021) rather than fixed hand-tuned weights; a
term-ablation validation plan (diffusion-only / +advection / full CDR) across four
generalization tracks, extending Step 8's own spatial-block/leave-region-out/
bootstrap methodology with a new leave-years-out track the per-month operator
framing makes possible.

**Status**: design complete end-to-end (equation, BC, IC, proof, architecture,
training scheme, validation plan). Implementation (the actual training notebook) not
yet started as of this writing — see `CDR_PINN_Final_Design_STEP_D.md` §7 for what
remains, all of it engineering defaults rather than open physics decisions.

**Citations** (added here; full entries in the Consolidated Reference List below):
Li, Zheng, Kovachki, Jin, Chen, Liu, Azizzadenesheli & Anandkumar (2023) for PINO;
Fisher (1937) and Kolmogorov, Petrovsky & Piskunov (1937) for the Fisher–KPP reaction
form; Aronson & Weinberger (1975) and Pazy (1983) for semilinear parabolic
well-posedness theory; Wang, Teng & Perdikaris (2021) for adaptive loss balancing;
Pinheiro & Collobert (2015) for the smooth-max weak-label pooling scheme; Evans
(2010) — already cited above for Step 8's diffusion term — extended here to its
general (drift- and reaction-inclusive) form.

---

## Cross-Cutting Issues to Address Before Submission

1. **RESOLVED 2026-08-10** — Forest-class definition inconsistency (13 codes in
   Step 1 vs. 11 codes in the assembly step, now Step 6 after the 2026-08-17 and
   2026-08-19 renumberings). Reconciled to Step 1's 13-code set (which has a literature
   citation trail via Sannigrahi et al.; the 11-code set had none). Step 6 + Step 7
   rerun completed 2026-08-10 (under the numbering at that time; label-only change
   since).
2. **RESOLVED 2026-08-10** — Mann-Kendall significance testing inconsistency. Step 3
   (LST) and Step 4 (FLDAS) now compute the identical normal-approximation p-value
   Step 2 (NDVI) does, added without changing any existing τ/anomaly feature values
   (verified byte-identical pre/post-fix, so no downstream rerun was needed). New
   significance counts documented in each step's own README.
3. **RESOLVED 2026-08-10** — CVSI's optimal-lag sweep extended from k=1..6 to
   k=1..12. New result: **k\*=8**, now a confirmed interior optimum (MI rises
   monotonically to k=8, peak 0.01246, then falls for k=9..12) — no longer an
   unverified boundary result. **Downstream impact**: the exported feature file
   renamed `F7_CVSI_k6.tif` → `F7_CVSI_k8.tif`; Step 6's hardcoded
   `'ndvi_cvsi_k6': 'F7_CVSI_k6.tif'` entry updated to `k8` (bundled with item 1's
   Step 6 rerun).
4. **RESOLVED 2026-08-10** — Himalayan-zone breakpoint threshold. Root cause was not
   sample size (falsified — the zone's sample was mid-pack, not undersized) but a
   genuine MLE non-identifiability failure: the unbounded Nelder-Mead search let θ
   drift onto a flat, non-identifiable NLL plateau once the fitted solution emptied
   one regime entirely (`n_below=0`). Fixed by bounding θ to the physically valid
   NDVI range and rejecting degenerate (regime-collapse) solutions during the
   multi-start selection. Corrected result: **θ\*=−0.001** (physically valid,
   genuine interior optimum). All other 5 zones numerically unchanged, confirming
   the fix altered only optimizer robustness, not the underlying data or method.
5. **RESOLVED 2026-08-10** — Step 7's CV forest now uses `n_estimators=200`,
   identical to the reported model (was 100). Corrected CV: mean AUC 0.9671, std
   0.0002 — same rounded values as before the fix (the earlier conclusion was
   directionally sound), now genuinely apples-to-apples rather than computed from a
   cheaper stand-in model.
6. **RESOLVED 2026-08-17** — a real, trained MaxEnt baseline was added to
   Step 7 specifically to close this gap (no Biswas-et-al. MaxEnt comparison existed
   anywhere in this project despite the pipeline's stated novelty framing relative
   to that paper). See Step 7 section above for training details and results.
7. **RESOLVED 2026-08-09** — the 22-class land-cover reclassification was flagged
   as an unconfirmed inference; a web-search verification pass against ESA CCI's own
   documentation confirmed it's the correct, standard Level-1 legend (22 global
   classes per the UN FAO LCCS scheme), not a project-specific guess. See the
   Step 4 section above for the citable phrasing and sources. No code change was
   needed — the method (`base_code = (raw_code // 10) * 10`) was already correct.
8. **Citation verification pass completed 2026-08-09** (web-search-verified against
   Crossref/publisher records, not just recall): 7 of 9 previously-flagged citations
   are now [cite-confirmed] with verified DOIs (Giglio 2016, Biswas 2025 — full
   title recovered, Uthappa 2025 — full citation located, Wan — corrected to the
   2014 Collection-6-specific paper not an earlier guess, McNally 2017, Rodrigues
   2024, Rothermel 1972). One correction found and fixed: Dahal & Lombardo's arXiv
   preprint metadata pointed to the wrong venue (JGR: ML&C); the actual published
   version is Engineering Geology (2025), 344, 107852 — corrected everywhere it
   appears in this document (Step 8's physics-constraint precedent; this citation
   does not appear in the CDR-PINN diffusion-equation documents, which cite
   different precedent work). One citation
   remains genuinely unresolved: Sannigrahi et al. (2018) — could not be matched to
   a real paper after a dedicated search; verify directly against Biswas et al.
   (2025)'s own bibliography (p. 4863) before using it in a submission.

---

## Consolidated Reference List (alphabetical)

Anselin, L. (1995). Local Indicators of Spatial Association — LISA. *Geographical
Analysis*, 27(2), 93–115.

Aronson, D.G., & Weinberger, H.F. (1975). Nonlinear diffusion in population
genetics, combustion, and nerve pulse propagation. In *Partial Differential
Equations and Related Topics*, Lecture Notes in Mathematics, vol. 446. Springer.
[cite-verify — recalled with reasonable confidence; confirm exact page range before
citing in the paper]

Ba, J.L., Kiros, J.R., & Hinton, G.E. (2016). Layer normalization. *arXiv:1607.06450*.

Biswas, U., Mahato, S., & Joshi, P.K. (2025). Spatial prediction of forest fires in
India: a machine learning approach for improved risk assessment and early warning
systems. *Environmental Science and Pollution Research*, 32(8), 4856–4878.
DOI: 10.1007/s11356-025-35982-8. [cite-confirmed — verified via Crossref 2026-08-09]

Breiman, L. (2001). Random forests. *Machine Learning*, 45(1), 5–32.

Chen, T., & Guestrin, C. (2016). XGBoost: A scalable tree boosting system. *KDD '16*,
785–794.

Cleveland, R.B., Cleveland, W.S., McRae, J.E., & Terpenning, I. (1990). STL: A
Seasonal-Trend Decomposition Procedure Based on Loess. *Journal of Official
Statistics*, 6(1), 3–73.

Cover, T.M., & Thomas, J.A. (2006). *Elements of Information Theory* (2nd ed.). Wiley.

Dahal, A., & Lombardo, L. (2025). Towards physics-informed neural networks for
landslide prediction. *Engineering Geology*, 344, 107852.
DOI: 10.1016/j.enggeo.2024.107852. [cite-confirmed — corrected 2026-08-09; the
arXiv preprint 2407.06785's own metadata incorrectly pointed to JGR: Machine
Learning and Computation, which is a different paper by the same authors]

Davis, J., & Goadrich, M. (2006). The relationship between Precision-Recall and ROC
curves. *ICML '06*, 233–240.

Efron, B. (1979). Bootstrap methods: Another look at the jackknife. *Annals of
Statistics*, 7(1), 1–26.

Efron, B., & Tibshirani, R.J. (1993). *An Introduction to the Bootstrap*. Chapman &
Hall.

Evans, L.C. (2010). *Partial Differential Equations* (2nd ed.). American
Mathematical Society. [cite-confirmed — standard graduate PDE reference, Ch. 7 used
throughout the CDR-PINN well-posedness proofs]

Fisher, R.A. (1937). The wave of advance of advantageous genes. *Annals of
Eugenics*, 7(4), 355–369. [cite-confirmed]

Giglio, L., Schroeder, W., & Justice, C.O. (2016). The Collection 6 MODIS active
fire detection algorithm and fire products. *Remote Sensing of Environment*, 178,
31–41. DOI: 10.1016/j.rse.2016.02.054. [cite-confirmed]

He, H., & Garcia, E.A. (2009). Learning from imbalanced data. *IEEE Transactions on
Knowledge and Data Engineering*, 21(9), 1263–1284.

Kendall, M.G. (1975). *Rank Correlation Methods*. Griffin, London.

Kingma, D.P., & Ba, J. (2015). Adam: A method for stochastic optimization. *ICLR*.

Kohavi, R. (1995). A study of cross-validation and bootstrap for accuracy estimation
and model selection. *IJCAI*, 1137–1143.

Kolmogorov, A., Petrovsky, I., & Piskunov, N. (1937). Study of the diffusion
equation with growth of the quantity of matter. *Moscow University Bulletin of
Mathematics*, 1, 1–25. [cite-confirmed]

Li, Z., Zheng, H., Kovachki, N., Jin, D., Chen, H., Liu, B., Azizzadenesheli, K., &
Anandkumar, A. (2023). Physics-informed neural operator for learning partial
differential equations. *arXiv:2111.03794*. [cite-confirmed]

Lloyd, S. (1982). Least squares quantization in PCM. *IEEE Transactions on
Information Theory*, 28(2), 129–137.

Mann, H.B. (1945). Nonparametric tests against trend. *Econometrica*, 13(3), 245–259.

McNally, A. et al. (2017). A land data assimilation system for sub-Saharan Africa
food and water security applications. *Scientific Data*, 4, 170012.
DOI: 10.1038/sdata.2017.12. [cite-confirmed]

Moran, P.A.P. (1950). Notes on continuous stochastic phenomena. *Biometrika*, 37(1/2),
17–23.

Muggeo, V.M.R. (2003). Estimating regression models with unknown break-points.
*Statistics in Medicine*, 22(19), 3055–3071.

Pazy, A. (1983). *Semigroups of Linear Operators and Applications to Partial
Differential Equations.* Springer. [cite-verify — standard reference for
semilinear-parabolic global existence via a globally-Lipschitz nonlinearity plus a
coercive linear part; exact chapter/theorem number should be confirmed before
citing in the paper]

Pinheiro, P.O., & Collobert, R. (2015). From image-level to pixel-level labeling
with convolutional networks. *CVPR*. [cite-verify — recalled with reasonable
confidence, confirm before citing]

Raissi, M., Perdikaris, P., & Karniadakis, G.E. (2019). Physics-informed neural
networks. *Journal of Computational Physics*, 378, 686–707.

Roberts, D.R. et al. (2017). Cross-validation strategies for data with temporal,
spatial, hierarchical, or phylogenetic structure. *Ecography*, 40(8), 913–929.

Rodgers, W.A., & Panwar, H.S. (1988). *Planning a Wildlife Protected Area Network in
India*. Wildlife Institute of India, Dehradun.

Rodrigues, M., Resco de Dios, V., Sil, Â., Cunill Camprubí, À., & Fernandes, P.M.
(2024). VPD-based models of dead fine fuel moisture provide best estimates in a
global dataset. *Agricultural and Forest Meteorology*, 346, 109868.
DOI: 10.1016/j.agrformet.2023.109868. [cite-confirmed]

Rothermel, R.C. (1972). *A mathematical model for predicting fire spread in
wildland fuels.* USDA Forest Service Research Paper INT-115, Ogden, UT.
[cite-confirmed]. Cited in `CDR_PINN_Diffusion_Design_v2.md` §4.1 for the
qualitative fuel-moisture-modulates-spread relationship underlying the diffusion
coefficient's anomaly-modulation term — not as a claim that Rothermel's
semi-empirical rate-of-spread model is implemented directly.

Rouse, J.W., Haas, R.H., Schell, J.A., & Deering, D.W. (1974). Monitoring vegetation
systems in the Great Plains with ERTS. *NASA SP-351*, 3010–3017.

Sannigrahi, S. et al. (2018). [ESA-CCI/C3S forest land-cover class mapping — **still
unconfirmed after a dedicated web-search verification pass, 2026-08-09**. Candidate
papers checked and ruled out as not matching: Sannigrahi, Bhatt, Rahmat, Paul & Sen
(2018), *J. Environmental Management*, 223, 115–131 (ecosystem service valuation,
not forest classes); Sannigrahi et al. (2018), *Urban Climate*, 24, 803–819 (urban
land-surface temperature, not forest classes). Biswas et al. (2025)'s own reference
list (which cites this on p.4863) is paywalled and could not be retrieved. **Do not
cite this without independently checking Biswas et al.'s bibliography directly** —
this document cannot confirm which 2018 Sannigrahi paper is meant.]

Srivastava, N. et al. (2014). Dropout: A simple way to prevent neural networks from
overfitting. *Journal of Machine Learning Research*, 15(1), 1929–1958.

Tetens, O. (1930). Über einige meteorologische Begriffe. *Zeitschrift für
Geophysik*, 6, 297–309.

Uthappa, A.R., Das, B., Raizada, A., Kumar, P., Jha, P., & Prasad, P.V.V. (2025).
Forest fire susceptibility mapping using multi-criteria decision making and machine
learning models in the Western Ghats of India. *Journal of Environmental
Management*, 379, 124777. DOI: 10.1016/j.jenvman.2025.124777. [cite-confirmed —
identified and verified 2026-08-09]

Wan, Z. (2014). New refinements and validation of the collection-6 MODIS
land-surface temperature/emissivity product. *Remote Sensing of Environment*, 140,
36–45. DOI: 10.1016/j.rse.2013.08.027. [cite-confirmed — corrected 2026-08-09: this
is the correct Collection-6-specific paper, distinct from Wan's earlier C4/C5
algorithm papers that an initial best-recall guess could easily conflate it with]

Wang, S., Teng, Y., & Perdikaris, P. (2021). Understanding and mitigating gradient
flow pathologies in physics-informed neural networks. *SIAM Journal on Scientific
Computing*, 43(5), A3055–A3081. [cite-confirmed]
