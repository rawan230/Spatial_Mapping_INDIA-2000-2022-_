# Final Manuscript Numbers (verified)

Use only these values. Each has been recalculated in this audit. The full claim-by-claim table is in
`audit/MANUSCRIPT_NUMBER_AUDIT.csv`, with sources in `final/*.csv`. Always state the population, the
prevalence and the grid next to an AUC.

## Data

- **Forest-fire points:** 541,545 (MODIS C6.1, 2000-11-01 to 2022-12-15). Filter stages:
  2,804,373 → 2,801,347 → 1,599,471 → 1,599,466 → 541,545.
- **Confidence and type:** 4.29% of points have confidence < 30 and 0.21% have type ≠ 0.
  Filtering either changes ROC-AUC by < 0.001.
- **Annual counts vs Biswas et al.** (derived from their published shares): +0.5% to +2.4%,
  r = 0.99996 (2001–2020).
- **Grid:** EPSG:4326, 1/120°, 3,641 × 3,504; 4,160,768 analysis pixels, of which 1,197,538 are forest.
- **Fire-affected pixels:** 268,411 (containing-pixel rule). Prevalence 6.45% over all pixels and 22.4%
  over forest pixels.
- **Forest cover of India** (ESA-CCI, 13 codes): 18.3–19.3%. Do **not** cite 9.86–10.43%, which is
  computed over the download rectangle.
- **Features:** 55 (v2). Distance accuracy against geodesic distances: RMSE 0.31 / 0.65 / 0.32 km
  (roads / railways / waterways).

## Trends (Seasonal Kendall, BH-FDR q < 0.05)

- **NDVI:** 3,552,278 pixels greening and 72,305 browning; median Sen slope +0.0026 yr⁻¹.
- **LST day:** 2,435,163 pixels cooling (median −0.050 °C yr⁻¹).
- **LST night:** 2,080,747 pixels warming (+0.024 °C yr⁻¹).
- **DTR:** 3,273,301 pixels narrowing (−0.077 °C yr⁻¹).
- **FLDAS air temperature:** 9,988 / 29,056 FLDAS pixels significant (7,620 decreasing). Replaces the
  "trend is noise" statement.
- **Specific humidity:** 26,373 / 29,056 pixels increasing.
- **NDVI global Moran's I** (India cells, 8 × 8 block means): 0.9456 (z = 494.2, p = 0.001).

## Classical models (1 km, test set; all pixels | forest pixels)

| Model / track | ROC-AUC | AP |
|---|---|---|
| RF v2, random split | 0.975 \| 0.897 | 0.720 \| 0.721 |
| MaxEnt v2 (150k rows), random split | 0.967 \| 0.866 | 0.663 \| 0.664 |
| RF, Biswas-15 predictors, random split | 0.970 \| 0.885 | 0.692 \| 0.698 |
| RF v2, 2° spatial blocks (3 folds) | 0.959 \| 0.838 | 0.582 \| 0.583 |
| RF v2, leave one region out (6) | 0.935 \| 0.782 | 0.412 \| 0.413 |
| RF v2, unseen years | 0.965 \| 0.872 | 0.282 \| 0.282 |
| Persistence null, unseen years | 0.807 \| 0.744 | 0.131 \| 0.146 |

- **Paired effects (DeLong, identical pixels):** added predictors over Biswas-15 +0.005 | +0.012;
  RF over MaxEnt +0.008 | +0.031.
- **Calibration:** RF v2 ECE 0.064 | 0.219; MaxEnt v2 ECE 0.015 | 0.054. No calibrated uncertainty
  estimate was established.

## CDR-PINO (256 × 256 grid, 22,542 cells; mean of 3 seeds; all cells)

| Track | No physics | Full CDR | RF, same cells & covariates | Null baseline |
|---|---|---|---|---|
| Random split (prev. 42%) | 0.945 | 0.939 | 0.980 | — |
| 2° spatial blocks | 0.724 | 0.719 | 0.974 | — |
| Leave one region out | 0.614 | 0.570 | 0.959 | — |
| Unseen years (cell-months, prev. 2.46%) | 0.904 | 0.893 | 0.972 (with month) | 0.908 (frequency), 0.930 (seasonal) |

- **Physics term ablation** (random split): none 0.945, diffusion 0.924, diffusion + advection
  0.939, full 0.939. Full minus none is −0.006 (p < 0.02 in every seed).
- **Physics cost:** 2.3–2.4× training time.
- **Trained field:** median |∂u/∂t| ≤ 0.002 month⁻¹; the PDE residual is 74–616× |∂u/∂t|, and the
  diffusion term is ≤ 0.3% of the right-hand side.

## Biswas-style reimplementation (0.25°, 2020 presences, MaxEnt)

- **AUC:** test 0.893 ± 0.009 (10 splits); train 0.902 ± 0.003. Biswas et al. reported 0.879 / 0.894
  under their own data (comparability: moderate).

## Numbers to remove or reword

- **"Beats Biswas (0.9576 vs 0.879)"** — not comparable, and the number cannot be traced to any output.
- **"Temporal generalisation strong (0.8960)"** — it is below the persistence nulls.
- **"Each mechanism contributes measurable value (0.602 / 0.924 / 0.940)"** — contradicted by the
  controlled ablation.
- **"RF 0.950 vs CDR 0.751 on the same fold scheme"** — the folds are not the same. Use the
  same-cells values above.
- **"Specific humidity should read relative humidity"** — incorrect; both are predictors.
- **"National forest cover ~10%"** — the correct figure for India is 18.3–19.3%.
- **"MK significant pixel counts"** and **"Moran's I 0.8322"** — replace with the values above.
- **"Elevation dominance" as a driver finding** — it is specific to CDR-PINO's 7 covariates.
- **"Zero-shot super-resolution", "resolution independence", "instance-wise fine-tuning"** — not
  evaluated; present as future work only.
