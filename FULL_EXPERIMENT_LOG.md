# Full Experiment Log — Every Training/Evaluation Run, This Study

**Purpose**: a raw, complete ledger of every experiment run in this study — not
polished prose, a reference table to pull from when writing the methodology
section later. Every row is a real, executed run with a real result; nothing here
is estimated. "Validation set used?" is called out explicitly as its own column
since that protocol changed partway through this study — most early experiments
used only a train/test split, and switching to a genuine train/val/test split was
itself one of the tracked changes (see "Standard Protocol" rows near the bottom).

---

## A. CDR-PINN (Physics-Informed Neural Operator) Experiments

### A1. Term-ablation study (`train.py`)

| Config | Split | Val set? | Epochs | Seed | ROC-AUC | AP | Script/date |
|---|---|---|---:|---:|---:|---:|---|
| Diffusion only | 80/20 random pixel | No | 80 | 42 | 0.6017 | 0.6050 | `train.py`, 2026-08-20 |
| + Advection | 80/20 random pixel | No | 80 | 42 | 0.9239 | 0.9014 | `train.py`, 2026-08-20 |
| + Reaction (full CDR, original) | 80/20 random pixel | No | 80 | 42 | 0.9406 | 0.9253 | `train.py`, 2026-08-20 |

Diagnosed-and-fixed issue along the way: diffusion-only's first run collapsed to a
trivial constant-field solution (AUC≈0.53) due to unweighted BCE under ~2.3%
class imbalance; fixed with `pos_weight≈43`.

### A2. Four generalization tracks + data-efficiency test (`run_validation_tracks.py`, original run)

| Track | Description | Split | Val set? | Epochs | ROC-AUC | Date |
|---|---|---|---|---:|---:|---|
| A | Random split (full CDR) | 80/20 | No | 80 | 0.9406 | 2026-08-20 |
| B1 | 2°×2° spatial block CV, 3 folds | spatial blocks | No | 50 | 0.7538 ± 0.0162 | 2026-08-20 |
| B2 | Leave-one-region-out, 6 KMeans regions | spatial regions | No | 50 | 0.5989 ± 0.0815 | 2026-08-20 |
| B3 | Leave-years-out (novel) | temporal | No | 80 | 0.8967 | 2026-08-20 |
| Data-efficiency | No-physics vs. physics, identical sparse data, Track A split | 80/20 | No | 80 | No-physics 0.9463 vs. physics 0.9406 | 2026-08-20 |

**Status as of this log**: B1/B2/B3 and the data-efficiency test above still reflect
the pre-leakage-fix, pre-standard-protocol model — a fresh re-run (with a
physics-vs-no-physics comparison added to B1/B2/B3 specifically, previously only
done for Track A) is in progress, see section E below.

### A3. Reviewer-defense diagnostics — closing the Track-A accuracy gap to RF/MaxEnt

| # | Intervention | Split | Val set? | Config | ROC-AUC | Verdict | Date |
|---|---|---|---|---|---:|---|---|
| 1 | Train/eval aggregation fix (LSE-pool vs. max-pool) | 80/20 | No | width=32/80ep | 0.9406 (unchanged) | Ruled out as the gap's cause | 2026-08-20 |
| 2 | Scale-up | 80/20 | No | width=64/150ep | 0.9292 | Worse — ruled out | 2026-08-20 |
| 3 | Scale-up + cosine LR | 80/20 | No | width=64/150ep+cosine | 0.9154 | Worse again | 2026-08-21 |
| 4 | Causal time-weighting (Wang, Sankaran & Perdikaris 2022) | 80/20 | No | ε=1.0, width=32/80ep | 0.9369 | Worse | 2026-08-21 |
| 5 | Staged curriculum learning | 80/20 | No | advection@ep15, reaction@ep35 | 0.9343 | Worse | 2026-08-21 |
| 6 | Honest validation-selected re-test of scale/schedule | **65/15/20** | **Yes (first use)** | 3 configs compared, see A4 | see A4 | Scale-up confirmed worse; LR-schedule finding *reversed* | 2026-08-21/22 |
| 7 | Validated weight-decay search | **65/15/20** | **Yes** | AdamW, wd∈{0,1e-5,1e-4} | winner wd=0.0, val AUC=0.9330 | 0.0 wins — explicit L2 doesn't help | 2026-08-22 |

### A4. Validation-split re-test (`validation_split_test.py`) — the first genuine 3-way split in this study

