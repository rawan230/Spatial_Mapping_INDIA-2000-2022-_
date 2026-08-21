# Step 3 — Land Surface Temperature (LST) Analysis: Audit & Documentation

**Scope:** `LST_analysis/LST_DAY_NIGHT.ipynb` (24 cells, hand-authored, no generator
script; kernel `wildfire_env`, Python 3.10.20), outputs in `LST_analysis/LST_Outputs/`.
Read-only audit based on the notebook's actual executed cell outputs, the saved plots,
and the CSV/GeoTIFF exports on disk — no notebook edits or re-runs were made.

---

## What Was Done

Step 3 turns the raw MOD11A2.061 8-day, 1km MODIS Terra LST archive (1,013 composites,
2000–2022, downloaded as GeoTIFF via NASA AppEEARS rather than HDF) into a set of
pixel-level thermal features for the fire-risk model, and quantifies how those features
relate to Step 1's real fire points:

1. **QA-filtered day/night LST** — `LST_Day_1km`/`LST_Night_1km` bands filtered against
   `QC_Day`/`QC_Night` (keeps Good/Marginal reliability only).
2. **Diurnal Temperature Range (DTR)** = Day − Night, its own derived feature.
3. **Climatology** — per-pixel, per-calendar-month baseline over a fixed 2001–2020
   reference period.
4. **Anomalies** — Day, Night, and DTR deviation from climatology, at monthly resolution.
5. **Mann-Kendall trend test** — τ, S, and trend direction per pixel for Day, Night, and
   DTR at monthly resolution, GPU-tiled (row-tiled to bound VRAM use).
6. **Significance testing, now dual-reported** — a normal-approximation p-value (erf-based,
   same method as Step 2/NDVI), reported both as **raw uncorrected p<0.05** and, since a
   2026-08-21 fix, as **Benjamini-Hochberg FDR-corrected** (α=0.05; Wilks 2006, *J. Appl.
   Meteor. Climatol.* 45:1181). Verified present and landed correctly: `requirements.txt`
   and the import cell aside (see Gaps below), the notebook literally imports
   `from statsmodels.stats.multitest import multipletests`, applies it separately to each
   of Day/Night/DTR's full valid p-value set, and stores `sig_fdr`/`p_fdr` per pixel. Real
   executed numbers confirm the documented shrinkage: Day 1,063,120 → 393,838 significant
   pixels (−63%), Night 234,318 → 17,935 (−92%), DTR 2,545,287 → 2,290,051 (−10%), all
   recorded in both `LST_trend_summary.csv` (raw and FDR columns side by side) and paired
   GeoTIFFs (`MannKendall_pvalue_*`, `MannKendall_qvalue_FDR_*`,
   `MannKendall_significant_FDR_*`).
7. **Fire thermal footprint** — Step 1's 541,545 forest-fire points rasterized onto the
   LST grid via the exact affine transform (0 excluded as out-of-bounds); 270,655 pixels
   (2.02% of the in-India grid) register ≥1 fire detection.
8. **NDVI-grid reprojection** — key monthly features reprojected via
   `rasterio.warp.reproject` onto Step 2's exact 3641×3504 grid for pixel-for-pixel
   stacking in Step 6.

## How It Was Done

The notebook streams all 1,013 composites in a single pass (859.4 sec measured runtime),
accumulating running sums/counts for climatology and monthly aggregation rather than
materializing a dense (T, H, W) cube — the full native-resolution stack at
3,781×3,536 px would be ~217 GB across all four bands, versus the ~37.2 GB accumulator
footprint actually used. Only the much smaller monthly-resolution arrays (266 months) are
retained for trend analysis and export. Mann-Kendall S is computed via a GPU-tiled
(CuPy, row_tile=200) full lag sweep — `sign(x_{t+lag} − x_t)` summed over every valid
`(i, j)` pair — completing in 109.1 sec for all three metrics (Day/Night/DTR) together.
The India boundary (`India_State_Boundary.shp`, dissolved, reprojected from its raw
EPSG:3857 declaration) masks the grid to 4,184,729 in-India pixels (31.3% of the full
grid). Fire points are rasterized using the same affine-transform row/col convention used
throughout the project (not a nearest-neighbor spatial join).

