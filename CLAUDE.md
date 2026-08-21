# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A multi-step, GPU-accelerated forest-fire-risk research pipeline for India (2000–2022),
implemented as a sequence of Jupyter notebooks — not a conventional application codebase.
Each step ingests raw remote-sensing/climate data (MODIS fire hotspots, ESA-CCI/C3S land
cover, NDVI, LST, FLDAS land-surface variables), derives features on a common grid, and
hands its outputs to the next step purely through files on disk (CSV/GeoTIFF/Parquet) —
there is no shared Python package or import graph between steps.

Per-step deep-dive detail (exact feature lists, environment gotchas, known bugs already
fixed) lives in `.claude/skills/<step-name>/SKILL.md` — one skill per analysis
(`fire-points-extraction`, `ndvi-analysis`, `lst-analysis`, `fldas-climatic-variables`,
`terrain-accessibility-analysis`, `integrated-fire-risk-model`), auto-invoked when
relevant or callable directly as `/<skill-name>`. This file stays at the overview level;
check the matching skill before doing nontrivial work in a given step's folder.

For substantial hands-on work in one step's folder (editing a notebook, debugging its
environment, extending its features), dispatch that work to an isolated subagent context
instead of doing it in the main thread — each step's `.claude/agents/<step-name>.md` file
is a self-contained brief (file paths, kernel, conventions, and a mandate to think about
publication-grade novelty and reproducibility, since this project's end goal is a
Q1-journal submission) scoped to exactly one step: `fire-points-extraction`,
`ndvi-analysis`, `lst-analysis`, `fldas-climatic-variables` (Step 4),
`terrain-accessibility-analysis` (Step 5), `integrated-feature-alignment` (Step 6),
`fire-susceptibility-model` (Step 7).