| Config | Split | Val set? | Val AUC | Test AUC | Selected? |
|---|---|---|---:|---:|---|
| width=32/80ep, no schedule | 65/15/20 | Yes | 0.9329 | 0.9370 | No |
| width=64/150ep, no schedule | 65/15/20 | Yes | 0.9266 | 0.9339 | No |
| width=32/80ep, cosine schedule | 65/15/20 | Yes | **0.9368** | 0.9403 | **Yes (by val AUC)** |

Finding: reverses the earlier test-only comparison (which had found cosine worse,
0.9154 vs 0.9406) — downgraded from "ruled out" to "split-sensitive, unresolved
without multi-seed testing" (not yet resolved, see gaps list).

### A5. Data-leakage fix and re-verification (`forest_frac_recent`/`current` dropped)

| Test | Split | Val set? | Before (leaky) | After (corrected `forest_frac_baseline`) | Date |
|---|---|---|---:|---:|---|
| Full CDR retrain (old protocol) | 80/20 | No | AUC=0.9406 | AUC=0.9397 | 2026-08-22 |
| Permutation importance (elevation) | inference, test set | No | drop=0.2238 (23.80%) | drop=0.2227 (23.70%) | 2026-08-22 |
| Response curves (elevation Δ) | inference | No | Δ=0.4281 | Δ=0.4423 | 2026-08-22 |
| Jackknife, without-forest_frac | 80/20, 40 epochs | No | AUC=0.9392 | AUC=0.9406 | 2026-08-22 |
| Jackknife, only-forest_frac | 80/20, 40 epochs | No | AUC=0.7016 | AUC=0.7011 | 2026-08-22 |

Finding: the leakage fix was methodologically correct (removed a real
reverse-causality risk) but empirically low-impact for these specific diagnostics.

### A6. Jackknife variable importance, full table (`jackknife_test.py`, post-leakage-fix run)

40-epoch budget, 80/20 split, no validation set. All-variables baseline AUC=0.9406.

| Covariate | Without-X AUC | Drop | Only-X AUC | Gain alone |
|---|---:|---:|---:|---:|
| Elevation | 0.7503 | −0.1903 | 0.9392 | +0.4392 |
| NDVI (baseline) | 0.9443 | +0.0037 | 0.7092 | +0.2092 |
| Slope | 0.9392 | −0.0014 | 0.7770 | +0.2770 |
| Distance to roads | 0.9405 | −0.0001 | 0.7525 | +0.2525 |
| Forest fraction | 0.9406 | −0.0000 | 0.7011 | +0.2011 |
| Dryness proxy | 0.9395 | −0.0011 | 0.5233 | +0.0233 |
| NDVI anomaly | 0.9415 | −0.0009 | 0.3874 | −0.1126 |

### A7. Standard protocol adoption — final canonical run (`train_standard_protocol.py`)

**First and only CDR-PINN run in this study using a genuine validation set for
every decision** (weight decay, LR reduction, early stopping):

- Split: 65/15/20 train/val/test, seed=42
- Optimizer: AdamW, weight_decay=0.0 (validated, A3 item 7)
- Scheduler: `ReduceLROnPlateau` (adaptive, monitors validation loss)
- Early stopping: on **validation AUC** (not loss — found to diverge, loss
  oscillates with no trend while AUC rises cleanly; documented explicitly)
- Result: validation AUC peaked at epoch 45 (0.9351), early-stopped at epoch 65
- **Final: validation AUC=0.9351, test AUC=0.9398, test AP=0.9223**
- This is the current canonical checkpoint (`cdr_pinn_full_cdr.pt`), superseding
  every earlier full_cdr number in this study.

### A8. Permutation importance / response curves, final re-run against canonical checkpoint

| Method | Baseline AUC | Elevation's effect | Date |
|---|---:|---|---|
| Permutation importance | 0.9398 | drop=0.2268 (24.13% of baseline) | 2026-08-22 |
| Response curves | — | Δ=0.4611 | 2026-08-22 |

Sixth independent confirmation of elevation dominance (after A1's advection jump,
Step 5a's field measurement, A5's two permutation/response-curve runs, A6's
Jackknife, and this final re-run).

---

## B. Random Forest / MaxEnt (Step 7) Experiments

