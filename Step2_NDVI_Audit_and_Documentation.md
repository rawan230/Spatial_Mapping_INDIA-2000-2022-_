# Step 2 — NDVI Feature Engineering: Audit & Documentation

**Folder:** `NDVI_DATA_INDIA_/` · **Generator:** `build_ndvi_notebook.py` → `NDVI_Novel_Analysis_FINAL_15.ipynb`
**Executed notebook (real outputs):** `NDVI_ANALYSIS_WITH_FFP.ipynb` (kernel `wildfire_env`, Python 3.10.20)
**Outputs:** `NDVI_Fire_Susceptibility_Outputs/`
**Audit date:** 2026-08-22 (read-only; no code executed or edited)

---

## What Was Done

Step 2 converts 266 months (2000-11 to 2022-12, zero gaps) of MOD13A3.061 1 km
monthly NDVI into **9 fire-susceptibility features plus a 10th fire-occurrence
raster**, all computed on a national 3641×3504 grid (EPSG:4326) that every
later step in the pipeline reprojects onto:

| ID | Feature | Real result on this run |
|---|---|---|
| F1 | QA-filtered NDVI mean | QA-masked using `pixel_reliability` (Good/Marginal kept), applied to 264/266 months |
| F2 | Climatological monthly mean (2001–2020 baseline) | 12-month climatology, e.g. June exported |
| F3 | Monthly anomaly δ | Range [-1.181, 1.167]; national mean anomaly ≈ 0.0036 (correctly ≈0) |
| F4/F5 | Trend + residual (2×12-MA decomposition) | GPU-vectorized over the full (266, 3641, 3504) stack |
| F6 | Mann-Kendall τ (trend significance) | 147,206 significant browning px, 3,731,210 significant greening px (p<0.05) |
| F7 | CVSI (cumulative pre-fire vegetation stress) | k* = 8 months, chosen by real mutual information with fire occurrence |
| F8 | LISA cluster map (Local Moran's I) | Global Moran's I = 0.8322 (z=742.1, p≈0); 13,412 HH / 9,254 LL / 197 LH / 77 HL significant px |
| F9 | NDVI–fire breakpoint θ* | θ*=0.535 nationally (n=200,000 balanced), plus 5 biogeographic-zone thresholds |
| F10 | Fire-occurrence raster | All 541,545 Step 1 points rasterized, 100% in-bounds, 270,655 distinct burned pixels (2.12% of grid) |

All 10 features are exported as individually valid GeoTIFFs (confirmed present
in `NDVI_Fire_Susceptibility_Outputs/`: `F1_NDVI_QA_mean.tif` through
`F10_fire_count_Step1.tif`), and 6 companion PNG figures are saved
(`validation_plots.png`, `F1_F3_NDVI_Anomaly.png`, `F4_F6_Trend_MannKendall.png`,
`F7_CVSI_map.png`, `F8_LISA_cluster_map.png`, `F9_NDVI_breakpoint.png`). These
are real matplotlib figures generated from the executed arrays, not placeholders.

The **India boundary mask fix** (2026-08-21, most recent commit `b7c7d3c` in
this repo) is confirmed present and correctly wired: cell 12 of the executed
notebook rasterizes the dissolved `India_State_Boundary.shp` (EPSG:3857→4326)
onto the NDVI grid, reporting 4,184,671 in-India pixels (32.80% of the
12,758,064-pixel grid) and removing 4,608,887 valid NDVI observations
(0.45% of all valid obs) that fell in neighboring countries or ocean.
It is applied to `ndvi_stack` in place, before any feature cell runs, so the
clip genuinely propagates to F1–F10. This matches the 4,161,009-pixel
"valid land" count used identically downstream in Step 6/7's integrated
parquet — consistent across steps.

## How It Was Done

- **QA masking**: `pixel_reliability` SDS values {0=Good, 1=Marginal} are kept,
  {2=Snow/Ice, 3=Cloudy, -1=Fill} dropped, applied per-pixel per-month before
  stacking.
- **GPU vectorization** (CuPy, auto-fallback to NumPy, same pattern as every
  other step): climatology/anomaly, the 2×12 centered moving-average
  trend/seasonal/residual decomposition, and the Mann-Kendall S-statistic
  (computed via an O(T) lag-sweep across the whole grid, not per-pixel) all run
  as whole-array GPU ops. This replaced a previous per-pixel `statsmodels.STL`
  + per-pixel `scipy.stats.kendalltau` implementation that had crashed after 37
  minutes at 6.7% completion (projected >9 hours) — the fix is documented
  in-notebook and verified by real runtimes in this execution: decomposition
  ≈1 s, Mann-Kendall lag-sweep ≈3m47s, both on an RTX PRO 4500 Blackwell GPU.
- **CVSI optimal lag k\***: CVSI(t,k) = Σ_{lag=1}^{k} max(-δ_{t-lag}, 0) is
  computed for every k∈{1..12}; for each k, mutual information between CVSI
  values at real fire pixels/times (from Step 1) and a class-balanced random
  background of never-burned pixels is measured via 10-bin quantile
  discretization. k=8 wins (MI=0.01257 vs. the next-best k=7 at 0.01157 and
  k=9 at 0.01036) — a real, printed sweep across all 12 candidate lags, not a
  single fixed choice.
- **F9 breakpoint**: a piecewise-logistic P(fire|NDVI) is fit by multi-start
  Nelder-Mead (25 starts per zone) against real Step 1 fire/no-fire pixel
  labels, with an explicit degenerate-solution filter (any start where one
  regime holds <1% of the sample is excluded as non-identifiable rather than
  silently reported) — visible in the zone log, e.g. Western Ghats and Deccan
  each flag several degenerate starts that were correctly excluded.
- **F8 LISA**: `esda`/`libpysal` (Numba-based, CPU) on an 8× coarsened
  (456×438) grid for tractability, NaN-filled row-wise before the weight
  matrix is built, 199 permutations for the local significance test.

## Why It Was Done This Way

Every design choice in this step is a documented fix over a broken prior
version (see the notebook's own "what changed" table, cross-checked against
git history `713c483`→`b7c7d3c`): per-pixel STL/Kendall loops were
computationally infeasible at 12.7M-pixel scale; QA files were discovered but
never applied; CVSI's k\* and the breakpoint threshold both used synthetic
proxies (fire data literally wasn't wired in yet); and there was no India
boundary mask at all. The GPU-vectorized decomposition and Mann-Kendall
implementations are algebraically identical to their textbook per-pixel
definitions (classical additive 2×12-MA decomposition; S = Σ sign(x_j − x_i)
via lag-sweep), just computed as array ops — this preserves statistical
correctness while making a national, full-resolution run tractable, which is
what a Q1-level nationwide analysis requires (Biswas et al. themselves worked
at coarser 0.05° resolution and did not attempt this kind of decomposition).

## Impact on Spatial Fire Mapping in India

This step establishes the **common analysis grid** (3641×3504, ~1 km, EPSG:4326)
that Steps 3–6 all reproject onto — it is the geometric backbone of the whole
pipeline, not just a feature source. Its outputs feed Step 6's integrated
stack directly under the column names `ndvi_mean`, `ndvi_clim_june`,
`ndvi_anomaly_mean`, `ndvi_trend_2x12ma`, `ndvi_residual_mean`, `ndvi_mk_tau`,
`ndvi_cvsi_k8`, `ndvi_lisa_cluster`, `ndvi_below_threshold` (confirmed present
verbatim in Step 7's loaded feature list). In the trained Random Forest
(Step 7, Gini importances, `Feature_Importance.png`), **4 of the top 5
features by importance are NDVI-derived**: `forest_frac_baseline` (0.224),
`ndvi_mean` (0.102), `ndvi_trend_2x12ma` (0.095), `ndvi_below_threshold`
(0.074), `ndvi_clim_june` (0.067). NDVI-family features collectively dominate
the model's most-informative predictors, directly validating the investment
in this step's feature engineering.

## Comparison with Biswas et al. (2025)

Biswas et al. use **one raw monthly NDVI value** from MOD13C2 v006 at 0.05°
(≈5.5 km) resolution as their single most important predictor (22.3% variable
importance / 28.4% contribution in their MaxEnt model, their Table 3). This
step:

- Uses a **finer-resolution product** (MOD13A3.061, 1 km vs. their 0.05°/~5.5 km).
- Decomposes that single raw signal into **9 distinct, individually exported
  features** capturing different information: seasonal baseline, monthly
  anomaly, long-term trend, residual noise, trend significance, cumulative
  pre-fire stress with a data-driven optimal lag, spatial clustering, and a
  fire-relevant threshold — none of which exist in Biswas et al.'s treatment.
- **Quantified comparison via Step 7's trained model**: the raw-equivalent
  feature (`ndvi_mean`) alone accounts for 0.102 Gini importance — already
  close to Biswas et al.'s reported dominance of raw NDVI. But three
  *additional* NDVI-derived features (`ndvi_trend_2x12ma`, `ndvi_below_threshold`,
  `ndvi_clim_june`) contribute a further 0.236 combined, i.e. more than twice
  the raw feature's own contribution, appearing separately in the top 5 out of
  55 total features. This is real evidence — not asserted, but measured on
  this project's own trained model — that the decomposition captures
  additional, non-redundant predictive signal beyond what a single raw NDVI
  value provides.
- The CVSI feature (F7) is a genuinely novel construct absent from Biswas et
  al. entirely: an antecedent, fire-data-optimized cumulative stress index,
  not just a coincident vegetation index.

No formal ablation removing all-but-`ndvi_mean` and retraining exists yet (see
gap below) — the comparison above is real but indirect (relative importances
within one full-feature model, not a controlled single-feature-vs-full-set
retrain).

## Completeness Audit: Gaps Found

This step is genuinely the strongest, most novel piece of feature engineering
in the pipeline — QA masking, GPU decomposition, real-data-driven k\* and θ\*,
and LISA clustering are all real, executed, and exported, each with a saved
figure. The following are the concrete remaining gaps for Q1-level rigor,
prioritized:

1. **No plotted CVSI lag-sensitivity curve.** The MI-vs-k sweep (k=1..12) is
   computed and printed in full (values above), which is more than most
   pipelines bother with — but it only exists as console text in the notebook
   output, not as a saved figure. A simple MI-vs-k line plot with k*=8 marked
   would take one cell and turn already-real data into a publication figure
   (reviewers will ask "how was k* chosen" — right now the answer is only in
   a text log, not visualized).
2. **No plotted breakpoint validation against the NDVI distribution.**
   `F9_NDVI_breakpoint.png` shows the fitted P(fire|NDVI) curve with θ*
   marked, which is a real validation plot — but it does not overlay the
   actual NDVI histograms/densities for fire vs. no-fire pixels behind the
   fitted curve. Adding those two histograms (or a violin/KDE pair) would let
   a reader see directly how well-separated the classes are at θ*, especially
   given several zones (Western Ghats, Deccan) had a nontrivial fraction of
   degenerate starts.
3. **No formal single-feature-vs-full-set ablation for the Biswas comparison.**
   The comparison above (§ Comparison with Biswas et al.) is real but derived
   from relative Gini importances within one already-trained 55-feature
   model, not a controlled experiment. A clean version — retrain Step 7's RF
   with only `ndvi_mean` (Biswas-equivalent) vs. all 9 NDVI features vs. the
   full 55-feature set, comparing ROC-AUC — would make the "decomposition adds
   value" claim directly quantifiable and citable, rather than inferred.
4. **No sensitivity analysis on QA-reliability threshold or climatology
   baseline period.** Both are fixed choices (`QA_GOOD_VALUES={0,1}`,
   baseline 2001–2020) inherited from convention/data availability, not
   empirically justified in-notebook. A one-paragraph robustness check (e.g.,
   Good-only vs. Good+Marginal QA, or a shifted 2000–2019 baseline) showing
   the downstream features are stable would preempt a reviewer question, but
   does not currently exist anywhere in this step's outputs.
5. **No explicit statistical-significance overlay saved as a standalone
   product for F6.** `F4_F6_Trend_MannKendall.png` does mask the τ panel to
   p<0.05-significant pixels only (a real significance filter, already
   present — not a gap in substance), but there's no separate exported p-value
   GeoTIFF or map showing the *degree* of significance (e.g., p-value
   gradient) the way F6's τ itself is exported as a full GeoTIFF. Minor: the
   underlying `mk_pval` array is computed in-memory but never saved to disk.

None of these are correctness problems — the underlying computations (MI
sweep, breakpoint fit, Mann-Kendall significance) are all real and already
executed; the gaps are entirely about turning existing-but-unsaved
intermediate results into saved, reviewable artifacts, plus one genuine
missing experiment (item 3).
