"""FINAL_FEATURE_DICTIONARY.csv: every v2 feature (primary) plus the v1 historical features."""
import json
import os

import numpy as np
import pandas as pd

RES = r"D:\FOREST FIRE MAPPING(INDIA)\results"
S = json.load(open(os.path.join(RES, "recalculated", "FEATURE_SETS.json")))
rep = json.load(open(os.path.join(RES, "recalculated", "FEATURE_TABLE_v2_report.json")))
LC = {10: "cropland rainfed", 20: "cropland irrigated", 30: "mosaic cropland", 40: "mosaic natural vegetation",
      50: "tree broadleaved evergreen", 60: "tree broadleaved deciduous", 70: "tree needleleaved evergreen",
      80: "tree needleleaved deciduous", 90: "tree mixed", 100: "mosaic tree and shrub", 110: "mosaic herbaceous",
      120: "shrubland", 130: "grassland", 150: "sparse vegetation", 160: "tree flooded fresh/brackish",
      170: "tree flooded saline", 180: "shrub/herbaceous flooded", 190: "urban", 200: "bare areas", 210: "water", 220: "snow and ice"}
FL = {"tair": ("Air temperature", "Tair_f_tavg", "K", "Air temperature", "reproduced (same source)"),
      "qair": ("Specific humidity", "Qair_f_tavg", "kg/kg", "Specific humidity", "reproduced (same source)"),
      "rh": ("Relative humidity (derived)", "Qair, Tair, Psurf via Magnus", "%", "none", "new"),
      "wind": ("Near-surface wind speed", "Wind_f_tavg", "m/s", "Near-surface wind speed", "reproduced (same source)"),
      "precip": ("Precipitation", "Rainf_f_tavg x 86400 x days", "mm/month", "Precipitation (Biswas: GPM IMERG)", "reproduced (different source)"),
      "lwnet": ("Net longwave radiation", "Lwnet_tavg", "W/m2", "Net longwave radiation flux (Biswas: GLDAS)", "reproduced (different source)"),
      "soilm": ("Soil moisture 0-10 cm", "SoilMoi00_10cm x 0.1 m x 1000", "kg/m2", "Soil moisture (Biswas: GLDAS)", "reproduced (different source)")}
rows = []


def add(f, name, eq, src, prod, ores, tres, unit, agg, qa, lk, bis, status):
    rows.append(dict(ID=len(rows) + 1, feature=f, name=name, equation=eq, source=src, product=prod, original_resolution=ores,
                     final_resolution="1/120 deg (~0.93 km)", temporal_resolution=tres, units=unit, aggregation=agg, QA=qa,
                     normalization="none; median imputation fitted on training rows",
                     nan_pct_all_pixels=round(rep["v2_nan_pct"].get(f, np.nan), 4), leakage_risk=lk, biswas_equivalent=bis, status=status))


QA_NDVI = "pixel_reliability in {0,1}; VI_Quality MODLAND bits for 2007-03/04"
add("v2_ndvi_mean", "NDVI mean", "mean_t NDVI(t)", "NASA LP DAAC", "MOD13A3.061", "1 km", "monthly -> static (266 months)", "-", "temporal mean", QA_NDVI, "none", "NDVI (MOD13C2)", "reproduced (different product)")
add("v2_ndvi_clim_june", "NDVI June climatology", "mean over June 2001-2020", "NASA LP DAAC", "MOD13A3.061", "1 km", "climatology", "-", "calendar-month mean", QA_NDVI, "none", "-", "new")
add("v2_ndvi_sk_tau", "NDVI Seasonal Kendall tau", "S / sum_m C(n_m,2) (Hirsch et al. 1982)", "NASA LP DAAC", "MOD13A3.061", "1 km", "monthly series", "-", "per pixel", QA_NDVI, "none", "-", "new")
add("v2_ndvi_sen_slope", "NDVI seasonal Sen slope", "median of within-month pairwise slopes", "NASA LP DAAC", "MOD13A3.061", "1 km", "monthly series", "NDVI/yr", "per pixel", QA_NDVI, "none", "-", "new")
add("v2_ndvi_cvsi", "Cumulative vegetation stress index", "mean_t sum_{l=1..8} max(-delta_{t-l}, 0)", "NASA LP DAAC", "MOD13A3.061", "1 km", "monthly", "NDVI units", "temporal mean", QA_NDVI,
    "low: k*=8 selected by MI using training labels only (same k as all-label selection)", "-", "new")
add("v2_ndvi_lisa", "LISA cluster of NDVI mean", "Local Moran (queen, row-standardised, 199 permutations, p<0.05) on 8x8 block means, India cells only",
    "NASA LP DAAC", "MOD13A3.061", "8 km blocks", "static", "category 0-4", "nearest upsampling", QA_NDVI, "none", "-", "new")
