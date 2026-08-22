# Why the 22 ESA-CCI Land-Cover Classes Are Model Features, Not Just a Mask

**Question asked:** Biswas et al. (2025) use only 15 predictor variables. Why does
this project's Random Forest / MaxEnt feature set (57 columns as of the
2026-08-22 specific-humidity retrain) include 22 separate `landcover_frac_LC22_*`
columns — doesn't that inflate dimensionality and computational cost for little
benefit?

## What these 22 columns actually are

Step 6 (`Integrated_Analysis/Step6_Integrated_FireRisk_Analysis.ipynb`) takes the
yearly ESA-CCI/C3S 22-class land-cover raster and, for each analysis pixel,
computes the **fraction of that pixel's footprint occupied by each of the 22
Level-1 LCCS classes** (cropland-rainfed, cropland-irrigated, tree-broadleaved-
deciduous, grassland, urban, water, snow-and-ice, etc.) — a soft/fractional
composition encoding, not a single dominant-class label. This is necessary because
the raw LULC product's native resolution is finer than the analysis grid, so any
one analysis pixel is genuinely a mixture of underlying classes, not a pure one.

## Why Biswas et al.'s 15-variable set has no equivalent

Checked directly against the reference paper's Table 2/Table 3 (verified via
direct PDF extraction, see `reference_biswas2025_primary_paper` memory): ESA-CCI
land cover appears in their Table 2 as a dataset used **only to filter fire
points to forest pixels** — it is explicitly **not** one of the 15 MaxEnt
predictor variables in their Table 3. Biswas et al. never test whether the
*type* of vegetation around a pixel (deciduous forest vs. cropland vs. grassland)
carries independent predictive signal beyond NDVI/forest-fraction — they discard
that information after using it once for masking.

This project's inclusion of the 22 fractional columns as actual model features
is a deliberate **extension beyond the reference paper**, not an oversight:
different land-cover types carry genuinely different fuel loads, flammability,
and human-proximity signals (e.g., cropland-adjacent forest edges burn for
different reasons than continuous evergreen canopy), and Biswas et al. simply
never tested this. It's consistent with this project's stated methodology
(CLAUDE.md: "extended with real fire-point integration and GPU-vectorized
statistics not present in the reference paper").

## Does it actually help, or is it just dimensional bloat?

Checked directly against the trained Step 7 Random Forest (57 features,
`max_depth=25, min_samples_leaf=3`, the current headline model, test AUC=0.9704):

| Metric | Value |
|---|---:|
| Land-cover columns in the feature set | 22 / 57 (38.6% of all features) |
| Their **combined** Gini importance | 0.1529 (15.3% of total importance) |
| Importance concentrated in top 4 classes (60/10/20/100) | 0.1365 (89.3% of the land-cover group's own total) |
| Land-cover classes with importance < 0.001 each | 14 / 22 |
| Land-cover classes with importance < 0.0001 each (~zero) | 8 / 22 |

The honest picture: **land cover as a group is genuinely useful** (15.3% of
total importance is real, not noise — it's driven by `landcover_frac_LC22_60_
tree_broadleaved_deciduous` alone ranking #5 overall at 6.5%, ahead of terrain
slope and elevation). But that usefulness is **concentrated in 4 classes**:

| Class | Gini importance | What it is |
|---|---:|---|
| LC22_60 tree_broadleaved_deciduous | 0.0653 | dominant forest type at fire-affected pixels |
| LC22_10 cropland_rainfed | 0.0314 | human-adjacent land use, fire-edge proxy |
| LC22_20 cropland_irrigated | 0.0201 | same, irrigated variant |
| LC22_100 mosaic_tree_and_shrub | 0.0197 | mixed/degraded forest edge |

The other 18 classes — snow_and_ice, tree_mixed, lichens_and_mosses, tree_flooded
fresh/saline water, sparse_vegetation, urban, water, etc. — are geographically
rare or simply irrelevant to forest-fire risk in India's actual land-cover
distribution, and 8 of them contribute next to nothing (<0.0001 each; two,
`LC22_140_lichens_and_mosses` and `LC22_160_tree_flooded_fresh_or_brakish_water`,
are ~10⁻⁷–0 in this run).

## Computational cost, honestly assessed

- **Random Forest**: cost is dominated by row count (3.3M training rows) and
  tree depth, not feature count — `max_features='sqrt'` means going from 35→57
  candidate features only grows per-split candidate evaluation from √35≈5.9 to
  √57≈7.5 (≈28% more per split), a real but modest cost, not the dominant driver
  of Step 7's ~218s RF train time.
- **MaxEnt**: more feature-count sensitive (hinge/product feature transforms
  scale more directly with input dimensionality) — the 22 land-cover columns are
  a real, non-trivial contributor to MaxEnt's much longer ~1290s fit time on the
  150k-row subsample, more so than for RF.
- **CDR-PINN**: land-cover fractions are **not used at all** — the PINN's
  covariate stack is a fixed 7-channel set (`ndvi_f1, ndvi_anomaly, forest_frac,
  dryness, slope, dist_roads, elevation`). This concern doesn't apply to the
  physics-informed side of the study.

## Recommendation (not yet acted on — your call)

Given 14/22 classes individually contribute <0.001 and 8/22 are ~zero, a
defensible dimensionality-reduction pass exists: keep the 4 meaningfully-
contributing classes (60, 10, 20, 100) plus maybe 2-3 more above a 0.001
threshold, and collapse the rest into a single `landcover_frac_other` bucket.
This would cut the feature set from 57 to roughly 39-43 columns with
near-zero AUC cost (the dropped classes' combined importance is <2% of total),
and would measurably help MaxEnt's fit time specifically. This is a standard,
citable practice (near-zero-importance feature pruning) but changes the trained
feature set again — flagging it as a recommendation rather than doing it, since
you may want the full 22-class breakdown preserved for the paper's own
land-cover discussion even where individual classes don't move the AUC needle.

## Sources for these numbers

Reproduced directly from the current (post-specific-humidity) Step 7 model:
`Integrated_Analysis/Model_Outputs/Feature_Importance.png` (top-5 verified
identical to the notebook's own printed output), full 57-feature Gini
importance list extracted via a standalone retrain matching the notebook's
exact configuration (`RandomForestClassifier(n_estimators=200, max_depth=25,
min_samples_leaf=3, class_weight='balanced', random_state=42)`, same
`train_test_split(test_size=0.2, stratify=y, random_state=42)`, target column
`fire_ever`, `DROP_COLS=["lon","lat","fire_count","fire_ever"]` — matching
`Step7_FireRisk_Susceptibility_Model.ipynb`'s own configuration cell exactly).
