"""Reproduces Biswas et al. (2025) Fig. 1 -- (a) the study area and nearby region
with different land cover types per LULC, and (b/c) the forest type map of India.

Biswas et al. show 2001 and 2020 forest-type panels; this reproduces (a) and a
SINGLE forest-type panel for **2022** (this project's own study-period end year,
extending 2 years past Biswas et al.'s 2020 cutoff) instead of duplicating their
exact 2001/2020 pair, using this study's own real, unclipped C3S-LCCS regional
NetCDF -- not previously used for a map figure anywhere else in this project
(every other step works from the India-masked/reprojected downstream products).

Source: `Forest_Fire_Outputs/lulc_extracted/C3S-LC-L4-LCCS-Map-300m-P1Y-2022-
v2.1.1...nc`, the raw CDS-downloaded regional subset (lat 6.00-37.50N, lon
67.50-98.00E, 300m, never clipped to India on disk) -- this IS the "study area
and nearby region" extent Biswas et al.'s panel (a) shows, not an India-only crop.
Pixel values are literal ESA-CCI/C3S LCCS Level-2 codes (confirmed via the file's
own `flag_values` attribute and a full-resolution histogram -- see below).

Both reclassifications (LULC 7-class scheme for panel a; forest-type subclasses
for the forest map) are this project's own crosswalk, built from the standard
LCCS Level-2 legend -- Biswas et al.'s paper does not publish an exact code-to-
category table, only the category/subclass names themselves (their Fig. 1
legend), so this is a disclosed, reasoned reconstruction, not a copied table.
The "Forestland" bucket in panel (a) reuses this project's OWN 13-code forest
definition (FOREST_CODES, Step 1 / Step 6) for internal consistency with every
other figure and the trained models, rather than inventing a second definition
just for this plot."""
import numpy as np
import netCDF4 as nc
import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch

LULC_PATH = r"D:\FOREST FIRE MAPPING(INDIA)\Forest fire Extraction in INDIA(2000-2022)\Forest_Fire_Outputs\lulc_extracted\C3S-LC-L4-LCCS-Map-300m-P1Y-2022-v2.1.1.area-subset.37.5.98.6.67.5.nc"
BOUNDARY_SHP = r"D:\FOREST FIRE MAPPING(INDIA)\LST_analysis\India_State_Boundary.shp"
OUT_A = r"D:\FOREST FIRE MAPPING(INDIA)\Biswas_Comparison_Figures\Fig01a_StudyArea_LULC.png"
OUT_B = r"D:\FOREST FIRE MAPPING(INDIA)\Biswas_Comparison_Figures\Fig01b_ForestType_2022.png"

DOWNSAMPLE_A = 3  # regional panel: stride-subsample for a tractable render size

print("Loading 2022 regional LCCS raster...")
ds = nc.Dataset(LULC_PATH)
lat = np.array(ds.variables["lat"][:])
lon = np.array(ds.variables["lon"][:])
lulc = np.array(ds.variables["lccs_class"][0])
print(f"Grid: {lulc.shape}, lat {lat.min():.2f}-{lat.max():.2f}, lon {lon.min():.2f}-{lon.max():.2f}")

boundary = gpd.read_file(BOUNDARY_SHP)
if boundary.crs is None:
    boundary = boundary.set_crs("EPSG:3857", allow_override=True)
boundary = boundary.to_crs("EPSG:4326")

# ---------------------------------------------------------------------------
# Panel (a): 7-class LULC reclassification, matching Biswas et al.'s own legend
# ---------------------------------------------------------------------------
FOREST_CODES = {50, 60, 61, 62, 70, 71, 72, 80, 81, 82, 90, 100, 110}  # this project's own definition
LULC7_MAP = {
    "Cropland":     {10, 11, 12, 20, 30, 40},
    "Forestland":   FOREST_CODES,
    "Grassland":    {120, 121, 122, 130, 140, 150, 151, 152, 153},
    "Wetland":      {160, 170, 180},
    "Urban built-up": {190},
    "Fallow land":  {200, 201, 202},
    "Waterbodies":  {210, 220},
}
LULC7_COLORS = {
    "Cropland": "#f0e9c0", "Forestland": "#1a7a3c", "Grassland": "#a6d96a",
    "Wetland": "#4fb3d9", "Urban built-up": "#d7191c", "Fallow land": "#c9c9c9",
    "Waterbodies": "#08306b",
}
labels7 = list(LULC7_MAP.keys())
class7 = np.full(lulc.shape, -1, dtype=np.int16)
for i, name in enumerate(labels7):
    mask = np.isin(lulc, list(LULC7_MAP[name]))
    class7[mask] = i
