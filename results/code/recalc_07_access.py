"""
Recalculation R7 -- distance to roads / railways / waterways from the RAW Geofabrik OSM
zone GeoPackages (2022).

Re-implements the historical method (class filters, clip to India, rasterise with
all_touched on a 1 km India equidistant-conic grid, Euclidean distance transform, bilinear
back to the NDVI grid) and VALIDATES it against exact geodesic point-to-line distances for
a random sample of in-India pixel centres (the historical step had no such validation).
"""
import os
import time

import geopandas as gpd
import numpy as np
import pandas as pd
import pyproj
import shapely
from rasterio.features import rasterize
from rasterio.transform import from_origin
from rasterio.warp import reproject, Resampling
from scipy.ndimage import distance_transform_edt

from audit_common import P, RES, provenance, dump, ndvi_grid, india_geom, compare

OUT = os.path.join(RES, "recalculated", "R7_access")
os.makedirs(OUT, exist_ok=True)
t0 = time.time()
rep = dict(provenance=provenance(__file__))
ZONES = ["central-zone", "eastern-zone", "north-eastern-zone", "northern-zone", "southern-zone", "western-zone"]
FILT = {
    "roads": ("gis_osm_roads_free", "fclass IN ('motorway','motorway_link','trunk','trunk_link','primary','primary_link',"
              "'secondary','secondary_link','tertiary','tertiary_link')"),
    "railways": ("gis_osm_railways_free", "fclass NOT IN ('subway')"),
    "waterways": ("gis_osm_waterways_free", "fclass IN ('river','canal','stream')"),
}
EQDC = pyproj.CRS.from_proj4("+proj=eqdc +lat_1=12 +lat_2=30 +lat_0=20 +lon_0=82.5 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs")
india = india_geom("state")
india_eq = gpd.GeoSeries([india], crs="EPSG:4326").to_crs(EQDC).iloc[0]
minx, miny, maxx, maxy = india_eq.bounds
PX = 1000.0
Wm, Hm = int(np.ceil((maxx - minx) / PX)), int(np.ceil((maxy - miny) / PX))
trm = from_origin(minx, maxy, PX, PX)
g = ndvi_grid(); H, W = g["shape"]
pq = pd.read_parquet(P["parquet"], columns=["lon", "lat", "access_dist_roads", "access_dist_railways", "access_dist_waterways"])
rr = np.floor((pq.lat.values - g["transform"].f) / g["transform"].e).astype(int)
cc = np.floor((pq.lon.values - g["transform"].c) / g["transform"].a).astype(int)
rng = np.random.RandomState(42)
samp = rng.choice(len(pq), 3000, replace=False)
geod = pyproj.Geod(ellps="WGS84")
to_ll = pyproj.Transformer.from_crs(EQDC, "EPSG:4326", always_xy=True)
to_eq = pyproj.Transformer.from_crs("EPSG:4326", EQDC, always_xy=True)
sx, sy = to_eq.transform(pq.lon.values[samp], pq.lat.values[samp])
out = {}
for name, (layer, where) in FILT.items():
    parts = [gpd.read_file(os.path.join(P["osm_dir"], f"{z}.gpkg"), layer=layer, where=where, columns=["fclass"], engine="pyogrio")
             for z in ZONES]
    gdf = pd.concat(parts, ignore_index=True)
    n_raw = len(gdf)
    geoms = gdf.geometry.to_crs("EPSG:4326").values
    geoms = geoms[shapely.is_valid(geoms) & ~shapely.is_empty(geoms)]
    shapely.prepare(india)
    inside = shapely.covered_by(geoms, india)
    border = geoms[~inside]
    border = border[shapely.intersects(border, india)]
    border = shapely.intersection(border, india)
    geoms = np.concatenate([geoms[inside], border[~shapely.is_empty(border)]])
    geq = gpd.GeoSeries(geoms, crs="EPSG:4326").to_crs(EQDC).values
    pres = rasterize(((gg, 1) for gg in geq), out_shape=(Hm, Wm), transform=trm, fill=0, all_touched=True, dtype=np.uint8)
    dist = distance_transform_edt(pres == 0).astype(np.float32) * PX / 1000.0  # km
    dst = np.full((H, W), np.nan, np.float32)
    reproject(dist, dst, src_transform=trm, src_crs=EQDC, dst_transform=g["transform"], dst_crs=g["crs"],
              dst_nodata=np.nan, resampling=Resampling.bilinear)
    out[name] = dst[rr, cc]
    col = f"access_dist_{name}"
    cmp = compare(out[name], pq[col].values, name=f"{name} recalculated vs parquet")
    # exact geodesic validation: nearest point on the line set (planar search in eqdc), geodesic length
    tree = shapely.STRtree(geq)
    pts = shapely.points(sx, sy)
    near_idx = tree.nearest(pts)
    npt = shapely.shortest_line(pts, geq[near_idx])
    ex = []
    for ln in npt:
        (x0, y0), (x1, y1) = ln.coords[0], ln.coords[-1]
        lo0, la0 = to_ll.transform(x0, y0); lo1, la1 = to_ll.transform(x1, y1)
        ex.append(geod.inv(lo0, la0, lo1, la1)[2] / 1000.0)
    ex = np.array(ex)
    rast = pq[col].values[samp]
    err = rast - ex
    lat_s = pq.lat.values[samp]
    rep[name] = dict(n_features_raw=n_raw, n_features_clipped=int(len(geq)), historical_comparison=cmp,
                     validation=dict(n=len(samp), mean_exact_km=float(ex.mean()), mean_raster_km=float(rast.mean()),
                                     bias_km=float(err.mean()), mae_km=float(np.abs(err).mean()), rmse_km=float(np.sqrt((err ** 2).mean())),
                                     p95_abs_err_km=float(np.percentile(np.abs(err), 95)),
                                     rel_err_median_pct_where_exact_gt5km=float(np.median(100 * err[ex > 5] / ex[ex > 5])) if (ex > 5).any() else None,
                                     bias_by_lat_band={f"{lo}-{lo+5}": float(err[(lat_s >= lo) & (lat_s < lo + 5)].mean())
                                                       for lo in range(5, 40, 5) if ((lat_s >= lo) & (lat_s < lo + 5)).any()}))
    print(name, rep[name]["n_features_clipped"], cmp.get("pearson_r"), cmp.get("max_abs_diff"), rep[name]["validation"], round(time.time() - t0), flush=True)
pd.DataFrame(out).to_parquet(os.path.join(OUT, "access_pixels.parquet"), index=False)
rep["runtime_sec"] = time.time() - t0
dump(rep, os.path.join(OUT, "R7_report.json"))
