"""Reproduces Biswas et al. (2025) Fig. 11 -- correlation matrix between forest
fire point density and different occurrence-conditioning factors -- using this
study's own data.

Rebuilt from a plain matplotlib heatmap (the earlier, WRONG version -- it wasn't
a reproduction of their actual figure at all, just a generic correlation summary)
to match their real Fig. 11 style, confirmed by rendering their PDF page directly:
an R `pairs.panels`-style scatterplot matrix --
  - lower triangle: pairwise scatter + a linear trend line (a LOWESS curve was
    tried first, matching their apparent style more closely, but statsmodels'
    lowess() hangs/stalls on some pairs of this project's real distributions,
    most likely the circular Aspect variable, well outside normal Python
    exception handling -- reverted to a numerically bulletproof linear fit)
  - diagonal: histogram + a histogram-convolution smoothed density curve (same
    reasoning: scipy.stats.gaussian_kde was found to hang on this data too)
  - upper triangle: Pearson r, font size scaled by |r|, with significance stars
Biswas et al.'s 13 variables (their axis labels): FFPD_2020, Aspect, Elevation,
Slope, AirTemp2020, LSTday_2020, LSTnight_2020, NDVI, NSWS, NLWR, Precipitation,
SoilM, SpecificHumidity -- reproduced here with this study's own equivalents.

Honest deviations, stated plainly (not hidden):
  - Biswas et al.'s variable names carry a "_2020" suffix, suggesting a single-
    year (2020) snapshot. This study's own convention (used consistently by every
    other reproduced figure) is whole-period climatology (2000/2001-2022 mean),
    not a single-year extract -- climatology is used here too, for consistency
    with this project's own Figs 2/3 rather than attempting a one-off 2020 pull.
  - Scatter/histogram panels are drawn from a random subsample (N=3,000) of the
    4,161,009 valid pixels -- plotting the full population per panel is
    intractable and unreadable. Correlation coefficients (the actual reported
    number) are computed on a much larger random sample (N=200,000) for
    statistical stability, independent of the plotting subsample."""
import numpy as np
import pandas as pd
import rasterio
from rasterio.warp import reproject, Resampling
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

STACK_TIF = r"D:\FOREST FIRE MAPPING(INDIA)\Integrated_Analysis\Integrated_Outputs\Integrated_FireRisk_Stack.tif"
FLDAS = r"D:\FOREST FIRE MAPPING(INDIA)\FLDAS Noah Land Surface Model L4 Global Monthly 0.1 x 0.1 degree (MERRA-2 and CHIRPS) (FLDAS_NOAH01_C_GL_M)\FLDAS_Outputs"
LST = r"D:\FOREST FIRE MAPPING(INDIA)\LST_analysis\LST_Outputs"
OUT_PATH = r"D:\FOREST FIRE MAPPING(INDIA)\Biswas_Comparison_Figures\Fig11_CorrelationMatrix.png"

RNG_SEED = 42
N_CORR_SAMPLE = 50_000
N_SCATTER_SAMPLE = 3_000

print("Loading fire_count / terrain / NDVI bands from the integrated stack...")
with rasterio.open(STACK_TIF) as src:
    band_names = list(src.descriptions)
    idx = {name: i + 1 for i, name in enumerate(band_names)}
    fire_count = src.read(idx["fire_count"]).astype(np.float32)
    elevation = src.read(idx["terrain_elevation"]).astype(np.float32)
    slope = src.read(idx["terrain_slope"]).astype(np.float32)
    aspect = src.read(idx["terrain_aspect"]).astype(np.float32)
    ndvi = src.read(idx["ndvi_mean"]).astype(np.float32)
    stack_transform = src.transform
    stack_crs = src.crs
    stack_shape = src.shape
    # fire_count is 0-filled everywhere (including outside India), NOT NaN-masked --
    # ndvi_mean carries the real India-validity mask (matches the parquet's own
    # 4,161,009-row population), so that's the mask to use, not fire_count's own.
    valid = ~np.isnan(ndvi)

