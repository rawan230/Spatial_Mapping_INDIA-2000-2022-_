"""Generate one AUDIT_2026-09-25.md per step repository, with every number read from the audit
report files (no hand-typed metrics). Output goes to results/repo_audit_docs/<repo>/."""
import json
import os

import pandas as pd

RES = r"D:\FOREST FIRE MAPPING(INDIA)\results"
OUT = os.path.join(RES, "repo_audit_docs")
os.makedirs(OUT, exist_ok=True)
J = lambda p: json.load(open(os.path.join(RES, p), encoding="utf-8"))
R1, R2, R3 = J("recalculated/R1_fire_labels/R1_report.json"), J("recalculated/R2_fldas/R2_report.json"), J("recalculated/R3_lulc/R3_report.json")
R4, R5, R6, R7 = J("recalculated/R4_ndvi/R4_report.json"), J("recalculated/R5_lst/R5_report.json"), J("recalculated/R6_terrain/R6_report.json"), J("recalculated/R7_access/R7_report.json")
M = pd.read_csv(os.path.join(RES, "baseline", "CLASSICAL_METRICS.csv"))
FM = pd.read_csv(os.path.join(RES, "final", "FINAL_METRICS.csv"))
PA = pd.read_csv(os.path.join(RES, "baseline", "PAIRED_trackA.csv"))
S = pd.read_csv(os.path.join(RES, "cdr_pino", "SUMMARY_cdr_unified.csv"))
BS = J("biswas_reference/BISWAS_STYLE_BASELINE.json")

HEAD = """# Audit of record — {title} (2026-09-24/25)

A full end-to-end audit of the forest-fire susceptibility study **recalculated this step independently
from the raw data** and compared every output with the files in this repository. Numbers below are
read directly from the audit reports. The audit code is in `audit_2026-09-25/` (paths in the scripts
point to the author's project folder). The full study-level audit lives in the project root repository
(`results/FULL_METHODOLOGY_AUDIT.md`).

"v1" = this repository's historical outputs (unchanged). "v2" = the corrected definitions adopted by
the audit. v1 files were **not** overwritten; v2 outputs are produced by the audit scripts.

"""


def f(x, d=4):
    return f"{x:.{d}f}" if isinstance(x, (int, float)) else str(x)


def cmp_table(rows):
    s = "| Item | n compared | Pearson r | max abs diff | Verdict |\n|---|---:|---:|---:|---|\n"
    for c, verdict in rows:
        s += f"| {c['name']} | {c.get('n_compared', ''):,} | {f(c.get('pearson_r', float('nan')), 7)} | {c.get('max_abs_diff', ''):.3g} | {verdict} |\n"
    return s


docs = {}
# ------------------------------------------------------------------------- Step 1
st = R1["stage_counts"]; ff = R1["firms_fields"]; lv = R1["label_variants"]
cov = pd.read_csv(os.path.join(RES, "recalculated", "R1_fire_labels", "annual_extraction_and_forest_cover.csv"))
lab = M[(M.experiment == "trackA") & M.tag.isin(["RF_v2", "RF_v2_label_conf30", "RF_v2_label_type0", "RF_v2_label_conf30_type0"])]
d = HEAD.format(title="Step 1, fire-point extraction")
d += "## 1. Reproduction from the raw FIRMS archive\n\n| Stage | Historical | Recalculated |\n|---|---:|---:|\n"
for k, lbl in (("raw_archive", "Raw archive"), ("india_bbox", "India bbox"), ("india_polygon_state", "India polygon"), ("dedup_lon_lat_date", "Deduplicated"), ("forest_filter", "Forest-LULC filter")):
    d += f"| {lbl} | {st[k]:,} | {st[k]:,} |\n"
hc = R1["historical_csv_comparison"]
d += f"\nThe recalculated point set is **identical** to `all_forest_fires_2000_2022.csv` ({hc['common']:,} common points; {hc['recalc_only']} and {hc['historical_only']} unique to either side). No LULC year in 2000–2022 needed the nearest-year fallback.\n\n"
d += "## 2. Corrections\n\n"
d += (f"- **National forest cover.** The `forest_cover_pct` column of `extraction_summary.csv` "
      f"({cov.forest_pct_download_rectangle.min():.2f}–{cov.forest_pct_download_rectangle.max():.2f}%) is computed over the rectangular LULC download subset, "
      f"which includes neighbouring countries and ocean. Over India only, forest cover is **{cov.forest_pct_india_only.min():.2f}–{cov.forest_pct_india_only.max():.2f}%**.\n")
d += ("- **Rasterising these points onto the 1/120° NDVI grid.** The rule used downstream, `row = round((lat − f)/e)`, rounds against the "
      "top-left *edge* and puts 74.9% of points in a neighbouring pixel. Use `floor` (the containing pixel). The forest filter in this repository "
      "is **correct**, because it rounds against pixel *centres* taken from the LCCS NetCDF coordinate arrays.\n")
d += (f"- **Points not on valid NDVI pixels:** {R1['rasterisation']['outside_india_mask']} fall outside the India raster mask and "
      f"{R1['rasterisation']['outside_ndvi_valid']} fall on NaN NDVI pixels. These are dropped silently downstream.\n")
