"""Reproduces Biswas et al. (2025) Fig. 6 -- spatial distribution of forest fire
count per pixel for (a) 2001-2020, (b) 2001-2010, (c) 2011-2020 -- using this
study's own real fire-point data, for direct visual comparison."""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import geopandas as gpd

FIRE_CSV = r"D:\FOREST FIRE MAPPING(INDIA)\Forest fire Extraction in INDIA(2000-2022)\Forest_Fire_Outputs\all_forest_fires_2000_2022.csv"
BOUNDARY_SHP = r"D:\FOREST FIRE MAPPING(INDIA)\LST_analysis\India_State_Boundary.shp"
OUT_PATH = r"D:\FOREST FIRE MAPPING(INDIA)\Biswas_Comparison_Figures\Fig06_FireDensity_3Period.png"

df = pd.read_csv(FIRE_CSV)
df["acq_date"] = pd.to_datetime(df["acq_date"])
df["year"] = df["acq_date"].dt.year

boundary = gpd.read_file(BOUNDARY_SHP)
if boundary.crs is None:
    boundary = boundary.set_crs("EPSG:3857", allow_override=True)
boundary = boundary.to_crs("EPSG:4326")

periods = [
    ("a) 2001-2020", df[(df["year"] >= 2001) & (df["year"] <= 2020)]),
    ("b) 2001-2010", df[(df["year"] >= 2001) & (df["year"] <= 2010)]),
    ("c) 2011-2020", df[(df["year"] >= 2011) & (df["year"] <= 2020)]),
]

fig, axes = plt.subplots(1, 3, figsize=(18, 7))
for ax, (label, sub) in zip(axes, periods):
    boundary.boundary.plot(ax=ax, color="black", linewidth=0.5)
    hb = ax.hexbin(sub["longitude"], sub["latitude"], gridsize=120, cmap="YlOrRd",
                    bins="log", mincnt=1, extent=[68, 97.5, 6, 37.5])
    ax.set_title(f"{label}  (n={len(sub):,})")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    fig.colorbar(hb, ax=ax, fraction=0.04, pad=0.02, label="log(fire count)")

fig.suptitle("Spatial Distribution of Forest Fire Count per Pixel -- India\n"
             "(reproduces Biswas et al. 2025, Fig. 6, using this study's own 541,545-point dataset)")
fig.tight_layout()
fig.savefig(OUT_PATH, dpi=150, facecolor="white")
print(f"Saved: {OUT_PATH}")
print(f"Counts: 2001-2020={len(periods[0][1]):,}, 2001-2010={len(periods[1][1]):,}, 2011-2020={len(periods[2][1]):,}")
