# Study Status — What's Done, What's In Progress, What's Still Needed

**Snapshot as of 2026-08-22.** This is a working checkpoint document, not a paper
section — its job is to give you a single, accurate picture of the rigor-upgrade work
triggered by the literature audit (2026-08-21 onward) so you can decide what to
prioritize next.

---

## 1. Fully done, verified, and committed

| # | Fix | Real result | Where |
|---|---|---|---|
| 1 | **Step 2 (NDVI): India boundary masking added** — the one step that had none at all | 8,573,393 px (67.2% of grid) now correctly excluded as ocean/neighboring-country land; breakpoint θ* shifted 0.529→0.535 (expected) | `NDVI_DATA_INDIA_` repo, commit `b7c7d3c` |
| 2 | **Step 3 (LST): FDR correction** on Mann-Kendall trend significance | Day 1,063,120→393,838 sig. px (−63%), Night 234,318→17,935 (−92%), DTR 2,545,287→2,290,051 (−10%) | `LST_analysis` repo, commit `b19d2f1` |
| 3 | **Step 4 (FLDAS): same FDR fix** + resolution-caveat disclosure | Air temp's 636-px "trend" → 0 (was pure noise); other variables shrank 19–73% | FLDAS repo, commit `18d44fc` |
| 4 | **Step 5b: Euclidean-distance limitation** disclosed (doc only) | — | `Distance_Roads_Railways_Waterways_Analysis` repo, commit `263b508` |
| 5 | **Step 6: forest-fraction leakage fixed** — dropped `forest_frac_recent`/`current`/loss (2020/2022, overlapped the fire label window); kept only `forest_frac_baseline` (2001) | 60→57 bands, 62→59 columns, 58→55 features. Verified directly against the parquet schema. | `Integrated_Analysis` repo, commit `9ba00c0` |
| 6 | **Step 7: retrained on corrected features + spatial-block CV added** (untuned baseline) | Random-split: RF 0.9687 (was 0.9683), MaxEnt 0.9594 (was 0.9595) — essentially unchanged despite losing top-3 features. **Spatial-block CV (new, matches CDR-PINN's Track B1 exactly): RF 0.9501±0.0031, MaxEnt 0.9455±0.0050 — both far above CDR-PINN's own 0.7510 (re-run 2026-08-23 with validation-driven early stopping, was 0.754).** *(This row is the 2026-08-22 snapshot; since superseded twice — specific-humidity added 2026-08-22 (57 features, RF 0.9704) and MaxEnt's `beta_multiplier` validated-tuned 2026-08-23 (MaxEnt 0.9598 random-split / 0.9465±0.0054 spatial-block) — see `FULL_EXPERIMENT_LOG.md` §B for the current numbers; both models are now validation-tuned, closing this doc's own "untuned baseline" label.)* | `Integrated_Analysis` repo, commit `16d093a` |
| 7 | **CDR-PINN: `forest_frac` covariate rebuilt** from the corrected baseline source | full_cdr retrain: AUC 0.9406→0.9397 (unchanged). Permutation/response-curve/Jackknife all re-run: elevation dominance reconfirmed a 5th time; `forest_frac`'s own contribution barely moved (Jackknife only-forest_frac: 0.7016→0.7011) — the leakage fix was methodologically correct but empirically low-impact here | `Physics_Informed_FireRisk_Model` repo, commit `0832e20` |
| 8 | **Standard train/val/test protocol adopted** — genuine 65/15/20 split, `preprocessing.py` built and verified for both CDR-PINN and Step 7 | Split fractions/columns verified directly against real data | Both repos |
| 9 | **Architecture documented in standard DL terminology** (channels, "no real kernel," no pooling and why) | — | `CDR_PINN_Methodology_Section.md` §4.1a |
| 10 | **Preprocessing pipeline mapped to canonical stage names** (your proposed structure) | — | `CDR_PINN_Full_Paper_Draft.md` §2.1 |
| 11 | **PINN-literature techniques tested**: causal time-weighting, staged curriculum learning | Both underperformed baseline (0.9369, 0.9343 vs 0.9406) — real negative results, documented | Paper draft §4.7 |
| 12 | **All 3 of Biswas et al.'s variable-understanding analyses reproduced** (permutation importance, response curves, Jackknife) | 5 independent methods now converge on elevation dominance | Paper draft §4.4–4.6 |

---

## 2. Currently running (launched, not yet complete)

| Job | Purpose | Status |
|---|---|---|
| `hp_search_weight_decay.py` (CDR-PINN) | Validated AdamW weight-decay search (0, 1e-5, 1e-4), selected by validation AUC | Running on GPU |
| `hp_search_rf.py` (Step 7) | Validated RF hyperparameter search (4 configs varying max_depth/min_samples_leaf), selected by validation AUC | Running on CPU |

**Queued immediately after these finish:**
- `train_standard_protocol.py` — the final CDR-PINN training run: genuine val/test split, validated weight decay, `ReduceLROnPlateau`, early stopping, loss-curve plot (epoch vs. train/val loss) saved to disk. This becomes the new canonical CDR-PINN checkpoint and headline number, superseding every earlier full_cdr number in this study.
- Step 7's final tuned RF fit + test evaluation using the `hp_search_rf.py` winner.
- Once the new CDR-PINN checkpoint exists: permutation importance, response curves, and Jackknife need re-running against it *again* (they currently reflect the pre-standard-protocol checkpoint) for full consistency.

---

## 3. Known, real gaps — not yet started

Ranked by how much they'd matter to a reviewer:

1. **Step 1 fire-point filtering (FIRMS confidence + spatial thinning)** — the biggest
   remaining gap. All 541,545 points are used unfiltered; no spatial declustering
   before use as ML labels. Fixing this changes the ground-truth labels themselves,
   which cascades through **every** downstream step (2 through 8) — a multi-hour,
   full-pipeline rebuild, not a contained fix. Deliberately not started without your
   explicit go-ahead given the cost.
2. **No figures generated for CDR-PINN** — no susceptibility probability map (the
   actual "spatial mapping" deliverable), no plotted ROC/PR curves. The new loss-curve
   plot (item 2 above, once it lands) will be the *first* real figure this model has
   ever produced.
3. **Physics-vs-no-physics comparison on Tracks B1/B2/B3** — still only run on Track A.
   Given today's finding that RF/MaxEnt now clearly beat CDR-PINN on spatial CV too,
   this comparison matters even more: does the physics constraint at least narrow that
   gap on the hard tracks, even if it doesn't close it?
4. **Multi-seed robustness / bootstrap CIs** — every CDR-PINN number in this study,
   including today's, is still single-seed.
5. **Stale cross-references from the Step 6 feature-count change** — "58-feature" /
   "60-band" / "62-column" language still appears in `CDR_PINN_Full_Paper_Draft.md`,
   `CLAUDE.md`, `FULL_STUDY_RESULTS_SUMMARY.md`, `CDR_PINN_Study_Clarifications_QA.md`,
   `CDR_PINN_Novelty_Comparison_Advantages.md`, `METHODOLOGY.md`,
   `CDR_PINN_Final_Design_STEP_D.md` — found via a sweep, not yet fixed (deliberately
   held until real final numbers exist, so the fix happens once, not twice).
6. **The paper's spatial-generalization narrative needs rewriting**, not just number
   updates — §2 above's spatial-CV finding (RF/MaxEnt clearly ahead of CDR-PINN on
   spatial CV, not just random split) changes what "the honest story" actually is:
   temporal generalization (Track B3) is now unambiguously CDR-PINN's *only* real
   generalization advantage, not one of several open questions.
7. **Step 1's own README/notebook** and the fldas/integrated-feature-alignment agent
   briefs still need the same kind of pass this document just did for the paper docs.

---

## 4. Decisions that are yours to make next

- Proceed with Step 1's fire-point filtering (item 3.1) now, accepting the full-pipeline
  rebuild cost, or leave it for a later phase?
- Once the queued CDR-PINN/Step 7 work finishes, should I immediately do the full
  stale-reference sweep (item 3.5) and narrative rewrite (item 3.6), or wait for
  further instruction?
- Priority order for items 3.2–3.4 (figures, B1/B2/B3 physics-vs-no-physics,
  multi-seed) — all three are real, literature-flagged gaps but represent real
  additional compute/time.

---

*This document will go stale the moment the two running searches finish — treat it as
a snapshot, not a living reference. `FULL_STUDY_RESULTS_SUMMARY.md` remains the
complete, step-by-step results reference; `project_pipeline_wide_literature_audit.md`
(Claude's memory) tracks the audit itself.*
