"""
Recalculation R5 -- MOD11A2.061 LST day/night and DTR, from the RAW 8-day GeoTIFFs.

Historical rules reproduced (Step 3): composites dated 2000-11-01..2022-12-15 having all
four layers; LST = DN*0.02 - 273.15 (DN>0); QC bits 0-1 <= 1 kept; 8-day composites
averaged into the calendar month of their START date; climatology 2001-2020; DTR_month =
Day_month - Night_month; features computed on the native LST grid, then area-averaged
(Resampling.average) onto the NDVI grid.

Audit additions: composite inventory; MK-on-raw-monthly (historical) vs Seasonal Kendall
(v2) for Day, Night and DTR (the DTR trend never reached the historical stack); v2 level
features (2001-2020 climatological annual means); resolution sensitivity toward Biswas et
al.'s MOD11C3 (0.05 deg CMG): block-average the monthly fields to 0.05 deg and report the
spatial variance retained -- NOT a substitute for MOD11C3 itself, which is not on disk.
"""
import glob
import os
import re
import sys
import time
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from audit_common import P, RES, provenance, dump, ndvi_grid, india_geom, compare, save_tif  # noqa: E402
from trend_stats import mk_raw, seasonal_kendall, seasonal_sen, bh_fdr  # noqa: E402

OUT = os.path.join(RES, "recalculated", "R5_lst")
TMP = os.path.join(OUT, "tmp")
os.makedirs(TMP, exist_ok=True)


def _work(args):
    s, e, name = args
    x = np.load(os.path.join(TMP, f"monthly_{name}.npy"), mmap_mode="r")[:, s:e].astype(np.float64)
    months = np.load(os.path.join(TMP, "months.npy")); years = np.load(os.path.join(TMP, "years.npy"))
    _, _, tau_raw, p_raw = mk_raw(x)
    _, tau_sk, _, p_sk, _ = seasonal_kendall(x, months)
    sen = seasonal_sen(x, months, years)
    return name, s, e, tau_raw, p_raw, tau_sk, p_sk, sen


