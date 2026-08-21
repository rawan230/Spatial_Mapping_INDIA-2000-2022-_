# Step 5 — Terrain & Accessibility Analysis: Audit and Documentation

**Scope:** Step 5a (`Terrain_Elevation_Slope_Aspect_Analysis/`, notebook
`Step5a_Terrain_Elevation_Slope_Aspect.ipynb`) and Step 5b
(`Distance_Roads_Railways_Waterways_Analysis/`, notebook
`Step5b_Accessibility_Distance_Analysis.ipynb`), audited together as one logical step.
Read-only audit of notebook cells, executed outputs, saved CSVs, and saved PNGs — no
code was edited or re-run.

## What Was Done

Step 5 closes 6 of the 15 predictor variables in Biswas, Mahato & Joshi (2025) Table 3
that this pipeline had zero coverage of before 2026-08-18: **elevation, slope, aspect**
(Step 5a) and **distance to roads, railways, waterways** (Step 5b). Both sub-steps
produce, per variable: a full-India raster at the shared NDVI grid's native ~1km
resolution, a 0.25° "comparison" raster (built only to benchmark against Biswas et al.'s
working resolution, not consumed downstream), a summary-statistics CSV, a fire-point
coincidence/enrichment CSV, and two PNG figures each (a 3-panel spatial map, a
fire-coincidence bar chart).

Verified outputs actually on disk, both folders:
- `Terrain_Outputs/`: `T1_Elevation_native_1km.tif`, `T2_Slope_native_1km.tif`,
  `T3_Aspect_native_1km.tif`, `T3b_Aspect_8class_native_1km.tif` (bonus categorical
  aspect), each with a `_comparison_025deg.tif` sibling, plus
  `Terrain_summary_statistics.csv`, `Terrain_aspect_summary.csv`,
  `Terrain_Fire_Coincidence.csv`, `Terrain_Spatial_Maps.png`,
  `Terrain_Fire_Coincidence.png`.
- `Accessibility_Outputs/`: `D1_Distance_to_Roads_native_1km.tif`,
  `D2_Distance_to_Railways_native_1km.tif`, `D3_Distance_to_Waterways_native_1km.tif`,
  each with a `_comparison_025deg.tif` sibling, plus
  `Accessibility_summary_statistics.csv`, `Accessibility_Fire_Coincidence.csv`,
  `Accessibility_Spatial_Maps.png`, `Accessibility_Fire_Coincidence.png`.

Real results (India-masked, native 1km grid):

| Variable | Min | Max | Mean | P95 |
|---|---:|---:|---:|---:|
| Elevation (m) | −46.9 | 8,169.0 | 737.2 | 4,406.5 |
| Slope (°) | 0.00 | 77.31 | 5.72 | 28.66 |
| Aspect | — | — | 161.6° (S), circular mean | — |
| Distance to roads (km) | 0.00 | 260.1 | 5.69 | 15.90 |
| Distance to railways (km) | 0.00 | 1,611.2 | 38.28 | 160.07 |
| Distance to waterways (km) | 0.00 | 386.4 | 6.74 | 26.49 |

Fire-point coincidence, tested against all 541,545 (541,206 valid) real Step 1 fire
points:

| Variable | Finding |
|---|---|
| Slope | 12.3° mean at fire points vs. 5.7° nationally (**+115%**); 15–20° band is 4.8× overrepresented, 0–5° band is 0.34× underrepresented |
| Elevation | non-monotonic — 1000–1500m band 5.3× overrepresented; <200m (0.39×) and >3000m (0.029×) both underrepresented |
| Aspect | Flat terrain 0.06× underrepresented; circular mean skews SW at fire points (203.2°) vs. S nationally (161.6°) |
| Distance to roads | −40.1% (3.41 km at fires vs. 5.69 km nationally) |
| Distance to railways | +4.8% (40.12 km vs. 38.28 km — essentially no effect) |
| Distance to waterways | −64.7% (2.38 km vs. 6.74 km — the strongest accessibility signal) |