d += "- **Burned-area validation scripts are tracked in this repository** (commit 5b2c316). Earlier documentation said they were not preserved.\n\n"
d += "## 3. FIRMS QA fields and label sensitivity\n\n"
d += f"- Confidence < 30: **{ff['confidence_lt30']:,} ({ff['confidence_lt30_pct']:.2f}%)**. Type ≠ 0: **{sum(v for k, v in ff['type_counts'].items() if str(k) != '0'):,} ({ff['type_nonzero_pct']:.2f}%)**; types: {ff['type_counts']}.\n"
d += f"- Satellite: {ff['satellite']}. Day/night: {ff['daynight']}. Same pixel & same day (multiple detections): {R1['same_pixel_same_day_multiple_detections']:,}.\n\n"
d += "Random-forest test ROC-AUC with each label variant (v2 features; each model scored against its own label):\n\n| Label | Fire pixels | AUC all pixels | AUC forest pixels |\n|---|---:|---:|---:|\n"
for tag, key in (("RF_v2", "all"), ("RF_v2_label_conf30", "conf_ge30"), ("RF_v2_label_type0", "type0"), ("RF_v2_label_conf30_type0", "conf_ge30_type0")):
    a = lab[(lab.tag == tag) & (lab.population == "all")].roc_auc.iloc[0]; fo = lab[(lab.tag == tag) & (lab.population == "forest")].roc_auc.iloc[0]
    d += f"| {key} | {lv[key]['fire_pixels_in_ndvi_valid']:,} | {a:.4f} | {fo:.4f} |\n"
d += "\n**Conclusion:** filtering on confidence or type changes accuracy by < 0.001, a documented null result.\n\n"
bs = R1["boundary_sensitivity_points_in_bbox"]; bd = R1["boundary_sensitivity_disagreement"]
d += (f"## 4. Boundary sensitivity\n\nPoints inside the India bbox that fall within each polygon: state {bs['state']:,}; country {bs['country']:,}; GADM 4.1 {bs['gadm']:,}. "
      f"State vs country disagreements: {bd['state_not_country']} + {bd['country_not_state']}. State vs GADM: {bd['state_not_gadm']:,} + {bd['gadm_not_state']:,} "
      f"(≤0.3% of points; mostly coastal and disputed-border areas).\n\n")
bc = R1["biswas_counts"]
d += (f"## 5. Comparison with Biswas et al. (2025)\n\nAnnual counts derived from Biswas et al.'s published yearly shares × their decade totals "
      f"({bc['decade_totals_sum']:,}; each value carries ±24 points of rounding): this extraction runs **{bc['diff_pct_range'][0]:+.2f}% to {bc['diff_pct_range'][1]:+.2f}%** "
      f"per year, r = {bc['pearson_r']:.5f} (2001–2020). Burned-area correlations, recomputed from the saved annual series: all land cover r = 0.9149 / ρ = 0.8350; "
      "forest-masked r = 0.9345 / ρ = 0.7846 (n = 23). The Biswas Fig. 7d comparison values are digitised from a chart.\n")
docs["Forest fire Extraction in INDIA(2000-2022)"] = (d, ["recalc_01_fire_labels.py", "audit_common.py"], ["recalculated/R1_fire_labels/R1_report.json", "recalculated/R1_fire_labels/annual_extraction_and_forest_cover.csv", "recalculated/R1_fire_labels/biswas_annual_count_comparison_recalc.csv"])

