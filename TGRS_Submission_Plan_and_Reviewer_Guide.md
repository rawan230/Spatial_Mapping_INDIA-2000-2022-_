# TGRS Submission Plan and Reviewer Guide

<!-- AUDIT-UPDATE-2026-09-25 -->
> ### Audit update (2026-09-25)
> A full end-to-end audit recalculated every step from raw data and re-ran every model (`results/FULL_METHODOLOGY_AUDIT.md`).
> Take paper numbers **only** from `results/FINAL_MANUSCRIPT_NUMBERS.md`. The pre-update copy of this file is in
> `_Archive_Unwanted_2026-09-25/pre_audit_document_snapshots/TGRS_Submission_Plan_and_Reviewer_Guide.md`. Statements in this document superseded by the audit:
>
> - **Term ablation (0.602 / 0.924 / 0.940)**: historical single-seed, fixed-budget runs, with no no-physics arm. Under one validated protocol with 3 seeds: **no physics 0.945, diffusion 0.924, diff + adv 0.939, full 0.939** (Track A). No physics configuration beats no physics on any track.
> - **Physics vs no physics**: confirmed and extended (3 seeds, paired tests). Full − none: −0.006 (A, p < 0.02 for every seed), CI including 0 (B1, B2), −0.011 (B3).
> - **'RF 0.950 vs CDR 0.751 on the same fold scheme'**: not the same folds, grid, label or features. On CDR-PINO's own cells, splits and covariates, RF scores **0.974** (B1), 0.959 (B2) and 0.980 (A), vs CDR-PINO 0.719 / 0.570 / 0.939.
> - **CDR-PINO historical numbers** (0.9398, 0.7510 ± 0.0182, 0.6187 ± 0.0680, 0.8960) reproduce bit-exactly. Under the unified protocol (3 seeds), full CDR scores 0.939 / 0.719 / 0.570 / 0.893 (A / B1 / B2 / B3), and Track A and B1–B3 were separate models trained under different protocols.
> - **Zero-shot super-resolution, resolution independence and instance-wise fine-tuning**: not evaluated. Present them as future work only.
> - **22 land-cover fractions** come from the 2020 map, inside the label window. v2 uses the 2001 map; the measured leakage effect is small.
> - **RF 0.9704 / MaxEnt 0.9598** reproduce exactly (v1, all pixels). v2: RF 0.975 all / **0.897 forest pixels** (the primary population, because forest fraction alone gives AUC 0.91).
> - **−46.9 m elevation**: located at the Neyveli open-cast lignite mines; most likely real terrain, not an SRTM artefact.
<!-- AUDIT-UPDATE-2026-09-25 -->


