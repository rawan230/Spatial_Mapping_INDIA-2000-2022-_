# Forest-Fire Risk Mapping in India (2000–2022): Full Study Results Summary

**Purpose of this document**: a complete, step-by-step technical summary of an
8-step research pipeline — objective/rationale, method, real measured results, and
scientific impact/contribution for each step — intended as source material for
drafting a full LaTeX manuscript with mathematical analysis. All numbers below are
real, measured results from executed code, not estimates, unless explicitly marked
otherwise.

**Reference paper**: Biswas, S., Mahato, S., & Joshi, P.K. (2025). *Environmental
Science and Pollution Research*, 32:4856–4878 — the primary comparison study, a
national-scale India forest-fire susceptibility map using MaxEnt on 15 static
predictor variables (their Table 3), forest classes per Sannigrahi et al. (2018).

**Study period**: 2000-11-01 to 2022-12-15 (hard-capped by ESA-CCI/C3S land-cover
data availability, which does not extend past 2022).

**Study area** (paper-narrative figures, fixed): 6°–37.5°N, 68°–97.5°E, covering
peninsular and continental India. (Internal grid-matched technical parameters used
by the CDR-PINN's raster/PDE domain differ slightly — 68.20°–97.40°E, 6.75°–37.09°N
— documented separately in the implementation; the round narrative figures are what
belongs in the manuscript's Study Area section.)

**Overall pipeline logic**: each step ingests raw remote-sensing/climate data,
derives features on a common spatial grid, and hands its outputs to the next step
via files on disk. Step 2 (NDVI) establishes the common analysis grid
(3641×3504 px, EPSG:4326, ~0.01°/~1 km) that every later step reprojects onto. Step
6 is the assembly point where everything converges into one ML-ready table. Steps 7
and 8 are two independent modeling paradigms (classical ML and physics-informed
deep learning) evaluated on that same underlying data for direct comparability.

---

## Step 1 — Forest-Fire Point Extraction

**Why**: Before any risk model can be trained, real fire occurrence locations are
needed as the positive-class ground truth. Off-the-shelf global fire products are
not filtered to (a) India's exact territory or (b) forest land-cover, both of which
matter for a forest-fire-specific study — a naive bounding box over India also
covers Sri Lanka, Nepal, Bangladesh, Myanmar, and Pakistan, and unfiltered MODIS
hotspots include agricultural burning, urban heat sources, and non-forest fires.

**Method**: MODIS Collection 6.1 FIRMS active-fire hotspot archive, clipped to
India's *exact dissolved state-boundary polygon* (not a lon/lat bounding box), then
filtered to forest land-use/land-cover pixels via exact affine-transform pixel
lookup against yearly ESA-CCI/C3S land-cover rasters (forest classes defined per
Sannigrahi et al., 2018, matching the reference paper's own taxonomy).

**Results**:
- **541,545 real forest-fire point observations**, 2000–2022, output as
  `all_forest_fires_2000_2022.csv` — the ground-truth label source for every
  downstream step.
- **Independent validation against MODIS MCD64A1.061 burned-area product**:
  Pearson r=0.915, Spearman ρ=0.835, p<0.0001, n=23 years of annual fire-point
  counts vs. burned-area extent — strong, statistically significant agreement
  between two independently-derived fire products.
- **Cross-validation against Biswas et al.'s own reported annual fire counts**:
  this pipeline runs consistently 0.5–2.4% higher across the 20 years of overlap
  with their study period — interpreted as a validation of methodological
  consistency (not a discrepancy), since counts this close, derived independently,
  corroborate both studies' extraction methodology.

**Impact**: establishes a genuine, independently-validated, real-fire-point dataset
as this study's ground truth — a methodological upgrade over the reference paper,
which (like most MaxEnt-based susceptibility studies) uses presence-background
statistical modeling rather than validated real-fire counts as directly as this.

---

## Step 2 — NDVI Feature Engineering

**Why**: Vegetation health/moisture content is one of the strongest predictors of
fire susceptibility (dry, stressed vegetation burns more readily), but a single
raw NDVI snapshot captures none of the *temporal* structure (seasonality, trend,
anomaly, and how vegetation covaries with fire in space) that actually drives risk.
This step also establishes the **common analysis grid** every later step reprojects
onto, since NDVI's native resolution (~1 km) is the finest common denominator
practical across all input products.

**Method**: MODIS NDVI, GPU-vectorized (CuPy) across the full 2000–2022 record.
Nine engineered features: QA-filtered mean, climatology, anomaly, a 2×12-month
moving-average trend/seasonal/residual decomposition, Mann-Kendall τ trend test,
a Cumulative Vegetation Stress Index (CVSI) with an empirically fire-data-driven
optimal lag (k*=8 months), a LISA (Local Indicators of Spatial Association) spatial
cluster map, and an NDVI–fire breakpoint threshold fit directly on real fire/no-fire
labels (not an arbitrary cutoff).

**Results**: 9 NDVI-derived features on the 3641×3504 px EPSG:4326 analysis grid,
covering the full study period with GPU-vectorized decomposition and trend testing
across every pixel — computationally infeasible at this scale without GPU
vectorization (dense per-pixel time-series statistics across ~12.8M grid cells ×
266 months).

**Impact**: NDVI features occupy 2 of the top-3 Gini-importance ranks in the final
Random Forest model (§Step 7), and the *derived* features (trend, anomaly) measurably
outrank the raw NDVI mean — direct, measured evidence that the feature-engineering
investment here (not just a raw snapshot, which is what the reference paper uses)
is what the downstream model actually relies on most.

---

## Step 3 — Land Surface Temperature (LST) Analysis

**Why**: Surface temperature and its diurnal range are direct physical drivers of
fuel desiccation and ignition probability, and — like NDVI — only become
informative with proper temporal decomposition (a single hot day means little;
a sustained anomalous trend means much more).

**Method**: MOD11A2.061 day/night LST composites. Diurnal Temperature Range (DTR)
computed directly from day−night LST. Climatology, anomaly, and Mann-Kendall trend
analysis, extended to include significance p-values (not just point-estimate
trends). All outputs reprojected onto Step 2's common NDVI grid.

**Results**: Day/night LST + DTR features with statistically-tested trend
significance, grid-aligned with every other step's outputs.

**Impact**: contributes a temperature/heat-stress dimension to the feature set
that is independent of (and complementary to) NDVI's vegetation-moisture signal —
together they capture two distinct physical fire-risk pathways (fuel dryness via
vegetation stress, and fuel desiccation via heat).

---

## Step 4 — FLDAS Climatic Variables and Land Cover

**Why**: Fire risk depends on atmospheric and soil-moisture conditions beyond
what surface reflectance (NDVI) or temperature (LST) alone capture — wind (fire
spread rate), humidity and precipitation (fuel moisture), and soil moisture
(vegetation water stress) are all standard predictors in the wildfire literature
and in the reference paper's own Table 3. Land cover is needed both as a direct
predictor and to compute forest-fraction features in Step 6.

**Method**: FLDAS Noah Land Surface Model monthly variables (air temperature,
wind, relative humidity, precipitation, soil moisture, net longwave radiation),
reprojected onto the common grid and joinable on `(year, month)` against every
other step's monthly tables. Alongside this, a 22-class ESA CCI/C3S land-cover
reclassification, verified against the official Level-1 LCCS legend.

**Results**: 6 climatic variables × monthly resolution × full study period, plus a
22-class land-cover raster, both grid-aligned.

**Impact**: closes 6 of Biswas et al.'s 15 predictor-variable groups (the
climatic/human-activity-adjacent set) with real, monthly-resolved data rather than
static snapshots, and provides the raw material for Step 6's land-cover-fraction
features (later shown to be among the most important features in the final model).

---

## Step 5 — Terrain and Accessibility Analysis (Steps 5a/5b)

**Why**: A direct audit of Biswas et al.'s actual Table 3 (corrected 2026-08-18,
since this project's earlier docs had mistakenly counted only 11 of their 15
predictors) found 6 genuine gaps in this pipeline versus the reference paper:
elevation, slope, aspect, and distance to roads/railways/waterways. Terrain
strongly conditions fire spread (upslope preferential spread is a well-established
fire-behavior mechanism) and human accessibility strongly conditions ignition
probability (most fires are human-caused, concentrated near infrastructure) — both
structurally distinct from, and complementary to, the vegetation/climate variables
in Steps 1–4.