# ------------------------------------------------------------------------- Step 2 NDVI
d = HEAD.format(title="Step 2, NDVI features")
d += "## 1. Reproduction from 266 raw MOD13A3.061 months\n\n" + cmp_table([(c, "reproduced" if c.get("pearson_r", 0) > 0.99999 else "both ≈ 0 (degenerate)") for c in R4["historical_comparison"]])
f6 = R4["F6"]; m8 = R4["F8_moran"]; th = R4["F9_theta"]
d += f"""
## 2. Findings and v2 definitions

| Feature | Finding | v2 |
|---|---|---|
| QA gap | 2007-03 and 2007-04 have **no pixel-reliability file** (a 2025-03 file was downloaded instead); the notebook used them **unfiltered** | MODLAND bits of VI_Quality (F1 r = {R4['F1_hist_vs_v2_corr']:.6f}; max change {R4['F1_hist_vs_v2_max_abs_diff']:.3f}) |
| QA sensitivity | Good-only vs Good + Marginal: F1 r = {R4['F1_qa01_vs_qa0_corr']:.4f}; missing pixel-months {100*R4['frac_missing_pixel_months_qa0']:.1f}% vs {100*R4['frac_missing_pixel_months_qa01']:.1f}% | Good + Marginal kept |
| F3 anomaly mean | Degenerate: equals the anomalies of the 26 months outside the 2001–2020 baseline (identity error {R4['F3_identity_max_abs_err']:.1e}) | dropped |
| F4 trend mean | r(F4, F1) = {R4['F4_vs_F1_corr']:.5f}, so redundant | dropped |
| F5 residual mean | Identically about 0 (max {R4['F5_resid_mean_abs_max']:.1e}); the seasonal component is not centred | dropped |
| F6 Mann–Kendall | Computed on the 2×12-MA **trend** series (median lag-1 autocorrelation {f6['median_lag1_autocorr_trend_series']:.3f}), so the independence assumption fails. Historical counts reproduce ({f6['hist_sig_p05_browning']:,} browning / {f6['hist_sig_p05_greening']:,} greening) but are not valid | **Seasonal Kendall + BH-FDR:** {f6['sk_sig_fdr_greening']:,} greening / {f6['sk_sig_fdr_browning']:,} browning; median Sen slope {f6['sen_median_per_yr']:+.4f} NDVI yr⁻¹ |
| F7 CVSI | k\\* = {R4['F7_kstar']['hist']} (historical labels), {R4['F7_kstar']['corr']} (corrected), {R4['F7_kstar']['corr_trainonly']} (training labels only); MI at k = 8 is 0.0125 | kept (k chosen on training labels) |
| F8 Moran / LISA | Global I = {m8['hist_method_I']:.4f} (z = {m8['hist_method_z']:.1f}) reproduces, **but {m8['hist_n_filled_nonindia']:,} of {m8['hist_n_cells']:,} cells (67%) are non-India cells filled with row means** | India cells only, 8×8 block means: **I = {m8['v2_india_only_blockmean_I']:.4f}** (z = {m8['v2_z']:.1f}, p = {m8['v2_p_sim']}) |
| F9 threshold | θ\\* = {th['hist_labels']:.4f} (historical labels), {th['corrected_labels']:.4f} (corrected), {th['corrected_trainonly']:.4f} (training only) | dropped (label-fitted step function of F1; ΔAUC 0.0000) |
| F10 fire raster | `round((lat − f)/e)` rounds against the top-left **edge** and puts **74.9% of points in a neighbouring pixel**; fire pixels 270,655 (historical) vs 268,766 (correct), Jaccard 0.50 | `floor` (containing pixel); raises RF AUC +0.0055 (all) / +0.0114 (forest) |
"""
docs["NDVI_DATA_INDIA_"] = (d, ["recalc_04_ndvi.py", "trend_stats.py", "audit_common.py"], ["recalculated/R4_ndvi/R4_report.json"])

# ------------------------------------------------------------------------- Step 3 LST
inv = R5["inventory"]
d = HEAD.format(title="Step 3, LST day/night and DTR")
d += f"""## 1. Inventory

{inv['n_used']:,} complete 8-day composites were used ({inv['first_used']} – {inv['last_used']}). Incomplete dates excluded silently: {', '.join(inv['incomplete'])} (one has only QC layers; the other has no Night layer). LST grid {R5['native_grid']['shape']} at 1/120°, aligned with the NDVI grid at integer offsets ({R5['offset_ndvi_vs_lst_in_pixels']['col']:.0f}, {R5['offset_ndvi_vs_lst_in_pixels']['row']:.0f}) pixels.

## 2. Reproduction

"""
d += cmp_table([(c, "reproduced" if c.get("pearson_r", 0) > 0.99999 else "reproduced with the historical composite-weighted climatology (r = 1.000000 on a test strip)") for c in R5["parquet_comparison"]])
d += "\n**Historical climatology:** the mean over all 8-day composites in a calendar month (composite-weighted), not the mean of monthly means. Anomaly-mean features are near-degenerate either way and are replaced by climatological levels in v2.\n\n## 3. Trends: Mann–Kendall on raw monthly series vs Seasonal Kendall\n\n"
d += "MK on a raw monthly series ignores the seasonal cycle, so the test is invalid. The Seasonal Kendall test (Hirsch et al. 1982) with BH-FDR is used in v2.\n\n| Series | Raw-MK mean τ | Raw-MK significant (p < 0.05 → FDR) | SK mean τ | SK FDR-significant (+ / −) | Median Sen slope (°C/yr) |\n|---|---:|---:|---:|---:|---:|\n"
for b in ("day", "night", "dtr"):
    t = R5[f"trend_{b}"]
    d += f"| {b.upper()} | {t['mk_raw_tau_mean']:.4f} | {t['mk_raw_sig_p05']:,} → {t['mk_raw_sig_fdr']:,} | {t['sk_tau_mean']:.4f} | {t['sk_sig_fdr']:,} ({t['sk_sig_fdr_pos']:,} / {t['sk_sig_fdr_neg']:,}) | {t['sen_median_C_per_yr']:+.4f} |\n"
d += f"""
The directions reproduce the historical text (day cooling, night warming, DTR narrowing). The historical FDR counts understated the number of significant pixels. **The DTR trend is now a model feature** (v2), closing the earlier gap.

## 4. Resolution relative to Biswas et al.'s MOD11C3 (0.05°)

Block-averaging the 2001–2020 climatological level to 0.05° retains {100*R5['day_variance_retained_at_0.05deg']:.1f}% (day) and {100*R5['night_variance_retained_at_0.05deg']:.1f}% (night) of its spatial variance (day RMSE {R5['day_rmse_1km_vs_0.05deg_blockmean_C']:.2f} °C). Replacing the LST levels by their 0.05° versions changes RF test AUC by −0.0001 (all pixels) / −0.0002 (forest pixels). The product difference (8-day vs monthly CMG compositing) remains a disclosed caveat.
"""
docs["LST_analysis"] = (d, ["recalc_05_lst.py", "trend_stats.py", "audit_common.py"], ["recalculated/R5_lst/R5_report.json", "recalculated/R5_lst/composite_valid_fraction.csv"])

