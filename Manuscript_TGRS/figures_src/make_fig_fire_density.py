"""Fig. 2 (spatial distribution of the corrected fire label).

Reads Step 1's real fire-point archive directly (541,545 points, the same file every
downstream step joins against) and draws a light-theme hexbin density map, styled to match
Fig. 8's map (white background, EPSG:4326 lon/lat axes) rather than the dark-themed
exploratory plot in Forest_Fire_Outputs/plots/05_spatial_density_map.png.
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(ROOT, "Forest fire Extraction in INDIA(2000-2022)", "Forest_Fire_Outputs",
                    "all_forest_fires_2000_2022.csv")
OUT = os.path.join(HERE, "..", "figures", "FigFire_point_density.png")

df = pd.read_csv(SRC, usecols=["latitude", "longitude"])
assert len(df) == 541545, f"expected 541,545 points, got {len(df)}"

plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
fig, ax = plt.subplots(figsize=(5.2, 5.6))
hb = ax.hexbin(df.longitude, df.latitude, gridsize=180, mincnt=1, bins="log",
                cmap="YlOrRd", linewidths=0.1, extent=(68, 97.5, 6, 37.5))
cb = fig.colorbar(hb, ax=ax, shrink=0.75, pad=0.02)
cb.set_label("Fire points per cell (log scale)")
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.set_title(f"MODIS forest-fire points, {len(df):,} detections\n(2000-11-01 to 2022-12-15, forest-LULC filtered)")
ax.set_aspect("equal")
fig.tight_layout()
fig.savefig(OUT, dpi=200)
print("saved", OUT, "n_points", len(df))