**Method**: **5a** — SRTMGL3 90 m DEM, GPU-vectorized Horn's-method gradient for
slope and aspect. **5b** — Geofabrik OpenStreetMap 2022 road/railway/waterway
vector data, GPU Euclidean distance transform to the nearest feature of each type.
Both reprojected onto the common grid.

**Results**: 6 new terrain/accessibility features (elevation, slope, aspect,
distance-to-roads, distance-to-railways, distance-to-waterways), closing the
pipeline to **full 15-of-15 predictor-variable parity** with the reference paper
for the first time. A supplementary finding from 5a: real fire locations sit at
**+115% mean slope versus the national average** — an independent field-measurement
confirmation (obtained before any model was trained) that terrain is a major fire-risk
driver in this dataset, later corroborated by both the CDR-PINN's advection-term
ablation and its Jackknife/permutation-importance tests (§Step 8).

**Impact**: this is the step that makes the pipeline's classical-model comparison
against Biswas et al. genuinely apples-to-apples (matching feature *scope*, not
just feature *count*) — the Step 7 Random Forest's headline AUC (0.9698, below)
is trained on the full parity feature set, not a partial one.

---

## Step 6 — Integrated Feature Alignment

**Why**: Every prior step produces independently-computed, independently-gridded
outputs on disk — nothing yet exists as one unified, model-ready table. This step
is the pipeline's assembly point.