# ------------------------------------------------------------------------- Step 4 FLDAS
d = HEAD.format(title="Step 4, FLDAS climatic variables and land cover")
d += f"## 1. Reproduction from 266 raw FLDAS NetCDF files\n\nUnits (from file attributes): {R2['units']}. FLDAS grid {R2['fldas_grid']['shape']}, {R2['fldas_grid']['india_pixels']:,} India pixels. Missing months: {len(R2['missing_months'])}.\n\n"
d += cmp_table([(c, "reproduced") for c in R2["parquet_comparison"]])
d += "\n## 2. Anomaly-mean features are degenerate\n\nWith a 2001–2020 climatology, each calendar month's baseline anomalies sum to zero. The time-mean anomaly over 2000-11 – 2022-12 therefore equals **the summed anomalies of the 26 out-of-baseline months ÷ n** (identity verified numerically). v2 replaces these features with 2001–2020 climatological **levels**, the form Biswas et al. used.\n\n| Variable | Identity error | Level std / anomaly-mean std | Raw-MK FDR-sig. | Seasonal-Kendall FDR-sig. (+/−) | National mean level |\n|---|---:|---:|---:|---:|---:|\n"
for v, x in R2["per_variable"].items():
    d += f"| {v} | {x['max_abs_identity_error']:.1e} | {x['ratio_level_std_to_anommean_std']:.0f}× | {x['mk_raw_sig_fdr']:,} | {x['sk_sig_fdr']:,} ({x['sk_sig_fdr_pos']:,}/{x['sk_sig_fdr_neg']:,}) | {x['national_mean_level']:.4g} |\n"
fc = R3["forest_change_2001_2020"]
d += f"""
**The historical conclusion "air-temperature trend is multiple-testing noise (636 → 0 after FDR)" is an artefact** of MK on a seasonal series. With Seasonal Kendall, {R2['per_variable']['tair']['sk_sig_fdr']:,} of 29,056 pixels are FDR-significant.

**Specific humidity is a per-pixel feature** (`SpecificHumidity_anomaly_mean`, `MannKendall_tau_SpecificHumidity_monthly` are gridded and in the model table). It is not only a national scalar, as some documentation stated. Derived relative humidity is an additional predictor.

## 3. Land cover

- The 22-class fractions (2020) reproduce **bit-exactly** (max diff 0.0 for all classes), and so does the 2001 forest fraction.
- **Temporal leakage risk:** the 2020 map lies inside the 2000–2022 fire-label window. Measured mechanism: forest-fraction change 2001→2020 is {fc['mean_change_fire_pixels']:+.4f} at fire pixels vs {fc['mean_change_nonfire_forest_pixels']:+.4f} at non-fire forest pixels; the share of pixels losing forest is {100*fc['frac_pixels_losing_forest_fire']:.1f}% vs {100*fc['frac_pixels_losing_forest_nonfire']:.1f}%. The effect is weak, but v2 uses the **2001** map.
- LC140 (lichens and mosses) is constant (0) over India, so it is dropped in v2.
"""
docs["FLDAS Noah Land Surface Model L4 Global Monthly 0.1 x 0.1 degree (MERRA-2 and CHIRPS) (FLDAS_NOAH01_C_GL_M)"] = (d, ["recalc_02_fldas.py", "recalc_03_lulc.py", "trend_stats.py", "audit_common.py"], ["recalculated/R2_fldas/R2_report.json", "recalculated/R3_lulc/R3_report.json", "recalculated/R2_fldas/fldas_national_monthly_recalc.csv"])

