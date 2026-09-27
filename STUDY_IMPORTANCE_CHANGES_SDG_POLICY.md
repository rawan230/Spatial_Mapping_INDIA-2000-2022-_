# Methodology Changes, Why They Matter, and This Study's Policy/SDG Relevance

**Prepared:** 2026-09-27, from the 2026-09-24/25 audit (`results/FULL_METHODOLOGY_AUDIT.md`,
`results/FINAL_MANUSCRIPT_NUMBERS.md`) and the rewritten manuscript
(`CDR_PINN_Full_Paper_Draft.md` / `Manuscript_TGRS/main.tex`).

This document answers three questions directly:
1. **What exactly changed** between the original (v1) pipeline and the audited (v2) pipeline, and
   *why* each change was made.
2. **Why these changes make your study more valuable**, not less — to reviewers, to other
   researchers, and to anyone using it for real decisions.
3. **What this study is worth to India's forest-fire policy and government strategy**, and which
   UN Sustainable Development Goals (SDGs) it genuinely supports — stated honestly, not inflated.

---

## Part 1 — What changed, and why

| # | Change (v1 → v2) | Why it was necessary | What it fixed |
|---|---|---|---|
| 1 | Fire-point rasterisation: `round()` → `floor()` (containing pixel) | `round()` measures from a pixel's *edge*, not its centre. This silently shifted **74.9% of the 541,545 fire points** into a neighbouring pixel. | Label now matches the correct pixel. Random Forest accuracy rose by +0.006 (all pixels) / +0.011 (forest) once fixed — a real, measurable improvement, not just a technicality. |
| 2 | Climate/LST/NDVI "anomaly-mean" features → 2001–2020 **climatological levels** | An anomaly averaged over its own 20-year baseline is mathematically close to zero by construction (it only reflects the 26 months outside the baseline). These features were carrying almost no information. | Replaced with the actual variable *levels* (temperature, humidity, NDVI, etc.) — the same form Biswas et al. (2025) used, so the model can finally learn from real climate signal instead of noise. |
| 3 | Mann–Kendall trend test → **Seasonal Kendall** test + Benjamini–Hochberg FDR correction | Mann–Kendall assumes independent, non-seasonal data. Applying it to monthly climate series (which are strongly seasonal) gives wrong significance counts — understated by **6.7× to 117×** depending on the variable. | Trend findings are now statistically defensible. One conclusion even reversed: air temperature's trend was earlier dismissed as "multiple-testing noise" — with the correct test, **9,988 of 29,056 pixels show a real, significant trend**. |
| 4 | Moran's I (spatial clustering) computed over India-only cells, not filled/synthetic cells | The original calculation (I = 0.83) included cells outside India that had been filled with placeholder values, artificially diluting the true spatial pattern. | Corrected value is **I = 0.9456** — an even *stronger*, and now honest, spatial-clustering result. |
| 5 | Land-cover year: 2020 → **2001** | Using land cover from 2020 — inside the same window as the 2000–2022 fire label — risks reverse causality (burned forest is often reclassified as shrub/agriculture in later maps, so the model could be "cheating" by seeing the fire's own aftermath). | Land cover now comes from *before* almost the entire study period, closing a real data-leakage risk (measured effect was small, but the risk itself is now closed, not just noticed). |
| 6 | CDR-PINN's "unseen years" test: label rebuilt from **training years only** | The original label pooled fire occurrence across *all* years, including the four years held out for testing — so the model's temporal test was quietly seeing test-period information during training. | Leak-free result: 0.893 AUC on unseen years — honest, and (importantly) it revealed the model actually performs *below* a simple year-over-year fire-frequency baseline (0.908–0.930), which the leaky version had hidden. |
| 7 | Evaluation now reports **forest pixels** as the primary population, not just "all pixels" | Non-forest pixels can never be positive under a forest-fire label, so scoring over all of India inflates accuracy for free (forest fraction alone gives AUC 0.91). | Honest number: **0.897 AUC on forest pixels** (vs. 0.975 on all pixels). This is the number that matters for real deployment, because forest is where the decision actually has to be made. |
| 8 | Added three missing controls: (a) the same neural network **without** the physics equation, (b) classical models trained on the **exact same cells and inputs** as CDR-PINN, (c) **covariate-free** persistence baselines | Without these three controls, any claim that "physics helps" or "the model generalises well" is unfalsifiable — there was nothing to compare against. | These controls are what actually let the study answer its own central question honestly (see Part 2). |
| 9 | Added a **physical-consistency check** (does the trained model actually obey its own equation?) | A model can score well on accuracy while its internal field violates the very physics it was supposedly built around — nobody had checked this. | Found that the trained field is nearly static and its equation residual is 74–616× larger than its own rate of change — the model was not behaving as a physical solution at all. |
| 10 | Corrected factual/documentation errors: grid spacing (0.01° → **1/120°**), feature count (57/58 → **55** in v2), untraceable "beats Biswas 0.9576" claim removed | Small errors like these erode a reviewer's trust in everything else once found — better to find and fix them first. | A genuine, traceable Biswas-style reimplementation now replaces the unverifiable claim: **0.893 ± 0.009 vs. their reported 0.879** — moderately comparable, and defensible under scrutiny. |
| 11 | Sensitivity tests added: FIRMS confidence/type filtering, MaxEnt training-size, slope algorithm, DEM resolution, distance accuracy against real geodesic distances | To pre-empt the most obvious reviewer questions ("did you check if X matters?") before they are asked. | All came back as **null results** (changes of <0.001–0.01 AUC) — which is itself valuable: it shows the pipeline's main findings are not fragile artefacts of arbitrary choices. |
| 12 | Equation-vs-code audit (12 discrepancies found and disclosed: the reaction term is not literally Fisher–KPP, the loss-weight formula in early text didn't match the code, etc.) | A physics-informed paper's credibility depends on the equations in the text matching the equations actually implemented. | Every mismatch is now disclosed and corrected in the text, closing off a category of criticism that is fatal if a reviewer finds it *before* you disclose it. |

**In one sentence:** every change either (a) fixed something that was quietly wrong and would have
produced an incorrect scientific claim, or (b) added a control/test that was previously missing
and without which the study's central claims could not be trusted.

---

## Part 2 — Why this makes your study *more* important, not less

It is natural to worry that a study which ends up saying "the physics didn't help" is a weaker
paper than one that reports a clean success. The opposite is true here, for four concrete reasons.

### 1. It is now a genuinely defensible, citable pipeline
Every one of the 55 features, the fire label, and the trend statistics has been recalculated from
raw data and matches an independent audit exactly. A reviewer or a future researcher can pull any
number in the paper and trace it to a script and a result file. This is rare — most susceptibility
mapping papers in this literature (including the reference study) do not publish this level of
traceability. That alone is a publishable methodological contribution.

### 2. A rigorous negative result is scientifically rarer, and more useful, than a positive one
Almost every physics-informed-learning paper in the environmental literature reports a positive
result, because negative results are usually never written up (this is called publication bias).
Your study is one of the few that:
- built the physics-informed model to a genuinely high standard (proven well-posedness, correct
  architecture, proper training protocol),
- tested it under the *exact* conditions the literature says should favour it (spatial shift,
  temporal shift, sparse labels, multiple seeds),
- and still found no benefit — with the receipts to prove it wasn't a coding bug or an unfair
  comparison.

This makes the paper useful to a much wider audience than a regional fire-mapping paper normally
reaches: it is now directly relevant to anyone in remote sensing, hydrology, or environmental
ML deciding whether to invest in a physics-informed architecture for their own problem. That is a
methodological caution the field needs and rarely gets in writing.

### 3. The corrected classical model is a genuinely deployable product
Because of the fixes above, the Random Forest model (0.897 AUC on forest pixels, validated across
random, spatial, and temporal splits) is now a trustworthy, ready-to-use national susceptibility
map — not a number that will fall apart under scrutiny. This is the part of the work with the
most direct, immediate value to a government agency (see Part 3).

### 4. It closes gaps the reference study (Biswas et al., 2025) left open
Your pipeline now has genuine 15/15 predictor-group parity with the reference paper, a corrected
and reproducible label, spatial and temporal cross-validation the reference study never attempted,
and an honest, like-for-like reimplementation of their own method for comparison. That is a real,
citable extension of the national reference study — independent of whatever the physics equation
does or does not do.

---

## Part 3 — Policy relevance, government strategy, and the SDGs

This section is written to the same standard as the rest of the audit: only claims the corrected
results actually support are made. Some connections below are strong (directly evidenced by your
own numbers); others are plausible extensions, and are labelled as such.

### 3.1 Direct relevance to India's forest-fire governance

| Government mechanism | How this study feeds it |
|---|---|
| **National Action Plan on Forest Fires (2018)** and the **National Forest Fire Prevention and Management Scheme (2003)**, administered by the Ministry of Environment, Forest and Climate Change | The corrected national susceptibility map (`results/final/maps/Susceptibility_RF_v2_score.tif`, five risk classes, forest-pixel-validated) gives a spatially explicit, statistically defensible risk layer at ~1 km resolution — usable directly for pre-fire-season resource pre-positioning. |
| **State-level fire management strategies** (Uttarakhand, Himachal Pradesh, Maharashtra, and the Forest Survey of India's own annual forest fire monitoring) | The terrain and accessibility findings (fires cluster on steeper slopes, and 38.9%/64.4% closer to roads/waterways than average) give concrete, quantified targeting criteria for patrol allocation and firebreak placement, rather than qualitative guidance. |
| **India's climate-adaptation planning** (State Action Plans on Climate Change, National Adaptation Fund) | The corrected trend analysis is now genuinely defensible evidence: nights are warming, days are cooling, and the diurnal temperature range is narrowing at millions of pixels (Seasonal Kendall + FDR, not the invalid earlier test). This is real, citable evidence of a changing fire-weather regime for state climate planning documents. |
| **Early-warning system design** (FSI's existing MODIS/SNPP-VIIRS fire alert system) | A validated risk-stratified map lets an early-warning system prioritise which alerts to escalate first, rather than treating every detection identically. |
| **Budget and resource allocation decisions** | Because Random Forest is cheap to run and retrain (216 seconds training time vs. CDR-PINO's far higher cost) and *more* accurate on this problem, this study gives a direct, evidence-based recommendation: **for near-term operational deployment, the classical model is both cheaper and better** — a concrete, actionable finding for a resource-constrained agency, not an abstract "future work" caveat. |

### 3.2 UN Sustainable Development Goals — honestly mapped

The earlier draft claimed nine SDGs by extending the (now-disproven) physics mechanism story. That
framing is withdrawn along with the mechanism claims it depended on. The SDG relevance below is
instead tied to what the corrected pipeline actually demonstrates.

**Strongly supported (direct evidence in your results):**

- **SDG 15 — Life on Land.** The core contribution: a corrected, validated national forest-fire
  susceptibility map is a direct life-on-land / forest-conservation tool. India's forest cover
  figure itself was corrected in this audit (18.3–19.3% inside India's boundary, not the earlier
  9.9–10.4% computed over the wrong area) — a small but genuine improvement in the accuracy of
  a number that would otherwise be miscited in future work.
- **SDG 13 — Climate Action.** The corrected Seasonal Kendall trend results are real, statistically
  sound evidence of a shifting fire-weather regime (temperature, humidity, and diurnal-range
  trends over 22 years) — exactly the kind of evidence climate-adaptation planning needs, and
  now defensible in a way the original (invalid) trend test was not.
- **SDG 9 — Industry, Innovation and Infrastructure.** The accessibility analysis (validated
  against real geodesic distances) quantifies how transport infrastructure relates to fire risk,
  directly informing infrastructure and early-warning-system planning.

**Plausible, reasonable extensions (not directly tested, but a defensible next step):**

- **SDG 1 (No Poverty) and SDG 2 (Zero Hunger).** Forest-dependent and rural communities are
  disproportionately affected by both fire damage and fire-suppression policy (e.g., restrictions
  on traditional burning practices). A risk-stratified map lets patrol and prevention resources be
  targeted more precisely, reducing both fire damage *and* unnecessary blanket restrictions —
  this is a reasonable policy application, not something this study measured directly.
- **SDG 3 — Good Health and Well-Being.** Forest fires are a documented source of air-quality
  degradation; a validated early-warning capability contributes indirectly to this goal, though
  this study did not model smoke or health outcomes.
- **SDG 17 — Partnerships for the Goals.** The fully reproducible, auditable pipeline (every
  script and result file traceable) is itself a resource other researchers and government
  technical agencies can build on directly, rather than starting from scratch.

**What is honestly *not* claimed:** the earlier draft's SDG 5, SDG 6, and SDG 12 connections
(via the physics mechanism story) are dropped, because the mechanism they depended on
(diffusion→vegetation policy, advection→terrain policy, reaction→ignition policy as *separable,
independently useful* signals) was the exact thing the audit found unsupported — advection turned
out to be redundant with the full predictor set, and the model does not behave as its equation
predicts. Claiming those SDG links now would repeat the same kind of unverified assertion this
audit exists to catch.

### 3.3 The bottom line for policy value

Your study's policy value does **not** come from the CDR-PINO equation — that result is a genuine,
rigorously-tested negative finding, valuable to science but not to a deployment decision. Its
policy value comes from:
1. a corrected, forest-population-validated national risk map ready for use,
2. statistically sound, citable climate-trend evidence for India's forests, and
3. a clear, evidence-based recommendation on which model to actually deploy (the cheaper, more
   accurate classical model) — which is exactly the kind of finding a government agency spending
   real money needs, and exactly the kind of honest recommendation a purely accuracy-chasing paper
   would never surface.

---

*Sources for every number above: `results/FINAL_MANUSCRIPT_NUMBERS.md`, `results/FULL_METHODOLOGY_AUDIT.md`, and the corresponding repo READMEs listed in `CLAUDE.md`.*
