"""Reproduces Biswas et al. (2025) Fig. 10 format -- Jackknife test as horizontal
bar charts per variable (without-X / only-X / all-variables AUC) -- using this
study's own real Jackknife retraining results for CDR-PINN (14 retrains + baseline,
Physics_Informed_FireRisk_Model/CDR_PINN_Data/cdr_pinn_jackknife_results.json).

Biswas et al.'s own Fig. 10 has 3 panels (train-data jackknife, test-data jackknife,
AUC-on-test-data jackknife) because MaxEnt reports separate training-gain and
test-AUC jackknife metrics. This study's Jackknife test only ever measured
held-out test AUC (a single, honest number per config, not a separate training-gain
metric) -- reproduced here as one panel, captioned to state that difference
explicitly rather than fabricating a second metric that was never computed."""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

JACKKNIFE_JSON = r"D:\FOREST FIRE MAPPING(INDIA)\Physics_Informed_FireRisk_Model\CDR_PINN_Data\cdr_pinn_jackknife_results.json"
OUT_PATH = r"D:\FOREST FIRE MAPPING(INDIA)\Biswas_Comparison_Figures\Fig10_Jackknife_BarChart.png"

with open(JACKKNIFE_JSON) as f:
    d = json.load(f)

all_auc = d["all"]["auc"]
covariates = ["elevation", "ndvi_f1", "slope", "dist_roads", "forest_frac", "dryness", "ndvi_anomaly"]
without_auc = [d[f"without_{c}"]["auc"] for c in covariates]
only_auc = [d[f"only_{c}"]["auc"] for c in covariates]

order = np.argsort(only_auc)  # ascending, so highest (most important alone) plots at top
covariates = [covariates[i] for i in order]
without_auc = [without_auc[i] for i in order]
only_auc = [only_auc[i] for i in order]

y = np.arange(len(covariates))
fig, ax = plt.subplots(figsize=(9, 6))
ax.barh(y - 0.2, without_auc, height=0.38, color="#4c72b0", label="Without variable")
ax.barh(y + 0.2, only_auc, height=0.38, color="#dd8452", label="With only variable")
ax.axvline(all_auc, color="#2ca02c", linestyle="--", linewidth=2, label=f"With all variables (AUC={all_auc:.4f})")
ax.set_yticks(y)
ax.set_yticklabels(covariates)
ax.set_xlabel("Held-out test ROC-AUC")
ax.set_xlim(0, 1)
ax.set_title("CDR-PINN Jackknife Test of Variable Importance\n"
             "(reproduces Biswas et al. 2025 Fig. 10 format -- test-AUC panel only, see caption)")
ax.legend(loc="lower right")
ax.grid(alpha=0.3, axis="x")

fig.text(0.01, 0.01,
         "Note: Biswas et al.'s Fig. 10 has 3 panels (training-data jackknife, test-data jackknife, "
         "test-AUC jackknife) because MaxEnt reports a separate training-gain metric. This study's "
         "Jackknife retraining only ever measured held-out test AUC (a single honest metric per "
         "configuration) -- shown here as one panel rather than fabricating a training-gain analogue "
         "that was never computed.", fontsize=7, wrap=True, style="italic")

fig.tight_layout(rect=[0, 0.05, 1, 1])
fig.savefig(OUT_PATH, dpi=150, facecolor="white")
print(f"Saved: {OUT_PATH}")