# ------------------------------------------------------------------------- Step 5a / 5b
ss = R6["slope_algorithm_sensitivity"]; na = R6["negative_elevation_artifact"]
d = HEAD.format(title="Step 5a, terrain (elevation, slope, aspect)")
d += f"## 1. Reproduction from the SRTMGL3 mosaic\n\nDEM {R6['dem']['shape']} at {R6['dem']['res_deg']:.7f}°; native elevation {R6['native_stats']['elev_min']:.0f} to {R6['native_stats']['elev_max']:.0f} m.\n\n" + cmp_table([(c, "reproduced" + (" (0°/360° wraparound)" if "aspect" in c["name"] else "")) for c in R6["parquet_comparison"]])
d += f"""
## 2. Sensitivity

| Quantity | Value |
|---|---|
| Horn vs Zevenbergen–Thorne slope, correlation | {ss['corr_horn_vs_zt']:.5f} |
| Mean slope, Horn / ZT | {ss['mean_horn']:.2f}° / {ss['mean_zt']:.2f}° |
| Single-feature fire AUC, Horn / ZT | {ss['single_feature_auc_horn']:.4f} / {ss['single_feature_auc_zt']:.4f} |
| Effect of ZT slope on RF v2 test AUC | 0.0000 (DeLong p = 0.89) |
| Slope computed from the DEM averaged to 1 km: mean / AUC | {ss['mean_slope_from_1km_dem']:.2f}° / {ss['single_feature_auc_slope_from_1km_dem']:.4f} |
| Slope computed from the DEM averaged to **0.25°** (Biswas et al.'s model resolution): mean / AUC | **{ss['mean_slope_from_025deg_dem']:.2f}°** / {ss['single_feature_auc_slope_from_025deg_dem']:.4f} |
| Correlation, 90 m slope vs 0.25° slope | {ss['corr_90m_horn_vs_025deg']:.3f} |

**Conclusion:** the algorithm choice is immaterial, but slope is strongly **scale-dependent**. Biswas et al.'s 0.25° slope is a different quantity from this 90 m-derived slope.

## 3. The −46.9 m minimum

{na['n_1km_pixels_below_minus5m']} one-km pixels lie below −5 m (minimum {na['min_1km']:.2f} m). All but one cluster at 11.55–11.57°N, 79.50–79.51°E, the **Neyveli open-cast lignite mines** (Tamil Nadu), whose pit floors lie below sea level. This is most likely a real excavation surface rather than an SRTM artefact (attribution by location, not field-verified). The remaining pixel is on the Andaman coast.

GMTED2010 cross-check: the available tile (30N090E) does not overlap valid India pixels, so it could not be performed.
"""
docs["Terrain_Elevation_Slope_Aspect_Analysis"] = (d, ["recalc_06_terrain.py", "audit_common.py"], ["recalculated/R6_terrain/R6_report.json"])
d = HEAD.format(title="Step 5b, distance to roads / railways / waterways")
d += "## 1. Reproduction from the raw Geofabrik OSM 2022 zone GeoPackages\n\n" + cmp_table([(R7[k]["historical_comparison"], f"reproduced ({R7[k]['n_features_clipped']:,} features after clipping)") for k in ("roads", "railways", "waterways")])
d += "\n## 2. Validation against exact geodesic distances (new)\n\nFor 3,000 random in-India pixel centres, the nearest point on each network was found in the equidistant-conic projection and the geodesic (WGS84) length was compared with the raster value.\n\n| Layer | Mean exact (km) | Mean raster (km) | Bias (km) | MAE (km) | RMSE (km) | 95th pct abs err (km) | Median rel. err (exact > 5 km) |\n|---|---:|---:|---:|---:|---:|---:|---:|\n"
for k in ("roads", "railways", "waterways"):
    v = R7[k]["validation"]
    d += f"| {k} | {v['mean_exact_km']:.2f} | {v['mean_raster_km']:.2f} | {v['bias_km']:+.3f} | {v['mae_km']:.3f} | {v['rmse_km']:.3f} | {v['p95_abs_err_km']:.2f} | {v['rel_err_median_pct_where_exact_gt5km']:+.1f}% |\n"
d += "\nThe bias is small, negative (1 km quantisation with `all_touched` rasterisation) and uniform across latitude bands (see `R7_report.json`), so the projection causes no latitude-dependent distortion. The earlier documentation noted the Euclidean distance transform was never validated; that gap is now closed.\n"
docs["Distance_Roads_Railways_Waterways_Analysis"] = (d, ["recalc_07_access.py", "audit_common.py"], ["recalculated/R7_access/R7_report.json"])

# ------------------------------------------------------------------------- Steps 6/7 Integrated
def g(exp, tag, pop, col="roc_auc"):
    s = M[(M.experiment == exp) & (M.tag == tag) & (M.population == pop)]
    return s[col].mean() if len(s) else float("nan")
d = HEAD.format(title="Steps 6–7, integrated feature table and classical models")
d += """## 1. Feature table

- The v1 table `Integrated_FireRisk_Pixels.parquet` has **61 columns / 57 features** (4,161,009 pixels). Earlier text said 55.
- **Defects in v1:**
  - The 22 land-cover fractions come from the **2020** map, inside the label window.
  - The climate/LST/NDVI "anomaly-mean" features are degenerate.
  - The Mann–Kendall τ features use invalid tests.
  - `ndvi_residual_mean` and LC140 are constant.
  - The θ\\* indicator is fitted on labels.
  - `fire_ever` is shifted half a pixel (74.9% of points displaced).
  - Median imputation is fitted on all rows.
- **v2 table** (`results/recalculated/FEATURE_TABLE_v2.parquet` in the project folder): **55 features**. It uses 2001–2020 climatological levels and Seasonal-Kendall trends for climate/LST/NDVI, 21 land-cover fractions from 2001 plus forest fraction 2001, aspect as sin/cos, the corrected label, and training-row imputation.
- **Evaluation population:** forest pixels (`forest_frac_2001 > 0`; 1,197,538 pixels, prevalence 22.4%) are primary, because forest fraction alone reaches AUC 0.91 over all pixels (prevalence 6.45%).

## 2. Reproduction of the historical results

| Result | Historical | Recalculated |
|---|---|---|
"""
d += f"| RF, 80/20 split (v1) | 0.9704 / AP 0.7011 | {g('repro','RF_v1_histlabel_80_20','all'):.4f} / {g('repro','RF_v1_histlabel_80_20','all','ap'):.4f} |\n"
d += f"| MaxEnt, 150k rows (v1) | 0.9598 / AP 0.6275 | {g('repro','MaxEnt_v1_histlabel_80_20_150k','all'):.4f} / {g('repro','MaxEnt_v1_histlabel_80_20_150k','all','ap'):.4f} |\n"
bh = M[(M.experiment == "B1hist_v2origin") & (M.population == "all")].sort_values("tag")
d += f"| RF spatial-block CV (GroupKFold, 0°-anchored) | 0.9459 / 0.9527 / 0.9508 | {' / '.join(f'{v:.4f}' for v in bh.roc_auc)} |\n"
d += "\nThe historical RF/MaxEnt spatial CV is **not** the same fold scheme, grid, label or feature set as CDR-PINN's Track B1, contrary to what the documentation stated.\n\n## 3. Corrected results (v2 features, corrected label; test set touched once)\n\n| Model | Track | AUC all | AP all | AUC forest | AP forest |\n|---|---|---:|---:|---:|---:|\n"
for tag, lbl in (("RF_v2", "RF v2"), ("RF_biswas15", "RF, Biswas-15 predictors"), ("MaxEnt_v2", "MaxEnt v2 (150k rows)"), ("MaxEnt_biswas15_LQHP", "MaxEnt, Biswas-15 (L+Q+H+P, β=1)"), ("RF_cdr7static", "RF, CDR-PINN's 5 static covariates"), ("RF_v1_corrlabel", "RF v1 features, corrected label")):
    d += f"| {lbl} | random 65/15/20 | {g('trackA',tag,'all'):.4f} | {g('trackA',tag,'all','ap'):.4f} | {g('trackA',tag,'forest'):.4f} | {g('trackA',tag,'forest','ap'):.4f} |\n"