## Why It Was Done This Way

- **Streaming rather than dense-array processing** is a hard memory constraint, not a
  stylistic choice — the raw 8-day cube is too large to hold safely even on a large
  workstation, and this pattern matches the project's established "GPU where it matters,
  stream where memory forces it" convention from Steps 1–2.
- **DTR, climatology/anomaly, and a trend test are genuine additions beyond raw day/night
  values** because Biswas et al. (2025) — this project's reference paper — use the two
  MOD11C3 monthly bands as static, undifferentiated predictors with no seasonal baseline,
  no anomaly, and no significance-tested trend. Deriving DTR and anomaly captures thermal
  dynamics (atmospheric/vegetation moisture control, deviation from expected seasonal
  state) the raw values alone cannot.
- **FDR correction was added specifically because ~4.17M independent per-pixel
  significance tests make a raw p<0.05 threshold produce a large number of chance false
  positives** — a documented, literature-driven fix (Wilks 2006) consistent with the
  project's stated "every methodological choice must be Q1/A*-cited" standard. It changes
  only which pixels are labeled significant, not τ, S, or trend direction, and both raw
  and corrected counts are kept for transparency.
- **Reprojection onto the NDVI grid** (rather than any other step's grid) follows the
  project-wide convention that Step 2 establishes the canonical 1km analysis grid every
  later step must match.

## Impact on Spatial Fire Mapping in India

The fire-coincidence analysis (Cell 18/20 outputs, `LST_Fire_Coincidence_Monthly.png`)
is the step's clearest fire-relevant finding: mean LST Day anomaly at fire pixel-months is
**+0.75°C**, versus **−0.09°C** grid-wide — an 0.84°C gap between where/when fires occur
and the general grid. LST Night anomaly shows the same pattern at smaller magnitude
(+0.31°C at fire pixel-months vs. +0.02°C grid-wide). This is a real, quantified signal
that anomalously warm conditions — not just seasonally hot conditions — coincide with
forest fire occurrence, distinct from what a raw/undifferentiated LST value could show.
Spatially, the Mann-Kendall τ maps show nighttime LST warming (τ mean +0.043, FDR-significant
warming at 17,927 pixels, almost all of the FDR-significant Night set) outpacing daytime
change (τ mean −0.041, FDR-significant cooling dominates at 381,512 pixels), consistent
with DTR significantly narrowing at the large majority of its FDR-significant pixels
(2,274,723 narrowing vs. 15,328 widening) — a genuine India-wide thermal signature that
downstream vegetation-stress and moisture-balance reasoning in the CDR-PINN design can
draw on.

## Comparison with Biswas et al. (2025)

Biswas et al.'s Table 3 uses two static predictors — LST nighttime (10.1% importance,
8.9% contribution) and LST daytime (9.6% importance, 4.5% contribution) — both raw
MOD11C3 v006 monthly values at 0.05°, with no DTR, anomaly, or trend treatment. This
project instead carries forward **five** derived LST features into the Step 6/7 feature
stack: `lst_day_anomaly_mean`, `lst_night_anomaly_mean`, `dtr_anomaly_mean`,
`lst_day_mk_tau_monthly`, `lst_night_mk_tau_monthly` — no raw climatological mean is
carried forward at all, DTR appears only as its anomaly (not DTR's own trend τ, despite
`mk_dtr_monthly` being fully computed in Step 3 — see Gaps).