def main():
    import pandas as pd
    import rasterio
    from rasterio.features import rasterize
    from rasterio.warp import reproject, Resampling
    t0 = time.time()
    rep = dict(provenance=provenance(__file__))
    bands = {}
    for f in glob.glob(os.path.join(P["lst_raw"], "MOD11A2.061_*_doy*.tif")) + glob.glob(os.path.join(P["lst_raw"], "MOD11A2.061_*T000000_aid0001.tif")):
        m = re.search(r"MOD11A2\.061_(LST_Day_1km|LST_Night_1km|QC_Day|QC_Night)_(\d{8})T", os.path.basename(f))
        if m:
            bands.setdefault(m.group(1), {})[m.group(2)] = f
    dates_all = sorted(set().union(*[set(v) for v in bands.values()]))
    complete = [d for d in dates_all if all(d in bands[b] for b in ("LST_Day_1km", "LST_Night_1km", "QC_Day", "QC_Night"))]
    study = [d for d in complete if "20001101" <= d <= "20221215"]
    rep["inventory"] = dict(n_dates_any_layer=len(dates_all), n_complete=len(complete), n_used=len(study),
                            incomplete=[d for d in dates_all if d not in complete],
                            first_used=study[0], last_used=study[-1])
    with rasterio.open(bands["LST_Day_1km"][study[0]]) as s:
        tr0, crs0, (Hn, Wn) = s.transform, s.crs, s.shape
    rep["native_grid"] = dict(shape=[Hn, Wn], a=tr0.a, e=tr0.e, c=tr0.c, f=tr0.f)
    g = ndvi_grid()
    off_c = (g["transform"].c - tr0.c) / tr0.a; off_r = (g["transform"].f - tr0.f) / tr0.e
    rep["offset_ndvi_vs_lst_in_pixels"] = dict(col=off_c, row=off_r, same_resolution=bool(abs(tr0.a - g["transform"].a) < 1e-12))
    imask = rasterize([(india_geom("state"), 1)], out_shape=(Hn, Wn), transform=tr0, fill=0, dtype=np.uint8).astype(bool)
    idx = np.flatnonzero(imask.ravel()); N = idx.size
    keys = [(p.year, p.month) for p in pd.period_range("2000-11", "2022-12", freq="M")]
    kmap = {k: i for i, k in enumerate(keys)}; T = len(keys)
    sums = {b: np.zeros((T, N), np.float32) for b in ("day", "night")}
    cnts = {b: np.zeros((T, N), np.uint8) for b in ("day", "night")}
    qc_hist = {"day": np.zeros(4, np.int64), "night": np.zeros(4, np.int64)}
    per_comp_valid = []
    for d in study:
        ti = kmap[(int(d[:4]), int(d[4:6]))]
        rec = {"date": d}
        for b, lb, qb in (("day", "LST_Day_1km", "QC_Day"), ("night", "LST_Night_1km", "QC_Night")):
            with rasterio.open(bands[lb][d]) as s:
                raw = s.read(1).ravel()[idx]
            with rasterio.open(bands[qb][d]) as s:
                qc = s.read(1).ravel()[idx]
            q2 = qc & 0x03
            for v in range(4):
                qc_hist[b][v] += int((q2 == v).sum())
            val = np.where((raw > 0) & (q2 <= 1), raw.astype(np.float32) * 0.02 - 273.15, np.nan)
            ok = np.isfinite(val)
            sums[b][ti] += np.where(ok, val, 0); cnts[b][ti] += ok
            rec[f"{b}_valid_frac"] = float(ok.mean())
        per_comp_valid.append(rec)
    pd.DataFrame(per_comp_valid).to_csv(os.path.join(OUT, "composite_valid_fraction.csv"), index=False)
    rep["qc_mandatory_bits_counts_0_1_2_3"] = {b: v.tolist() for b, v in qc_hist.items()}
    print("read composites", round(time.time() - t0), "s", flush=True)
    years = np.array([k[0] for k in keys]); months = np.array([k[1] for k in keys])
    np.save(os.path.join(TMP, "years.npy"), years); np.save(os.path.join(TMP, "months.npy"), months)
    mon = {b: np.where(cnts[b] > 0, sums[b] / np.maximum(cnts[b], 1), np.nan).astype(np.float32) for b in sums}
    del sums
    mon["dtr"] = mon["day"] - mon["night"]
    base = (years >= 2001) & (years <= 2020)
    feats = {}
    for b in ("day", "night", "dtr"):
        np.save(os.path.join(TMP, f"monthly_{b}.npy"), mon[b])
        clim = np.full((12, N), np.nan, np.float32)
        for m in range(1, 13):
            clim[m - 1] = np.nanmean(mon[b][base & (months == m)], axis=0)
        # historical DTR climatology = clim_day - clim_night (differs from clim of DTR when counts differ)
        feats[f"{b}_level_clim_annual"] = np.nanmean(clim, axis=0)
        feats[f"{b}_anom_mean_hist"] = np.nanmean(mon[b] - clim[months - 1], axis=0)
        feats[f"{b}_mean_allmonths"] = np.nanmean(mon[b], axis=0)
        rep[f"{b}_missing_month_frac"] = float(np.isnan(mon[b]).mean())
    # historical DTR anomaly used clim_day - clim_night
    cd = np.stack([np.nanmean(mon["day"][base & (months == m)], 0) for m in range(1, 13)])
    cn = np.stack([np.nanmean(mon["night"][base & (months == m)], 0) for m in range(1, 13)])
    feats["dtr_anom_mean_hist"] = np.nanmean(mon["dtr"] - (cd - cn)[months - 1], axis=0)
    del cd, cn
    # MOD11C3-resolution sensitivity: fraction of spatial variance of the climatological level retained at 0.05 deg
    for b in ("day", "night"):
        full = np.full(Hn * Wn, np.nan, np.float32); full[idx] = feats[f"{b}_level_clim_annual"]; full = full.reshape(Hn, Wn)
        hb, wb = Hn // 6, Wn // 6
        blk = np.nanmean(full[:hb * 6, :wb * 6].reshape(hb, 6, wb, 6), axis=(1, 3))
        up = np.repeat(np.repeat(blk, 6, 0), 6, 1)
        sub = full[:hb * 6, :wb * 6]; ok = np.isfinite(sub) & np.isfinite(up)
        rep[f"{b}_variance_retained_at_0.05deg"] = float(np.var(up[ok]) / np.var(sub[ok]))
        rep[f"{b}_rmse_1km_vs_0.05deg_blockmean_C"] = float(np.sqrt(np.mean((sub[ok] - up[ok]) ** 2)))
        # 0.05 deg block version on the native grid, for the model sensitivity run
        feats[f"{b}_level_clim_annual_005deg"] = up.ravel()[np.clip(idx, 0, hb * 6 * wb * 6 - 1)] if False else None
        up_full = np.full((Hn, Wn), np.nan, np.float32); up_full[:hb * 6, :wb * 6] = up
        feats[f"{b}_level_clim_annual_005deg"] = up_full.ravel()[idx]
    del mon
    print("features", round(time.time() - t0), "s", flush=True)
    jobs = [(s, min(s + 60000, N), b) for b in ("day", "night", "dtr") for s in range(0, N, 60000)]
    res = {b: {k: np.full(N, np.nan) for k in ("tau_raw", "p_raw", "tau_sk", "p_sk", "sen")} for b in ("day", "night", "dtr")}
    with Pool(22) as pool:
        for b, s, e, *vals in pool.imap_unordered(_work, jobs):
            for k, v in zip(("tau_raw", "p_raw", "tau_sk", "p_sk", "sen"), vals):
                res[b][k][s:e] = v
    for b in ("day", "night", "dtr"):
        q_raw = bh_fdr(res[b]["p_raw"]); q_sk = bh_fdr(res[b]["p_sk"])
        feats[f"{b}_mk_tau_raw_hist"] = res[b]["tau_raw"]; feats[f"{b}_sk_tau"] = res[b]["tau_sk"]
        feats[f"{b}_sk_q"] = q_sk; feats[f"{b}_sen_per_yr"] = res[b]["sen"]
        rep[f"trend_{b}"] = dict(
            mk_raw_tau_mean=float(np.nanmean(res[b]["tau_raw"])), mk_raw_sig_p05=int(np.nansum(res[b]["p_raw"] < 0.05)),
            mk_raw_sig_fdr=int(np.nansum(q_raw < 0.05)), sk_tau_mean=float(np.nanmean(res[b]["tau_sk"])),
            sk_sig_p05=int(np.nansum(res[b]["p_sk"] < 0.05)), sk_sig_fdr=int(np.nansum(q_sk < 0.05)),
            sk_sig_fdr_pos=int(np.nansum((q_sk < 0.05) & (res[b]["tau_sk"] > 0))),
            sk_sig_fdr_neg=int(np.nansum((q_sk < 0.05) & (res[b]["tau_sk"] < 0))),
            sen_median_C_per_yr=float(np.nanmedian(res[b]["sen"])))
        print(b, rep[f"trend_{b}"], flush=True)
    # regrid every feature to the NDVI grid (average, historical) and compare with parquet
    pq = pd.read_parquet(P["parquet"], columns=["lon", "lat", "lst_day_anomaly_mean", "lst_night_anomaly_mean", "dtr_anomaly_mean",
                                                 "lst_day_mk_tau_monthly", "lst_night_mk_tau_monthly"])
    rr = np.floor((pq.lat.values - g["transform"].f) / g["transform"].e).astype(int)
    cc = np.floor((pq.lon.values - g["transform"].c) / g["transform"].a).astype(int)
    H, W = g["shape"]
    out = {}
    for k, v in feats.items():
        full = np.full(Hn * Wn, np.nan, np.float32); full[idx] = v; full = full.reshape(Hn, Wn)
        dst = np.full((H, W), np.nan, np.float32)
        reproject(full, dst, src_transform=tr0, src_crs=crs0, dst_transform=g["transform"], dst_crs=g["crs"],
                  src_nodata=np.nan, dst_nodata=np.nan, resampling=Resampling.average)
        out[k] = dst[rr, cc]
    rep["parquet_comparison"] = [
        compare(out["day_anom_mean_hist"], pq.lst_day_anomaly_mean.values, name="LST day anomaly_mean"),
        compare(out["night_anom_mean_hist"], pq.lst_night_anomaly_mean.values, name="LST night anomaly_mean"),
        compare(out["dtr_anom_mean_hist"], pq.dtr_anomaly_mean.values, name="DTR anomaly_mean (clim_day-clim_night)"),
        compare(out["day_mk_tau_raw_hist"], pq.lst_day_mk_tau_monthly.values, name="LST day MK tau (raw monthly)"),
        compare(out["night_mk_tau_raw_hist"], pq.lst_night_mk_tau_monthly.values, name="LST night MK tau (raw monthly)")]
    for c in rep["parquet_comparison"]:
        print(c["name"], c.get("pearson_r"), c.get("max_abs_diff"), c["n_compared"], flush=True)
    pd.DataFrame(out).assign(lon=pq.lon.values, lat=pq.lat.values).to_parquet(os.path.join(OUT, "lst_features_pixels.parquet"), index=False)
    rep["runtime_sec"] = time.time() - t0
    dump(rep, os.path.join(OUT, "R5_report.json"))
    print("done", round(time.time() - t0), "s")


if __name__ == "__main__":
    main()
