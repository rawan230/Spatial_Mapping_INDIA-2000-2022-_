"""Reproduces Biswas et al. (2025) Figs. 2/3 -- spatial distribution maps of the
predictor variables -- using this study's own real GeoTIFFs.

Rebuilt to match Biswas et al.'s actual cartographic style (verified by rendering
their PDF pages directly, not guessed): full-bleed map per panel, bold variable
name + units overlaid directly on the map, a simple two-stop "High/Low" gradient
legend swatch (not a full tick-heavy colorbar), no axis ticks, a compass rose, a
shared scale bar, and a bold "Drivers of Forest Fire Occurrence" heading.

Grouping now matches Biswas et al. exactly (their Fig 2 vs Fig 3 split is by
variable, verified from their own figure, NOT "atmospheric/biophysical" vs
"temperature/topographic" as originally guessed):
  Fig 2 (6 panels): Near-surface wind speed, Net LW radiation, Precipitation,
                     NDVI, Soil moisture, Specific humidity
  Fig 3 (9 panels): Air temperature, LST daytime, LST nighttime,
                     Distance to roads, Distance to waterways, Distance to railways,
                     Elevation, Slope, Aspect (categorical, 8-direction + flat)

Units are this study's own real units, stated honestly even where they differ from
Biswas et al.'s Table 2 units for the same variable (LST: this project stores it in
degC, not K; precipitation: this project's climatology raster is mm/month, not
mm/h) -- each such case is called out in-panel and in the caption rather than
silently relabeled to look identical."""
import numpy as np
import rasterio
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import geopandas as gpd

OUT_DIR = r"D:\FOREST FIRE MAPPING(INDIA)\Biswas_Comparison_Figures"
BOUNDARY_SHP = r"D:\FOREST FIRE MAPPING(INDIA)\LST_analysis\India_State_Boundary.shp"

boundary = gpd.read_file(BOUNDARY_SHP)
if boundary.crs is None:
    boundary = boundary.set_crs("EPSG:3857", allow_override=True)
boundary = boundary.to_crs("EPSG:4326")

FLDAS = r"D:\FOREST FIRE MAPPING(INDIA)\FLDAS Noah Land Surface Model L4 Global Monthly 0.1 x 0.1 degree (MERRA-2 and CHIRPS) (FLDAS_NOAH01_C_GL_M)\FLDAS_Outputs"
LST = r"D:\FOREST FIRE MAPPING(INDIA)\LST_analysis\LST_Outputs"
DIST = r"D:\FOREST FIRE MAPPING(INDIA)\Distance_Roads_Railways_Waterways_Analysis\Accessibility_Outputs"
TERR = r"D:\FOREST FIRE MAPPING(INDIA)\Terrain_Elevation_Slope_Aspect_Analysis\Terrain_Outputs"
NDVI = r"D:\FOREST FIRE MAPPING(INDIA)\NDVI_DATA_INDIA_\NDVI_Fire_Susceptibility_Outputs"

FIG2_ITEMS = [
    ("Near Surface\nWind Speed", "(m/s)", f"{FLDAS}\\Wind_climatology_annualmean.tif", "turbo"),
    ("Net Long Wave\nRadiation Flux", "(W/m2)", f"{FLDAS}\\NetLWRadiation_climatology_annualmean.tif", "PuOr"),
    ("Precipitation", "(mm/month) *", f"{FLDAS}\\Precip_climatology_annualmean.tif", "GnBu"),
    ("NDVI", "(unitless)", f"{NDVI}\\F1_NDVI_QA_mean.tif", "YlGn"),
    ("Soil Moisture", "(kg/m2)", f"{FLDAS}\\SoilMoisture_climatology_annualmean.tif", "copper_r"),
    ("Specific Humidity", "(kg/kg)", f"{FLDAS}\\SpecificHumidity_climatology_annualmean.tif", "Blues"),
]