Checking this actually pays off required going to Step 7's trained models
(`Integrated_Analysis/Model_Outputs/Feature_Importance.png`,
`MaxEnt_Feature_Importance.png`): in the Random Forest's Gini importance, all five LST
features rank in the bottom half of 55 features (`lst_night_mk_tau_monthly` highest among
them at roughly rank 20, `lst_day_anomaly_mean` near the bottom); the same ordering holds
in MaxEnt's permutation importance. In other words, **this project's DTR-plus-anomaly-plus-
trend treatment of LST contributes far less to the trained models than Biswas et al.
report for their raw day/night values (10.1%/9.6%)** — a genuine, quantifiable, and so far
undocumented finding that the richer LST feature engineering here does not translate into
higher model weight than the reference paper's simpler treatment, likely because
`forest_frac_baseline` and the NDVI-derived features dominate. This comparison exists only
implicitly (visible if you cross the two steps' outputs) — it is not stated anywhere in
Step 3's own docs.

## Completeness Audit: Gaps Found

1. **`requirements.txt` is missing `statsmodels`** (Priority: high, quick fix). The
   2026-08-21 FDR fix added a hard `from statsmodels.stats.multitest import
   multipletests` import in Cell 4, but `LST_analysis/requirements.txt` still lists only
   `geopandas, numpy, pandas, matplotlib, tqdm, rasterio, pyogrio`. A fresh
   `pip install -r requirements.txt` environment will fail at that import. This is a real
   reproducibility break, not a style nit.
2. **README's Step 3 section is stale relative to the FDR fix** (Priority: medium). The
   markdown trend table in `LST_analysis/README.md` still shows only the raw p<0.05
   counts; it never shows the FDR-corrected counts even though the notebook, CSV, and
   GeoTIFF exports all now report both. A reader relying on the README alone would see
   pre-correction numbers as if they were final.
3. **No spatial climatology or anomaly maps are ever plotted** (Priority: medium). Day/Night
   climatology and Day/Night/DTR anomaly are all exported as GeoTIFFs but never rendered
   as a figure — only the Mann-Kendall τ maps and the 8-day/monthly time series appear in
   `LST_Summary_Analysis.png`. For a Q1 submission, a spatial climatology map (showing the
   Himalayan/Deccan/coastal thermal contrast) and an anomaly map are standard and currently
   absent as visuals (data exists, just unvisualized).
4. **FDR significance masks are exported but never visualized** (Priority: medium). The
   entire point of the 2026-08-21 fix — which pixels survive multiple-testing correction —
   has no map in the notebook; a reader only sees aggregate counts, not where the
   FDR-significant trend pixels are located.
5. **No seasonal-cycle (single averaged annual profile) plot** (Priority: low). The time
   series shows the full 22-year record but never an averaged Jan–Dec climatological
   cycle for Day/Night/DTR, which would make the amplitude and phase of the seasonal
   signal easier to read at a glance.
6. **No validation against an independent LST/temperature product** (Priority: medium for
   a Q1 paper). No cross-check against ERA5-Land skin temperature, AVHRR, or
   ground-station data exists — MOD11A2's own accuracy is taken as given.
7. **No ablation/sensitivity analysis** (Priority: low-medium). No test of alternative
   climatology baseline windows (e.g. shorter/longer than 2001–2020) or comparison against
   an alternative LST product (e.g. MOD11C3, the actual Biswas et al. product, vs. this
   project's MOD11A2) exists.
8. **DTR's own Mann-Kendall trend (τ) is computed but not carried into the feature stack**
   (Priority: low-medium, a real but silent feature-parity gap). `mk_dtr_monthly` is fully
   computed and exported (`MannKendall_tau_DTR_monthly.tif`, FDR-corrected significance
   included), but Step 6/7's feature list has `lst_day_mk_tau_monthly` and
   `lst_night_mk_tau_monthly` only — no `dtr_mk_tau`. Since DTR is otherwise treated as a
   first-class feature (its own anomaly is carried forward), this looks like an
   unintentional omission rather than a deliberate exclusion.
9. **No explicit written comparison against Biswas et al.'s LST treatment, and no
   cross-reference to Step 7's feature-importance result** (Priority: medium, addressed by
   this document but not by the project's own artifacts). Neither the notebook nor the
   README states what the DTR/anomaly/trend treatment adds over Biswas et al.'s raw values,
   nor references that Step 7 shows these engineered features actually rank low in trained
   model importance — a finding worth having in the paper's discussion either as a
   limitation or as a motivation for the CDR-PINN's more structured treatment of thermal
   drivers.

**What's already solid and should not be re-worked:** the streaming/GPU architecture, the
dual raw+FDR significance reporting (correctly implemented and already committed,
`b19d2f1`), the exact affine-transform fire-point rasterization, the NDVI-grid
reprojection for downstream stacking, and the fire-vs-grid thermal anomaly comparison are
all genuinely strong and already at publication quality.
