"""Reproduces Biswas et al. (2025) Figs. 2/3 -- spatial distribution maps of the
predictor variables, split the same way: Fig 2 = atmospheric + biophysical factors,
Fig 3 = temperature + human-interference + topographical factors -- using this
study's own real GeoTIFFs (no simulation)."""
import numpy as np
import rasterio
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT_DIR = r"D:\FOREST FIRE MAPPING(INDIA)\Biswas_Comparison_Figures"

FIG2_ATMOSPHERIC_BIOPHYSICAL = [
    ("Air temperature (anomaly)", r"D:\FOREST FIRE MAPPING(INDIA)\FLDAS Noah Land Surface Model L4 Global Monthly 0.1 x 0.1 degree (MERRA-2 and CHIRPS) (FLDAS_NOAH01_C_GL_M)\FLDAS_Outputs\AirTemp_climatology_annualmean.tif", "coolwarm"),
    ("Specific humidity", r"D:\FOREST FIRE MAPPING(INDIA)\FLDAS Noah Land Surface Model L4 Global Monthly 0.1 x 0.1 degree (MERRA-2 and CHIRPS) (FLDAS_NOAH01_C_GL_M)\FLDAS_Outputs\SpecificHumidity_climatology_annualmean.tif", "YlGnBu"),
    ("Precipitation", r"D:\FOREST FIRE MAPPING(INDIA)\FLDAS Noah Land Surface Model L4 Global Monthly 0.1 x 0.1 degree (MERRA-2 and CHIRPS) (FLDAS_NOAH01_C_GL_M)\FLDAS_Outputs\Precip_climatology_annualmean.tif", "Blues"),
    ("Wind speed", r"D:\FOREST FIRE MAPPING(INDIA)\FLDAS Noah Land Surface Model L4 Global Monthly 0.1 x 0.1 degree (MERRA-2 and CHIRPS) (FLDAS_NOAH01_C_GL_M)\FLDAS_Outputs\Wind_climatology_annualmean.tif", "PuBu"),
    ("Net LW radiation", r"D:\FOREST FIRE MAPPING(INDIA)\FLDAS Noah Land Surface Model L4 Global Monthly 0.1 x 0.1 degree (MERRA-2 and CHIRPS) (FLDAS_NOAH01_C_GL_M)\FLDAS_Outputs\NetLWRadiation_climatology_annualmean.tif", "RdPu"),
    ("Soil moisture", r"D:\FOREST FIRE MAPPING(INDIA)\FLDAS Noah Land Surface Model L4 Global Monthly 0.1 x 0.1 degree (MERRA-2 and CHIRPS) (FLDAS_NOAH01_C_GL_M)\FLDAS_Outputs\SoilMoisture_climatology_annualmean.tif", "BrBG"),
    ("NDVI", r"D:\FOREST FIRE MAPPING(INDIA)\NDVI_DATA_INDIA_\NDVI_Fire_Susceptibility_Outputs\F1_NDVI_QA_mean.tif", "YlGn"),
]

FIG3_TEMP_HUMAN_TOPO = [
    ("LST daytime", r"D:\FOREST FIRE MAPPING(INDIA)\LST_analysis\LST_Outputs\LST_Day_climatology_annualmean.tif", "hot"),
    ("LST nighttime", r"D:\FOREST FIRE MAPPING(INDIA)\LST_analysis\LST_Outputs\LST_Night_climatology_annualmean.tif", "hot"),
    ("Distance to roads", r"D:\FOREST FIRE MAPPING(INDIA)\Distance_Roads_Railways_Waterways_Analysis\Accessibility_Outputs\D1_Distance_to_Roads_native_1km.tif", "viridis"),
    ("Distance to railways", r"D:\FOREST FIRE MAPPING(INDIA)\Distance_Roads_Railways_Waterways_Analysis\Accessibility_Outputs\D2_Distance_to_Railways_native_1km.tif", "viridis"),
    ("Distance to waterways", r"D:\FOREST FIRE MAPPING(INDIA)\Distance_Roads_Railways_Waterways_Analysis\Accessibility_Outputs\D3_Distance_to_Waterways_native_1km.tif", "viridis"),
    ("Elevation", r"D:\FOREST FIRE MAPPING(INDIA)\Terrain_Elevation_Slope_Aspect_Analysis\Terrain_Outputs\T1_Elevation_native_1km.tif", "terrain"),
    ("Slope", r"D:\FOREST FIRE MAPPING(INDIA)\Terrain_Elevation_Slope_Aspect_Analysis\Terrain_Outputs\T2_Slope_native_1km.tif", "YlOrBr"),
]


def plot_panel(items, title, out_name, ncols=4):
    nrows = int(np.ceil(len(items) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(4.2 * ncols, 4.2 * nrows))
    axes = np.array(axes).reshape(-1)
    for ax, (name, path, cmap) in zip(axes, items):
        try:
            with rasterio.open(path) as src:
                arr = src.read(1, masked=True)
                bounds = src.bounds
            im = ax.imshow(arr, cmap=cmap, extent=[bounds.left, bounds.right, bounds.bottom, bounds.top])
            fig.colorbar(im, ax=ax, fraction=0.046, pad=0.02)
            ax.set_title(name, fontsize=10)
            ax.set_xticks([]); ax.set_yticks([])
        except Exception as e:
            ax.text(0.5, 0.5, f"{name}\n(load error: {e})", ha="center", va="center", transform=ax.transAxes, fontsize=8)
            ax.set_xticks([]); ax.set_yticks([])
    for ax in axes[len(items):]:
        ax.axis("off")
    fig.suptitle(title, fontsize=13)
    fig.tight_layout()
    out_path = f"{OUT_DIR}/{out_name}"
    fig.savefig(out_path, dpi=140, facecolor="white")
    print(f"Saved: {out_path}")


plot_panel(FIG2_ATMOSPHERIC_BIOPHYSICAL,
           "Spatial Distribution of Atmospheric and Biophysical Predictor Variables\n"
           "(reproduces Biswas et al. 2025, Fig. 2, using this study's own data)",
           "Fig02_Atmospheric_Biophysical_Maps.png")

plot_panel(FIG3_TEMP_HUMAN_TOPO,
           "Spatial Distribution of Temperature, Human-Interference, and Topographic Predictor Variables\n"
           "(reproduces Biswas et al. 2025, Fig. 3, using this study's own data)",
           "Fig03_Temperature_Human_Topographic_Maps.png")