**Renumbered twice.** On 2026-08-17: FLDAS/land-cover became Step 4 (was Step 6),
integrated alignment became Step 5 (was Step 4), the susceptibility model became Step 6
(was Step 5) — training was made the last step in the actual execution order, not an
oddly-numbered middle step. On 2026-08-19: a new Step 5 (Terrain & Accessibility
Analysis — elevation/slope/aspect + distance to roads/railways/waterways, closing the
last 6 of Biswas et al.'s 15 predictor variables) was inserted between FLDAS and
Integration, bumping Integration to Step 6, the Susceptibility Model to Step 7, and the
already-built PINN comparison (see below) to Step 8. Neither renumbering changed any
code or data flow, only labels — this was always the real dependency order (FLDAS and
Terrain/Accessibility both had to run before assembly, regardless of their old numbers).
Agent/skill *names* are unaffected by either renumbering (they were already topic-named,
e.g. `fldas-climatic-variables`, not number-named).

**How to dispatch depends on the environment.** In a plain terminal Claude Code CLI
session, `.claude/agents/*.md` files are auto-discovered as named subagent types and can
be invoked directly (`subagent_type: fire-points-extraction`). **In the VSCode-extension
environment this project has mostly been used from, that registration does not happen**
(confirmed 2026-08-08 — the Agent tool only lists a fixed built-in set:
`claude, claude-code-guide, Explore, general-purpose, Plan, statusline-setup`; a named
step-agent call fails with "Agent type not found"). The working fallback there: dispatch
via the `general-purpose` agent and hand it the matching `.claude/agents/<step-name>.md`
file's path/content as its brief in the prompt — same context-isolation and token-reduction
effect, just without the named `subagent_type` shortcut. Check which situation you're in
before assuming a named-agent dispatch will work.

Methodology follows Biswas et al. (2025), *Environ. Sci. Pollut. Res.*, 32:4856–4878
(forest classes per Sannigrahi et al. 2018), extended with real fire-point integration and
GPU-vectorized statistics not present in the reference paper.

## Repository structure — this is NOT a single git repo

Each step folder is (or is meant to become) its **own independent git repository with its
own GitHub remote**, its own `README.md`, `requirements.txt`, and `.gitignore`. The project
root also has its own git repo now (initialized 2026-08-21, local only, no remote) —
but it is deliberately scoped to loose root-level files only (CDR-PINN design/paper
docs, this file, `METHODOLOGY.md`, a couple of root-level notebooks) via a root
`.gitignore` that excludes every subdirectory (`*/`), so it never crawls into any
step folder's nested `.git`. Before any git operation, check which folder you're
actually in and whether *that* folder has its own `.git`:

| Step | Folder | Has own `.git`? |
|---|---|---|
| 1 — Fire point extraction | `Forest fire Extraction in INDIA(2000-2022)/` | Yes |
| 2 — NDVI features | `NDVI_DATA_INDIA_/` | Yes |
| 3 — LST analysis | `LST_analysis/` | Yes |
| 4 — FLDAS climatic vars | `FLDAS Noah Land Surface Model L4 Global Monthly 0.1 x 0.1 degree (MERRA-2 and CHIRPS) (FLDAS_NOAH01_C_GL_M)/` | Yes |
| 5a — Terrain (elevation/slope/aspect) | `Terrain_Elevation_Slope_Aspect_Analysis/` | Yes (added 2026-08-18, numbered + pushed 2026-08-19) |
| 5b — Accessibility (distance to roads/rail/water) | `Distance_Roads_Railways_Waterways_Analysis/` | Yes (added 2026-08-18, numbered + pushed 2026-08-19) |
| 6 — Integrated alignment | `Integrated_Analysis/` | Yes (pushed 2026-08-07) |
| 7 — Susceptibility model | `Integrated_Analysis/` (same folder as Step 6) | Yes (same repo as Step 6) |
| 8 — PINN comparison | `Physics_Informed_FireRisk_Model/` | Yes (initialized 2026-08-21, pushed 2026-08-21) |

`Forest fire Extraction in INDIA(2000-2022)/` remote: https://github.com/rawan230/Forest-Fire-Points-Extraction-in-India-2000-2022-
`Integrated_Analysis/` remote: https://github.com/rawan230/Integrated-Fire-Risk-Analysis-in-India-and-Impliment-Baseline-Random-Forest-Model-
`Physics_Informed_FireRisk_Model/` remote: https://github.com/rawan230/_PINO_For_Spatial_Mapping_INDIA-2000-2022- — also holds
`Design_and_Paper/`, a copy of the CDR-PINN design/paper `.md` docs that otherwise live at the
project root, added 2026-08-21 so this remote is a self-contained PINO deliverable (implementation +
design + manuscript together). The project-root copies remain the canonical working copies, tracked
separately by the root's own (unpushed) git repo.
`Terrain_Elevation_Slope_Aspect_Analysis/` remote: https://github.com/rawan230/Terrain-Elevation-Slope-Aspect-India-SRTMGL3-90m-forest_fire_India-2000-2022-
`Distance_Roads_Railways_Waterways_Analysis/` remote: https://github.com/rawan230/India_Distance_Analysis-Roads-Railways-Waterways-Forest-Fire-in-India-2000-2022-

Never `git add -A` / commit from the project root assuming one repo — always `cd` into
the specific step folder first, or the harness may try to walk into a nested `.git` it
shouldn't touch.

## The pipeline: eight steps

1. **Fire point extraction** (`FOREST_FIRE_POINTS_EXTRACTION(INDIA).ipynb`, generated by
   `build_notebook.py`) — clips the MODIS Collection 6.1 FIRMS archive to India's exact
   boundary polygon (not a lon/lat bbox — that also covers Sri Lanka/Nepal/Bangladesh/
   Myanmar/Pakistan), then filters to forest LULC pixels via exact affine pixel lookup
   against yearly ESA-CCI/C3S land-cover rasters. Output: 541,545 real forest-fire points,
   `Forest_Fire_Outputs/all_forest_fires_2000_2022.csv` — **every later step depends on
   this exact file.** Also has a supplementary burned-area validation analysis (added
   2026-08-18, re-run 2026-08-20 once the previously-missing Jan/Feb months finally
   downloaded — see below): MODIS MCD64A1.061 annual burned area, correlated against
   this step's own fire-point counts (Pearson r=0.915, Spearman ρ=0.835, p<0.0001,
   n=23 years, full Jan–Dec coverage — 2000/2022 are partial by study-period design,
   not a data gap) and cross-checked year-by-year against Biswas et al.'s own reported
   annual fire counts (this project runs consistently 0.5–2.4% higher across all 20
   overlapping years — a validation, not a discrepancy, unchanged by the re-run). See
   `Forest_Fire_Outputs/Annual_BurnedArea_vs_FireCount.csv` and
   `Biswas2025_AnnualFireCount_Comparison.csv`.