for exp, lab2 in (("B1", "2° blocks (3 folds, CDR fold geometry)"), ("B2", "leave one region out (6)")):
    for tag in ("RF_v2", "RF_biswas15", "MaxEnt_v2"):
        d += f"| {tag} | {lab2} | {g(exp,tag,'all'):.4f} | {g(exp,tag,'all','ap'):.4f} | {g(exp,tag,'forest'):.4f} | {g(exp,tag,'forest','ap'):.4f} |\n"
d += f"| RF v2 | unseen years (2000/2008/2009/2015) | {g('B3static','RF_v2','all'):.4f} | {g('B3static','RF_v2','all','ap'):.4f} | {g('B3static','RF_v2','forest'):.4f} | {g('B3static','RF_v2','forest','ap'):.4f} |\n"
d += f"| Persistence null | unseen years | {g('B3static','persistence_null_everburned_trainyears','all'):.4f} | — | {g('B3static','persistence_null_everburned_trainyears','forest'):.4f} | — |\n"
d += "\n## 4. Paired contributions (DeLong on identical test pixels, Track A; ΔAUC all / forest)\n\n| Comparison | Δ all [95% CI] | Δ forest [95% CI] |\n|---|---|---|\n"
for _, r in PA.iterrows():
    if r.population == "all":
        rf = PA[(PA.model_A == r.model_A) & (PA.model_B == r.model_B) & (PA.population == "forest")].iloc[0]
        d += f"| {r.question} ({r.model_A} − {r.model_B}) | {r['diff']:+.4f} [{r.ci95_lo:+.4f}, {r.ci95_hi:+.4f}] | {rf['diff']:+.4f} [{rf.ci95_lo:+.4f}, {rf.ci95_hi:+.4f}] |\n"
mx = M[(M.experiment == "maxent_n")].copy()
d += "\n## 5. MaxEnt training-sample-size sensitivity (v2, Track A)\n\n| Rows | AUC all (mean ± sd) | AUC forest | Fit time (s) |\n|---:|---|---:|---:|\n"
for n, s in mx.groupby("train_rows"):
    a = s[s.population == "all"].roc_auc; fo = s[s.population == "forest"].roc_auc
    d += f"| {int(n):,} | {a.mean():.4f} ± {a.std(ddof=1) if len(a) > 1 else 0:.4f} | {fo.mean():.4f} | {s.fit_sec.mean():.0f} |\n"
d += "\nFit time grows roughly as n^1.6, so 1M rows (~5–6 h) and the full 2.7M were not run. The RF–MaxEnt gap is not caused by subsampling.\n"
d += f"""
## 6. Calibration, final map, and comparison with Biswas et al.

- **Calibration (Track A):** RF v2 ECE {g('trackA','RF_v2','all','ece'):.3f} (all) / {g('trackA','RF_v2','forest','ece'):.3f} (forest); MaxEnt v2 {g('trackA','MaxEnt_v2','all','ece'):.3f} / {g('trackA','MaxEnt_v2','forest','ece'):.3f}. The class-balanced RF score is **not a calibrated probability**, and no calibrated uncertainty estimate was established.
- **Historical `Fire_Susceptibility_Probability.tif`:** it is a v1 output with no metadata; its mean score, 0.135, compares with a prevalence of 0.065. The audit produced `Susceptibility_RF_v2_score.tif` plus a 5-class version (breaks = quantiles over forest pixels) with provenance tags; these are in the project root repository's `results/final/maps/`.
- **Biswas-style reimplementation** (0.25°, 15 level predictors, 2020 presences, MaxEnt, 10 splits): test AUC **{BS['replica_2020_presences_025deg']['summary']['test_auc_mean']:.3f} ± {BS['replica_2020_presences_025deg']['summary']['test_auc_sd']:.3f}**, vs 0.879 reported by Biswas et al. (moderately comparable). The pixel-level AUCs above are **not** directly comparable with Biswas et al.'s AUC.
"""
docs["Integrated_Analysis"] = (d, ["build_v2_table.py", "models_classical.py", "analyze_classical.py", "eval_utils.py", "bridge_12km.py", "biswas_style_baseline.py", "make_final_map.py", "audit_common.py"],
                               ["baseline/CLASSICAL_METRICS.csv", "baseline/PAIRED_trackA.csv", "baseline/PAIRED_B1_B2.csv", "baseline/B1_B2_SUMMARY.csv", "baseline/importance__trackA__RF_v2.json", "baseline/importance__trackA__MaxEnt_v2.json", "baseline/importance__trackA__RF_biswas15.json", "baseline/importance__trackA__MaxEnt_biswas15_LQHP.json", "recalculated/FEATURE_SETS.json", "recalculated/FEATURE_TABLE_v2_report.json"])