## How It Was Done

**5a (elevation/slope/aspect):** SRTMGL3 90m DEM, mosaicked from four
OpenTopography latitude-band requests (a single full-India request exceeds the 90m
product's area cap). Slope/aspect computed via a GPU-vectorized (CuPy, NumPy fallback)
implementation of Horn's (1981) 3×3-kernel method — the same algorithm ArcGIS/QGIS/GDAL's
`gdaldem`/richdem use internally — computed at the DEM's **native 90m resolution before**
resampling to the shared 1km NDVI grid, specifically to avoid smoothing away
gradient detail. Pixel spacing is latitude-corrected (longitude spacing shrinks ~20.2%
south to north). A sign-convention self-test is run at execution time (south-facing
patch → aspect 180°, east-facing → 90°, ESRI/Horn convention) and passed.

**5b (distance to roads/railways/waterways):** Geofabrik OSM 2022 vector extracts (6
India zone `.gpkg` files) — the same source vintage Biswas et al. cite. Feature-class
filtering is documented rather than defaulted: roads keep
motorway/trunk/primary/secondary/tertiary + `_link` (884,940 of 10.7M features, 8.3%,
deliberately including `tertiary` as the standard rural/forest-fringe access class);
railways exclude only `subway` (100,915 of 105,263 kept); waterways keep
river/canal/stream and exclude `drain` (234,313 of 255,094 kept). Distances are computed
with a GPU/CPU Euclidean distance transform in a custom India-centred equidistant conic
projection (chosen because a flat degree×111km conversion is wrong by >19% across
India's latitude range).

Both notebooks reuse the project-wide fire-point rasterization pattern (affine-transform
row/col lookup, not nearest-neighbor join) and the standard CuPy GPU-detect/fallback
pattern documented in the root `CLAUDE.md`.

## Why It Was Done This Way

Horn's method was chosen because it is the de facto standard gradient algorithm in GIS
tooling and because computing it at native 90m rather than after resampling preserves
terrain detail that a downsampled DEM would smooth away — a defensible, literature-aligned
default even though Biswas et al.'s own Table 2 names no DEM resolution or gradient
algorithm to match against directly.

Euclidean distance for the accessibility variables is explicitly disclosed as a
limitation in the Step 5b README (confirmed present, dated 2026-08-21): it is "the
accepted, mainstream choice for this variable in the current wildfire-ignition-risk
literature (matching Biswas et al.'s own approach, and recent Q1 work such as the NHESS
2025 study on human-caused ignition likelihood across Europe)," but does not capture the
distance–time/accessibility relationship a cost-distance surface would. This is framed
correctly as a one-sentence limitations-section item, not a pre-submission blocker.

The India-centred equidistant conic projection and the latitude-corrected gradient
spacing are both justified with concrete, quantified reasoning (>19% and ~20.2%
distortion respectively) rather than asserted — a good practice worth preserving in the
paper's methods section.

## Impact on Spatial Fire Mapping in India

These six variables bring the pipeline to full 15/15 predictor-group parity with Biswas
et al.'s Table 3 (previously 9/15), directly enabling Step 6's 60-band stack and Step 7's
full-58-feature retrain (ROC-AUC 0.9683, up from the earlier 9-feature model). The
fire-coincidence results are not marginal: slope shows the single largest enrichment
ratio in either sub-step (4.8× at 15–20°), and distance-to-waterways shows the largest
percentage shift of the three accessibility variables (−64.7%). Both are consistent
with, and now cited as corroborating, the CDR-PINN's own advection-term ablation, where
elevation/terrain was found to dominate model accuracy almost completely (confirmed six
independent ways in Step 8) — i.e., three independent lines of evidence in this project
(Biswas et al.'s MaxEnt contribution ranking, this step's own field-measurement fire
coincidence, and the CDR-PINN ablation) now converge on terrain as the dominant physical
driver.

## Comparison with Biswas et al. (2025)

| Variable | Biswas importance | Biswas contribution | This project |
|---|---:|---:|---|
| Slope | 5.6% | **16.7%** (2nd-highest overall) | Built, verified; fires at +115% mean slope |
| Elevation | 2.4% | 2.0% | Built, verified; non-monotonic mid-elevation peak |
| Aspect | 1.7% | 3.8% | Built, verified; SW skew at fire points |
| Distance to roads | 5.7% | 2.6% | Built, verified; −40.1% at fire points |
| Distance to railways | 4.6% | 4.9% | Built, verified; +4.8% (matches Biswas's low-contribution ranking for this variable) |
| Distance to waterways | 0.5% | 1.7% | Built, verified; −64.7% at fire points |

The connection back to Biswas et al.'s specific numbers is made explicitly, not left
implicit: both READMEs state the slope finding "directly corroborates Biswas et al.'s
own finding that slope is their second-most-important variable (16.7% model
contribution, behind only NDVI)," and the railways finding is explicitly matched to
"Biswas et al.'s own model where distance-to-railway is their lowest-contribution
human-activity factor after waterways." This is a solid, already-realized connection —
not a missed opportunity as originally hypothesized.

Two points Biswas et al. leave unspecified and this project cannot directly benchmark
against: their DEM source/resolution (Table 2 names neither) and their exact
proximity-distance algorithm (described only as "OSM proximity," not named as Euclidean,
network, or cost-distance). Both gaps are already disclosed in the respective READMEs
rather than silently assumed away.

## Completeness Audit: Gaps Found

1. **No algorithm-choice ablation/sensitivity analysis (real gap, moderate priority).**
   Neither notebook tests Horn's method against an alternative gradient algorithm (e.g.
   Zevenbergen & Thorne, or a simple D8/finite-difference slope), and Step 5b never
   validates its Euclidean distance-transform output against a known reference distance
   (e.g. a hand-checked point-to-road distance, or a comparison against a cost-distance
   surface for a sample region). Given slope is Biswas et al.'s second-highest
   contribution variable, a short algorithm-sensitivity check would strengthen a Q1
   submission's methods section, even if the expected result is "negligible difference."
   This was searched for directly (grep across both notebooks for algorithm-comparison
   terms) and found absent, not merely unlabeled.

2. **The −46.9m elevation artifact is disclosed but not resolved (low priority, already
   flagged by the notebook itself).** The Step 5a README states this explicitly as "not
   yet masked out — worth a one-line footnote in the paper, or a targeted patch if it
   matters for a specific downstream use." Since p5 is already +25.0m, this is a tail
   effect confined to a handful of pixels (likely an SRTM radar-return artifact over a
   lake/reservoir) and is unlikely to affect model training, but it should get the
   one-line footnote before submission rather than being silently left in the reported
   min/max range.

3. **Fire-coincidence visualization: no gap found.** Both sub-steps do visualize their
   headline coincidence findings, not just state them as numbers —
   `Terrain_Fire_Coincidence.png` is a 3-panel grouped bar chart (land-area % vs.
   fire-point % by slope/elevation/aspect band) and
   `Accessibility_Fire_Coincidence.png` is a 2-panel chart (mean-distance comparison +
   a "fire-point proximity bias" percentage-difference chart). This closes what could
   otherwise have been a real gap.

4. **Biswas-connection framing: no gap found.** Both READMEs explicitly tie their own
   fire-coincidence numbers back to Biswas et al.'s specific importance/contribution
   percentages (slope's 16.7% contribution ranking, railways' low-contribution ranking).
   This connection already exists and is prominent, not buried.

5. **DEM-source/algorithm disclosure: no gap found.** Both the unspecified Biswas DEM
   resolution and the unspecified Biswas distance algorithm are already called out
   explicitly in this project's own documentation as open questions on the reference
   paper's side, rather than silently assumed to match.