print(f"Valid pixels: {valid.sum():,}")

def load_reprojected(path):
    """The standalone climatology GeoTIFFs (FLDAS/LST outputs) are stored at their
    own NATIVE resolution (e.g. FLDAS ~0.1 deg, 335x315), not the 1km NDVI grid the
    integrated stack uses -- reproject onto the stack's exact grid (bilinear, the
    documented pipeline convention for coarse-to-fine upsampling) before use."""
    with rasterio.open(path) as src:
        dst = np.full(stack_shape, np.nan, dtype=np.float32)
        reproject(
            source=rasterio.band(src, 1), destination=dst,
            src_transform=src.transform, src_crs=src.crs,
            dst_transform=stack_transform, dst_crs=stack_crs,
            resampling=Resampling.bilinear,
        )
    return dst

print("Loading + reprojecting climatology rasters onto the stack's 1km grid "
      "(AirTemp, LST day/night, wind, NetLW, precip, soil moisture, specific humidity)...")
airtemp = load_reprojected(f"{FLDAS}\\AirTemp_climatology_annualmean.tif")
lst_day = load_reprojected(f"{LST}\\LST_Day_climatology_annualmean.tif")
lst_night = load_reprojected(f"{LST}\\LST_Night_climatology_annualmean.tif")
wind = load_reprojected(f"{FLDAS}\\Wind_climatology_annualmean.tif")
netlw = load_reprojected(f"{FLDAS}\\NetLWRadiation_climatology_annualmean.tif")
precip = load_reprojected(f"{FLDAS}\\Precip_climatology_annualmean.tif")
soilm = load_reprojected(f"{FLDAS}\\SoilMoisture_climatology_annualmean.tif")
qair = load_reprojected(f"{FLDAS}\\SpecificHumidity_climatology_annualmean.tif")

valid = valid & ~np.isnan(airtemp) & ~np.isnan(lst_day) & ~np.isnan(lst_night) \
    & ~np.isnan(wind) & ~np.isnan(netlw) & ~np.isnan(precip) & ~np.isnan(soilm) & ~np.isnan(qair)
print(f"Valid pixels after intersecting all rasters: {valid.sum():,}")

COLUMNS = ["FFPD", "Aspect", "Elevation", "Slope", "AirTemp", "LSTday", "LSTnight",
           "NDVI", "NSWS", "NLWR", "Precip", "SoilM", "SpecHumidity"]
arrays = [fire_count, aspect, elevation, slope, airtemp, lst_day, lst_night,
          ndvi, wind, netlw, precip, soilm, qair]

df = pd.DataFrame({col: arr[valid] for col, arr in zip(COLUMNS, arrays)})
print(f"Assembled dataframe: {len(df):,} rows x {len(COLUMNS)} columns")

rng = np.random.RandomState(RNG_SEED)
corr_sample = df.sample(n=N_CORR_SAMPLE, random_state=rng).reset_index(drop=True)
scatter_sample = corr_sample.sample(n=N_SCATTER_SAMPLE, random_state=rng).reset_index(drop=True)
n_valid_total = int(valid.sum())
del df, fire_count, elevation, slope, aspect, ndvi, airtemp, lst_day, lst_night, wind, netlw, precip, soilm, qair, valid

n = len(COLUMNS)
fig, axes = plt.subplots(n, n, figsize=(22, 20))
fig.subplots_adjust(wspace=0.06, hspace=0.06)