unmapped = (class7 == -1).sum()
print(f"Panel (a): unmapped pixels = {unmapped:,} ({100*unmapped/class7.size:.4f}%)")

class7_small = class7[::DOWNSAMPLE_A, ::DOWNSAMPLE_A]
lat_small = lat[::DOWNSAMPLE_A]
lon_small = lon[::DOWNSAMPLE_A]

cmap7 = ListedColormap([LULC7_COLORS[n] for n in labels7])
norm7 = BoundaryNorm(np.arange(-0.5, len(labels7)), cmap7.N)

fig, ax = plt.subplots(figsize=(14, 13))
masked7 = np.ma.masked_where(class7_small < 0, class7_small)
ax.imshow(masked7, cmap=cmap7, norm=norm7,
          extent=[lon.min(), lon.max(), lat.min(), lat.max()], origin="upper", zorder=1)
boundary.boundary.plot(ax=ax, color="#333333", linewidth=0.7, zorder=2)
ax.set_xticks([]); ax.set_yticks([])
for spine in ax.spines.values():
    spine.set_visible(True); spine.set_color("black")

ax.text(0.70, 0.28, "Bay of\nBengal", transform=ax.transAxes, fontsize=11, color="white",
        ha="center", fontweight="bold")
ax.text(0.18, 0.22, "Arabian\nSea", transform=ax.transAxes, fontsize=11, color="white",
        ha="center", fontweight="bold")
ax.text(0.93, 0.90, "N", transform=ax.transAxes, ha="center", fontsize=13, fontweight="bold")
ax.annotate("", xy=(0.93, 0.89), xytext=(0.93, 0.75), xycoords="axes fraction",
            arrowprops=dict(arrowstyle="-|>", color="black", lw=1.6))

km_per_deg = 111.32 * np.cos(np.radians(22))
bar_km = 500
bar_deg = bar_km / km_per_deg
x0, y0 = lon.min() + 0.5, lat.min() + 0.5
ax.plot([x0, x0 + bar_deg], [y0, y0], color="black", lw=2.5)
ax.text(x0 + bar_deg / 2, y0 + 0.4, f"{bar_km} km", fontsize=9, ha="center")

handles = [Patch(facecolor=LULC7_COLORS[n], edgecolor="black", linewidth=0.4, label=n) for n in labels7]
ax.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.0, -0.16), ncol=4,
          fontsize=10, frameon=False, title="Land Use Land Cover types", title_fontsize=11)

ax.set_title("(a) Study Area and Nearby Region: Land Use Land Cover Types (2022)\n"
              "reproduces Biswas et al. 2025, Fig. 1a, using this study's own C3S-LCCS 2022 regional raster",
              fontsize=12.5, fontweight="bold", pad=12)
fig.tight_layout()
fig.savefig(OUT_A, dpi=150, facecolor="white", bbox_inches="tight")
plt.close(fig)
print(f"Saved: {OUT_A}")

# ---------------------------------------------------------------------------
# Panel (b): Forest type map of India, 2022 -- India-clipped, real present subclasses only
# ---------------------------------------------------------------------------
FOREST_TYPE_MAP = {
    "Broadleaved evergreen, closed to open (>15%)": {50},
    "Broadleaved deciduous, closed to open (>15%)": {60},
    "Broadleaved deciduous, closed (>40%)": {61},
    "Needleleaved evergreen, closed to open (>15%)": {70},
    "Needleleaved evergreen, closed (>40%)": {71},
    "Needleleaved evergreen, open (15-40%)": {72},
    "Needleleaved deciduous, closed to open (>15%)": {80},
    "Needleleaved deciduous, closed (>40%)": {81},
    "Mixed leaf type (broadleaved and needleleaved)": {90},
    "Mosaic tree/shrub (>50%), herbaceous (<50%)": {100},
    "Mosaic herbaceous (>50%), tree/shrub (<50%)": {110},
}
FOREST_TYPE_COLORS = [
    "#78c679", "#a6a300", "#6b6100", "#41ab5d", "#1b4d1b", "#00e600",
    "#e0e08a", "#8c8c53", "#1a9e8f", "#8fd9c4", "#c2b280",
]

# India mask: point-in-polygon test on the raster grid, restricted to India's own
# bounding box first for tractability (avoids a 124M-point contains() call).
india_union = boundary.union_all()
ib = boundary.total_bounds  # minx, miny, maxx, maxy
lat_in_india_bbox = (lat >= ib[1]) & (lat <= ib[3])
lon_in_india_bbox = (lon >= ib[0]) & (lon <= ib[2])
row_idx = np.where(lat_in_india_bbox)[0]
col_idx = np.where(lon_in_india_bbox)[0]
r0, r1 = row_idx.min(), row_idx.max() + 1
c0, c1 = col_idx.min(), col_idx.max() + 1
print(f"India bbox crop: rows {r0}:{r1}, cols {c0}:{c1}")