for v, (nm, var, u, bis, st) in FL.items():
    add(f"v2_{v}_level", f"{nm} (climatological level)", f"mean over months of the 2001-2020 calendar-month means of {var}", "NASA GES DISC",
        "FLDAS_NOAH01_C_GL_M.001", "0.1 deg", "monthly -> climatology", u, "bilinear 0.1 deg -> 1 km", "fill <= -9998 -> NaN",
        "none (covariate climatology, not label)", bis, st)
    add(f"v2_{v}_sk_tau", f"{nm} Seasonal Kendall tau", "Hirsch et al. 1982 on monthly series", "NASA GES DISC", "FLDAS_NOAH01_C_GL_M.001",
        "0.1 deg", "monthly series", "-", "bilinear", "fill -> NaN", "none", "-", "new")
for b, bis, st in (("day", "LST daytime (MOD11C3)", "reproduced (different product)"), ("night", "LST night-time (MOD11C3)", "reproduced (different product)"), ("dtr", "-", "new")):
    add(f"v2_lst_{b}_level", f"LST {b} climatological level", "2001-2020 mean of monthly means of 8-day composites", "NASA LP DAAC", "MOD11A2.061",
        "1 km", "8-day -> monthly -> climatology", "deg C", "area mean (grids aligned)", "QC bits 0-1 <= 1; DN > 0; DN x 0.02 - 273.15", "none", bis, st)
    add(f"v2_lst_{b}_sk_tau", f"LST {b} Seasonal Kendall tau", "Hirsch et al. 1982", "NASA LP DAAC", "MOD11A2.061", "1 km", "monthly series", "-",
        "area mean", "as above", "none", "-", "new")
add("v2_elevation", "Elevation", "area mean of 90 m DEM", "NASA", "SRTMGL3", "90 m", "static", "m", "area mean", "outside India masked", "none",
    "Elevation (DEM not reported by Biswas)", "reproduced (source unspecified by Biswas)")
add("v2_slope", "Slope (Horn)", "atan(sqrt(zx^2 + zy^2)), Horn 3x3, latitude-dependent dx", "NASA", "SRTMGL3", "90 m", "static", "deg",
    "area mean of 90 m slope", "-", "none", "Slope", "reproduced (scale differs: slope of a 0.25-deg DEM is ~20x smaller)")
add("v2_aspect_sin", "Aspect sine", "sin(circular-mean Horn aspect)", "NASA", "SRTMGL3", "90 m", "static", "-", "circular mean", "flat -> NaN", "none", "Aspect", "modified (circular encoding)")
add("v2_aspect_cos", "Aspect cosine", "cos(circular-mean Horn aspect)", "NASA", "SRTMGL3", "90 m", "static", "-", "circular mean", "flat -> NaN", "none", "Aspect", "modified (circular encoding)")
for k, bis in (("roads", "Distance to roads"), ("railways", "Distance to railways"), ("waterways", "Distance to waterways")):
    add(f"v2_dist_{k}", f"Distance to {k}", "Euclidean distance transform on 1 km equidistant-conic raster (all_touched), bilinear to grid",
        "Geofabrik", "OpenStreetMap 2022", "vector", "static (2022)", "km", "EDT", "class filter",
        "low (2022 snapshot post-dates part of label period)", bis, "reproduced")
for c, nm in LC.items():
    add(f"v2_lc2001_{c}", f"Land-cover fraction {c} {nm} (2001)", "area fraction of Level-1 class (code//10*10)", "ESA CCI",
        "LCCS v2.0.7cds 2001", "300 m", "static (2001)", "fraction", "area mean", "-", "none (map predates label period)",
        "- (Biswas used LULC only as fire filter)", "new")
add("v2_forest_frac_2001", "Forest fraction 2001", "area fraction of the 13 forest codes", "ESA CCI", "LCCS v2.0.7cds 2001", "300 m", "static", "fraction",
    "area mean", "-", "structural: label is FOREST fire, non-forest pixels almost never positive (not leakage, but dominates all-pixel AUC)", "-", "new")
v2cols = [r["feature"] for r in rows]
assert sorted(v2cols) == sorted(S["v2_57"]), set(v2cols) ^ set(S["v2_57"])
D = pd.DataFrame(rows); D["feature_set"] = "v2 (primary)"
v1 = pd.DataFrame(dict(feature=S["v1_57"], feature_set="v1 (historical, retained for comparison)"))
lk = {"v1_ndvi_below_threshold": "label-derived threshold (Delta AUC 0.0000 when removed)",
      "v1_ndvi_cvsi_k8": "lag chosen with labels (k unchanged with training-only labels)",
      "v1_ndvi_residual_mean": "degenerate (identically ~0)"}


def v1risk(f):
    if f in lk:
        return lk[f]
    if "landcover_frac" in f:
        return "in-window 2020 map (measured effect small)"
    if f.endswith("_anomaly") or f.endswith("_anomaly_mean"):
        return "degenerate: out-of-baseline 26-month residue"
    if "mk_tau" in f:
        return "invalid test (MK on seasonal/autocorrelated series)"
    return ""


v1["leakage_or_validity_issue"] = v1.feature.map(v1risk)
pd.concat([D, v1], ignore_index=True).to_csv(os.path.join(RES, "final", "FINAL_FEATURE_DICTIONARY.csv"), index=False)
print(len(D), "v2 +", len(v1), "v1")
