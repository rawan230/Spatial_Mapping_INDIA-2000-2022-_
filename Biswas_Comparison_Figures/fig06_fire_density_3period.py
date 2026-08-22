"""Reproduces Biswas et al. (2025) Fig. 6 -- spatial distribution of forest fire
count per pixel (625 km^2, their exact stated resolution) for (a) 2001-2020,
(b) 2001-2010, and (c) 2011-2020 -- using this study's own real fire-point data.

Matches Biswas et al.'s actual Fig. 6 convention (verified by rendering their PDF
page directly): a SHARED set of fixed count-class breaks across all three panels
(computed once from panel a's full-period data, not re-classified per panel --
using the same breaks per panel is what makes (a) vs (b) vs (c) visually
comparable), in-India zero-count cells colored as the lowest class (matching
their solid-blue "0-36" background) rather than left blank, and a single
horizontal class legend placed in the blank margin below all three panels
-- not overlapping the map, which is what a per-panel in-axes legend did before."""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch
import geopandas as gpd
from shapely.geometry import box

FIRE_CSV = r"D:\FOREST FIRE MAPPING(INDIA)\Forest fire Extraction in INDIA(2000-2022)\Forest_Fire_Outputs\all_forest_fires_2000_2022.csv"
BOUNDARY_SHP = r"D:\FOREST FIRE MAPPING(INDIA)\LST_analysis\India_State_Boundary.shp"
OUT_PATH = r"D:\FOREST FIRE MAPPING(INDIA)\Biswas_Comparison_Figures\Fig06_FireDensity_3Period.png"

AEA_CRS = "+proj=aea +lat_1=12 +lat_2=32 +lat_0=22 +lon_0=82 +datum=WGS84 +units=m +no_defs"
CELL_M = 25_000.0  # 25km x 25km = 625 km^2, matching Biswas et al.'s stated Fig. 6 resolution

df = pd.read_csv(FIRE_CSV)
df["acq_date"] = pd.to_datetime(df["acq_date"])
df["year"] = df["acq_date"].dt.year

pts = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df["longitude"], df["latitude"]), crs="EPSG:4326")
pts_aea = pts.to_crs(AEA_CRS)
df["x_aea"] = pts_aea.geometry.x
df["y_aea"] = pts_aea.geometry.y

boundary = gpd.read_file(BOUNDARY_SHP)
if boundary.crs is None:
    boundary = boundary.set_crs("EPSG:3857", allow_override=True)
boundary_aea = boundary.to_crs(AEA_CRS)
india_union = boundary_aea.union_all()

xmin, ymin, xmax, ymax = boundary_aea.total_bounds
nx = int(np.ceil((xmax - xmin) / CELL_M))
ny = int(np.ceil((ymax - ymin) / CELL_M))
xedges = xmin + np.arange(nx + 1) * CELL_M
yedges = ymin + np.arange(ny + 1) * CELL_M

# Which grid cells actually fall inside India (by center point) -- lets us paint
# true zero-fire cells with the bottom class color instead of leaving them blank.
cx = (xedges[:-1] + xedges[1:]) / 2
cy = (yedges[:-1] + yedges[1:]) / 2
cxx, cyy = np.meshgrid(cx, cy)
cell_pts = gpd.GeoSeries(gpd.points_from_xy(cxx.ravel(), cyy.ravel()), crs=AEA_CRS)
in_india = cell_pts.within(india_union).values.reshape(cxx.shape)  # shape (ny, nx), matches counts.T

periods = [
    ("a) 2001-2020", df[(df["year"] >= 2001) & (df["year"] <= 2020)]),
    ("b) 2001-2010", df[(df["year"] >= 2001) & (df["year"] <= 2010)]),
    ("c) 2011-2020", df[(df["year"] >= 2011) & (df["year"] <= 2020)]),
]

counts_by_period = {}
for label, sub in periods:
    counts, _, _ = np.histogram2d(sub["x_aea"], sub["y_aea"], bins=[xedges, yedges])
    counts_by_period[label] = counts

# Fixed shared classification, computed once from panel (a)'s full-period, full-
# India nonzero cells -- 8 classes via quantiles (Biswas et al.'s own exact break
# method -- likely Jenks natural breaks -- isn't stated in their paper text, so
# quantile breaks are used here and disclosed as such).
counts_a = counts_by_period["a) 2001-2020"]
nonzero_a = counts_a.T[in_india & (counts_a.T > 0)]
N_CLASSES = 8
qs = np.quantile(nonzero_a, np.linspace(0, 1, N_CLASSES))
bounds = np.concatenate(([0], np.unique(qs)))
bounds = np.unique(bounds)
n_classes = len(bounds) - 1

CMAP = ListedColormap(["#2166ac", "#4393c3", "#92c5de", "#ffffbf", "#fed976", "#fd8d3c", "#e31a1c", "#800026"][:n_classes])
CLASS_LABELS = ["Very low", "Low", "Low-mod", "Moderate", "Mod-high", "High", "Very high", "Extreme"][:n_classes]

fig, axes = plt.subplots(1, 3, figsize=(19, 8.2))
for ax, (label, sub) in zip(axes, periods):
    counts = counts_by_period[label]
    grid = counts.T.copy()
    grid_masked = np.ma.masked_where(~in_india, grid)  # only mask cells truly outside India
    norm = BoundaryNorm(bounds, n_classes)

    ax.pcolormesh(xedges, yedges, grid_masked, cmap=CMAP, norm=norm, zorder=2)
    boundary_aea.boundary.plot(ax=ax, color="black", linewidth=0.5, zorder=3)
    ax.set_title(f"{label}  (n={len(sub):,} points)", fontsize=11, fontweight="bold")
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_aspect("equal")
    for spine in ax.spines.values():
        spine.set_visible(True); spine.set_color("black")

handles = [Patch(facecolor=CMAP(i), edgecolor="black", linewidth=0.4,
                  label=f"{CLASS_LABELS[i]}: {int(bounds[i])}-{int(bounds[i+1])}")
           for i in range(n_classes)]
fig.legend(handles=handles, loc="lower center", ncol=n_classes, fontsize=9,
           frameon=False, bbox_to_anchor=(0.5, 0.02), title="Forest fire count per 625 km2 cell (shared across a/b/c)")

fig.suptitle(f"Spatial Distribution of Forest Fire Count per 625 km2 Pixel -- India  ({nx}x{ny} grid)\n"
             "(reproduces Biswas et al. 2025, Fig. 6, using this study's own 541,545-point dataset;\n"
             "shared quantile-based classes computed from panel a, not re-classified per panel)",
             fontsize=12.5, y=1.0)
fig.tight_layout(rect=[0, 0.09, 1, 0.87])
fig.savefig(OUT_PATH, dpi=150, facecolor="white", bbox_inches="tight")
print(f"Saved: {OUT_PATH}")
print(f"Counts: 2001-2020={len(periods[0][1]):,}, 2001-2010={len(periods[1][1]):,}, 2011-2020={len(periods[2][1]):,}")
print(f"Grid: {nx} x {ny} cells, 625 km2/cell; shared class bounds: {bounds}")