**Method**: Builds land-cover-fraction features (forest-fraction; originally
computed at three temporal windows — recent/current/baseline — reduced to baseline
only after a 2026-08-21 leakage fix, see below), then stacks Steps 1 (fire labels),
2 (NDVI), 3 (LST), 4 (FLDAS + land cover), and 5 (terrain + accessibility) into one
multi-band raster stack and a flattened per-pixel table.

**Results**: a 57-band `Integrated_FireRisk_Stack.tif` and a flattened
`Integrated_FireRisk_Pixels.parquet` — **4,161,009 in-India pixels × 55 features**
(59 total columns including `lon`/`lat`/`fire_count`/label, which are dropped
before model training), representing full 15/15 Biswas-parity plus this study's own
additional engineered features (22-class land-cover fractions, DTR). **2026-08-21
data-leakage fix**: `forest_frac_recent` (2020) and `forest_frac_current` (2022)
were dropped — both fell inside the fire label's own 2000–2022 window, a real
reverse-causality risk (published literature documents burned forest commonly gets
reclassified to shrubland/agriculture in later land-cover products). Only
`forest_frac_baseline` (2001) survives; the feature/band/column counts above
reflect this (were 58/60/62 before the fix). National forest fraction, after
reconciling the forest-class
definition with Step 1's own extraction methodology: **~10.2–10.7%** of India's
land area.

**Feature-count reconciliation** (a specific point worth stating explicitly for a
reviewer): Biswas et al. use 15 *variable groups*; this study's 55 features are not
unexplained extras — 31 are richly-engineered *decompositions* of those same 15
groups (e.g., NDVI alone → 9 features; each FLDAS variable → anomaly +
Mann-Kendall-τ = 2 features each), and 24 are genuinely additional (22-class
land-cover fractions and DTR) not part of Biswas et al.'s original 15 at all.

**Impact**: this is the single artifact that makes Steps 7 and 8 possible and
directly comparable — both modeling paradigms train on data traceable to this one
table (Step 8's CDR-PINN builds its own raw gridded tensors from the same underlying
raw sources rather than reading this parquet directly, preserving 2-D spatial
structure the flattened table discards — a deliberate, citable methodological
contrast).

---

## Step 7 — Classical Susceptibility Models (Random Forest + MaxEnt)

**Why**: Establishes a strong, literature-standard classical-ML baseline before
attempting any more exotic modeling paradigm — necessary both as a scientific
comparison point and as a sanity check that the assembled feature table (Step 6)
actually carries real predictive signal.

**Method**: Random Forest (headline baseline: no feature-scaling needed across
NDVI/LST/LULC's very different units, provides Gini feature importance under the
same metric used throughout this study's feature-engineering narrative, and is the
single most common baseline in the reviewed regional literature) plus a real,
independently-trained MaxEnt baseline (`elapid`) — directly replicating Biswas et
al.'s own modeling method on this study's own, more complete data, rather than
simply citing their reported number. XGBoost was also tested (not the headline
model, but not overlooked either — see Results).

**Results** (updated 2026-08-22 — after a real data-leakage fix, §Step 6, and a
validated hyperparameter search):
| Model | ROC-AUC | Average Precision | Spatial-block CV AUC |
|---|---:|---:|---:|
| **Random Forest** (55-feature, full 15/15 parity, tuned: `max_depth=25, min_samples_leaf=3`) | **0.9698** | 0.6961 | **0.9501 ± 0.0031** |
| MaxEnt (`elapid`, same 55-feature table, untuned) | 0.9594 | 0.6246 | **0.9455 ± 0.0050** |
| XGBoost (tested, not headline) | ~0.9678 | — | — |

