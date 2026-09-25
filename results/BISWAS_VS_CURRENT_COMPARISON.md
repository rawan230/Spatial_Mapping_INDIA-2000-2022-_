# Biswas et al. (2025) vs the Current Study

Biswas et al. (2025) is the reference framework. Nothing below ranks the two studies on a
metric unless both were evaluated in a comparable way; each comparison carries a comparability label.
"Not reported by Biswas et al." means exactly that. No missing value has been estimated.

## 1. Reference-study contribution matrix (Phase 38)

| Component | Biswas et al. | Current study (v2) | Status | Scientific contribution |
|---|---|---|---|---|
| Fire data | MODIS C6.1, 2001–2020; model uses 2020 | MODIS C6.1, 2000-11 – 2022-12, 541,545 forest points (reproduced exactly) | EXTENDED | Longer record; label misregistration found and fixed |
| NDVI | MOD13C2 0.05° | MOD13A3.061 1 km + 5 derived features | MODIFIED + EXTENDED | Finer resolution; valid trend tests |
| LST | MOD11C3 0.05° monthly | MOD11A2.061 1 km 8-day → monthly | MODIFIED (product) | Resolution effect tested: negligible |
| Climate (T, q, wind) | FLDAS levels | FLDAS levels + Seasonal-Kendall trends | REPRODUCED + EXTENDED | Same source |
| Humidity | Specific humidity | Specific humidity (per pixel) + derived RH | REPRODUCED + EXTENDED | — |
| Precipitation | GPM 3IMERGHHL | FLDAS (CHIRPS forcing) | MODIFIED (source) | Not equivalent |
| Soil moisture, net LW | GLDAS | FLDAS | MODIFIED (source) | Not equivalent |
| LULC | Forest filter only | Forest filter + 21 class fractions (2001) + forest fraction | EXTENDED | +0.003 / +0.008 AUC (paired) |
| Elevation / slope / aspect | DEM not reported; 0.25° | SRTMGL3 90 m → 1 km (Horn) | MODIFIED | Slope at 0.25° is a different quantity (~20× smaller) |
| Roads / railways / waterways | OSM 2022, method not reported | OSM 2022, EDT, geodesically validated | REPRODUCED | Accuracy quantified |
| Temporal features | None | Seasonal-Kendall τ and Sen slopes | NEW | +0.001 / +0.006 AUC |
| Spatial features | None | CVSI, LISA | NEW | Included in the +0.005 / +0.012 predictor gain |
| ML model | MaxEnt 3.4.4 | RF, MaxEnt (elapid), logistic regression | EXTENDED | RF > MaxEnt by +0.008 / +0.031 |
| Physics | None | CDR-PINO | NEW | **No controlled accuracy benefit**; field static; PDE not satisfied |
| Spatial validation | Not reported by Biswas et al. | 2° block CV (3 folds) | NEW | Establishes the transfer gap |
| Temporal validation | Not reported by Biswas et al. | Leave-years-out + persistence nulls | NEW | Nulls are essential to interpret it |
| Regional validation | Not reported by Biswas et al. | Leave-one-region-out (6) | NEW | Largest drop of all tracks |
| Interpretability | Permutation importance, contribution, jackknife | Permutation (feature + group), PDP, reimplemented jackknife | REPRODUCED | Ranking differences are mostly a model-family effect |
| Leakage control | Not reported by Biswas et al. | 7 sources audited and quantified | NEW | — |
| Final output | 5-class MaxEnt probability map (0.25°) | 1 km RF relative score + forest-quantile classes, with provenance | MODIFIED | — |

## 2. Manuscript table (Phase 39)

**Table X. Comparison between the reference framework of Biswas et al. (2025) and the present framework.**