FIG3_CONTINUOUS_ITEMS = [
    ("Air Temperature", "(K)", f"{FLDAS}\\AirTemp_climatology_annualmean.tif", "RdYlBu_r"),
    ("LST Daytime", "(degC) *", f"{LST}\\LST_Day_climatology_annualmean.tif", "hot_r"),
    ("LST Nighttime", "(degC) *", f"{LST}\\LST_Night_climatology_annualmean.tif", "hot_r"),
    ("Distance to\nRoads", "(km)", f"{DIST}\\D1_Distance_to_Roads_native_1km.tif", "YlOrBr"),
    ("Distance to\nWaterways", "(km)", f"{DIST}\\D3_Distance_to_Waterways_native_1km.tif", "PuBu"),
    ("Distance to\nRailways", "(km)", f"{DIST}\\D2_Distance_to_Railways_native_1km.tif", "OrRd"),
    ("Elevation", "(m)", f"{TERR}\\T1_Elevation_native_1km.tif", "gist_earth"),
    ("Slope", "(degree)", f"{TERR}\\T2_Slope_native_1km.tif", "YlOrBr"),
]
ASPECT_PATH = f"{TERR}\\T3_Aspect_native_1km.tif"

# Distance-to-feature rasters are heavily right-skewed (most of India sits close
# to a road/railway/waterway, a few remote areas sit far) -- a linear color scale
# renders almost the entire map as one flat color and hides real structure, so
# these get a power-law (gamma<1) normalization instead to spread out the
# near-zero range where nearly all the pixels actually live.
GAMMA_OVERRIDE = {
    "Distance to\nRoads": 0.5,
    "Distance to\nWaterways": 0.5,
    "Distance to\nRailways": 0.5,
}
# Same three rasters also have a long tail of extreme-outlier pixels (e.g. remote
# Himalaya/island cells tens of km from the nearest mapped road) that pin the
# color scale's top end and wash out the gamma correction above -- the color
# scale is additionally capped at the 97th percentile (true max still reported
# in the "High:" legend text, just not used to set the color scale's top).
CLIP_PCTL_OVERRIDE = {
    "Distance to\nRoads": 90,
    "Distance to\nWaterways": 97,
    "Distance to\nRailways": 97,
}


def draw_compass(ax):
    ax.annotate("N", xy=(0.93, 0.90), xycoords="axes fraction", ha="center", fontsize=11, fontweight="bold")
    ax.annotate("", xy=(0.93, 0.89), xytext=(0.93, 0.73), xycoords="axes fraction",
                arrowprops=dict(arrowstyle="-|>", color="black", lw=1.5))


def draw_scalebar(ax, lat_for_scale=22.0):
    km_per_deg = 111.32 * np.cos(np.radians(lat_for_scale))
    bar_km = 500
    bar_deg = bar_km / km_per_deg
    x0, y0 = 69.0, 7.2
    ax.plot([x0, x0 + bar_deg], [y0, y0], color="black", lw=2, transform=ax.transData)
    for frac, lbl in [(0, "0"), (1, f"{bar_km} km")]:
        ax.text(x0 + frac * bar_deg, y0 + 0.5, lbl, fontsize=6.5, ha="center")