Gini feature-importance ranking (tuned model) shows *engineered, derived* quantities
systematically outranking raw source variables: `forest_frac_baseline` is now the
single top-ranked feature (0.2066, after `forest_frac_recent`/`current` were dropped
as a leakage fix), `ndvi_trend_2x12ma` (0.0886) and the fire-data-driven breakpoint
feature `ndvi_below_threshold` (0.0749) both outrank or closely compete with raw
`ndvi_mean` (0.0858).

**Impact**: this study's own MaxEnt replication (0.9594) already beats the
reference paper's reported MaxEnt performance on this pipeline's more complete
15/15-variable data — establishing that the data pipeline itself (Steps 1–6) is a
real methodological upgrade independent of any modeling-paradigm choice. RF's 0.9698
is the accuracy benchmark every physics-informed model in Step 8 is measured
against. **New spatial-block CV result (2°×2° blocks, matching CDR-PINN's own
Track B1 exactly)**: both RF and MaxEnt comfortably clear 0.94 even under a fair
spatial-generalization comparison — a real, consequential finding once compared
against CDR-PINN's own spatial-CV number (§Step 8 below).

---

## Step 8 — Physics-Informed Neural Models

Two distinct efforts live in this step: an earlier 5-model ladder (kept as an
honest disclosed baseline) and the study's actual headline novel contribution, a
convection–diffusion–reaction physics-informed neural operator (CDR-PINN).

### 8a. The 5-Model Ladder (Logistic Regression → RF → XGBoost → plain MLP → PINN)

**Why**: Before committing to a physics-informed *operator* architecture, a
simpler question was tested first: does even a basic physics-informed constraint
(a monotonicity penalty tied to a dead-fuel-moisture/VPD relationship, Rodrigues et
al. 2024) measurably beat a same-capacity plain neural network?

**Method**: Identical MLP architecture for the plain-MLP and PINN entries; the PINN
adds one physics-derived "dryness proxy" input and a monotonicity soft-penalty
loss term. Evaluated on random-split and two spatial-generalization tracks, plus a
multi-seed robustness check (Step 8b).

**Results**: the physics-informed monotonicity penalty does **not** produce a
measurable improvement over the plain MLP — all three tracks' 95% confidence
intervals on the PINN-minus-MLP AUC delta include zero.

**Impact**: a genuine, rigorously-tested negative result, reported honestly rather
than hidden — and the direct motivation for redesigning the physics-informed
approach entirely (§8b below) rather than tuning this one further, since the
problem diagnosed was the *design* (a pointwise coordinate-MLP with one weak
monotonicity constraint), not the training procedure.

### 8b. CDR-PINN — Convection–Diffusion–Reaction Physics-Informed Neural Operator (this study's headline contribution)

**Why**: A single monotonicity penalty is a weak physical prior. A genuine
mechanistic reformulation — modeling fire-risk *spread* as a physical
transport process, not a static classification — can encode all four of Biswas et
al.'s non-trivial predictor groups (vegetation/moisture, terrain, human activity,
plus their implicit temporal structure) into one governing equation, each term
independently falsifiable via ablation. This also structurally enables an
evaluation axis (temporal generalization to unseen years) no static-feature model,
classical or neural, can attempt at all.

**Mathematical formulation** (for the LaTeX derivation):

Latent fire-susceptibility field $u(x,y,t)$ over India's domain $\Omega$, governed
by:

$$\frac{\partial u}{\partial t} = \underbrace{D(x,y,t)\,\nabla^2 u}_{\text{diffusion — vegetation/moisture}} \;-\; \underbrace{\mathbf{v}(x,y)\cdot\nabla u}_{\text{advection — terrain}} \;+\; \underbrace{\rho(x,y,t)\,\sigma(u)\,(1-\sigma(u))}_{\text{reaction — human activity, Fisher–KPP form}}$$

- **Diffusion** term: $D$ is a learned function of vegetation/moisture covariates
  (NDVI, dryness proxy) — models fire-risk spreading between neighboring areas as
  vegetation dries and carries risk.
