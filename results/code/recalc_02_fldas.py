"""
Recalculation R2 -- FLDAS_NOAH01_C_GL_M.001 climatic variables, from the 266 RAW NetCDF files.

1. Monthly fields (units verified against the file attributes):
   Tair_f_tavg K; Qair_f_tavg kg/kg; Psurf_f_tavg Pa; Wind_f_tavg m/s;
   Rainf_f_tavg kg m-2 s-1 -> mm/month (x 86400 x days-in-month);
   Lwnet_tavg W m-2; SoilMoi00_10cm_tavg m3/m3 -> kg/m2 (x 0.1 m x 1000);
   RH (%) derived: e = q p /(0.622 + 0.378 q), e_s = 6.112 exp(17.67 Tc/(Tc+243.5)).
2. Climatology 2001-2020 per calendar month; anomalies.
3. Historical feature reproduction: anomaly_mean = nanmean_t(x - clim) over all 266 months,
   and MK tau on the raw monthly series; + numerical proof of the identity
   anomaly_mean = sum(anomalies outside 2001-2020) / n_valid.
4. v2 features: 2001-2020 climatological annual-mean LEVELS (Biswas-comparable), Seasonal
   Kendall tau + p + BH-FDR q, seasonal Sen slope.
5. Bilinear regrid to the NDVI grid (historical convention) and pixel-wise comparison with
   the historical parquet columns.
"""
import glob
import os
import re
import time

import numpy as np
import pandas as pd
import rasterio
import xarray as xr
from rasterio.features import rasterize
from rasterio.transform import from_origin
from rasterio.warp import reproject, Resampling

from audit_common import P, RES, provenance, dump, ndvi_grid, india_geom, save_tif, compare
from trend_stats import mk_raw, seasonal_kendall, seasonal_sen, bh_fdr

OUT = os.path.join(RES, "recalculated", "R2_fldas")
os.makedirs(OUT, exist_ok=True)
t0 = time.time()
rep = dict(provenance=provenance(__file__))

files = {}
for f in glob.glob(os.path.join(P["fldas_raw"], "FLDAS_NOAH01_C_GL_M.A??????.001.nc")):
    m = re.search(r"\.A(\d{4})(\d{2})\.001\.nc$", os.path.basename(f))
    files[(int(m.group(1)), int(m.group(2)))] = f
months = pd.period_range("2000-11", "2022-12", freq="M")
keys = [(p.year, p.month) for p in months]
rep["n_months_expected"] = len(keys)
rep["missing_months"] = [k for k in keys if k not in files]

# units from the first file
with xr.open_dataset(files[keys[0]]) as ds:
    rep["units"] = {v: ds[v].attrs.get("units") for v in
                    ["Tair_f_tavg", "Qair_f_tavg", "Psurf_f_tavg", "Wind_f_tavg", "Rainf_f_tavg", "Lwnet_tavg", "SoilMoi00_10cm_tavg"]}
    X, Y = ds["X"].values, ds["Y"].values
xs = np.where((X >= 67.0) & (X <= 98.5))[0]
ys = np.where((Y >= 5.0) & (Y <= 38.5))[0]
lon = X[xs]; lat = Y[ys][::-1]  # north-up
res = float(lon[1] - lon[0])
tr = from_origin(lon[0] - res / 2, lat[0] + res / 2, res, res)
Hf, Wf = len(lat), len(lon)
imask = rasterize([(india_geom("state"), 1)], out_shape=(Hf, Wf), transform=tr, fill=0, dtype=np.uint8).astype(bool)
rep["fldas_grid"] = dict(shape=[Hf, Wf], res_deg=res, india_pixels=int(imask.sum()))

VARS = ["tair", "qair", "rh", "wind", "precip", "lwnet", "soilm"]
T = len(keys)
stack = {v: np.full((T, Hf, Wf), np.nan, np.float32) for v in VARS}
for i, (y, mo) in enumerate(keys):
    with xr.open_dataset(files[(y, mo)]) as ds:
        def g(v):
            a = ds[v].values[0][np.ix_(ys, xs)][::-1].astype(np.float32)
            return np.where(a <= -9998, np.nan, a)
        tk, q, ps = g("Tair_f_tavg"), g("Qair_f_tavg"), g("Psurf_f_tavg")
        tc = tk - 273.15
        es = 6.112 * np.exp(17.67 * tc / (tc + 243.5))
        e = q * (ps / 100.0) / (0.622 + 0.378 * q)
        fr = dict(tair=tk, qair=q, rh=np.clip(100 * e / es, 0, 100), wind=g("Wind_f_tavg"),
                  precip=g("Rainf_f_tavg") * 86400.0 * pd.Period(f"{y}-{mo}").days_in_month,
                  lwnet=g("Lwnet_tavg"), soilm=g("SoilMoi00_10cm_tavg") * 0.1 * 1000.0)
    for v in VARS:
        stack[v][i] = np.where(imask, fr[v], np.nan)
print(f"read {T} months in {time.time()-t0:.0f}s", flush=True)

