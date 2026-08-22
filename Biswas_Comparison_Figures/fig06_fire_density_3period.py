"""Reproduces Biswas et al. (2025) Fig. 6 -- spatial distribution of forest fire
count per pixel (625 km^2, their exact stated resolution) for (a) 2001-2020,
(b) 2001-2010, and (c) 2011-2020 -- using this study's own real fire-point data.

Rebuilt from a continuous hexbin+log-colorbar version to a proper classified
choropleth: a real 25km x 25km (625 km^2) equal-area grid (Albers Equal-Area
Conic centered on India, standard parallels 12N/32N -- the conventional choice
for India-extent equal-area grids), fire counts binned into discrete classes,
plotted with a legend of colored boxes (one per class) rather than a continuous
colorbar -- matching the classified-map convention Biswas et al.'s Fig. 6 uses
and giving a real per-class distribution instead of an unbinned density surface."""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch
import geopandas as gpd

FIRE_CSV = r"D:\FOREST FIRE MAPPING(INDIA)\Forest fire Extraction in INDIA(2000-2022)\Forest_Fire_Outputs\all_forest_fires_2000_2022.csv"
BOUNDARY_SHP = r"D:\FOREST FIRE MAPPING(INDIA)\LST_analysis\India_State_Boundary.shp"
OUT_PATH = r"D:\FOREST FIRE MAPPING(INDIA)\Biswas_Comparison_Figures\Fig06_FireDensity_3Period.png"

# Albers Equal-Area Conic centered on India -- standard parallels 12N/32N is the
# conventional choice for India-extent equal-area analyses (matches common
# India climate/GIS grid definitions), giving true km^2 cell areas rather than
# an unprojected degree-grid approximation.
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

xmin, ymin, xmax, ymax = boundary_aea.total_bounds
nx = int(np.ceil((xmax - xmin) / CELL_M))
ny = int(np.ceil((ymax - ymin) / CELL_M))
xedges = xmin + np.arange(nx + 1) * CELL_M
yedges = ymin + np.arange(ny + 1) * CELL_M

periods = [
    ("a) 2001-2020", df[(df["year"] >= 2001) & (df["year"] <= 2020)]),
    ("b) 2001-2010", df[(df["year"] >= 2001) & (df["year"] <= 2010)]),
    ("c) 2011-2020", df[(df["year"] >= 2011) & (df["year"] <= 2020)]),
]

# Discrete classification: 5 classes via quantile breaks on nonzero cells (a
# standard classified-choropleth scheme -- comparable in spirit to Biswas et
# al.'s own classed fire-density symbology, though their exact break method
# isn't stated in the paper text).
CLASS_LABELS = ["Very low", "Low", "Moderate", "High", "Very high"]
CMAP = ListedColormap(["#ffffb2", "#fecc5c", "#fd8d3c", "#f03b20", "#bd0026"])

fig, axes = plt.subplots(1, 3, figsize=(19, 7.5))
for ax, (label, sub) in zip(axes, periods):
    counts, _, _ = np.histogram2d(sub["x_aea"], sub["y_aea"], bins=[xedges, yedges])
    nonzero = counts[counts > 0]
    bounds = np.unique(np.quantile(nonzero, [0, 0.2, 0.4, 0.6, 0.8, 1.0]))
    if len(bounds) < 2:
        bounds = np.array([nonzero.min() if len(nonzero) else 0, (nonzero.max() if len(nonzero) else 1) + 1])
    n_classes = len(bounds) - 1
    class_cmap = ListedColormap(CMAP.colors[:n_classes])
    norm = BoundaryNorm(bounds, n_classes)

    masked = np.ma.masked_where(counts.T == 0, counts.T)
    boundary_aea.boundary.plot(ax=ax, color="black", linewidth=0.5, zorder=3)
    ax.pcolormesh(xedges, yedges, masked, cmap=class_cmap, norm=norm, zorder=2)
    ax.set_title(f"{label}  (n={len(sub):,} points, {nx}x{ny} grid @ 625 km2/cell)", fontsize=10)
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_aspect("equal")

    class_labels_this = CLASS_LABELS[:n_classes] if n_classes <= 5 else [f"Class {i+1}" for i in range(n_classes)]
    handles = [Patch(facecolor=class_cmap(i),
                      label=f"{class_labels_this[i]}: {int(bounds[i])}-{int(bounds[i+1])} fires/cell")
               for i in range(n_classes)]
    ax.legend(handles=handles, loc="lower left", fontsize=6.5, framealpha=0.9, title="Fire count class")

fig.suptitle("Spatial Distribution of Forest Fire Count per 625 km2 Pixel -- India\n"
             "(reproduces Biswas et al. 2025, Fig. 6, using this study's own 541,545-point dataset;\n"
             "classified into quantile-based count classes with a discrete legend, not a continuous density surface)",
             y=1.06)
fig.tight_layout(rect=[0, 0, 1, 0.86])
fig.savefig(OUT_PATH, dpi=150, facecolor="white", bbox_inches="tight")
print(f"Saved: {OUT_PATH}")
print(f"Counts: 2001-2020={len(periods[0][1]):,}, 2001-2010={len(periods[1][1]):,}, 2011-2020={len(periods[2][1]):,}")
print(f"Grid: {nx} x {ny} cells, {CELL_M/1000:.0f}km x {CELL_M/1000:.0f}km = {(CELL_M/1000)**2:.0f} km2/cell")