| Aspect | Biswas et al. (2025) | Present study |
|---|---|---|
| Study period | 2001–2020 (MaxEnt fitted on 2020 records) | 2000-11-01 – 2022-12-15 |
| Study region | India | India (37-state dissolved boundary) |
| Fire data | MODIS C6.1, forest-filtered (ESA-CCI) | MODIS C6.1, forest-filtered per acquisition year (ESA-CCI/C3S) |
| Predictors | 15 | 15 Biswas-equivalent variables (16 columns; aspect as sin/cos) + 39 additional (55 in total) |
| LST product | MOD11C3 v006 (0.05°, monthly) | MOD11A2.061 (1 km, 8-day) |
| Climate product | FLDAS (T, q, wind); GLDAS (soil moisture, net LW) | FLDAS for all |
| Precipitation source | GPM 3IMERGHHL v06 | FLDAS (CHIRPS-based forcing) |
| Humidity variable | Specific humidity | Specific humidity + derived relative humidity |
| Terrain data | Not reported by Biswas et al. | SRTMGL3 (90 m), Horn's method |
| Accessibility data | OpenStreetMap 2022 | OpenStreetMap 2022 (Geofabrik), Euclidean distance transform |
| Spatial resolution | 0.25° | 1/120° (~0.93 km); CDR-PINO 256 × 256 (~12 km) |
| Temporal resolution | Monthly inputs, static model | Monthly inputs; static RF/MaxEnt; monthly CDR-PINO rollout |
| Feature engineering | Variable levels | Levels + Seasonal-Kendall trends + NDVI stress/cluster indices + land-cover fractions |
| Model | MaxEnt | RF, MaxEnt, CDR-PINO |
| Physics | None | CDR-PINO (no accuracy benefit under controlled comparison) |
| Spatial validation | Not reported by Biswas et al. | 2° spatial-block CV |
| Temporal validation | Not reported by Biswas et al. | Leave-years-out with persistence baselines |
| Regional validation | Not reported by Biswas et al. | Leave-one-region-out |
| Interpretability | Permutation importance, contribution, jackknife | Permutation importance (feature and group), partial dependence |
| Final output | Five-class probability map | Relative-susceptibility score + five classes (quantiles over forest pixels) |

## 3. Quantitative comparison (Phases 7–8)

| Result | Biswas et al. | Current (recalculated) | Comparability |
|---|---|---|---|
| Test AUC under a Biswas-style protocol | 0.879 | 0.893 ± 0.009 (reimplementation; 10 presence splits) | **Moderate:** same protocol type, five different data sources, different presence count |
| Train AUC under a Biswas-style protocol | 0.894 | 0.902 ± 0.003 | Moderate |
| Pixel-level test AUC (RF v2, 1 km) | Not reported by Biswas et al. | 0.975 all / 0.897 forest | **Not directly comparable** |
| NDVI permutation importance | 22.3% | 19.0% | Moderate |
| Air-temperature importance | 13.1% | 13.2% | Moderate |
| LST night / day importance | 10.1 / 9.6% | 14.3 / 8.1% | Moderate |
| Specific-humidity importance | 13.0% | 3.1% | Moderate — **not reproduced** |
| Elevation importance | 2.4% | 10.7% | Moderate — not reproduced |
| Slope importance | 5.6% | 5.8% | Limited (slope definition is scale-dependent) |
| r(NDVI, fire density) | 0.43 | 0.456 | Moderate |
| r(slope, fire density) | 0.40 | 0.223 | Limited |
| r(wind, fire density) | −0.32 | −0.363 | Moderate |
| Annual fire counts 2001–2020 | Derived from reported shares | +0.5% to +2.4%, r = 0.99996 | High |
| Sensitivity, specificity, precision, F1, calibration | Not reported by Biswas et al. | `final/FINAL_METRICS.csv` | — |

Recommended wording for the paper: *"Under a Biswas-style protocol reimplemented with this study's
data, test ROC-AUC was 0.893 ± 0.009, compared with 0.879 reported by Biswas et al. (2025) under
their own data. The pixel-level ROC-AUCs of this study (0.975 over all pixels; 0.897 over forest
pixels) are not comparable with Biswas et al.'s presence–background AUC."*

## 4. Why variable importance differs (Phase 37)

The differences are not treated as contradictions. The controlled evidence points to the following causes:

- **Model family.** Under the same Biswas-15 inputs, MaxEnt ranks NDVI ≫ LST night > LST day >
  elevation > specific humidity. RF spreads the importance across correlated variables. MaxEnt's
  additive structure concentrates it on forest fraction (v2) or NDVI (Biswas-15).
- **Resolution and scale.** Slope computed at 0.25° is ~20× smaller and only r = 0.70 correlated
  with the 90 m slope. Slope importance and correlation are not comparable across the two scales.
- **Source differences.** Soil moisture and net LW (FLDAS vs GLDAS) correlate more strongly with
  fire density here (0.39 / 0.36 vs 0.27 / 0.28).
- **Specific humidity.** Its dominance in Biswas's jackknife is not reproduced (alone: test AUC
  0.723 vs NDVI 0.799). With specific humidity from the same FLDAS product, the most plausible
  remaining causes are the sample and presence definition (their 2,439 presences are unexplained) and
  the MaxEnt feature classes and regularisation (not reported by Biswas et al.). This cannot be resolved
  without their data.
- **Elevation / terrain.** Its importance is model-specific. It is high in CDR-PINO (only 7
  covariates) and moderate in the 0.25° MaxEnt, but redundant with the full 1 km predictor set
  (ΔAUC −0.0001 when removed).