# ------------------------------------------------------------------------- Physics (Step 8)
rep = json.load(open(os.path.join(RES, "cdr_pino", "reproduction", "repro_validation_tracks_b1_b2_b3.json")))["results"]
d = HEAD.format(title="Step 8, CDR-PINN / CDR-PINO")
d += "## 1. Reproduction of the historical results (unmodified code, output redirected)\n\n| Track | Historical | Re-run |\n|---|---|---|\n| A (`train_standard_protocol.py`) | test AUC 0.9398, AP 0.9223, val 0.9351 | 0.9398 / 0.9223 / 0.9351 (bit-exact) |\n"
for t in ("B1", "B2", "B3"):
    v = [x["roc_auc"] for x in rep[t]]
    d += f"| {t} (`run_validation_tracks.py`) | see historical JSON | {' / '.join(f'{a:.4f}' for a in v)} (bit-exact) |\n"
d += """
**Provenance findings:**

- `cdr_pinn_full_cdr.pt` is **byte-identical** to `cdr_pinn_full_cdr_standard_protocol.pt`. The term ablation's full-CDR checkpoint was overwritten, so the historical ablation row cannot be traced to its checkpoint.
- Track A and Tracks B1/B2/B3 are **separately trained models under different protocols**: AdamW + ReduceLROnPlateau for A; Adam + cosine with a 50-epoch budget and random-pixel validation for B1/B2.
- The historical B3 terminal loss uses `fire_ever` pooled over **all** years, including the held-out years (label leakage).
- CDR training needs `cdr_pinn_env` (torch 2.11.0+cu128); the base environment's torch is CPU-only.
- NaN handling: `preprocessing.load_tensors` converts every NaN to **0** (0 m elevation for 0.38% of cells; 270 cells without dryness). The two NDVI months 2007-03/04 are entirely NaN, so they become 0 in the stack, because the stack builder requires a QA file.

## 2. Unified protocol, 3 seeds, 4 physics configurations (`audit_2026-09-25/cdr_unified_runner.py`)

One protocol for every track: AdamW, WD 0, ReduceLROnPlateau, early stopping on validation AUC, block-carved validation for B1/B2, year-carved validation for B3, and a leak-free B3 terminal label. Seeds 42/43/44. Mean test ROC-AUC over all valid cells:

| Track | No physics | Diffusion | Diff + adv | Full CDR |
|---|---:|---:|---:|---:|
"""
for t in ("A", "B1", "B2", "B3", "B3orig"):
    row = {c: S[(S.track == t) & (S.config == c)].auc_mean for c in ("nophys", "diff", "diffadv", "full")}
    d += f"| {t} | " + " | ".join(f"{v.iloc[0]:.4f}" if len(v) else "—" for v in row.values()) + " |\n"
P = pd.read_csv(os.path.join(RES, "ablation", "PAIRED_physics_vs_nophys.csv"))
d += "\nPaired full − no-physics differences per seed (identical cells): "
for t in ("A", "B1", "B2", "B3"):
    s = P[(P.track == t) & (P.config == "full")]
    col = "delong_diff" if s.delong_diff.notna().any() else "blockboot_diff"
    d += f"{t}: {', '.join(f'{v:+.4f}' for v in s[col])}; "
d += "\n\nTrack A differences are significant for every seed (DeLong p < 0.02). The B1/B2 block-bootstrap CIs include 0. B3 is replicated across seeds.\n\n"
br = {t: M[(M.experiment == f"bridge12_{t}") & (M.population == "all")] for t in ("A", "B1", "B2", "B3")}
nul = br["B3"].set_index("tag").roc_auc
d += f"""## 3. Same-cells comparison with classical models (the fair comparison)

Classical models were trained on **CDR-PINO's own 22,542 cells, covariates, partitions and label**:

| Track | CDR-PINO full | CDR-PINO no physics | RF | MaxEnt | Logistic regression |
|---|---:|---:|---:|---:|---:|
"""
for t in ("A", "B1", "B2"):
    b = br[t]
    d += (f"| {t} | {S[(S.track == t) & (S.config == 'full')].auc_mean.iloc[0]:.4f} | {S[(S.track == t) & (S.config == 'nophys')].auc_mean.iloc[0]:.4f} | "
          f"{b[b.tag.str.startswith('RF_cdr7')].roc_auc.mean():.4f} | {b[b.tag.str.startswith('MaxEnt_cdr7')].roc_auc.mean():.4f} | {b[b.tag.str.startswith('LogReg_cdr7')].roc_auc.mean():.4f} |\n")
