# Step 7 — Fire Susceptibility Model: Audit and Documentation

**Scope:** `Integrated_Analysis/Step7_FireRisk_Susceptibility_Model.ipynb`, `Integrated_Analysis/hp_search_rf.py`, `Integrated_Analysis/preprocessing.py`, and everything in `Integrated_Analysis/Model_Outputs/`, as they actually exist on disk as of 2026-08-22. All numbers below are read directly from executed notebook cell outputs, `.json`/`.csv` result files, and log files — none are invented or extrapolated.

**Update, 2026-08-23**: two things changed after this audit was originally written, superseding the specific numbers below (the discovery narrative — how the RF tuning grid was chosen, why MaxEnt is trained fresh rather than cited from Biswas et al. — is unchanged and still accurate): (1) Step 6 wired specific humidity into the feature stack (55→57 features), moving RF to **ROC-AUC 0.9704, AP 0.7011** (spatial-block CV 0.9498±0.0035); (2) MaxEnt's `beta_multiplier` was validated-tuned (`hp_search_maxent.py`, grid {0.5,1.0,1.5,2.5,4.0} by validation AUC — the grid was essentially flat, 0.9589-0.9592, a genuine near-null result), moving MaxEnt to **ROC-AUC 0.9598, AP 0.6275** (spatial-block CV 0.9465±0.0054). The RF-vs-MaxEnt qualitative story (RF modestly ahead on both protocols, both far above CDR-PINN's own Track B1) is unchanged.

## What Was Done

