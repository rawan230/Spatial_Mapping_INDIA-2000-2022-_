# Pipeline-Wide Completeness Audit — Summary

**Purpose**: a synthesis of the 8 per-step audit/documentation files
(`Step1_..._Audit_and_Documentation.md` through `Step8_..._Audit_and_Documentation.md`,
all in the project root), each produced by an independent read-only investigation of
the real, current code and outputs — not assumptions. This document is the "what to
decide next" layer; the 8 individual files are the full detail per step.

---

## Findings already fixed during this same pass

1. **LST's `requirements.txt` was missing `statsmodels`** (hard-imported by the FDR
   fix) — would have broken a fresh install. Fixed and committed.
2. **Step 7's notebook was training with untuned hyperparameters while the docs
   already claimed the tuned result.** A validated search (`hp_search_rf.py`) found
   `max_depth=25, min_samples_leaf=3` beats the old defaults, but the *notebook
   itself* — the thing that produces every plot, map, and exported artifact — was
   never updated to match. Fix dispatched, running now (re-executing the full
   notebook with the tuned config, ~90 minutes, CPU-bound).

## Real, new findings — not yet fixed, need your decision

Ranked by how much they'd matter to a reviewer, with which step found them:

1. **[Step 4] Biswas et al.'s actual predictor — specific humidity — never gets
   spatial treatment.** Only relative humidity (a substituted, non-Biswas variable)
   gets the full climatology/anomaly/trend pipeline and feeds the trained model.
   Specific humidity is stored as a national scalar only. This is silent — nowhere
   is it disclosed as a deliberate substitution. Specific humidity is Biswas et
   al.'s **third-highest-contribution predictor (13.0% importance / 15.0%
   contribution)** — this is the most consequential finding in the whole audit.
   Fixing it properly means adding specific humidity's full spatial pipeline to
   Step 4, then re-wiring Step 6, retraining Step 7, and possibly rebuilding
   CDR-PINN's `dryness_proxy` covariate if it was built from RH rather than
   specific humidity — a real, multi-step cascade, comparable in scope to the
   forest-fraction leakage fix.
2. **[Step 1] The burned-area validation analysis has no reproducible source.**
   `Annual_BurnedArea_vs_FireCount.csv`, the Biswas year-by-year comparison, and
   the associated plot exist only as committed output files — no script or
   notebook cell that produces them exists anywhere in the tracked repo, only git
   commit messages describing what was done. A reviewer or future researcher
   couldn't regenerate this analysis. Needs either the original code recovered or
   the analysis rebuilt from scratch.
3. **[Step 1] FIRMS confidence/type filtering — quantified now, not just flagged.**
   4.29% of the final 541,545 points have confidence < 30; 0.21% have `type != 0`
   (MODIS's own non-vegetation-fire classification) — both currently unfiltered.
   Already known as a gap; now has real numbers attached. Still deliberately
   deferred given the cascading cost of changing ground-truth labels (see Step 1's
   own future-work item).
4. **[Step 5] No algorithm-choice sensitivity check for terrain/distance methods.**
   No comparison of Horn's method against an alternative slope algorithm, no
   validation of the Euclidean distance transform against a known reference
   distance. Lower stakes than items 1-2 but a real, literature-flaggable gap given
   slope is Biswas et al.'s second-highest-contribution predictor (16.7%).
5. **[Step 3] Several NDVI/LST/FLDAS features are computed but never plotted** —
   only exported as GeoTIFFs or reported as numbers (Mann-Kendall significance
   maps, CVSI lag-sensitivity curve, DTR's own trend τ isn't even carried into the
   final feature stack despite being fully computed in Step 3).
6. **[Step 6] `Integrated_Analysis/README.md`'s Step 7 section is stale** — flagged
   as "STALE, pending retrain" from an earlier pass, but the retrain already
   happened (twice, including the tuned version now in progress) and the README
   was never updated. Will self-resolve once the current Step 7 fix's README update
   lands.
7. **[Step 2] The strongest step in the pipeline, mostly complete** — CVSI's k*=8
   selection is a real sensitivity sweep, just never plotted (only console text).
   No controlled single-feature-vs-full-set ablation exists to make the
   "engineered features beat raw NDVI" claim a direct experiment rather than an
   inference from Step 7's feature importances.
8. **[Step 8/CDR-PINN] Already tracked in this session's own status document**
   (`STUDY_STATUS_AND_REMAINING_WORK.md`) — no full-country probability map, B1/B2/B3
   not re-run under the current checkpoint, no multi-seed testing, only one figure
   (the newly-added loss curve) exists for the whole model.

## What's already genuinely solid across the pipeline

Worth stating plainly, not just cataloguing gaps: Steps 1, 2, 3, 4, 5, and 6 all have
real, GPU/CPU-verified pipelines with dozens of real saved figures, and every
already-known methodological gap from the earlier literature audit (boundary masking,
FDR correction, the leakage fix, spatial-block CV) has been independently re-confirmed
as genuinely landed by these fresh audits — not just claimed. The pipeline's
foundational rigor is real; the remaining gaps are specific, bounded, and now
individually understood rather than a vague "needs more work."

## Suggested priority order, for your decision

1. Let the Step 7 hyperparameter-consistency fix finish (already running).
2. **Decide on the specific-humidity substitution (item 1)** — this is the one
   finding serious enough to warrant its own scoped fix, similar to the
   forest-fraction leakage fix. Your call on whether to fix it now or document it
   as a disclosed limitation and move on.
3. Recover or rebuild Step 1's burned-area validation script (item 2) — a
   reproducibility fix, moderate effort.
4. Everything else (items 4-7) is lower-stakes documentation/plotting debt — can be
   batched into a single pass once 2-3 are resolved.

I'm holding here per your own instruction — tell me which of these you want done
next.