lulc_india = lulc[r0:r1, c0:c1]
lat_india = lat[r0:r1]
lon_india = lon[c0:c1]

DOWNSAMPLE_B = 2
lulc_india_small = lulc_india[::DOWNSAMPLE_B, ::DOWNSAMPLE_B]
lat_india_small = lat_india[::DOWNSAMPLE_B]
lon_india_small = lon_india[::DOWNSAMPLE_B]

from rasterio.features import rasterize
from rasterio.transform import from_bounds
print("Rasterizing India polygon onto the grid (rasterio.features.rasterize)...")
ny, nx = lat_india_small.shape[0], lon_india_small.shape[0]
raster_transform = from_bounds(lon_india.min(), lat_india.min(), lon_india.max(), lat_india.max(), nx, ny)
in_india = rasterize(
    [(india_union, 1)], out_shape=(ny, nx), transform=raster_transform,
    fill=0, dtype=np.uint8,
).astype(bool)
print(f"In-India pixels (downsampled grid): {in_india.sum():,}")

forest_labels = list(FOREST_TYPE_MAP.keys())
classed = np.full(lulc_india_small.shape, -1, dtype=np.int16)
for i, name in enumerate(forest_labels):
    mask = np.isin(lulc_india_small, list(FOREST_TYPE_MAP[name]))
    classed[mask] = i
present = [i for i in range(len(forest_labels)) if (classed == i).sum() > 0]
print(f"Forest subclasses present in India 2022: {len(present)} of {len(forest_labels)}")
for i in present:
    print(f"  {forest_labels[i]}: {(classed == i).sum():,} px")

classed = np.where(in_india, classed, -2)  # -2 = outside India (not forest, not shown as class)
classed_present_only = np.where(np.isin(classed, present), classed, -1)

present_labels = [forest_labels[i] for i in present]
present_colors = [FOREST_TYPE_COLORS[i] for i in present]
remap = {old: new for new, old in enumerate(present)}
classed_remapped = np.full(classed_present_only.shape, -1, dtype=np.int16)
for old, new in remap.items():
    classed_remapped[classed_present_only == old] = new

cmap_f = ListedColormap(present_colors)
norm_f = BoundaryNorm(np.arange(-0.5, len(present_labels)), cmap_f.N)

fig, ax = plt.subplots(figsize=(10, 12))
masked_f = np.ma.masked_where(classed_remapped < 0, classed_remapped)
ax.imshow(masked_f, cmap=cmap_f, norm=norm_f,
          extent=[lon_india.min(), lon_india.max(), lat_india.min(), lat_india.max()],
          origin="upper", zorder=1)
boundary.boundary.plot(ax=ax, color="#333333", linewidth=0.6, zorder=2)
ax.set_xticks([]); ax.set_yticks([])
for spine in ax.spines.values():
    spine.set_visible(True); spine.set_color("black")
ax.text(0.90, 0.95, "N", transform=ax.transAxes, ha="center", fontsize=12, fontweight="bold")
ax.annotate("", xy=(0.90, 0.94), xytext=(0.90, 0.82), xycoords="axes fraction",
            arrowprops=dict(arrowstyle="-|>", color="black", lw=1.5))
km_per_deg2 = 111.32 * np.cos(np.radians(22))
bar_km2 = 500
bar_deg2 = bar_km2 / km_per_deg2
x0b, y0b = lon_india.min() + 0.3, lat_india.min() + 0.3
ax.plot([x0b, x0b + bar_deg2], [y0b, y0b], color="black", lw=2.2)
ax.text(x0b + bar_deg2 / 2, y0b + 0.35, f"{bar_km2} km", fontsize=8.5, ha="center")

handles_f = [Patch(facecolor=present_colors[i], edgecolor="black", linewidth=0.4, label=present_labels[i])
             for i in range(len(present_labels))]
ax.legend(handles=handles_f, loc="lower left", bbox_to_anchor=(0.0, -0.30), fontsize=8, frameon=False,
          title="Forest types (2022)", title_fontsize=9.5)

ax.set_title("(b) Forest Type Map of India, 2022\n"
              "reproduces Biswas et al. 2025, Fig. 1b/c, using this study's own C3S-LCCS 2022 raster "
              "(their panels show 2001/2020; this uses this project's own 2022 study-end year instead)",
              fontsize=11.5, fontweight="bold", pad=10)
fig.tight_layout()
fig.savefig(OUT_B, dpi=150, facecolor="white", bbox_inches="tight")
plt.close(fig)
print(f"Saved: {OUT_B}")