Step 7 trains and evaluates two independent classical fire-susceptibility models on Step 6's corrected, leakage-fixed 55-feature pixel table (`Integrated_FireRisk_Pixels.parquet`, 4,161,009 pixels, 6.49% fire-positive): a **Random Forest** (the project's own headline model) and a **MaxEnt** model (`elapid`, a direct replication of Biswas et al. 2025's own method). Beyond training, the notebook delivers ROC/PR curves, Gini and permutation feature importance, two full-country probability GeoTIFFs (RF and MaxEnt), a reproducibility check (bit-exact re-run + 5-fold `StratifiedKFold` CV), a computational-cost/memory/storage report, and — new as of this run — a **2°×2° spatial-block cross-validation** (`GroupKFold`, 3 folds) for both models, added specifically to give this project's classical baselines a spatial-generalization number comparable to CDR-PINN's own Track B1.

Separately, a standalone script (`hp_search_rf.py`, backed by a new `preprocessing.py` module) ran a validated 4-point hyperparameter grid search for the Random Forest, selecting by validation-set AUC on a genuine 65/15/20 train/val/test split.

## How It Was Done

The main notebook (Cell 12) trains `RandomForestClassifier(n_estimators=200, max_depth=20, min_samples_leaf=5, class_weight="balanced", random_state=42)` on an 80/20 stratified split (3,328,807 train / 832,202 test pixels). Evaluated on the held-out test set: **ROC-AUC 0.9687, Average Precision 0.6814** (no-skill baseline 0.0649). The same hyperparameters are reused for the bit-exact reproducibility check (max diff 6.66e-16, attributed to `n_jobs=-1` float64 summation-order noise) and for 5-fold `StratifiedKFold` CV: **mean AUC 0.9683 ± 0.0002**, per-fold `[0.9683, 0.9684, 0.9686, 0.9680, 0.9683]`.

MaxEnt (`elapid.MaxentModel`, `feature_types=['linear','hinge','product']`) is trained on a 150,000-row stratified subsample of the same training split (recalibrated down from an originally-planned 450,000 rows after a measured super-linear fit-time scaling — 450k did not finish inside a 2-hour cell timeout) and evaluated on the identical 832,202-row test set: **ROC-AUC 0.9594, Average Precision 0.6246**. Random Forest leads by +0.0092 AUC / +0.0568 AP (`RF_vs_MaxEnt_Comparison.csv`).

The new spatial-block CV (Cell 29) partitions all 4,161,009 pixels into 116 unique 2°×2° `floor(lon/2)_floor(lat/2)` blocks, runs `GroupKFold(n_splits=3)`, refits both models per fold (RF with the same 20/5 hyperparameters; MaxEnt on a fresh 150k-row subsample of each fold's training portion), and per-fold median-imputes using only that fold's train data. Results, from `Model_Comparison_SpatialBlockCV.csv`:

| Model | Fold 1 AUC | Fold 2 AUC | Fold 3 AUC | Mean AUC | Std |
|---|---|---|---|---|---|
| Random Forest | 0.9465 | 0.9523 | 0.9515 | **0.9501** | **±0.0031** |
| MaxEnt | 0.9407 | 0.9507 | 0.9450 | **0.9455** | **±0.0050** |

Both drop modestly from their random-split numbers (RF: 0.9687 → 0.9501, a 1.9% relative drop; MaxEnt: 0.9594 → 0.9455, a 1.5% drop) — real but small evidence of spatial autocorrelation inflating the random-split score, not a collapse.

`hp_search_rf.py`, run afterward and independently, loads the same parquet via `preprocessing.py`'s 65/15/20 stratified split (train=2,704,655, val=624,152, test=832,202) and grid-searches `{max_depth, min_samples_leaf}` ∈ {(20,5), (15,5), (25,3), (20,10)}, selecting by validation AUC:

| max_depth / min_samples_leaf | Val AUC | Val AP |
|---|---|---|
| 20 / 5 (old default) | 0.9679 | 0.6772 |
| 15 / 5 | 0.9647 | 0.6456 |
| **25 / 3 (winner)** | **0.9694** | **0.6933** |
| 20 / 10 | 0.9680 | 0.6781 |

Refitting the winner and touching test once: **test ROC-AUC 0.9698, AP 0.6961** (`rf_hp_search_result.json`) — this is `hp_search_rf.py`'s own 65/15/20-split test number; the notebook's subsequent full retrain on its own 80/20 split (§ below) scores a close but not identical 0.9704.

## Why It Was Done This Way

Random Forest is the project's deliberate classical-ML extension beyond Biswas et al.'s MaxEnt-only methodology — chosen for its robustness to heterogeneous feature scales, native feature importances, and clean parallelism. MaxEnt is trained specifically to give a direct, apples-to-apples replication of the reference paper's own method on this project's own feature table, rather than citing Biswas et al.'s reported numbers, which would be a weaker comparison given their different feature set and 0.25° resolution. The 65/15/20 split and validation-only model selection in `hp_search_rf.py`/`preprocessing.py` exist to close a real, literature-grounded gap: `max_depth=20, min_samples_leaf=5` had been an untuned literature default since the notebook's inception, never chosen against held-out validation data — the same standard this project applies to CDR-PINN's own preprocessing. Spatial-block CV closes a second gap: without it, RF and MaxEnt had no spatial-generalization number comparable to CDR-PINN's Track B1, so any "classical baseline beats/loses to CDR-PINN" claim in a paper draft would be comparing different evaluation axes.

## Impact on Spatial Fire Mapping in India

`Fire_Susceptibility_Probability.tif` and `MaxEnt_Susceptibility_Probability.tif` are full-country, pixel-level (≈1 km) risk layers, directly usable in a GIS for operational planning. The spatial-block CV result is the more important number for genuine geographic transfer (e.g., predicting risk in a state with no training fires nearby): RF and MaxEnt both hold up well, staying above 0.94 AUC even when entire 2°×2° regions are held out — a materially stronger spatial-generalization result than CDR-PINN's own Track B1 (0.7510, re-run 2026-08-23 with validation-driven early stopping), by roughly +0.199 (RF) and +0.195 (MaxEnt) AUC. That is itself a notable, reportable finding for the paper: the classical baselines currently generalize spatially far better than the physics-informed neural operator, at least on this specific 2°×2°-block protocol.

## Comparison with Biswas et al. (2025)

The notebook and README are explicit that no numeric AUC from Biswas et al. (2025) is cited anywhere in this comparison — a deliberate choice, not an oversight, because their MaxEnt was fit at 0.25° resolution on a different 15-variable table, making a cross-paper AUC citation weaker than training MaxEnt fresh on this project's own data. A repo-wide search of this project's `.md` documentation (`METHODOLOGY.md`, README files) turns up no cited Biswas MaxEnt AUC figure to benchmark against — so the comparison implemented is the strongest one actually available: same test pixels, same features, same resolution, both models trained by this project. On that basis, this project's own MaxEnt replication (AUC 0.9594) and its RF extension (AUC 0.9687) both comfortably exceed the informal ≥0.7 "useful model" AUC threshold typically cited in the species-distribution-modeling literature MaxEnt comes from, and RF is a modest, consistent, honestly-reported improvement over the paper's own method on identical data.

## Completeness Audit: Gaps Found

1. ~~**Critical — the tuned hyperparameters never reached the notebook.**~~ **RESOLVED
   (verified 2026-08-23).** At the time this was written the notebook still hardcoded
   `max_depth=20, min_samples_leaf=5` despite `hp_search_rf.py` finding a better
   config. Confirmed via direct inspection of the current notebook: Cells now use
   `max_depth=25, min_samples_leaf=3` throughout (headline model, reproducibility CV,
   spatial-block CV), and MaxEnt's own `beta_multiplier=4.0` (validated 2026-08-23 via
   the same pattern, `hp_search_maxent.py`) is likewise wired into every MaxEnt
   instantiation in the notebook. `METHODOLOGY.md`'s claim is now accurate, not
   aspirational.
2. **Tuned-vs-untuned comparison is buried.** The 4-row grid comparison exists only in `rf_hp_search_result.json` — there is no plot, table, or notebook cell a reader would encounter without knowing to look for this file.
3. **No confusion-matrix plot.** Confusion matrices for both RF and MaxEnt are computed and printed as raw arrays (Cells 14, 24) but never rendered as a heatmap image — every other major result (ROC/PR, feature importance, maps) has a saved PNG; the confusion matrix does not.
4. **No spatial-block-CV map visualization.** Nothing plots the 116 2°×2° blocks or which ones fell into which of the 3 `GroupKFold` folds — a reader cannot see whether the folds are geographically balanced (e.g., whether one fold happens to concentrate in a specific region), even though the per-fold fire-rate numbers printed (5.0%–9.0%) suggest real regional imbalance across folds.
5. **No persisted three-model comparison table/figure.** The RF-vs-MaxEnt-vs-CDR-PINN spatial-block comparison is computed and printed (Cell 29) and stored in the JSON report's `spatial_block_cv` key, but `Model_Comparison_SpatialBlockCV.csv` itself only contains RF/MaxEnt rows — CDR-PINN's Track B1 (0.7510, hardcoded as `CDR_PINN_TRACK_B1_AUC`) is never appended as a row, so there is no single saved artifact a co-author could open and see all three models' spatial AUCs side by side without reading console output.
6. **Solid, no gap:** ROC/PR curves, full-country probability maps (single-model and side-by-side), Gini and permutation feature-importance plots, reproducibility evidence (bit-exact + 5-fold CV), and the computational-cost dashboard are all genuinely present, saved, and consistent with their printed numbers — these do not need further work.