yrs = np.array([k[0] for k in keys]); mos = np.array([k[1] for k in keys])
base = (yrs >= 2001) & (yrs <= 2020)
out_native = {}
ident = {}
for v in VARS:
    x = stack[v].reshape(T, -1)
    clim = np.full((12, x.shape[1]), np.nan, np.float32)
    for m in range(1, 13):
        clim[m - 1] = np.nanmean(x[base & (mos == m)], axis=0)
    anom = x - clim[mos - 1]
    anom_mean = np.nanmean(anom, axis=0)
    # identity: baseline anomalies sum to 0 per calendar month -> only out-of-baseline months remain
    nvalid = np.sum(np.isfinite(anom), axis=0)
    outside = np.nansum(anom[~base], axis=0) / np.maximum(nvalid, 1)
    inside_sum = np.nansum(anom[base], axis=0)
    ok = np.isfinite(anom_mean)
    ident[v] = dict(max_abs_identity_error=float(np.nanmax(np.abs(anom_mean[ok] - outside[ok]))),
                    max_abs_baseline_anomaly_sum=float(np.nanmax(np.abs(inside_sum[ok]))),
                    n_out_of_baseline_months=int((~base).sum()),
                    std_anomaly_mean=float(np.nanstd(anom_mean)),
                    std_climatological_level=float(np.nanstd(np.nanmean(clim, axis=0))),
                    ratio_level_std_to_anommean_std=float(np.nanstd(np.nanmean(clim, axis=0)) / max(np.nanstd(anom_mean), 1e-30)))
    _, _, tau_raw, p_raw = mk_raw(x)
    S, tau_sk, z, p_sk, npairs = seasonal_kendall(x, mos)
    q_sk = bh_fdr(np.where(imask.ravel(), p_sk, np.nan))
    sen = seasonal_sen(x, mos, yrs)
    q_raw = bh_fdr(np.where(imask.ravel(), p_raw, np.nan))
    out_native[v] = dict(level_clim_annual=np.nanmean(clim, axis=0), anom_mean_hist=anom_mean,
                         mk_tau_raw_hist=tau_raw, sk_tau=tau_sk, sk_p=p_sk, sk_q=q_sk, sen_slope_per_yr=sen)
    sel = imask.ravel()
    ident[v].update(
        mk_raw_sig_p05=int(np.nansum(p_raw[sel] < 0.05)), mk_raw_sig_fdr=int(np.nansum(q_raw[sel] < 0.05)),
        sk_sig_p05=int(np.nansum(p_sk[sel] < 0.05)), sk_sig_fdr=int(np.nansum(q_sk[sel] < 0.05)),
        sk_sig_fdr_pos=int(np.nansum((q_sk[sel] < 0.05) & (tau_sk[sel] > 0))),
        sk_sig_fdr_neg=int(np.nansum((q_sk[sel] < 0.05) & (tau_sk[sel] < 0))),
        mk_raw_tau_mean=float(np.nanmean(tau_raw[sel])), sk_tau_mean=float(np.nanmean(tau_sk[sel])),
        corr_mk_raw_vs_sk=float(pd.Series(tau_raw[sel]).corr(pd.Series(tau_sk[sel]))),
        sen_median_per_yr=float(np.nanmedian(sen[sel])),
        national_mean_level=float(np.nanmean(np.nanmean(clim, axis=0)[sel])))
    print(v, ident[v], flush=True)
rep["per_variable"] = ident

# national monthly series (reproduces FLDAS_monthly_statistics)
nat = pd.DataFrame({"year": yrs, "month": mos, **{f"{v}_national_mean": np.nanmean(stack[v].reshape(T, -1), axis=1) for v in VARS}})
nat.to_csv(os.path.join(OUT, "fldas_national_monthly_recalc.csv"), index=False)

# ---------------------------------------------------------------- regrid to NDVI grid + compare
g = ndvi_grid()
H, W = g["shape"]
pq = pd.read_parquet(P["parquet"])
rr = np.floor((pq.lat.values - g["transform"].f) / g["transform"].e).astype(int)
cc = np.floor((pq.lon.values - g["transform"].c) / g["transform"].a).astype(int)
hist_cols = {"tair": "fldas_airtemp", "qair": "fldas_qair", "rh": "fldas_rh", "wind": "fldas_wind",
             "precip": "fldas_precip", "lwnet": "fldas_netlwradiation", "soilm": "fldas_soilmoisture"}
cmp = []
v2 = {}
for v in VARS:
    for fname, arr in out_native[v].items():
        src = arr.reshape(Hf, Wf).astype(np.float32)
        dst = np.full((H, W), np.nan, np.float32)
        reproject(src, dst, src_transform=tr, src_crs="EPSG:4326", dst_transform=g["transform"], dst_crs=g["crs"],
                  src_nodata=np.nan, dst_nodata=np.nan, resampling=Resampling.bilinear)
        if fname in ("level_clim_annual", "sk_tau", "sen_slope_per_yr", "sk_q"):
            v2[f"{v}_{fname}"] = dst[rr, cc]
            save_tif(dst, os.path.join(OUT, "ndvi_grid", f"{v}_{fname}.tif"))
        if fname == "anom_mean_hist":
            cmp.append(compare(dst[rr, cc], pq[f"{hist_cols[v]}_anomaly"].values, name=f"{v} anomaly_mean vs parquet"))
        if fname == "mk_tau_raw_hist":
            cmp.append(compare(dst[rr, cc], pq[f"{hist_cols[v]}_mk_tau_monthly"].values, name=f"{v} mk_tau_monthly vs parquet"))
rep["parquet_comparison"] = cmp
pd.DataFrame(v2).assign(lon=pq.lon.values, lat=pq.lat.values).to_parquet(os.path.join(OUT, "fldas_v2_features_pixels.parquet"), index=False)
rep["runtime_sec"] = time.time() - t0
dump(rep, os.path.join(OUT, "R2_report.json"))
for c in cmp:
    print(c["name"], "r=", round(c.get("pearson_r", np.nan), 6), "maxdiff=", c.get("max_abs_diff"), "n=", c["n_compared"])