def render_continuous_panel(ax, name, units, path):
    with rasterio.open(path) as src:
        arr = src.read(1, masked=True)
        bounds = src.bounds
    vmin, vmax = float(arr.min()), float(arr.max())
    clip_pctl = CLIP_PCTL_OVERRIDE.get(name)
    vmax_color = float(np.percentile(arr.compressed(), clip_pctl)) if clip_pctl is not None else vmax
    gamma = GAMMA_OVERRIDE.get(name)
    if gamma is not None:
        norm = matplotlib.colors.PowerNorm(gamma=gamma, vmin=vmin, vmax=vmax_color)
        ax.imshow(arr, cmap=render_continuous_panel.cmap, norm=norm,
                  extent=[bounds.left, bounds.right, bounds.bottom, bounds.top], zorder=1)
    else:
        ax.imshow(arr, cmap=render_continuous_panel.cmap, vmin=vmin, vmax=vmax_color,
                  extent=[bounds.left, bounds.right, bounds.bottom, bounds.top], zorder=1)
    boundary.boundary.plot(ax=ax, color="#333333", linewidth=0.4, zorder=2)
    ax.set_xticks([]); ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(True); spine.set_color("black"); spine.set_linewidth(0.8)

    ax.text(0.55, 0.95, name, transform=ax.transAxes, ha="center", va="top",
            fontsize=10.5, fontweight="bold", zorder=3,
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.55))
    ax.text(0.55, 0.95 - 0.055 * (name.count("\n") + 1), units, transform=ax.transAxes,
            ha="center", va="top", fontsize=9, fontweight="bold", zorder=3,
            bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none", alpha=0.55))

    swatch = inset_axes(ax, width="7%", height="24%", loc="lower right",
                         bbox_to_anchor=(0.0, 0.05, 0.93, 1), bbox_transform=ax.transAxes, borderpad=0)
    grad_frac = np.linspace(1, 0, 256)
    if gamma is not None:
        grad_frac = grad_frac ** gamma  # match the panel's PowerNorm color mapping
    swatch.imshow(grad_frac.reshape(-1, 1), aspect="auto", cmap=render_continuous_panel.cmap, vmin=0, vmax=1)
    swatch.set_xticks([]); swatch.set_yticks([])
    for spine in swatch.spines.values():
        spine.set_color("black"); spine.set_linewidth(0.6)
    high_label = f"High: {vmax:.3g}" if clip_pctl is None else f"High: {vmax:.3g}\n(color capped\nat P{clip_pctl}={vmax_color:.3g})"
    ax.text(0.895, 0.295, high_label, transform=ax.transAxes, fontsize=6.8, ha="right", va="bottom",
             bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none", alpha=0.7))
    ax.text(0.895, 0.045, f"Low: {vmin:.3g}", transform=ax.transAxes, fontsize=6.8, ha="right", va="top",
             bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none", alpha=0.7))


AZ_DIRECTIONS = [
    ("North", 0, 22.5, "#e6194b"), ("Northeast", 22.5, 67.5, "#f58231"),
    ("East", 67.5, 112.5, "#ffe119"), ("Southeast", 112.5, 157.5, "#3cb44b"),
    ("South", 157.5, 202.5, "#42d4f4"), ("Southwest", 202.5, 247.5, "#4363d8"),
    ("West", 247.5, 292.5, "#911eb4"), ("Northwest", 292.5, 337.5, "#f032e6"),
    ("North ", 337.5, 360.0, "#e6194b"),
]
FLAT_COLOR = "#800000"


def render_aspect_panel(ax, path):
    with rasterio.open(path) as src:
        arr = src.read(1, masked=True)
        bounds = src.bounds
    classed = np.ma.masked_all(arr.shape, dtype=np.int16)
    valid = ~np.ma.getmaskarray(arr)
    raw = arr.data
    for i, (_, lo, hi, _) in enumerate(AZ_DIRECTIONS):
        # arr is a MaskedArray -- comparisons on it (arr >= lo) return a masked
        # boolean array whose underlying .data is unreliable at masked positions,
        # so boolean-indexing classed[sel] with that silently selects nothing.
        # Work on the plain ndarrays (raw, valid) instead.
        sel = valid & (raw >= lo) & (raw < hi)
        classed[sel] = i if i < 8 else 0  # wrap the second "North" slice back to class 0
    cmap = ListedColormap([c for _, _, _, c in AZ_DIRECTIONS[:8]])
    ax.imshow(classed, cmap=cmap, vmin=-0.5, vmax=7.5,
              extent=[bounds.left, bounds.right, bounds.bottom, bounds.top], zorder=1)
    boundary.boundary.plot(ax=ax, color="#333333", linewidth=0.4, zorder=2)
    ax.set_xticks([]); ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(True); spine.set_color("black"); spine.set_linewidth(0.8)
    ax.text(0.55, 0.95, "Aspect", transform=ax.transAxes, ha="center", va="top",
            fontsize=10.5, fontweight="bold", zorder=3,
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.55))
    ax.text(0.55, 0.895, "(degree, classified)", transform=ax.transAxes, ha="center", va="top",
            fontsize=8, fontweight="bold", zorder=3,
            bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none", alpha=0.55))
    from matplotlib.patches import Patch
    handles = [Patch(facecolor=c, edgecolor="black", linewidth=0.3, label=lbl)
               for lbl, _, _, c in AZ_DIRECTIONS[:8]]
    ax.legend(handles=handles, loc="lower right", fontsize=5.8, framealpha=0.85,
              handlelength=1.0, handleheight=1.0, labelspacing=0.25, borderpad=0.4)


def make_figure(items, ncols, out_name, fig_number, extra_note=""):
    nrows = int(np.ceil(len(items) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(4.4 * ncols, 4.9 * nrows))
    axes = np.array(axes).reshape(-1)
    for idx, (ax, (name, units, path, cmap)) in enumerate(zip(axes, items)):
        render_continuous_panel.cmap = cmap
        try:
            render_continuous_panel(ax, name, units, path)
        except Exception as e:
            ax.text(0.5, 0.5, f"{name}\n(load error: {e})", ha="center", va="center", transform=ax.transAxes, fontsize=8)
            ax.set_xticks([]); ax.set_yticks([])
        if idx == ncols - 1:
            draw_compass(ax)
    for ax in axes[len(items):]:
        ax.axis("off")
    draw_scalebar(axes[0])
    fig.suptitle(f"Drivers of Forest Fire Occurrence  (reproduces Biswas et al. 2025, Fig. {fig_number},\n"
                 f"using this study's own data{extra_note})", fontsize=12.5, fontweight="bold", y=1.0)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    out_path = f"{OUT_DIR}/{out_name}"
    fig.savefig(out_path, dpi=150, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path}")


make_figure(FIG2_ITEMS, ncols=3, out_name="Fig02_Atmospheric_Biophysical_Maps.png", fig_number=2,
            extra_note=";  * precipitation is this study's mm/month climatology, Biswas et al. report mm/h")

# Fig 3: 8 continuous panels + 1 categorical (Aspect) = 9 panels, 3x3 grid
nrows, ncols = 3, 3
fig, axes = plt.subplots(nrows, ncols, figsize=(4.4 * ncols, 4.9 * nrows))
axes = axes.reshape(-1)
for idx, (name, units, path, cmap) in enumerate(FIG3_CONTINUOUS_ITEMS):
    render_continuous_panel.cmap = cmap
    try:
        render_continuous_panel(axes[idx], name, units, path)
    except Exception as e:
        axes[idx].text(0.5, 0.5, f"{name}\n(load error: {e})", ha="center", va="center", transform=axes[idx].transAxes, fontsize=8)
        axes[idx].set_xticks([]); axes[idx].set_yticks([])
    if idx == 2:
        draw_compass(axes[idx])
render_aspect_panel(axes[8], ASPECT_PATH)
draw_scalebar(axes[6])
fig.suptitle("Drivers of Forest Fire Occurrence  (reproduces Biswas et al. 2025, Fig. 3,\n"
             "using this study's own data;  * LST is this study's degC climatology, Biswas et al. report K "
             "-- add 273.15 to convert)", fontsize=12.5, fontweight="bold", y=1.0)
fig.tight_layout(rect=[0, 0, 1, 0.93])
out_path = f"{OUT_DIR}/Fig03_Temperature_Human_Topographic_Maps.png"
fig.savefig(out_path, dpi=150, facecolor="white", bbox_inches="tight")
plt.close(fig)
print(f"Saved: {out_path}")