**Purpose of this document.** This is the navigation layer for the manuscript, not a
replacement for the material it points to. Every step's own README now carries a
`## Why this step, and how` walkthrough and a `## Comparison against Biswas et al.
(2025)` section (added/corrected 2026-09-23, see each repo's own git log) — this
document does **not** duplicate that prose, because duplicating it is exactly the
kind of cross-file drift this same audit pass spent most of its effort fixing
(the root/`Design_and_Paper` CDR-PINN doc divergence, the stale RF/MaxEnt numbers
in `PIPELINE_SUMMARY.md`, the month-old "not yet run" claim on the physics-vs-
no-physics test — all real, all found and corrected in this pass). Instead, this
document gives: (1) why IEEE TGRS is the right venue and what that implies
structurally, (2) one consolidated novelty/comparison table spanning all 8 steps
with pointers to the full prose, (3) a one-paragraph-per-step reviewer talking
point, and (4) the honest, current punch list of what is genuinely still open.

---

## 1. Why IEEE Transactions on Geoscience and Remote Sensing (TGRS)

TGRS is the right fit for this study, not a stretch, for four concrete reasons:

1. **Multi-source remote-sensing fusion at national scale is TGRS's core subject
   matter.** This study fuses MODIS fire hotspots, MODIS NDVI, MODIS LST, FLDAS
   Noah-LSM reanalysis, ESA-CCI/C3S land cover, SRTM DEM-derived terrain, and OSM
   vector-derived accessibility onto one common ~1km grid across 22 years — exactly
   the kind of heterogeneous EO-data-fusion pipeline TGRS regularly publishes.
2. **Physics-informed neural operators for Earth-system/geoscience prediction are
   an active, current TGRS topic area.** The CDR-PINN (an FNO/PINO applied to a
   convection-diffusion-reaction formulation of fire spread) is a methodological
   contribution of the kind TGRS's "machine learning for geoscience" scope
   explicitly covers — distinct from a purely ecological or environmental-health
   framing (which is what Biswas et al.'s venue, *Environmental Science and
   Pollution Research*, targets instead).
3. **TGRS expects rigorous, quantitative validation, including spatial
   cross-validation and disclosed negative results** — this pipeline already has
   both (spatial-block CV on RF/MaxEnt/CDR-PINN, temporal leave-years-out,
   honestly-reported physics-vs-no-physics negative results across all four
   tracks). That rigor is a fit for the venue, not a liability to soften.
4. **A full-pipeline paper (not just the CDR-PINN) is publishable as one TGRS
   article** because the paper's actual claim is a *system*-level one: a
   full-parity (15/15 Biswas et al. predictor groups), higher-resolution,
   temporally-resolved reproduction-and-extension of a published fire-susceptibility
   study, with three model classes (MaxEnt replication, tuned Random Forest, and a
   physics-informed neural operator) compared under a common, more rigorous
   validation protocol than the reference study used.

### What targeting TGRS changes structurally (do this before submission, not now)

- **Citation style**: IEEE numbered `[1]`, not author-year — every one of this
  project's `.md` docs currently cites author-year (`Biswas et al., 2025`) for
  working-draft readability; the actual manuscript LaTeX/Word file needs a
  reference list converted to IEEE numbered style with a `\bibliographystyle{IEEEtran}`
  (or the Word/Overleaf TGRS template equivalent).
- **Section structure** (IEEE Transactions convention): Abstract → Index Terms (5–8
  keywords, e.g. *wildfire susceptibility, physics-informed neural operator,
  Fourier neural operator, multi-source data fusion, spatial cross-validation,
  India*) → I. Introduction → II. Related Work → III. Study Area and Data →
  IV. Methodology → V. Experimental Results → VI. Discussion → VII. Conclusion.
  `Complete_Methodology_Section.md` is already assembled close to this shape for
  Section IV; `CDR_PINN_Full_Paper_Draft.md` is close to a full draft already but
  uses a slightly different section numbering — reconcile the two into one
  manuscript file before submission rather than submitting either as-is.
- **Length**: TGRS regular papers typically run 12–14 double-column pages. This
  project's existing draft material (Complete_Methodology_Section.md alone is
  ~1,400 lines) is comfortably enough raw content — the work remaining is
  compression and figure selection, not more writing.
- **Data/code availability statement**: TGRS increasingly expects one. This
  project's 8 separate public GitHub repos (listed in `CLAUDE.md`) already satisfy
  this in substance; the manuscript needs one consolidated statement listing all
  8 remote URLs plus the note that raw source rasters are excluded per each
  repo's own `.gitignore` (documented reasons: FLDAS `.nc` ~120MB×277 files, etc.)
  with re-download instructions in each README.

---

## 2. Consolidated Novelty and Comparison vs. Biswas, Mahato & Joshi (2025)

Biswas et al. (2025), *Environ. Sci. Pollut. Res.* 32:4856–4878, is a MaxEnt-only,
0.25°-resolution, single-random-split fire-susceptibility study using 15 predictor
variables across 4 groups (verified by direct PDF-table extraction, not secondhand
citation — see each step's own README for the exact importance/contribution
percentages). The table below is the one-paragraph-per-step version of "what we
changed and why," each row backed by the cited step's own, now-corrected README:

