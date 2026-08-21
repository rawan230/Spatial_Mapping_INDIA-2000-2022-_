# Step 4 — FLDAS Climatic Variables + Land Cover: Audit and Documentation

**Folder:** `FLDAS Noah Land Surface Model L4 Global Monthly 0.1 x 0.1 degree (MERRA-2 and CHIRPS) (FLDAS_NOAH01_C_GL_M)/`
**Notebook:** `Land Surface Model Variables Analysis.ipynb` (hand-authored, 26 cells, no generator script)
**Outputs:** `FLDAS_Outputs/`
**Audit date:** 2026-08-22, against commit `18d44fc` ("Add FDR correction to Mann-Kendall significance + resolution-caveat disclosure").

## What Was Done

Step 4 ingests 266 monthly FLDAS Noah Land Surface Model NetCDF files (Nov 2000–Dec
2022, ~120 MB each), crops them to India, and produces six climatic variables — wind
speed, precipitation, relative humidity, air temperature, net longwave radiation, and
soil moisture — each carried through climatology, anomaly, Mann-Kendall trend (τ), and
FDR-corrected trend significance. It also reclassifies the ESA CCI/C3S land-cover
archive into 22 base LCCS parent classes with fractional cover per NDVI-grid pixel for
2020, and runs a fire-coincidence check against Step 1's 541,545 real fire points.

Verified real results from the current run: the FLDAS-cropped India grid is 335×315 px
at 0.1° resolution, with 29,056 of 105,525 pixels (27.5%) inside the India boundary
mask; all 266 months streamed and cropped in 40.3 s. National monthly means (2000–2022):
wind 4.46 m/s, precipitation 94.5 mm/month, relative humidity 52.6%, air temperature
296.1 K (22.9 °C), net LW radiation −84.7 W/m², surface soil moisture 26.5 kg/m².
Mann-Kendall τ (computed in ~21 s GPU-tiled): wind −0.026, precipitation +0.045, RH
+0.096, air temperature −0.007, net LW radiation +0.082, soil moisture +0.090 — RH, net
LW radiation, and soil moisture show the most spatially extensive trends even after FDR
correction (24–38% of valid pixels). Fire-affected pixel-months are measurably drier
(precipitation anomaly −5.6 mm vs. +0.7 mm grid-wide) and slightly warmer (+0.29 K vs.
−0.01 K) than the grid-wide average. Land cover (2020, computed in 26.9 s): the top five
of 22 classes by national mean fraction are rainfed cropland (35.00%), irrigated
cropland (20.94%), broadleaved deciduous tree (8.02%), grassland (5.34%), and mosaic
natural vegetation (4.72%).

Both previously-flagged fixes are confirmed landed in the current notebook/outputs: (a)
Benjamini-Hochberg FDR correction on Mann-Kendall significance (air temperature's raw
636 significant pixels collapse entirely to 0 after correction — its apparent trend was
multiple-testing noise, not a real spatial pattern; wind 3,728→1,015, precipitation
2,754→1,840, RH 13,413→10,818, net LW radiation 10,197→7,204, soil moisture
11,615→6,926); (b) the README's one-sentence ~11 km effective-resolution disclosure for
bilinear-resampled FLDAS-derived features.

## How It Was Done

FLDAS files are read one month at a time (already natively monthly, unlike Step 3's
8-day LST composites), cropped to an India bounding box, flipped to north-up, and
stacked into `(T, H, W)` arrays. Climatology is the 2001–2020 monthly-mean baseline;
anomalies are per-month deviations from that baseline. Mann-Kendall τ is computed with
a GPU-tiled (CuPy, row-tiled at 200 rows to bound VRAM) lag-sweep S-statistic, identical
in structure to Steps 2 (NDVI) and 3 (LST); a two-sided normal-approximation p-value is
derived from the same S-statistic, then Benjamini-Hochberg FDR correction
(`statsmodels.stats.multitest.multipletests`, alpha=0.05) is applied per-variable across
that variable's full set of valid (n_valid≥10) per-pixel p-values — the FDR-corrected
mask, not the raw p<0.05 mask, is what downstream files treat as the real significance
signal. Fire points are rasterized onto the FLDAS grid via direct affine
`row/col = round((lat-f)/e), round((lon-c)/a)` lookup, the same pattern used pipeline-wide.
Reprojection onto the NDVI grid (0.1° → 0.01°, i.e., upsampling) uses
`rasterio.warp.reproject` with `Resampling.bilinear`. Land cover uses a single 2020 ESA
CCI/C3S LCCS raster, reclassified to 22 base parent codes and area-averaged onto the
NDVI grid.

