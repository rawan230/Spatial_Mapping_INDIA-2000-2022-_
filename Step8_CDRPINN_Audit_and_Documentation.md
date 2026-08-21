# Step 8 — Physics-Informed Neural Operator (CDR-PINN) — Audit and Documentation

*Written directly (not via subagent) given the depth of existing context — this step
carries the study's headline novel contribution and has by far the most existing
documentation (`CDR_PINN_Full_Paper_Draft.md`, `CDR_PINN_Methodology_Section.md`,
`CDR_PINN_Novelty_Comparison_Advantages.md`, `CDR_PINN_Study_Clarifications_QA.md`),
so this document synthesizes and audits against that existing base rather than
re-discovering it from scratch.*

## What Was Done

Two distinct pieces of work live under "Step 8":

**8a. The original 5-model ladder** (`Step8_PINN_FireRisk_Model.ipynb` +
`Step8b_PINN_Seed_Robustness_Check.ipynb`, `Physics_Informed_FireRisk_Model/`): Logistic
Regression → Random Forest → XGBoost → plain MLP → a plain-monotonicity PINN,
evaluated on random-split and two spatial-generalization tracks, plus a multi-seed
robustness check. Result: the physics-informed monotonicity penalty did not produce
a measurable improvement over a same-capacity plain MLP (all three tracks' 95% CIs
on the PINN-minus-MLP AUC delta include zero).

