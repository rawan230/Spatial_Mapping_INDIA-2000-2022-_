# Biswas Reference Baseline Specification

**Reference.** Biswas, U., Mahato, S., & Joshi, P. K. (2025). Spatial prediction of forest fires in
India: a machine learning approach for improved risk assessment and early warning systems.
*Environmental Science and Pollution Research*, 32, 4856–4878.

**How this was verified.** Text extracted directly from the user's own copy of the published PDF
(23 pages; `pypdf`), on 2026-09-24. Every entry below cites the page. Entries the paper does not state
are marked **Not reported by Biswas et al.** Nothing is inferred or estimated. The paper's prose is
paraphrased, never reproduced, because the PDF is copyrighted and this repository has a public remote.

---

## 1. Specification

| # | Item | What Biswas et al. report | Page |
|---|---|---|---|
| 1 | Study region | India, 3,287,263 km²; 6°44′N–35°30′N, 68°07′E–97°25′E | 4859 |
| 2 | Study period | Jan 2001 – Dec 2020 (fire analysis); dataset acquisition windows in Table 2 run 2000–2022 | 4857, 4859, 4863 |
| 3 | Fire dataset | MODIS Collection 6.1 active-fire points (Terra + Aqua) | 4859 |
| 4 | Fire-label definition | Fire points clipped (in GIS) to vectorised forest pixels of ESA-CCI LCCS maps; forest = codes {50, 60, 61, 62, 70, 71, 72, 80, 81, 82, 90, 100, 110} (Sannigrahi et al. 2018); non-forest 10–40, 120–210 | 4863 |
| 5 | Fire confidence / type filtering | **Not reported by Biswas et al.** | — |
| 6 | Predictor variables | 15: NDVI, air temperature, specific humidity, LST night, LST day, distance to roads, slope, distance to railways, soil moisture, precipitation, near-surface wind speed, elevation, net longwave radiation flux, aspect, distance to waterways | 4870 (Table 3) |
| 7 | Predictor groups | Climatic (precipitation, air temperature, specific humidity, wind, net LW); biophysical (NDVI, soil moisture); human-activity (distance to roads/railways/waterways); topographic (slope, aspect, elevation); LST reported separately | 4871 |
| 8 | Data sources | FLDAS NOAH01_C_GL_M v001 (air temp, wind, specific humidity; 0.1°, monthly); MOD11C3 v006 (LST day/night; 0.05°, monthly); GPM 3IMERGHHL v06 (precipitation; 0.1°, half-hourly, mm/h); GLDAS NOAH025_M v2.1 (soil moisture; 0.25°, monthly); MOD13C2 v006 (NDVI; 0.05°, monthly); GLDAS NOAH025_3H v2.1 (net LW; 0.25°, 3-hourly); OpenStreetMap 2022 (vector); ESA-CCI LC v2.0.7cds / v2.1.1 (300 m, yearly); MCD64A1.061 (burned area, 500 m) | 4861, 4863 (Table 2) |
| 9 | DEM source (slope/aspect/elevation) | **Not reported by Biswas et al.** (not listed in Table 2) | — |
| 10 | Distance algorithm | **Not reported by Biswas et al.** ("proximity" only) | 4857 |
| 11 | Spatial resolution of model input | All layers rasterised to 0.25° × 0.25° | 4861 |
| 12 | Temporal aggregation of predictors into the model | **Not reported by Biswas et al.** (e.g. which months/years were averaged for each raster) | — |
| 13 | Feature engineering (anomaly, trend, decomposition) | **Not reported by Biswas et al.** No derived temporal features are described; predictors are used as variable levels | — |
| 14 | Missing-value handling | **Not reported by Biswas et al.** | — |
| 15 | Multicollinearity handling | A correlation matrix with a 0.7–0.8 screening threshold is described; no variable is reported as removed | 4861–4862 |
| 16 | Train/test methodology | Text: 70% of occurrences for training, the remaining 30% for testing. Numbers: 1,830 training and 609 test presences (= 75.0 / 25.0%) | 4864 |
| 17 | Sample definition | "Ten percent" of 2020 forest fires; 11,360 points (background + presence) | 4864 |
| 18 | Validation methodology | Single random hold-out of presences, AUC against background | 4864, 4870 |
| 19 | Spatial / regional / temporal (unseen-year) validation | **Not reported by Biswas et al.** | — |
| 20 | Model | MaxEnt 3.4.4, maximum 10,000 iterations | 4864 |
| 21 | Feature classes / regularisation | **Not reported by Biswas et al.** | — |
| 22 | Statistical methods | Pearson correlation matrix (Fig. 11); fire-count trends by decade (Fig. 7); 25 km × 25 km fire-density grid, 7,851 cells | 4864, 4868–4870 |
| 23 | Variable-importance method | MaxEnt permutation importance (training-AUC drop, normalised %); MaxEnt percent contribution; jackknife (training gain, test gain, test AUC; Fig. 10) | 4864, 4870 |
| 24 | Reported performance | Training AUC **0.894**; test AUC **0.879** | 4870 |
| 25 | Sensitivity, specificity, precision, F1, AP, Brier, calibration | **Not reported by Biswas et al.** | — |
| 26 | Reported limitations | No dedicated limitations section. The conclusion notes that MaxEnt percent-contribution values vary with the optimisation path | 4876 |