2. **NDVI features** (`NDVI_ANALYSIS_WITH_FFP.ipynb`, generated by `build_ndvi_notebook.py`)
   — 9 NDVI-derived features (QA-filtered mean, climatology, anomaly, GPU-vectorized 2×12-MA
   trend/seasonal/residual decomposition, GPU-vectorized Mann-Kendall τ, CVSI with a
   real-fire-data-driven optimal lag (k*=8, extended/corrected 2026-08-10), LISA cluster
   map, NDVI–fire breakpoint threshold fit on real fire/no-fire labels). Establishes the
   **NDVI grid** (3641×3504 px, EPSG:4326, ~0.01°/1km) that Steps 3, 4, 5, and 6 all
   reproject onto.
3. **LST analysis** (`LST_DAY_NIGHT.ipynb`) — MOD11A2.061 day/night LST, diurnal temperature
   range (DTR), climatology/anomaly/Mann-Kendall trend (with significance p-values, added
   2026-08-10), reprojected onto the NDVI grid.
4. **FLDAS climatic variables + land cover** (`Land Surface Model Variables Analysis.ipynb`)
   — Noah LSM monthly variables (air temp, wind, humidity, precipitation, soil moisture, net
   LW radiation) plus a 22-class ESA CCI/C3S land-cover reclassification (verified 2026-08-09
   as the official Level-1 LCCS legend), both reprojected onto the NDVI grid and joinable on
   `(year, month)` against every other step's monthly tables.
