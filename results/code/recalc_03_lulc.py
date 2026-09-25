"""
Recalculation R3 -- ESA-CCI / C3S land cover (raw 300 m LCCS NetCDF).

* 22-class Level-1 fractions (code//10*10) area-averaged onto the NDVI grid, for 2001
  (v2: pre-label-period) and 2020 (v1: what the model actually used).
* Forest fraction (13-code Sannigrahi set) for 2001 / 2020 / 2022.
* Pixel-wise comparison with the historical parquet columns.
* Leakage mechanism test: forest change 2001->2020 in fire-affected vs unaffected forest
  pixels (post-fire reclassification would show as larger forest loss where fires occurred).
"""
import glob
import os
import re
import time

import netCDF4
import numpy as np
import pandas as pd
from rasterio.transform import from_origin
from rasterio.warp import reproject, Resampling

from audit_common import P, RES, FOREST_CODES, provenance, dump, ndvi_grid, compare

OUT = os.path.join(RES, "recalculated", "R3_lulc")
os.makedirs(OUT, exist_ok=True)
t0 = time.time()
rep = dict(provenance=provenance(__file__))
g = ndvi_grid(); H, W = g["shape"]
files = {int(re.search(r"P1Y-(\d{4})", os.path.basename(f)).group(1)): f for f in glob.glob(os.path.join(P["lulc_dir"], "*.nc"))}
CLASSES = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 220]

pq = pd.read_parquet(P["parquet"])
rr = np.floor((pq.lat.values - g["transform"].f) / g["transform"].e).astype(int)
cc = np.floor((pq.lon.values - g["transform"].c) / g["transform"].a).astype(int)


def load(year):
    with netCDF4.Dataset(files[year]) as ds:
        lc = np.asarray(ds["lccs_class"][0]).astype(np.int32)
        lat = np.asarray(ds["lat"][:]); lon = np.asarray(ds["lon"][:])
        ver = os.path.basename(files[year])
    if lat[0] < lat[-1]:
        lc, lat = lc[::-1], lat[::-1]
    rl, rt = float(lon[1] - lon[0]), float(lat[0] - lat[1])
    tr = from_origin(float(lon[0] - rl / 2), float(lat[0] + rt / 2), rl, rt)
    return lc, tr, ver


def to_grid(mask, tr):
    dst = np.full((H, W), np.nan, np.float32)
    reproject(mask.astype(np.float32), dst, src_transform=tr, src_crs="EPSG:4326", dst_transform=g["transform"],
              dst_crs=g["crs"], dst_nodata=np.nan, resampling=Resampling.average)
    return dst


rep["versions"] = {}
forest = {}
for y in (2001, 2020, 2022):
    lc, tr, ver = load(y)
    rep["versions"][y] = ver
    forest[y] = to_grid(np.isin(lc, FOREST_CODES), tr)[rr, cc]
    if y in (2001, 2020):
        base = np.where(lc == 0, 0, (lc // 10) * 10)
        fr = {f"lc{y}_{k}": to_grid(base == k, tr)[rr, cc] for k in CLASSES}
        pd.DataFrame(fr).to_parquet(os.path.join(OUT, f"lc22_fractions_{y}_pixels.parquet"), index=False)
        if y == 2020:
            cmpc = []
            for k in CLASSES:
                col = [c for c in pq.columns if c.startswith(f"landcover_frac_LC22_{k}_")][0]
                cmpc.append(compare(fr[f"lc2020_{k}"], pq[col].values, name=col))
            rep["lc2020_vs_parquet"] = cmpc
        if y == 2001:
            rep["lc2001_vs_lc2020_class_mean_abs_change"] = {}
            lc20 = pd.read_parquet(os.path.join(OUT, "lc22_fractions_2020_pixels.parquet")) if os.path.exists(os.path.join(OUT, "lc22_fractions_2020_pixels.parquet")) else None
    print(y, "done", round(time.time() - t0), "s", flush=True)
rep["forest2001_vs_parquet_baseline"] = compare(forest[2001], pq.forest_frac_baseline.values, name="forest_frac 2001 vs forest_frac_baseline")

# leakage mechanism: did forest decline more where fires occurred?
lc01 = pd.read_parquet(os.path.join(OUT, "lc22_fractions_2001_pixels.parquet"))
lc20 = pd.read_parquet(os.path.join(OUT, "lc22_fractions_2020_pixels.parquet"))
for k in CLASSES:
    rep["lc2001_vs_lc2020_class_mean_abs_change"][k] = float(np.nanmean(np.abs(lc20[f"lc2020_{k}"] - lc01[f"lc2001_{k}"])))
fire = pq.fire_ever.values > 0
f01 = forest[2001]; f20 = forest[2020]
had_forest = f01 > 0
d = f20 - f01
rep["forest_change_2001_2020"] = dict(
    mean_change_fire_pixels=float(np.nanmean(d[had_forest & fire])),
    mean_change_nonfire_forest_pixels=float(np.nanmean(d[had_forest & ~fire])),
    frac_pixels_losing_forest_fire=float(np.nanmean(d[had_forest & fire] < -1e-6)),
    frac_pixels_losing_forest_nonfire=float(np.nanmean(d[had_forest & ~fire] < -1e-6)),
    frac_pixels_gaining_forest_fire=float(np.nanmean(d[had_forest & fire] > 1e-6)),
    frac_pixels_gaining_forest_nonfire=float(np.nanmean(d[had_forest & ~fire] > 1e-6)),
    n_fire_forest=int((had_forest & fire).sum()), n_nonfire_forest=int((had_forest & ~fire).sum()),
    corr_forest2001_forest2020=float(np.corrcoef(np.nan_to_num(f01), np.nan_to_num(f20))[0, 1]),
    note="label = historical parquet fire_ever (half-pixel-shifted); see R1")
pd.DataFrame({"forest_frac_2001": f01, "forest_frac_2020": f20, "forest_frac_2022": forest[2022]}).to_parquet(
    os.path.join(OUT, "forest_frac_pixels.parquet"), index=False)
rep["runtime_sec"] = time.time() - t0
dump(rep, os.path.join(OUT, "R3_report.json"))
print(rep["forest2001_vs_parquet_baseline"])
print(rep["forest_change_2001_2020"])
print([(c["name"][-30:], round(c.get("pearson_r", np.nan), 6), c.get("max_abs_diff")) for c in rep["lc2020_vs_parquet"]])