## 2. Reported quantitative results (verbatim numbers)

### 2.1 Variable importance (Table 3, p. 4870)

| Variable | Permutation importance (%) | Percent contribution (%) |
|---|---:|---:|
| NDVI | 22.3 | 28.4 |
| Air temperature | 13.1 | 3.8 |
| Specific humidity | 13.0 | 15.0 |
| LST (night-time) | 10.1 | 8.9 |
| LST (daytime) | 9.6 | 4.5 |
| Distance to roads | 5.7 | 2.6 |
| Slope | 5.6 | 16.7 |
| Distance to railways | 4.6 | 4.9 |
| Soil moisture | 3.8 | 0.9 |
| Precipitation | 3.6 | 1.7 |
| Near-surface wind speed | 2.4 | 4.3 |
| Elevation | 2.4 | 2.0 |
| Net longwave radiation flux | 1.8 | 0.6 |
| Aspect | 1.7 | 3.8 |
| Distance to waterways | 0.5 | 1.7 |

**Group totals stated in the text (p. 4871):** climatic 33.9%, biophysical 26.1%, human-activity
10.8%, topographic 9.7%. **Audit check:** these sums reproduce exactly from the **permutation
importance** column (3.6+13.1+13.0+2.4+1.8 = 33.9; 22.3+3.8 = 26.1; 5.7+4.6+0.5 = 10.8;
5.6+1.7+2.4 = 9.7). They do not reproduce from the contribution column. The paper's prose calls them
"contributed", so the group figures are **permutation importance**, not percent contribution.
LST (19.7%) is outside all four groups; the four groups plus LST total 100.2% (rounding).

### 2.2 Other quantitative results

| Result | Value | Page |
|---|---|---|
| Train / test AUC | 0.894 / 0.879 | 4870 |
| Forest-fire incidents 2001–2010 / 2011–2020 | 232,189 / 243,761 | 4865 |
| Annual share of 2001–2020 fires | 2009 8.36% … 2002 0.88% (20 values; sum 99.99%) | 4865 |
| Pearson r with fire-point density | NDVI 0.43; slope 0.40; wind −0.32; net LW 0.28; soil moisture 0.27 | 4868–4870 |
| Jackknife | Qualitative only: specific humidity gives the highest gain alone and the largest loss when omitted; no numbers are given in the text (Fig. 10 is a chart) | 4866 |
| Susceptibility classes | Five classes; the class-break method is **Not reported by Biswas et al.** | 4870 |

## 3. Internal inconsistencies in the reference (disclosed, not resolved)

1. **Train/test proportion.** The text says 70/30; the counts (1,830 / 609) are 75/25.
2. **Sample size.** "Ten percent" of 2020 forest fires does not match 1,830 + 609 = 2,439 presences.
   Biswas's own derived 2020 count is 16,277 points (10% ≈ 1,628). The 11,360-point total is not
   decomposed into background and presence. The Biswas-style baseline tests whether 2,439 equals the
   number of unique 0.25° cells with 2020 forest fires.
3. **Importance naming.** The group totals come from the permutation-importance column but are
   described as contributions (Section 2.1).
4. **Dataset period vs model period.** Table 2 acquisition windows extend to 2022; the analysis and
   model are described as 2001–2020 (fire analysis) and 2020 (MaxEnt fitting).

## 4. What a "reproduction" can and cannot mean here

The original Biswas rasters, presence/background sample and MaxEnt settings are **not available**.
Any "Biswas-style" number in this audit is a re-implementation with this project's own data
(`results/code/biswas_style_baseline.py`), and is labelled as such everywhere. It is never presented
as the original Biswas et al. result.
