"""Redraw Fig. 7 (Track A contribution panel) for the manuscript with non-overlapping labels.

Values are read unchanged from the audit's plotted data,
results/final/FIGURE_DATA/FigA_contribution_1km.csv (written by results/code/make_figures.py).
Only the tick labels and figure width differ from results/final/figures/FigA_contribution_1km.png.
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(ROOT, "results", "final", "FIGURE_DATA", "FigA_contribution_1km.csv")
OUT = os.path.join(HERE, "..", "figures", "FigA_contribution_1km.png")

ORDER = [("MaxEnt_biswas15_LQHP", "MaxEnt\nref. 15", "#4393c3"),
         ("RF_biswas15", "RF\nref. 15", "#2166ac"),
         ("RF_cdr7static", "RF\n5 static", "#92c5de"),
         ("MaxEnt_v2", "MaxEnt\n55 feat.", "#4393c3"),
         ("RF_v2", "RF\n55 feat.", "#2166ac")]

d = pd.read_csv(SRC)
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
fig, ax = plt.subplots(1, 2, figsize=(10, 3.4))
for i, pop in enumerate(("all", "forest")):
    vals = [float(d[(d.population == pop) & (d.model == m)].roc_auc.iloc[0]) for m, _, _ in ORDER]
    ax[i].bar(range(len(ORDER)), vals, color=[c for _, _, c in ORDER], width=0.7)
    ax[i].set_xticks(range(len(ORDER)))
    ax[i].set_xticklabels([lab for _, lab, _ in ORDER])
    ax[i].set_ylim(min(vals) - 0.03, max(vals) + 0.01)
    for k, v in enumerate(vals):
        ax[i].text(k, v + 0.002, f"{v:.3f}", ha="center", fontsize=8)
    ax[i].set_title("Track A, 1 km, " + ("all pixels (prev. 6.5%)" if pop == "all" else "forest pixels (prev. 22.4%)"))
    ax[i].set_ylabel("Test ROC-AUC (truncated axis)")
fig.tight_layout()
fig.savefig(OUT, dpi=200)
print("saved", OUT)