**8b. CDR-PINN** (this study's actual headline contribution, `cdr_pinn/`): a
convection–diffusion–reaction (CDR) partial differential equation over a latent
fire-susceptibility field, solved by a physics-informed Fourier neural operator
(FNO/PINO). Real, GPU-verified implementation with:
- Term-ablation study (diffusion-only → +advection → full CDR)
- Four generalization tracks (random split, spatial-block CV, leave-one-region-out,
  leave-years-out)
- All three of Biswas et al.'s variable-understanding analyses reproduced
  (permutation importance, response curves, Jackknife retraining)
- Six literature-grounded tuning-side interventions tested against the RF/MaxEnt
  accuracy gap (metric-fix, scale-up, causal time-weighting, curriculum learning,
  LR-schedule tested twice, a validated weight-decay search)
- A genuine 65/15/20 train/validation/test protocol (adopted 2026-08-21/22,
  superseding every earlier ad-hoc fixed-epoch-budget run)

## How It Was Done

**Governing equation** (proven globally well-posed via Galerkin approximation,
Gårding's inequality, and a Gronwall energy estimate — not just written down):

$$\frac{\partial u}{\partial t} = D(x,y,t)\nabla^2 u - \mathbf{v}(x,y)\cdot\nabla u + \rho(x,y,t)\sigma(u)(1-\sigma(u))$$

diffusion↔vegetation/moisture, advection↔terrain, reaction↔human activity — mapping
onto Biswas et al.'s four non-trivial predictor groups. Homogeneous Neumann boundary
condition, zero initial condition.

**Architecture**: FNO backbone (Li et al., 2023), not a pointwise coordinate-MLP.
7 input channels → 32 hidden channels → 1 output channel, 4 spectral blocks, 16×16
Fourier-mode truncation. No spatial kernel anywhere except 1×1 pointwise
channel-mixing convolutions (`kernel_size=1, stride=1, padding=0`); no pooling
layer, by design (resolution-independence requires never downsampling). Three
minimal physics heads (0.04% of total parameters) predict D, v, ρ from covariates.
1,054,613 total parameters.

**Training**: per-month autoregressive rollout, truncated BPTT (24-month windows),
adaptive gradient-norm-balanced loss (Wang, Teng & Perdikaris, 2021) across
data/PDE/boundary/initial-condition terms, inverse-frequency `pos_weight≈43` for the
~2.3% monthly fire-positive class imbalance.

**Standard protocol** (current, canonical): genuine 65/15/20 train/val/test split;
AdamW with a validated weight-decay search (winner: 0.0 — spectral truncation
already regularizes sufficiently); `ReduceLROnPlateau` (adaptive, monitors
validation loss); early stopping on **validation AUC** specifically (found to
diverge from validation loss for this model — loss oscillates with no trend while
AUC rises cleanly and plateaus, so loss-based stopping would have kept a materially
worse checkpoint).

## Why It Was Done This Way

- **FNO over pointwise PINN**: the training data is structurally a family of 265
  monthly instances sharing one fixed spatial domain — exactly the regime neural
  operators amortize across. PINO's own reported finding (Li et al., 2023) is that
  plain PINNs specifically fail on long time horizons, structurally analogous to
  this study's 266-month record.
- **CDR equation structure over a single generic residual**: mapping each term to a
  distinct, falsifiable fire-behavior mechanism makes the model's internal structure
  testable via ablation — a capability no correlational baseline (RF, MaxEnt) offers
  by construction.
- **AUC-based, not loss-based, early stopping**: because the two metrics were found
  to diverge for this specific model — a real empirical finding, not an assumption,
  documented in the training log and the resulting two-panel diagnostic plot.
- **Weight decay tested rather than assumed**: a small validated search rather than
  either omitting regularization or adding it reflexively.

## Impact on Spatial Fire Mapping in India

CDR-PINN does not currently produce a more accurate susceptibility map than RF or
MaxEnt — that should be stated plainly, not buried. What it contributes instead:

1. **Mechanistic attribution**, not just ranking: the model can, in principle,
   decompose *why* a location is high-risk (terrain-driven spread vs.
   vegetation/moisture vs. human-activity), which RF/MaxEnt's feature-importance
   rankings cannot do at the same causal-structure level — each CDR-PINN term
   corresponds to a physical mechanism, not just a statistical association.
2. **Temporal generalization**: the only one of the three models in this study
   capable of being evaluated on leave-years-out generalization at all (Track B3,
   AUC=0.897), since RF/MaxEnt have no year-resolved feature table. This is a
   genuinely unique capability for early-warning-relevant susceptibility mapping,
   where predicting *future* years from *past* training data is closer to the
   actual deployment scenario than a random pixel split.
3. **A reusable, falsifiable framework**: the CDR formulation and its proofs are a
   contribution independent of this specific training run's accuracy — future work
   (larger architecture, multi-seed averaging, transfer learning for weak regions)
   has a principled structure to build on rather than starting from an unstructured
   black box.

## Comparison with Biswas et al. (2025)

- Biswas et al. use MaxEnt exclusively — a correlational, presence-background
  statistical model with no time dimension and no mechanistic structure. CDR-PINN is
  a categorically different paradigm: a physically-structured, time-marching neural
  operator.
- All three of Biswas et al.'s own variable-understanding analyses (Table 3
  permutation importance, Figs. 8/9 response curves, Fig. 10 Jackknife) are
  reproduced for CDR-PINN — full methodological parity, going further than simply
  citing their numbers.
- Both studies converge on **terrain/slope dominance**: Biswas et al. rank slope
  their second-most-important predictor (16.7% contribution); CDR-PINN's advection
  term (terrain-driven) accounts for +0.322 of the model's total +0.34 AUC gain, and
  five further independent methods (permutation, response curves, Jackknife ×2,
  Step 5's own field measurement) all confirm elevation/terrain dominance. This is a
  genuine point of convergent validation between two independently-built studies.
- **Where CDR-PINN currently loses to Biswas et al.'s paradigm**: on raw accuracy
  (this study's own RF/MaxEnt replications beat Biswas et al.'s reported numbers,
  and CDR-PINN trails those). On **spatial** generalization specifically, this
  study's own RF/MaxEnt (now with a genuine spatial-block CV number, 0.95/0.95) beat
  CDR-PINN (0.75) decisively — an honest, unfavorable-to-CDR-PINN finding that
  should be stated as plainly as the favorable ones.

## Completeness Audit: Gaps Found

Ranked by priority, drawing on the full session's own tracking (`STUDY_STATUS_AND_
REMAINING_WORK.md`) plus a fresh check against this file's own claims:

1. **[HIGH] No full-country susceptibility probability map generated for CDR-PINN.**
   RF/MaxEnt have one (`Model_Outputs/Fire_Susceptibility_Map*.png`); CDR-PINN, the
   study's own "spatial mapping" headline model, does not. This is the single most
   conspicuous missing deliverable for a paper about *spatial mapping*.
2. **[HIGH] Tracks B1/B2/B3 have not been re-run against the current standard-
   protocol checkpoint.** They still reflect the pre-leakage-fix, pre-standard-
   protocol model. The term-ablation's diffusion-only/+advection rows likewise
   haven't been re-run under the new protocol — only the full-CDR row has.
3. **[HIGH] Physics-vs-no-physics comparison has only ever been run on Track A.**
   Repeatedly flagged throughout this study's own documents as the single most
   important unresolved experiment — still not done.
4. **[MEDIUM] No multi-seed results anywhere.** Every CDR-PINN number in this study
   — including the ones that reversed each other (the LR-schedule split-sensitivity
   finding) — is single-seed. No bootstrap confidence intervals.
5. **[MEDIUM] Only one figure exists for CDR-PINN**: the newly-added epoch-vs-
   loss/AUC diagnostic plot. No ROC/PR curve plot (only the number is reported), no
   response-curve line plots (only a table), no permutation-importance bar chart.
6. **[LOW] Zero-shot super-resolution** (a proven FNO property, resolution-
   independence) has never actually been exercised on a trained checkpoint —
   architecturally true, operationally untested.
7. **[LOW] Instance-wise fine-tuning and self-adaptive per-point loss weighting**
   (both literature-prescribed, qualitatively different from the tuning already
   tested) — not yet attempted.
8. **What's already strong, stated plainly rather than underselling it**: the
   term-ablation study, all 3 Biswas variable-understanding analyses, the 7-way
   diagnostic sweep against the RF/MaxEnt accuracy gap, and the genuine standard
   train/val/test protocol (with a real, honest loss/AUC-divergence finding) are all
   real, rigorous, and — as of this session — properly validated rather than ad-hoc.
   This step's methodological rigor is not the weak point; its remaining
   *visualization* and *B1–B3 re-verification* debt is.