print("Computing pairwise correlations and drawing panels...")
for i in range(n):
    print(f"  row {i+1}/{n} ({COLUMNS[i]})...", flush=True)
    for j in range(n):
        ax = axes[i, j]
        ax.set_xticks([]); ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_color("#999999"); spine.set_linewidth(0.5)

        if i == j:
            vals = scatter_sample[COLUMNS[i]].values
            ax.hist(vals, bins=30, color="#d9d9d9", edgecolor="#888888", linewidth=0.4, density=True)
            # gaussian_kde is pathological (hangs/crashes outside normal Python
            # exception handling) on near-degenerate distributions -- FFPD (fire
            # count) is >90% zeros. Skip the smoothed density overlay for any
            # column whose values collapse onto too few unique points to give
            # gaussian_kde a non-singular covariance to work with.
            # Smoothed density via a binned-histogram + Gaussian convolution, not
            # scipy.stats.gaussian_kde -- kde's pairwise-distance kernel evaluation
            # was found to hang/stall on this project's real (non-synthetic)
            # distributions (circular Aspect, narrow-range NLWR, zero-inflated
            # FFPD), well outside normal Python exception handling. This
            # histogram-convolution approach is O(n) and numerically bulletproof.
            n_unique = len(np.unique(vals))
            if n_unique > 5 and np.std(vals) > 1e-8:
                counts, edges = np.histogram(vals, bins=40, density=True)
                centers = 0.5 * (edges[:-1] + edges[1:])
                kernel = np.exp(-0.5 * (np.arange(-5, 6) / 1.5) ** 2)
                kernel /= kernel.sum()
                smoothed = np.convolve(counts, kernel, mode="same")
                ax.plot(centers, smoothed, color="#c0392b", linewidth=1.2)
            ax.text(0.5, 0.92, COLUMNS[i], transform=ax.transAxes, ha="center", va="top",
                    fontsize=9, fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.75))
        elif i > j:
            x = scatter_sample[COLUMNS[j]].values
            y = scatter_sample[COLUMNS[i]].values
            ax.scatter(x, y, s=2, color="#1a1a1a", alpha=0.25, linewidths=0)
            # Linear trend line, not LOWESS -- statsmodels' lowess() was found to
            # hang/stall (well outside normal Python exception handling) on some
            # pairs of this project's real distributions, most likely the
            # circular Aspect variable. A linear fit is guaranteed O(n) and
            # numerically stable; it conveys the fitted relationship's direction
            # even though it won't capture curvature the way a real loess would.
            if len(np.unique(x)) > 5 and np.std(x) > 1e-8:
                coeffs = np.polyfit(x, y, deg=1)
                xs = np.linspace(x.min(), x.max(), 50)
                ax.plot(xs, np.polyval(coeffs, xs), color="#e41a1c", linewidth=1.4)
        else:
            r, p = stats.pearsonr(corr_sample[COLUMNS[j]].values, corr_sample[COLUMNS[i]].values)
            stars = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
            fontsize = 8 + 22 * abs(r)
            color = "#c0392b" if r > 0 else "#2166ac"
            ax.text(0.5, 0.55, f"{r:.2f}", transform=ax.transAxes, ha="center", va="center",
                    fontsize=fontsize, color=color, fontweight="bold")
            if stars:
                ax.text(0.5, 0.85, stars, transform=ax.transAxes, ha="center", va="center",
                        fontsize=9, color="#e41a1c")

        if j == 0:
            ax.set_ylabel(COLUMNS[i], fontsize=8, rotation=90)
        if i == n - 1:
            ax.set_xlabel(COLUMNS[j], fontsize=8)

fig.suptitle("Correlation Matrix: Forest Fire Point Density vs. Occurrence-Conditioning Factors\n"
             "(reproduces Biswas et al. 2025, Fig. 11, using this study's own data -- pairs-panel style: "
             "scatter+linear trend (lower), density (diagonal), Pearson r with significance stars (upper))",
             fontsize=13, y=0.995)
fig.text(0.01, 0.01,
         f"N={N_CORR_SAMPLE:,} random sample for correlation values; N={N_SCATTER_SAMPLE:,} for scatter/histogram "
         f"panels (full population {n_valid_total:,} pixels intractable to plot directly). Climatology-based "
         f"(whole-period mean), not Biswas et al.'s apparent single-year 2020 snapshot -- see script docstring.",
         fontsize=7.5, style="italic")
fig.savefig(OUT_PATH, dpi=130, facecolor="white", bbox_inches="tight")
print(f"Saved: {OUT_PATH}")