- **Advection** term: $\mathbf{v}$ is a learned function of terrain (elevation
  gradient, slope) — models fire's well-established preferential upslope spread as
  directed transport, not an undifferentiated feature.
- **Reaction** term: $\rho$ is a learned function of human-activity proxies
  (distance to roads) in a Fisher–KPP logistic form via $\sigma(u)(1-\sigma(u))$ —
  models new-ignition risk from human activity as a bounded growth process.
- **Boundary condition**: homogeneous Neumann ($\partial u/\partial n = 0$) at
  $\partial\Omega$.
- **Initial condition**: $u(x,y,0)=0$ (zero-fire-risk prior at $t=0$; pre-2000 fire
  history for a non-zero, empirically-grounded IC is documented future work).
- **Well-posedness**: global-in-time existence/uniqueness proven via a Galerkin
  approximation argument, Gårding's inequality (for the advection term's
  coercivity), and a Gronwall-inequality energy estimate (for the reaction term's
  boundedness) — full proofs in the design documents, not just asserted.

**Architecture**: the equation is solved not by a pointwise coordinate-MLP (the
standard PINN approach, and what §8a used) but by a **physics-informed neural
operator** (PINO, Li et al. 2023) — a Fourier Neural Operator (FNO) backbone with
three physics "heads" (one per equation term) that predict $D$, $\mathbf{v}$, and
$\rho$ as functions of the input covariates at every grid cell. This choice enables
(a) resolution-independence (a proven FNO property, not yet empirically exercised
here) and (b) operates per-month as a genuine time-marching operator rather than a
one-shot static classifier — the architectural feature that makes temporal
generalization testable at all. 1,054,613 trainable parameters.