| Step | What Biswas et al. did | What this study does differently | Full detail |
|---|---|---|---|
| 1. Fire points | Used a fire-count dataset at their working 0.25° grid | Point-level MODIS FIRMS C6.1 ground truth (541,545 points) filtered to forest LULC by exact affine lookup against the *exact* dissolved India boundary polygon (not a bounding box); independent forest-masked burned-area cross-validation (r=0.9044 vs. their Fig. 7d) they do not perform | [`Forest fire Extraction in INDIA(2000-2022)/README.md`](Forest%20fire%20Extraction%20in%20INDIA(2000-2022)/README.md) |
| 2. NDVI | One raw monthly MOD13C2 v006 value at 0.05° (their single most important predictor, 28.4% contribution) | 9-feature decomposition (climatology/anomaly/trend/residual/Mann-Kendall/CVSI with a fire-data-driven optimal lag/LISA/empirically-fit breakpoint) at 1km, ~30× finer resolution; CVSI, LISA, and the fitted breakpoint have no counterpart in their methodology at all | [`NDVI_DATA_INDIA_/README.md`](NDVI_DATA_INDIA_/README.md) |
| 3. LST | Static monthly MOD11C3 day/night means at 0.05° (19.7% combined contribution) | MOD11A2 8-day composites, an explicit diurnal temperature range (DTR) feature they don't compute, full climatology/anomaly/FDR-corrected Mann-Kendall trend testing at 1km | [`LST_analysis/README.md`](LST_analysis/README.md) |
| 4. FLDAS climatic + land cover | 5 static monthly-mean climatic variables at 0.25° (33.9% combined contribution) + no explicit land-cover feature table | Same 5 FLDAS variables reprojected to 1km with FDR-corrected trend/significance testing; a full 22-class ESA-CCI/C3S land-cover reclassification joinable on (year, month), a granularity absent from their Table 2 | [`FLDAS Noah Land Surface Model.../README.md`](<FLDAS Noah Land Surface Model L4 Global Monthly 0.1 x 0.1 degree (MERRA-2 and CHIRPS) (FLDAS_NOAH01_C_GL_M)/README.md>) |
| 5a. Terrain | Slope/elevation/aspect rasterized directly at 0.25° from an unspecified DEM/algorithm (topographic group 9.7% combined importance / **22.5% combined contribution**; slope alone their **2nd-highest** contribution variable overall at 16.7%) | Horn's (1981) gradient method on a native 90m SRTMGL3 DEM before resampling; an independent empirical cross-check (fires at +115% mean slope vs. national baseline) corroborating their own slope-contribution finding via an entirely different method | [`Terrain_Elevation_Slope_Aspect_Analysis/README.md`](../Terrain_Elevation_Slope_Aspect_Analysis/README.md) |
| 5b. Accessibility | Distance to roads/rail/waterways from OSM, unspecified algorithm, at 0.25° (human-activity group 10.8% combined importance / **9.2% combined contribution** — by contribution, less than half the topographic group's 22.5%, the reverse of an earlier draft's importance-vs-contribution mix-up, corrected 2026-09-23) | Full GPU Euclidean distance transform over Geofabrik OSM 2022 vector data at native ~1km in a proper equidistant-conic projection (avoiding the >19% latitude-dependent error a flat degree-to-km conversion introduces) | [`Distance_Roads_Railways_Waterways_Analysis/README.md`](../Distance_Roads_Railways_Waterways_Analysis/README.md) |
| 6. Integration | Implicit — one flat 0.25° feature table for MaxEnt | Explicit grid/temporal alignment of 7 heterogeneous sources onto one 1km, 4,161,009-pixel, 57-feature table, with a disclosed and corrected forest-fraction leakage fix (baseline-only feature retained, recent/current years dropped) that Biswas et al.'s own static land-cover treatment has no equivalent safeguard against | [`Integrated_Analysis/README.md`](../Integrated_Analysis/README.md) |
| 7. Susceptibility model | MaxEnt only, one random train/test split, no spatial CV | A real trained MaxEnt replication **and** a hyperparameter-tuned Random Forest, evaluated with random-split + 5-fold CV + 2°×2° spatial-block CV (Roberts et al. 2017) — RF 0.9704 AUC beats their reported MaxEnt performance outright, and this study's own MaxEnt (0.9598) is directly comparable since it is a faithful replication of their method, not a secondhand citation | [`Integrated_Analysis/README.md`](../Integrated_Analysis/README.md) |
| 8. CDR-PINN | No mechanistic/physical model of any kind — MaxEnt is purely correlational | A convection-diffusion-reaction PDE (diffusion↔biophysical/climatic, advection↔topographic, reaction↔human-activity, mapping onto their own 4 predictor groups) solved by a physics-informed Fourier neural operator, with proven global well-posedness, all 3 of their own variable-understanding analyses reproduced (permutation/response-curve/Jackknife), and a genuinely new temporal-generalization axis (leave-years-out) they have no equivalent of | [`Physics_Informed_FireRisk_Model/README.md`](../Physics_Informed_FireRisk_Model/README.md), full argument in [`CDR_PINN_Novelty_Comparison_Advantages.md`](CDR_PINN_Novelty_Comparison_Advantages.md) |

**Convergent validation, worth foregrounding in the Discussion section**: two
independently-built models — Biswas et al.'s MaxEnt (16.7% slope contribution) and
this study's CDR-PINN (advection/terrain term driving +0.322 of the model's total
+0.34 AUC gain; six independent methods total, including Step 5a's own field
measurement) — converge on the same physical driver (terrain/slope dominance) via
completely different statistical frameworks. That convergence is a stronger claim
for a Q1/TGRS submission than either finding alone, and should be stated as such in
the paper, not buried as a footnote.

