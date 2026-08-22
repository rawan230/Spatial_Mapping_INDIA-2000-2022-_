"""Reproduces Biswas et al. (2025) Fig. 11 -- correlation matrix between forest
fire point density and the occurrence-conditioning factors -- using this study's
own integrated pixel table (Step 6, 55 features, post-leakage-fix)."""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PARQUET_PATH = r"D:\FOREST FIRE MAPPING(INDIA)\Integrated_Analysis\Integrated_Outputs\Integrated_FireRisk_Pixels.parquet"
OUT_PATH = r"D:\FOREST FIRE MAPPING(INDIA)\Biswas_Comparison_Figures\Fig11_CorrelationMatrix.png"

# Representative subset (one per Biswas variable group, not all 55 engineered features --
# a 55x55 matrix would be unreadable; this keeps the figure comparable in scope to
# Biswas et al.'s own 15-variable version)
REP_COLS = [
    "fire_count", "ndvi_mean", "ndvi_trend_2x12ma", "lst_day_anomaly_mean",
    "lst_night_anomaly_mean", "dtr_anomaly_mean", "fldas_airtemp_anomaly",
    "fldas_rh_anomaly", "fldas_precip_anomaly", "fldas_wind_anomaly",
    "fldas_soilmoisture_anomaly", "fldas_netlwradiation_anomaly",
    "terrain_elevation", "terrain_slope", "terrain_aspect",
    "access_dist_roads", "access_dist_railways", "access_dist_waterways",
    "forest_frac_baseline",
]
LABELS = [
    "Fire count", "NDVI", "NDVI trend", "LST day anom.", "LST night anom.", "DTR anom.",
    "Air temp anom.", "RH anom.", "Precip anom.", "Wind anom.", "Soil moist anom.",
    "Net LW rad anom.", "Elevation", "Slope", "Aspect",
    "Dist. roads", "Dist. railways", "Dist. waterways", "Forest fraction",
]

df = pd.read_parquet(PARQUET_PATH, columns=REP_COLS)
print(f"Loaded {len(df):,} rows, {len(REP_COLS)} representative variables")
corr = df.corr(method="pearson")
corr.columns = LABELS
corr.index = LABELS

fig, ax = plt.subplots(figsize=(12, 10))
im = ax.imshow(corr.values, cmap="RdBu_r", vmin=-1, vmax=1)
ax.set_xticks(range(len(LABELS))); ax.set_xticklabels(LABELS, rotation=90, fontsize=8)
ax.set_yticks(range(len(LABELS))); ax.set_yticklabels(LABELS, fontsize=8)
for i in range(len(LABELS)):
    for j in range(len(LABELS)):
        v = corr.values[i, j]
        ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                fontsize=6, color="white" if abs(v) > 0.5 else "black")
cbar = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
cbar.set_label("Pearson correlation")
ax.set_title("Correlation Matrix: Fire Count vs. Occurrence-Conditioning Factors\n"
              "(reproduces Biswas et al. 2025, Fig. 11, on this study's own 4.16M-pixel table)")
fig.tight_layout()
fig.savefig(OUT_PATH, dpi=150, facecolor="white")
print(f"Saved: {OUT_PATH}")
print("\nFire count's own correlations:")
print(corr["Fire count"].sort_values(key=abs, ascending=False))