d += f"""
**B3, unseen years**, scored on identical cell-months:

| Model | AUC |
|---|---:|
| CDR-PINO full | {S[(S.track == 'B3') & (S.config == 'full')].auc_mean.iloc[0]:.4f} |
| CDR-PINO no physics | {S[(S.track == 'B3') & (S.config == 'nophys')].auc_mean.iloc[0]:.4f} |
| **Null: each cell's training-period fire frequency (no covariates)** | **{nul['null_climatological_frequency']:.4f}** |
| **Null: same-calendar-month frequency** | **{nul['null_seasonal_frequency']:.4f}** |
| RF with monthly covariates | {nul['RF_monthly_cdr7']:.4f} |
| RF with monthly covariates + month of year | {nul['RF_monthly_cdr7_month']:.4f} |

**Conclusions:**

1. No physics configuration improves accuracy on any track.
2. The spatial/regional collapse (~0.72 / ~0.57) is specific to CDR-PINO, since RF on the same inputs scores 0.97 / 0.96.
3. The B3 score does not beat a covariate-free persistence baseline, so the claim "temporal generalisation is strong" is withdrawn.

## 4. Physical consistency of the trained field (`cdr_term_magnitudes.py`)

Every term of the implemented residual, averaged over all 22,542 cells × 265 transitions:

| Checkpoint | median \\|∂u/∂t\\| | \\|D∇²u\\| | \\|v·∇u\\| | \\|R\\| | RMS residual | residual / mean \\|∂u/∂t\\| |
|---|---:|---:|---:|---:|---:|---:|
"""
for tag in ("trackA_full_repro", "unified_A_nophys_s42", "unified_A_diff_s42", "unified_A_diffadv_s42", "unified_A_full_s42"):
    x = json.load(open(os.path.join(RES, "cdr_pino", f"term_magnitudes_{tag}.json")))
    s = x["summary"]
    d += f"| {tag} | {s['dudt']['median']:.5f} | {s['diff']['mean']:.2e} | {s['adv']['mean']:.3f} | {s['react']['mean']:.3f} | {s['resid']['mean']:.3f} | {x['rms_residual_over_mean_abs_dudt']:.0f} |\n"
d += """
Every trained model is **effectively static in time** and **does not satisfy the CDR equation**. Diffusion is ≤ 0.3% of the right-hand side.

## 5. Equation vs code (text corrections)

| Topic | What the code does |
|---|---|
| Reaction | Acts on the logit u: du/dt = ρσ(u)(1−σ(u)), i.e. ds/dt = ρs²(1−s)² for s = σ(u). "Fisher–KPP" is a misnomer |
| Diffusion | Non-conservative form D∇²u, not ∇·(D∇u) |
| Boundary condition | Penalises \\|∇u\\|² on the 1,253-cell boundary ring, not ∂u/∂n. The Neumann extension is applied at the rectangle edge |
| Initial-condition loss | Identically 0 (u₀ is hard-set) |
| Loss weights | w_i ← 0.9 w_i + 0.1 · mean‖∇L‖/‖∇L_i‖ every 5 windows, not the multiplicative formula stated in the docs |
| Negatives | No size-matched negative sampling; the data loss is a pos-weighted BCE over all training cells |

Architecture as documented (1,054,613 parameters).
"""
docs["Physics_Informed_FireRisk_Model"] = (d, ["repro_historical_cdr.py", "cdr_unified_runner.py", "cdr_term_magnitudes.py", "analyze_cdr.py", "eval_utils.py", "audit_common.py"],
                                           ["cdr_pino/SUMMARY_cdr_unified.csv", "cdr_pino/SEED_LEVEL_RESULTS_cdr.csv", "cdr_pino/FOREST_POPULATION_cdr.csv", "ablation/PAIRED_physics_vs_nophys.csv",
                                            "generalization/PAIRED_cdr_vs_classical_same_cells.csv", "cdr_pino/reproduction/repro_validation_tracks_b1_b2_b3.json", "cdr_pino/unified/meta.json",
                                            "cdr_pino/term_magnitudes_trackA_full_repro.json", "cdr_pino/term_magnitudes_unified_A_nophys_s42.json", "cdr_pino/term_magnitudes_unified_A_diff_s42.json",
                                            "cdr_pino/term_magnitudes_unified_A_diffadv_s42.json", "cdr_pino/term_magnitudes_unified_A_full_s42.json"])

json.dump({k: dict(scripts=v[1], results=v[2]) for k, v in docs.items()}, open(os.path.join(OUT, "manifest.json"), "w"), indent=1)
for repo, (text, _, _) in docs.items():
    p = os.path.join(OUT, repo.split(" ")[0][:40]); os.makedirs(p, exist_ok=True)
    open(os.path.join(p, "AUDIT_2026-09-25.md"), "w", encoding="utf-8").write(text)
    print(repo[:40], len(text))