5. **Terrain & Accessibility Analysis** (`Step5a_Terrain_Elevation_Slope_Aspect.ipynb` in
   `Terrain_Elevation_Slope_Aspect_Analysis/`, `Step5b_Accessibility_Distance_Analysis.ipynb`
   in `Distance_Roads_Railways_Waterways_Analysis/`) — added 2026-08-18, numbered
   2026-08-19, split into two independent repos 2026-08-19 (both stay Step 5a/5b, no
   further renumbering). **Corrected 2026-08-18**: Biswas et al.'s actual predictor set
   (their Table 3) is 15 variables, not 11 as this project's docs previously claimed.
   Burned area was never actually one of their 15 predictors, just a dataset used
   elsewhere in their paper (see Step 1's burned-area analysis above instead). The 6
   genuine gaps — elevation, slope, aspect (SRTMGL3 90m DEM, GPU Horn's-method gradient)
   and distance to roads/railways/waterways (Geofabrik OSM 2022, GPU Euclidean distance
   transform) — are closed here, bringing this pipeline to full 15/15 predictor parity
   with the reference paper. Runs alongside Step 4, feeds Step 6, not yet wired in. See
   each repo's own `README.md` for full results and methodology.
6. **Integrated alignment** (`Step6_Integrated_FireRisk_Analysis.ipynb`, was
   `Step5_...ipynb` before the 2026-08-19 renumbering, `Step4_...ipynb` before that) — the
   assembly point: builds LULC forest-fraction features (the one input not yet
   grid-aligned) and stacks Steps 1, 2, 3, and 4 (FLDAS climatic variables + 22-class land
   cover) + LULC into one 54-band `Integrated_FireRisk_Stack.tif` and a flattened
   `Integrated_FireRisk_Pixels.parquet` (4,161,009 in-India pixels × 56 columns / 52
   features after dropping `lon`/`lat`/`fire_count`/label). FLDAS wiring was added
   2026-08-07; forest-class definition reconciled with Step 1 on 2026-08-10 (national
   forest fraction rose ~7.8-8.0% → ~10.2-10.7%). Step 5's terrain/accessibility features
   are not yet wired in — that's the next remaining task (no longer gated on anything;
   the burned-area Jan/Feb download that was previously blocking Step 1's own
   supplementary analysis landed and was re-run 2026-08-20, see above).
7. **Susceptibility model** (`Step7_FireRisk_Susceptibility_Model.ipynb`, was
   `Step6_...ipynb` before the 2026-08-19 renumbering, `Step5_...ipynb` before that) —
   Random Forest (+ a real trained MaxEnt baseline, added to compare directly against
   Biswas et al.'s own method) trained on Step 6's parquet table (dynamically picks up
   whatever feature columns are present), evaluated with ROC-AUC/PR/cross-validation, plus
   a computational-cost/reproducibility report and a full-country fire-susceptibility
   probability GeoTIFF. Current result on the full 58-feature set (retrained 2026-08-20
   after Step 5a/5b terrain/accessibility wiring — the model now genuinely trains on all
   15/15 of Biswas et al.'s predictor variables, not just 9): ROC-AUC 0.9683, 5-fold CV AUC
   0.9679 ± 0.0002. Kept as a classical-ML baseline, not a PINN dependency — see the
   `integrated-fire-risk-model` skill for the full reasoning.
8. **PINN comparison** (`Step8_PINN_FireRisk_Model.ipynb` + `Step8b_PINN_Seed_Robustness_
   Check.ipynb`, was `Step7_...`/`Step7b_...` before the 2026-08-19 renumbering) — already
   built with real results (run 2026-08-08/09, before this project even started tracking
   it as a numbered step): a 5-model ladder (Logistic Regression → Random Forest → XGBoost
   → plain MLP → PINN) evaluated on random-split and two spatial-generalization tracks,
   plus a multi-seed robustness check. Headline finding: the physics-informed monotonicity
   penalty does not produce a measurable improvement over a same-capacity plain MLP (all
   three tracks' 95% CIs on the PINN-minus-MLP AUC delta include zero) — a genuine,
   rigorously-tested negative result. Lives in `Physics_Informed_FireRisk_Model/`
   (own git repo since 2026-08-21, local only). See that folder's `README.md` for
   the full model ladder, both evaluation tracks, and the honest read of the
   results.

   **Superseded for the paper's actual novel contribution, 2026-08-19/20, now fully
   implemented and validated**: Step 8's plain-monotonicity PINN is kept as an
   honest disclosed-negative-result baseline, but the physics-informed model this
   project is carrying forward is a full **CDR-PINN** — a convection-diffusion-
   reaction PDE (diffusion↔biophysical/climatic, advection↔topographic,
   reaction↔human-activity, mapping all four Biswas et al. predictor groups onto one
   governing equation) embedded in a physics-informed neural *operator* (FNO/PINO,
   Li et al. 2023), not a pointwise coordinate-MLP. Design docs
   (`CDR_PINN_Diffusion_Design.md`/`_v2.md`, `CDR_PINN_Advection_Design.md`,
   `CDR_PINN_Reaction_Design.md`, `CDR_PINN_Final_Design_STEP_D.md`, all in the
   project root) are complete end-to-end (equation, BC/IC, proven global
   well-posedness, architecture, training scheme). Implementation
   (`Physics_Informed_FireRisk_Model/cdr_pinn/`) is real, GPU-verified, and fully
   tested as of 2026-08-21: term-ablation (AUC 0.60 diffusion-only → 0.94 full CDR),
   all four generalization tracks (temporal strong at 0.897, spatial weak at
   0.60–0.75), all three of Biswas et al.'s variable-understanding analyses
   reproduced (permutation importance, response curves, Jackknife retraining — all
   converge on near-total elevation dominance), and six tuning-side interventions
   (metric-fix, scale-up, causal time-weighting, curriculum learning, LR-schedule ×2)
   tested to rule out an optimization explanation for the RF/MaxEnt accuracy gap.
   Full writeup: `CDR_PINN_Full_Paper_Draft.md`, `CDR_PINN_Methodology_Section.md`,
   `CDR_PINN_Novelty_Comparison_Advantages.md`, `CDR_PINN_Study_Clarifications_QA.md`
   (all project root).

## Conventions shared by every step (read this before touching any notebook)

- **Study period is always `2000-11-01` to `2022-12-15`**, hard-capped because ESA-CCI/C3S
  LULC data (used by Step 1) doesn't exist past 2022. Any new step must match this exactly
  or its months won't align with the others' `(year, month)` join key.
- **Boundary**: `India_State_Boundary.shp` (dissolved), not `India_Country_Boundary.shp`
  (has ~60 degenerate sliver polygons near the Palk Strait). Ships with wrong/missing CRS
  info — raw coordinates are EPSG:3857 (Web Mercator) meters; every notebook sets that CRS
  explicitly then reprojects to EPSG:4326 before use.
- **Fire-point rasterization pattern**: every step that needs Step 1's fire points on its
  own grid does it the same way — extract the raster's affine transform coefficients
  (`a,b,c,d,e,f`) and compute `row/col` directly (`col = round((lon-c)/a)`,
  `row = round((lat-f)/e)`), not a nearest-neighbor spatial join. Reuse this pattern rather
  than reinventing it.
- **GPU pattern** (CuPy, identical across all six notebooks):
  ```python
  try:
      import cupy as cp
      _test = cp.array([1, 2, 3]) * 2   # force JIT compile now, not mid-pipeline
      GPU_AVAILABLE = True
  except Exception:
      import numpy as cp                 # alias so downstream cp.xxx code is unchanged
      GPU_AVAILABLE = False
  ```
  followed by `to_host()` / `free_gpu()` helpers. Falls back to CPU correctly, just slower.
  **After a successful GPU detect, also call `cp.cuda.set_pinned_memory_allocator(None)`** —
  CuPy's default pinned-memory transfer path for large arrays (`cp.asarray()` on multi-GB
  stacks) is fragile across concurrent or killed CUDA contexts on the same GPU and throws
  `cudaErrorAlreadyMapped`. Once a CUDA context hits that error it is **permanently broken**
  — re-running cells will not recover it, only a genuine process restart (new PID) will.
  Never run two GPU-heavy kernels (e.g. a background `nbconvert` execution and a live
  interactive kernel) against the same GPU at once.
- **Notebooks generated from scripts**: Steps 1 and 2's `.ipynb` files are generated by
  `build_notebook.py` / `build_ndvi_notebook.py` respectively. To change their code, edit
  the build script and regenerate (`python build_*.py`), don't hand-patch the notebook JSON
  — otherwise the two drift out of sync. Steps 3–6 are hand-authored notebooks with no
  generator script.
- **Large/raw data is never committed.** Each step's `.gitignore` excludes raw source data
  by extension (`*.nc`, `*.hdf`, `*.h5`, `*.tif`, `*.zip`, `*.csv`, `*.shp` family) —
  individual raw files routinely exceed GitHub's 100MB limit (FLDAS `.nc` files are
  ~120MB each, 277 of them). READMEs document where to (re)download the data. Small,
  meaningful result artifacts (summary CSVs, PNG plots, GeoTIFFs under ~40MB) are tracked.

## Environments

Two registered Jupyter kernels are used across the project — check a notebook's
`metadata.kernelspec.name` before assuming which one to run it with:

| Kernel name | Python | Interpreter path | Used by |
|---|---|---|---|
| `wildfire_env` | 3.10.20 | `C:\Users\Admin\anaconda3\envs\wildfire_env\python.exe` | Steps 1, 2 |
| `firerisk-anaconda3` | 3.12.7 | `C:\Users\Admin\anaconda3\python.exe` (base anaconda3) | Steps 4, 5, 6, 7, 8 |

Step 3 (`LST_analysis/`) has no kernelspec recorded in its notebook metadata and no
`requirements.txt` — its actual run environment is undocumented; there's an unrelated `uv`
(Python 3.14) `.venv/` in that folder that doesn't match the notebook's recorded Python
3.12.7, so don't assume it's the right one without checking first.

## Common commands

Install a step's dependencies (run from inside that step's folder):
```bash
pip install -r requirements.txt
```

Execute a notebook end-to-end, writing outputs back into the file:
```bash
jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.kernel_name=<wildfire_env|firerisk-anaconda3> --ExecutePreprocessor.timeout=3600 "<notebook>.ipynb"
```
Use a generous timeout — several cells (Mann-Kendall lag-sweeps, full-country decomposition)
run for minutes even on GPU, longer on CPU fallback.

Regenerate a build-script-based notebook after editing its source:
```bash
python build_notebook.py        # Step 1 -> FOREST_FIRE_POINTS_EXTRACTION(INDIA).ipynb
python build_ndvi_notebook.py   # Step 2 -> NDVI_Novel_Analysis_FINAL_15.ipynb
```

## Windows/PowerShell pitfall to watch for

`Out-File` / `Set-Content` in PowerShell default to **UTF-16** unless `-Encoding utf8` is
passed explicitly. A `.gitignore` (or any file a non-Windows tool must parse) written this
way is silently broken — git won't match its patterns, so "excluded" files get staged
anyway. This has already happened once in this project (root `.gitignore` had a UTF-16 BOM
and wasn't actually excluding anything). If a `.gitignore` seems to not be working, check
for a `FF FE` BOM before debugging the patterns themselves; prefer the `Write` tool (always
UTF-8) over PowerShell redirection for writing these files.