## Why It Was Done This Way

FLDAS's native monthly cadence removes the need for the multi-observation aggregation
Step 3 requires for 8-day LST composites. The GPU-tiled Mann-Kendall implementation and
the erf-based p-value formula are deliberately kept identical to Steps 2/3 so that
trend-significance reporting is methodologically consistent across every temporal-trend
feature in the pipeline, and the FDR correction (Wilks 2006) was added for the same
reason it was added to Step 3: a per-pixel raw p<0.05 threshold across ~29,000
independent tests produces a large expected false-positive count by chance, and FDR is
the standard field-significance fix in climate science for exactly this problem.
Bilinear (not nearest-neighbor) resampling is used because FLDAS is being upsampled
(coarse→fine), where bilinear is the literature-standard choice to avoid block artifacts
nearest-neighbor would introduce — though as noted below, this choice is asserted by
citation, not empirically tested within this step.

## Impact on Spatial Fire Mapping in India

This step closes 6 of Biswas et al.'s (2025) 15 Table 3 predictor variables and
delivers each one with a temporal-trend treatment (anomaly + Mann-Kendall τ +
FDR-significance) their study never attempted, at native ~11 km effective resolution
(vs. their 0.25° MaxEnt input grid). The fire-coincidence result — fire pixel-months
running drier and warmer than the grid-wide baseline — gives an independent, purely
data-driven sanity check that these climatic anomalies behave physically as expected
before they ever reach the susceptibility model. The 22-class land-cover fractions
supply Step 6/7 with the granular vegetation-type context that a binary forest mask
alone cannot, and the RH/soil-moisture/precipitation anomaly and trend layers now
feed directly into the 58-feature stack Step 7 trains on (ROC-AUC 0.9683 per the
pipeline's current headline result).

## Comparison with Biswas et al. (2025)

Biswas et al. use raw monthly (or in precipitation's case, half-hourly-source but
still not trend-decomposed) values at their variables' native resolutions, uniformly
rasterized to 0.25° for MaxEnt input, with no anomaly or trend treatment described for
any of the six variables this step covers. This step instead delivers climatology,
anomaly, Mann-Kendall τ, and FDR-corrected significance for every one of the six, at a
working resolution roughly 2.5× finer than their 0.25° grid (though the ~11 km
effective-resolution caveat above means the genuine information content gain is more
modest than the stored-grid resolution alone suggests). This comparison is implicit in
the README's per-variable table and its resolution-caveat sentence, but the notebook
and README never state it as an explicit, quantified side-by-side claim (e.g., "N%
of pixels show a significant trend Biswas et al.'s method could not have detected") —
see Gap 3 below.

**Relative humidity vs. specific humidity — confirmed, previously undocumented
substitution.** Biswas et al.'s Table 3 predictor #2 is specific humidity (`Qair_f_tavg`,
13.0%/15.0% importance/contribution). This project computes `qair_kgkg_mean` and stores
it only as a single national scalar per month in `FLDAS_monthly_statistics_NDVI_aligned.csv`
— confirmed by reading the notebook's export cell (cell 22): specific humidity never
appears in `native_layers` (the per-pixel climatology/anomaly/Mann-Kendall GeoTIFF
export dict) or in `aligned_layers` (the NDVI-grid reprojection dict), so it never
becomes a per-pixel spatial feature and is never reprojected onto the model's working
grid. Relative humidity — a derived, Clausius-Clapeyron quantity the README and
notebook markdown both correctly label "bonus, not in Biswas et al." — is the only
humidity variable that receives the full climatology/anomaly/Mann-Kendall/FDR/GeoTIFF
treatment, and it is confirmed (via `grep` of `Step6_Integrated_FireRisk_Analysis.ipynb`,
which loads `fldas_rh_anomaly` from `RH_anomaly_mean_on_NDVI_grid.tif`) to be the actual
humidity feature the trained Step 7 model consumes. In other words: the humidity
predictor that Biswas et al. use is present only as a coarse scalar with no spatial
resolution, while the spatial humidity feature that reaches the susceptibility model is
a variable Biswas et al. never used at all. Both facts are individually stated in the
README/notebook, but the corollary — that this is a real variable-definition
substitution at the trained-model level, not just an added bonus metric — is never
stated explicitly anywhere in the project's documentation.

## Completeness Audit: Gaps Found

1. **(Highest priority — reviewer-relevant) The RH-for-specific-humidity substitution
   is real and needs an explicit methods-section disclosure.** As detailed above, the
   model's humidity predictor is relative humidity, not the specific humidity Biswas et
   al. used, and this is currently only inferable by cross-referencing three files
   (this notebook, its README, and Step 6's notebook) rather than stated as one
   deliberate, justified decision. A Q1 submission should either (a) add specific
   humidity itself to the per-pixel export/reprojection pipeline so both variables are
   available and the model's choice is a tested comparison rather than an implicit
   substitution, or (b) add one explicit sentence/paragraph in the methods (and this
   step's README) stating why RH was substituted for specific humidity and that this is
   a deliberate, disclosed variable-definition difference from the reference study.

2. **No ablation or sensitivity analysis anywhere in the notebook.** A full-text search
   for "ablation," "sensitivit*," "nearest," "ERA5," "validat*," "reanalysis," and
   "ground station"/"IMD" returned zero matches. The bilinear-vs-nearest-neighbor
   resampling choice and the 2001–2020 climatology baseline window are both justified
   by citation/reasoning only, never tested empirically within this step (e.g., no
   comparison of aggregate statistics or downstream AUC under nearest-neighbor
   resampling or an alternate baseline window).

3. **No explicit, quantified side-by-side comparison against Biswas et al.'s raw/no-trend
   treatment.** The added value (trend detection, significance, working resolution) is
   real and documented piecewise across the README, but there is no single explicit
   statement quantifying what the anomaly+trend+FDR treatment adds that a
   raw-monthly-value MaxEnt input (their approach) structurally cannot capture.

4. **No independent climate-reanalysis or ground-station cross-check.** No comparison
   against ERA5, IMD gridded observations, or an independent precipitation product
   (Biswas et al. themselves used a different precipitation source, GPM 3IMERGHHL, not
   FLDAS/CHIRPS) exists anywhere in this step. Even a simple Pearson-r spot-check
   against one independent product would strengthen the climatic layers' credibility
   for review.

5. **Fire-coincidence check omits net LW radiation.** The coincidence analysis (cell 18)
   and its bar chart (`FLDAS_Fire_Coincidence.png`) test precipitation, wind, RH, air
   temperature, and soil moisture anomalies at fire vs. non-fire pixel-months — five of
   the six climatic variables — with no stated reason for excluding net LW radiation,
   which otherwise receives full treatment everywhere else in this step. Likely an
   oversight, low cost to fix.

6. **Stale internal notebook markdown.** The notebook's own final "Pipeline Complete"
   cell (cell 25) still reads "10 of 11 variables," lists burned area as "the one gap,"
   and references the pre-2026-08-19 step numbering — none of which reflects the
   2026-08-18 15-variable correction or the current step numbering that the README
   already carries. A reader working from the notebook directly (rather than the
   README) would get outdated framing. Low priority, but a five-minute fix for
   consistency.

7. **Land cover is a single static year (2020) while every climatic variable is
   time-varying across 2000–2022.** This matches the rest of the pipeline's LULC
   convention (Step 1's `LULC_RECENT_YEAR`) and is not a defect specific to this step,
   but is worth one explicit caveat sentence in the methods given the temporal-resolution
   mismatch between predictor groups feeding the same model.

**What is genuinely solid and does not need further work:** climatology, anomaly,
Mann-Kendall trend, and FDR-corrected significance maps exist for all six climatic
variables (matching Steps 2/3's treatment exactly); the 22-class land-cover national
mean fraction bar chart already exists (`LandCover_22Class_NationalMeanFraction.png`),
answering what the audit brief flagged as a possible gap; the fire-coincidence
comparison plot exists and shows a physically sensible result; and both previously
tracked fixes (FDR correction, resolution-caveat disclosure) are confirmed present in
the current committed code and outputs.