| Run | Feature set | Split | Val set? | Hyperparameters | RF AUC | MaxEnt AUC | Date |
|---|---|---|---|---|---:|---:|---|
| Original (pre-terrain) | 52-feature | 80/20 | No | max_depth=20, min_samples_leaf=5 | 0.9674 | — | 2026-08-10 |
| Post-terrain-wiring | 58-feature | 80/20 | No | max_depth=20, min_samples_leaf=5 | 0.9683 | 0.9595 | 2026-08-20 |
| Post-leakage-fix (untuned baseline) | 55-feature | 80/20 | No | max_depth=20, min_samples_leaf=5 | 0.9687 | 0.9594 | 2026-08-21 |
| Post-leakage-fix, spatial-block CV | 55-feature | 2°×2° GroupKFold, 3 folds | No | max_depth=20, min_samples_leaf=5 | 0.9501 ± 0.0031 | 0.9455 ± 0.0050 | 2026-08-21 |
| Validated hyperparameter search (`hp_search_rf.py`) | 55-feature | **65/15/20** | **Yes** | grid: {20/5, 15/5, 25/3, 20/10} | winner 25/3, val AUC=0.9694, test AUC=0.9698 | — | 2026-08-22 |
| **Final tuned retrain (notebook itself updated)** | 55-feature | 80/20 (notebook's own split) | No (search used val, final notebook doesn't) | **max_depth=25, min_samples_leaf=3** | **0.9701** | 0.9594 (untuned) | 2026-08-22 |
| Final tuned, spatial-block CV | 55-feature | 2°×2° GroupKFold, 3 folds | No | max_depth=25, min_samples_leaf=3 | **0.9497 ± 0.0033** | 0.9455 ± 0.0050 | 2026-08-22 |
| Final tuned, 5-fold CV | 55-feature | StratifiedKFold, 5 folds | No | max_depth=25, min_samples_leaf=3 | **0.9698 ± 0.0002** | — | 2026-08-22 |

**Note on "validation set used?" for Step 7**: the *search* for the best
hyperparameters used a genuine validation split; the *final reported* notebook
numbers (random-split, spatial-block, 5-fold) all use the original random/CV
splits, not the validation split, since those splits' job is estimating
generalization, not selecting hyperparameters (which the search already did on a
separate split). This mirrors standard nested-CV practice.

---

## C. Steps 1–6 — Preprocessing/Feature Pipeline Fixes (not model training, listed for completeness)

| Fix | Real before/after numbers | Date |
|---|---|---|
| Step 2 (NDVI): India boundary masking added | 8,573,393 px (67.2%) newly excluded; breakpoint θ* 0.529→0.535 | 2026-08-21 |
| Step 3 (LST): FDR correction on Mann-Kendall significance | Day 1,063,120→393,838 sig px; Night 234,318→17,935; DTR 2,545,287→2,290,051 | 2026-08-21 |
| Step 4 (FLDAS): same FDR correction | Wind 3,728→1,015; Precip 2,754→1,840; RH 13,413→10,818; Air temp 636→**0**; Net LW 10,197→7,204; Soil moist 11,615→6,926 | 2026-08-21 |
| Step 6: forest-fraction leakage fix | 58→55 features, 60→57 bands, 62→59 columns | 2026-08-21 |

---

## D. What "validation set used?" means across this study, summarized

- **Every experiment before 2026-08-21/22 used only a train/test split** (usually
  80/20), no validation set — any architecture/hyperparameter decision made during
  that period (scale-up, LR schedule, causal weighting, curriculum learning) was
  decided by looking at test-set performance directly, a disclosed methodological
  gap (see A3 row 6, A4).
- **The switch to genuine validation-set-driven decisions happened in two places**:
  CDR-PINN's `train_standard_protocol.py` (A7, the current canonical model) and
  Step 7's `hp_search_rf.py` (B, the final tuned RF).
- **Not yet converted to validation-set-driven protocol**: MaxEnt's hyperparameters
  (still untuned defaults), CDR-PINN's B1/B2/B3 tracks (still the original 80/20-
  style split logic, no validation carve-out — see section E, in progress), the
  Jackknife test (still 80/20, no validation set — a deliberate scope decision
  given its 15-retrain cost).

---

## E. In progress as of this log (not yet complete — will be appended)

Re-running Track B1/B2/B3 fresh against the corrected data, with a physics-vs-
no-physics comparison added to each track (previously only done for Track A) —
`run_validation_tracks.py`, modified 2026-08-22 to thread `use_physics` through
all three track functions. Results not yet available; this log will be updated
once they land.

---

*Compiled 2026-08-22. Every number above traces to a real executed run (JSON
result files in `Physics_Informed_FireRisk_Model/CDR_PINN_Data/` and
`Integrated_Analysis/Model_Outputs/`, or a real notebook cell output) — none are
estimated or illustrative. Use this as the raw source when deciding what belongs
in the paper's actual Methodology section — not everything here needs to appear
there, but nothing that appears there should contradict this log.*