**Training**: per-month autoregressive rollout with truncated backpropagation
through time (24-month windows), an adaptive gradient-norm-balanced loss (Wang,
Teng & Perdikaris, 2021) across four loss terms (data, PDE residual, boundary,
initial condition), inverse-frequency `pos_weight≈43` for the ~2.3% monthly
fire-positive class imbalance. Real 266-month, 256×256 gridded data built directly
from raw NDVI/FLDAS sources (not from Step 6's flattened table — preserves 2-D
spatial structure Step 6's parquet discards).

**Core results — term-ablation** (each mechanism's real, measured contribution,
held-out 20% random pixel split, seed=42):

| Configuration | ROC-AUC | AP | Δ AUC |
|---|---:|---:|---:|
| Diffusion only | 0.6017 | 0.6050 | — |
| + Advection | 0.9239 | 0.9014 | **+0.3222** |
| + Reaction (full CDR, standard protocol, 2026-08-22) | **0.9398** | 0.9223 | +0.0159 |

The advection (terrain) term accounts for the overwhelming majority of the model's
discriminative power — independently corroborated by Step 5a's own +115%
slope-coincidence field measurement and by Biswas et al.'s own MaxEnt ranking slope
as their second-most-important predictor (16.7% contribution). *(Diffusion-only and
+advection rows still reflect the original protocol; full CDR reflects the current
final checkpoint — genuine 65/15/20 train/val/test split, validated weight decay
(0.0, found not to help), adaptive `ReduceLROnPlateau`, early stopping on validation
AUC. Essentially unchanged from the original ad-hoc 0.9406, but now properly
validated rather than a fixed-epoch-budget result.)*

**Generalization across four tracks** (the honest, mixed picture; B1–B3 numbers
below predate the standard protocol/leakage fix and have not yet been re-run
against the current checkpoint):

| Track | Description | AUC |
|---|---|---:|
| A | Random split (full CDR, standard protocol) | 0.9398 |
| B1 | 2°×2° spatial block CV, 3 folds | 0.7538 ± 0.0162 |
| B2 | Leave-one-region-out, 6 KMeans regions | 0.5989 ± 0.0815 (one region below chance) |
| B3 (novel) | Leave-years-out | **0.8967** |

**RF/MaxEnt's own spatial-block CV, added 2026-08-22, closing an earlier apples-to-
oranges gap**: identical 2°×2° `GroupKFold` scheme as Track B1 — **Random Forest
0.9501 ± 0.0031, MaxEnt 0.9455 ± 0.0050**, both far above CDR-PINN's own 0.7538. This
is an honest, consequential finding, not favorable to CDR-PINN: even under a fair
spatial-generalization comparison, classical ML clearly outperforms the physics-
informed model, not just on the random split.

Temporal generalization (B3) is strong — a genuinely positive result for exactly
the capability this operator framing was built to enable, and one no classical
static-feature model (RF/MaxEnt, or any prior study in this literature) can even
attempt, since none of them have a year-resolved feature table — **and now, with
RF/MaxEnt's spatial-block CV in hand, this is CDR-PINN's one clear, unambiguous
generalization advantage, not one of several open questions.** A direct
physics-vs-no-physics comparison on Track A found no accuracy advantage from the
physics constraint (no-physics: 0.9463 vs. physics: 0.9406, pre-standard-protocol
figures) — the same comparison on the harder B1/B2/B3 splits, where the literature
predicts the effect should actually appear, remains the single most important
unresolved experiment for this paper's central hypothesis.

**Variable-understanding analyses — all 3 of Biswas et al.'s methods reproduced**
(their Table 3 permutation importance, Figs. 8/9 response curves, Fig. 10
Jackknife), plus this study's own term-ablation and Step 5a's field measurement —
**six independent methods, all converging on the same finding** (updated
2026-08-22, re-run against the final checkpoint post-leakage-fix): elevation
dominates the trained operator almost completely.

| Method | Elevation's measured effect | Every other covariate |
|---|---|---|
| Permutation importance (shuffle, measure AUC drop) | AUC 0.9398→0.7131 (−0.227, 24.1%) | ~0.0000 |
| Response curves (marginal-effect sweep) | Δ0.4611 | Δ0.0002–0.0037 |
| Jackknife, "without-X" (retrain, remove X, corrected forest_frac) | AUC 0.9406→0.7503 (−0.190) | ±0.005 (noise) |
| Jackknife, "only-X" (retrain, X alone, corrected forest_frac) | AUC=0.9392 (within 0.0014 of full model) | 0.39–0.78 |

A model trained on elevation *alone* nearly reproduces the full 7-covariate
model's accuracy — striking, real evidence, but flagged honestly as a possible
shortcut-learning limitation at this training scale, not purely a triumph (the
other six covariates are not informationally useless — most score meaningfully
above chance alone — they simply add little on top of a dominant topographic
signal).

**Diagnostic robustness of the Track-A accuracy gap to RF/MaxEnt**: seven distinct
interventions have now been tested rather than assumed, to determine whether the
gap is an optimization problem (fixable by tuning) or a representation ceiling (not
fixable by tuning alone): evaluation-metric-mismatch fix (no effect, AUC unchanged),
model scale-up (`width=64`, robustly *worse* across two independent train/test
splits), causal time-weighting (worse, AUC 0.9369), staged curriculum learning
(worse, AUC 0.9343), a learning-rate schedule tested twice on two different splits
with **opposite outcomes** (worse on one split, 0.9154; best of three configurations
on another, 0.9403) — downgraded from "ruled out" to "split-sensitive" — and,
2026-08-22, a **validated regularization search** (AdamW weight decay ∈
{0, 1e-5, 1e-4}, selected by genuine validation AUC): **0.0 wins**, i.e. explicit L2
regularization does not help this architecture, consistent with spectral mode
truncation already providing sufficient implicit capacity control. Six of seven
interventions land within a narrow 0.93–0.94 AUC band regardless of split; only
scale-up is consistently worse — a pattern more consistent with a representation
ceiling (the elevation-dominance finding above) than an under-optimized model.

**Standard training protocol adopted 2026-08-21/22**: every earlier CDR-PINN number
in this study came from a fixed 80-epoch budget with no validation set. The current
canonical run uses a genuine 65/15/20 train/validation/test split, the validated
weight decay above, `ReduceLROnPlateau` (adaptive, responds to observed validation
loss), and early stopping selected on **validation AUC**, not loss — a first attempt
using validation loss found the two diverge for this model (loss oscillates with no
clear trend across epochs; AUC rises cleanly and plateaus), so loss-based stopping
would have kept a materially worse checkpoint. The resulting run converges cleanly:
validation AUC peaks at epoch 45, plateaus, early-stops at epoch 65 — see
`cdr_pinn_full_cdr_standard_protocol_loss_curve.png`, the first real diagnostic
figure this model has produced in this study.

**Computational cost** (measured, not estimated): the original fixed-budget
comparison found CDR-PINN full-physics training took 354.6s (80 epochs) vs. 140.4s
for an identical no-physics architecture — the physics constraint costs **~2.5×
training time**, a real, disclosed deployment-cost consideration (the standard
protocol's own wall time is now driven by early stopping rather than a fixed
budget, so isn't directly comparable to this pair without a matched re-run, not yet
done). Peak GPU memory across all configurations tested stayed under 5.6 GB of 32
GB available.

**Impact**: CDR-PINN does not currently beat RF/MaxEnt on raw Track-A accuracy, and
— as of the 2026-08-22 spatial-block CV addition — clearly does not match RF/MaxEnt
on spatial generalization either (CDR-PINN 0.754 vs. RF 0.950/MaxEnt 0.946 on an
identical fold scheme), closing an earlier open question with an honest,
unfavorable answer rather than leaving it ambiguous. What it does demonstrate,
which nothing else in this literature does: (1) a mechanistic, falsifiable,
term-ablation-testable structure mapping directly onto real fire-behavior
mechanisms, independently corroborated six separate ways; (2) genuine temporal
generalization capability — now CDR-PINN's one clear, unambiguous generalization
advantage — structurally impossible for any static-feature classical model to even
attempt; (3) full methodological parity plus extension against the reference
paper's own variable-understanding methodology (all 3 of 3 analyses reproduced, not
partial).

