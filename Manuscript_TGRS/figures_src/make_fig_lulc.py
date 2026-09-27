"""Fig. 3 (dominant land-cover map).

Reads Step 4's real 2001 ESA-CCI/C3S 22-class fraction stack (the same file Step 6 reads for
the 21 land-cover features + forest fraction) and derives, per pixel, the argmax (dominant)
class, grouped into 8 readable categories for a legend. This is a genuine derived product of
the pipeline's own data, not a new download.
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import rasterio

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(ROOT, "FLDAS Noah Land Surface Model L4 Global Monthly 0.1 x 0.1 degree "
                          "(MERRA-2 and CHIRPS) (FLDAS_NOAH01_C_GL_M)", "FLDAS_Outputs",
                   "LandCover_22Class_Fractions_2001.tif")
OUT = os.path.join(HERE, "..", "figures", "FigLULC_dominant_class.png")

# band index (1-based, matches the GeoTIFF band order) -> broad group
GROUP = {
    1: "Cropland", 2: "Cropland", 3: "Cropland",
    4: "Mosaic vegetation", 11: "Mosaic vegetation",
    5: "Forest", 6: "Forest", 7: "Forest", 8: "Forest", 9: "Forest", 10: "Forest",
    16: "Forest", 17: "Forest",
    12: "Shrub / grassland", 13: "Shrub / grassland", 14: "Shrub / grassland",
    15: "Shrub / grassland", 18: "Shrub / grassland",
    19: "Urban", 20: "Bare", 21: "Water", 22: "Snow / ice",
}
GROUPS_ORDER = ["Cropland", "Forest", "Shrub / grassland", "Mosaic vegetation",
                "Urban", "Bare", "Water", "Snow / ice"]
COLORS = ["#e0d05a", "#1a7a35", "#a8c25a", "#c9a13b", "#c94b4b", "#b8ab8a", "#5b9bd5", "#e8f0f7"]

INDIA_MASK = os.path.join(ROOT, "NDVI_DATA_INDIA_", "NDVI_Fire_Susceptibility_Outputs", "india_mask.npy")

with rasterio.open(SRC) as ds:
    stack = ds.read().astype(np.float32)  # (22, H, W)
    bounds = ds.bounds

valid = stack.sum(axis=0) > 0.001
india = np.load(INDIA_MASK)  # same 3641x3504 grid as this LULC raster
assert india.shape == valid.shape, (india.shape, valid.shape)
valid &= india  # clip to India's boundary, not the rectangular download extent
dominant_band = np.argmax(stack, axis=0) + 1  # 1-based band index
group_idx = np.full(dominant_band.shape, -1, dtype=np.int16)
for band, grp in GROUP.items():
    group_idx[dominant_band == band] = GROUPS_ORDER.index(grp)
group_idx[~valid] = -1

cmap = mcolors.ListedColormap(COLORS)
cmap.set_bad(color="white")
disp = np.ma.masked_where(group_idx < 0, group_idx)

plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
fig, ax = plt.subplots(figsize=(5.2, 5.6))
im = ax.imshow(disp, extent=(bounds.left, bounds.right, bounds.bottom, bounds.top),
               cmap=cmap, vmin=-0.5, vmax=len(GROUPS_ORDER) - 0.5, interpolation="nearest")
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.set_title("Dominant land-cover class, ESA CCI/C3S 2001")
ax.set_aspect("equal")
patches = [plt.Rectangle((0, 0), 1, 1, color=COLORS[i]) for i in range(len(GROUPS_ORDER))]
ax.legend(patches, GROUPS_ORDER, loc="lower left", fontsize=7, framealpha=0.9)
fig.tight_layout()
fig.savefig(OUT, dpi=200)
print("saved", OUT)