**Honest, disclosed limitations of the comparison** (state these in the paper —
TGRS reviewers will ask if they're not pre-empted): (1) CDR-PINN trails both
classical baselines on spatial generalization (Track B1 0.7510 vs. RF 0.9498/MaxEnt
0.9465 on an identical fold scheme) — the paper's honest generalization-advantage
claim is temporal (Track B3, 0.8960), not spatial; (2) a direct physics-vs-no-physics
test found no accuracy benefit from the physics constraint on any of the four
tracks tested (Track A null; a real measured cost on B2/B3) — report this exactly
as measured; (3) Step 1's fire points have no FIRMS confidence-level filtering or
spatial declustering applied yet (a disclosed, deliberate scope decision, not an
oversight — see the Step 1 README's "Known limitation" section for the citations
and the reason it wasn't fixed in this pass).

---

## 3. One-Paragraph Reviewer Talking Points, Per Step

Use these as the spoken answer to "walk me through this step" — the full written
version with citations lives in each step's own README, linked above.

1. **Fire points**: "We start from real point-level MODIS fire detections, not an
   aggregated count — we clip to the exact India state-boundary polygon (not a
   bounding box, which would wrongly include Sri Lanka/Nepal/Bangladesh), filter to
   forest land cover by looking up each point's exact pixel in the year-matched
   land-cover raster, and independently validate our 22-year fire-count trend
   against MODIS burned-area products restricted to forest pixels only — matching
   Biswas et al.'s own forest-scoped validation approach rather than an all-land-
   cover comparison, which would overstate the correlation by 6–10×."
2. **NDVI**: "NDVI is the standard vegetation-moisture proxy for fire risk, but
   Biswas et al. use one raw monthly value. We decompose it into nine features —
   trend, anomaly, a fire-data-driven cumulative stress index, spatial clustering,
   and an empirically-fit threshold — because a single snapshot value can't
   distinguish a vegetation that's *chronically* stressed from one having one bad
   month."
3. **LST**: "Land surface temperature indicates surface heating and dryness. We
   add a diurnal temperature range feature — the day/night gap — as a fuel-curing
   proxy Biswas et al. don't compute, and we correct for the fact that testing
   millions of pixels for a significant trend produces false positives by chance
   alone, using a standard multiple-testing correction they don't apply either."
4. **FLDAS climatic variables + land cover**: "These five variables — temperature,
   humidity, wind, precipitation, radiation — are fire-weather proxies at the same
   resolution Biswas et al. use, reprojected onto our shared 1km grid. We add a
   full 22-class land-cover breakdown so the model can see forest-type composition
   directly, not just a binary forest/non-forest mask."
5. **Terrain**: "Slope is Biswas et al.'s second-most-important predictor by
   contribution, right after NDVI — fires spread faster uphill because heat
   preheats the fuel ahead of the flame front. We compute slope and aspect from a
   90-meter elevation model using a standard geomorphometric method, before
   downsampling, so we don't smooth away the terrain detail that makes it
   predictive — and we confirm the same effect independently in our own raw fire
   data: fires sit at more than double the national average slope."
6. **Accessibility**: "Most forest fires are human-caused, so distance to roads,
   railways, and waterways is a proxy for where people actually are. We compute
   these at full resolution using the same OpenStreetMap source Biswas et al.
   cite, and confirm fires cluster much closer to roads and waterways than the
   national average — consistent with a human-ignition mechanism."
7. **Integration**: "This step is where all six other data sources get aligned
   onto one common grid and joined into a single table the models train on. We
   also caught and fixed a subtle data-leakage risk here: land-cover features from
   years that overlap the fire label's own time window could let the model learn
   'this area got reclassified after a fire' rather than genuine pre-fire risk, so
   we kept only the earliest, cleanest land-cover snapshot."
8. **Modeling — RF, MaxEnt, and CDR-PINN**: "We don't just build one model. We
   replicate Biswas et al.'s own MaxEnt method as a direct baseline, train a
   modern Random Forest that outperforms it, and then build something genuinely
   new: a physics-informed neural operator that solves a partial differential
   equation for fire spread, where each mathematical term corresponds to a real
   fire-behavior mechanism. It doesn't yet beat the classical models on raw
   accuracy — we say so plainly — but it's the only model in this study capable of
   generalizing to *future, unseen years*, which is the actual early-warning use
   case, and it lets us ask *why* a location is high-risk in a way a black-box
   classifier can't."

---

## 4. Current Punch List — Genuinely Open Items (as of 2026-09-23)

Everything below is a real, disclosed gap — not hidden, not silently worked
around. Ranked by what would most strengthen a TGRS submission if addressed,
**none require immediate action**; this is the reference list for prioritizing
future sessions, per this pass's "docs-first, flag rather than fix" scope.

1. **[Cascades through the whole pipeline if changed]** Step 1's fire points have
   no FIRMS confidence-level filtering or spatial declustering/thinning applied.
   Literature-standard practice this pipeline currently skips (MODIS C6 Fire
   User's Guide; spatial-autocorrelation-in-fire-ML studies; MaxEnt-with-thinning
   precedent). Changing this means re-running every downstream step (2 through
   8/CDR-PINN) — a deliberate, scoped decision to make explicitly before
   attempting it, not a quick fix.
2. **[Contained to Step 6/7, needs a code change + rerun]** Step 3's DTR
   Mann-Kendall trend feature is computed and exported but never actually carried
   into Step 6/7's feature stack — a real feature-parity gap flagged by this
   session's own LST audit.
3. **[Contained to CDR-PINN]** Multi-seed coverage is still missing for the B1/B2/
   B3 generalization tracks and the term-ablation study (Track A alone has a
   3-seed check). Needed before any of those numbers can carry a confidence
   interval in the paper.
4. **[CDR-PINN, literature-prescribed, unattempted]** Zero-shot super-resolution
   evaluation (a proven FNO architectural property, never actually exercised on a
   trained checkpoint) and instance-wise fine-tuning (PINO's own prescribed
   second training phase, Li et al. 2023 §3.2) — both would strengthen the
   "resolution-independence" and "closing the RF/MaxEnt accuracy gap" arguments
   respectively, neither implemented yet.
5. **[Documentation/verification only]** `Complete_Methodology_Section.md`'s own
   editorial note flags one open cross-reference question: whether the
   `train_standard_protocol.py` checkpoint (Track A, AUC=0.9398) is the exact same
   checkpoint the B1/B2/B3 re-run was scored against, since they come from two
   different scripts. Worth a direct code check before this goes in a submission,
   not assumed either way.
6. **[Low priority, disclosed as acceptable]** The −46.9m elevation-minimum
   artifact (Step 5a, a likely SRTM radar-return artifact over a lake/reservoir)
   and the Euclidean-vs-cost-distance simplification (Step 5b) are both fine to
   state as one-sentence limitations rather than fix.
7. **[Documentation only, needs the user's own verification]** Step 5b's README
   cites an "NHESS 2025 study on human-caused ignition likelihood across Europe"
   as informal support for the Euclidean-distance limitation note. This was
   flagged by the auditing agent as an unverified reference — no confirmed
   author/DOI was available — and was deliberately left uncited rather than
   fabricated. Either supply the exact citation or remove the informal mention
   before submission.
8. **[Documentation only, needs remeasurement not guessing]** `Integrated_
   Analysis/README.md`'s Step 7 wall-time figure (~137 min / 8,241.2 sec) is
   attributed to the 55-feature leak-fixed run; Step 7 has since been retrained
   twice more (57-feature specific-humidity addition, MaxEnt tuning). The added
   column is unlikely to move this much, but it is not a freshly-measured number
   for the current run — remeasure on the next actual notebook execution rather
   than editing the figure without a real timing.
9. **[Fixed 2026-09-23, noted here for traceability]** Both Step 5a and 5b
   READMEs (and this document's own table above) mislabeled a combined
   *importance* sum as a combined *contribution* sum for the topographic and
   human-activity predictor groups, which also produced a reversed comparative
   claim ("human-activity contributes more than topographic" — actually the
   opposite once contribution is computed correctly: topographic 22.5% vs.
   human-activity 9.2%). Corrected in both repos and here; flagged as an example
   of the kind of cross-file numeric error this audit process is designed to
   catch, not just a one-off.

---

*This document was assembled 2026-09-23 as part of a pipeline-wide audit pass
that also corrected several real, dated inconsistencies found along the way
(see `CLAUDE.md`'s own commit history and each step repo's git log for the
specifics) — cross-check it against those sources if a number here ever looks
stale, the same way this pass caught the previous staleness.*