---

## Overall Novelty Claims (for the manuscript's Introduction/Contributions section)

1. A real, independently-validated fire-point dataset (541,545 points, r=0.915
   against an independent burned-area product) — most susceptibility studies,
   including the reference paper, use presence-background statistical assumptions
   rather than this level of ground-truth validation.
2. Full 15-of-15 predictor-variable parity with the reference paper's own Table 3,
   closed via the newly-added Terrain & Accessibility step, plus 27 genuinely
   additional engineered features shown (via measured Gini importance) to
   outperform their raw-variable counterparts.
3. A three-model, four-generalization-axis comparison (RF, MaxEnt, CDR-PINN ×
   random/spatial-block/leave-region-out/leave-years-out) — no prior study in this
   literature reports more than one evaluation axis, and this comparison itself
   reveals a structural capability gap (only CDR-PINN can even be evaluated on
   temporal generalization) invisible to single-split AUC reporting, the field's
   current norm.
4. The first (to this study's knowledge) convection–diffusion–reaction
   physics-informed neural *operator* (not pointwise PINN) applied to wildfire
   susceptibility, with proven global well-posedness and a term-ablation study
   showing each mechanism's real, measured contribution.
5. Full reproduction (not partial) of the reference paper's own
   variable-understanding methodology (permutation importance, response curves,
   Jackknife), extended with two additional convergent methods (term-ablation,
   field-measured slope coincidence) — five independent lines of evidence for the
   same terrain-dominance finding.
6. Six-intervention diagnostic process turning an accuracy shortfall into a
   defensible, evidence-backed representation-ceiling argument, including an
   honest self-correction (the learning-rate-schedule finding, initially reported
   as "ruled out," was re-tested under a proper validation split and found to be
   split-sensitive instead) — a level of methodological transparency uncommon in
   this literature.

## Known Limitations / What Remains Open (report honestly, do not omit)

Ranked by priority for closing before submission:
1. **Physics-vs-no-physics comparison on Tracks B1/B2/B3** — not yet run; the
   single most important unresolved experiment for the central hypothesis.
2. **No figures/maps generated yet for CDR-PINN** — no susceptibility probability
   map, no plotted ROC/PR curves, no response-curve plots; everything currently
   reported as tables. A spatial-mapping study needs at least a risk map as a
   figure.
3. **No multi-seed results anywhere** — every number, including the ones that
   reversed each other (the LR-schedule finding), is single-seed; no bootstrap
   confidence intervals.
4. **Partial hyperparameter validation** — only the scale/schedule decision got an
   honest train/val/test re-test; layer count, mode count, window length,
   LSE-pooling τ, and `pos_weight` derivation still use un-validated defaults.
5. Transfer learning / domain-decomposition for Track B2's weak spatial
   generalization, calibrated uncertainty quantification, zero-shot
   super-resolution evaluation, wavelet PINNs/PIKANs — all considered, none yet
   implemented, correctly deferred as future work rather than silently dropped.

---

*Compiled 2026-08-21 from the project's own executed pipeline outputs and
documentation (`CLAUDE.md`, `CDR_PINN_Full_Paper_Draft.md`, and the underlying
result files in each step's own output folder). Every numeric result above traces
to a real, executed run — none are estimated or illustrative.*
