"""Regenerate the audit figures from authoritative result files. Every figure's plotted data is
also written to results/final/FIGURE_DATA/. No figure mixes grids, populations or metrics in
one axis."""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from audit_common import RES  # noqa: E402

F = os.path.join(RES, "final"); FD = os.path.join(F, "FIGURE_DATA"); FG = os.path.join(F, "figures")
os.makedirs(FG, exist_ok=True)
FM = pd.read_csv(os.path.join(F, "FINAL_METRICS.csv"))
SEED = pd.read_csv(os.path.join(RES, "cdr_pino", "SEED_LEVEL_RESULTS_cdr.csv"))
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
C = {"cdr": "#b2182b", "rf": "#2166ac", "mx": "#4393c3", "null": "#7f7f7f", "lr": "#92c5de"}


def save(fig, name, data):
    fig.tight_layout(); fig.savefig(os.path.join(FG, f"{name}.png"), dpi=200); plt.close(fig)
    data.to_csv(os.path.join(FD, f"{name}.csv"), index=False)


# Fig A -- contribution decomposition at 1 km (Track A), separate panels per population
rows = [("MaxEnt\nBiswas-15", "MaxEnt_biswas15_LQHP", C["mx"]), ("RF\nBiswas-15", "RF_biswas15", C["rf"]),
        ("RF\nCDR 5 static", "RF_cdr7static", C["lr"]), ("MaxEnt\nv2 (55)", "MaxEnt_v2", C["mx"]), ("RF\nv2 (55)", "RF_v2", C["rf"])]
d = []
fig, ax = plt.subplots(1, 2, figsize=(9, 3.4))
for i, pop in enumerate(("all", "forest")):
    vals = [FM[(FM.track == "trackA") & (FM.model == m) & (FM.population == pop)].roc_auc.iloc[0] for _, m, _ in rows]
    ax[i].bar(range(len(rows)), vals, color=[c for *_, c in rows])
    ax[i].set_xticks(range(len(rows))); ax[i].set_xticklabels([r[0] for r in rows])
    lo = min(vals) - 0.03; ax[i].set_ylim(lo, max(vals) + 0.01)
    for k, v in enumerate(vals):
        ax[i].text(k, v + 0.002, f"{v:.3f}", ha="center", fontsize=8)
    ax[i].set_title(f"Track A, 1 km, {'all pixels (prev. 6.5%)' if pop == 'all' else 'forest pixels (prev. 22.4%)'}")
    ax[i].set_ylabel("Test ROC-AUC (truncated axis)")
    d += [dict(population=pop, model=m, roc_auc=v) for (_, m, _), v in zip(rows, vals)]
save(fig, "FigA_contribution_1km", pd.DataFrame(d))

# Fig B -- CDR-PINO physics ablation, seed-level, by track
tracks = ["A", "B1", "B2", "B3"]
cfgs = ["nophys", "diff", "diffadv", "full"]
fig, ax = plt.subplots(1, 4, figsize=(11, 3.2))
d = []
for i, t in enumerate(tracks):
    s = SEED[SEED.track == t]
    for j, c in enumerate(cfgs):
        v = s[s.config == c].groupby("seed").test_auc.mean()
        if len(v):
            ax[i].scatter([j] * len(v), v.values, color=C["cdr"] if c != "nophys" else "k", s=18)
            ax[i].plot([j - .2, j + .2], [v.mean()] * 2, color="k", lw=1)
            d += [dict(track=t, config=c, seed=int(sd), test_auc=float(val)) for sd, val in v.items()]
    ax[i].set_xticks(range(4)); ax[i].set_xticklabels(["none", "D", "D+A", "D+A+R"]); ax[i].set_title(f"Track {t}")
ax[0].set_ylabel("Test ROC-AUC per seed\n(B1/B2: mean over folds)")
ax[2].text(1.5, ax[2].get_ylim()[0], "D, D+A not run on B2", ha="center", va="bottom", fontsize=7, color="grey")
fig.suptitle("CDR-PINO physics-term ablation, identical protocol, 3 seeds (12 km cells)", fontsize=9)
save(fig, "FigB_cdr_ablation_seeds", pd.DataFrame(d))

# Fig C -- same-cells comparison at 12 km: CDR-PINO vs classical models on CDR covariates
d = []
fig, ax = plt.subplots(1, 3, figsize=(10, 3.2))
for i, t in enumerate(["A", "B1", "B2"]):
    items = [("CDR\nfull", FM[(FM.track == f"CDR_{t}") & (FM.model == "CDR-PINO_full") & (FM.population == "all")].roc_auc.iloc[0], C["cdr"]),
             ("CDR no\nphysics", FM[(FM.track == f"CDR_{t}") & (FM.model == "CDR-PINO_nophys") & (FM.population == "all")].roc_auc.iloc[0], "#ef8a62")]
    br = pd.read_csv(os.path.join(RES, "baseline", "CLASSICAL_METRICS.csv"))
    br = br[(br.experiment == f"bridge12_{t}") & (br.population == "all")]
    for lab, pre, col in (("LogReg", "LogReg_cdr7", C["lr"]), ("MaxEnt", "MaxEnt_cdr7", C["mx"]), ("RF", "RF_cdr7", C["rf"])):
        items.append((lab, br[br.tag.str.startswith(pre)].roc_auc.mean(), col))
    ax[i].bar(range(len(items)), [v for _, v, _ in items], color=[c for *_, c in items])
    ax[i].set_xticks(range(len(items))); ax[i].set_xticklabels([n for n, *_ in items], fontsize=8)
    ax[i].set_ylim(0.5, 1.0); ax[i].axhline(0.5, color="grey", lw=.5); ax[i].set_title(f"Track {t} (same cells, splits, covariates)")
    for k, (_, v, _) in enumerate(items):
        ax[i].text(k, v + 0.005, f"{v:.3f}", ha="center", fontsize=7)
    d += [dict(track=t, model=n.replace("\n", " "), roc_auc=v) for n, v, _ in items]
ax[0].set_ylabel("Test ROC-AUC, all 12 km cells (prev. ~41%)")
save(fig, "FigC_same_cells_cdr_vs_classical", pd.DataFrame(d))

# Fig D -- B3 unseen years vs persistence nulls (identical cell-months)
br = pd.read_csv(os.path.join(RES, "baseline", "CLASSICAL_METRICS.csv"))
b3 = br[(br.experiment == "bridge12_B3") & (br.population == "all")].set_index("tag").roc_auc
items = [("CDR-PINO full\n(leak-free)", FM[(FM.track == "CDR_B3") & (FM.model == "CDR-PINO_full") & (FM.population == "all")].roc_auc.iloc[0], C["cdr"]),
         ("CDR-PINO\nno physics", FM[(FM.track == "CDR_B3") & (FM.model == "CDR-PINO_nophys") & (FM.population == "all")].roc_auc.iloc[0], "#ef8a62"),
         ("Null: cell fire\nfrequency", b3["null_climatological_frequency"], C["null"]), ("Null: same-month\nfrequency", b3["null_seasonal_frequency"], C["null"]),
         ("RF monthly\ncovariates", b3["RF_monthly_cdr7"], C["rf"]), ("RF monthly\n+ month", b3["RF_monthly_cdr7_month"], C["rf"])]
fig, ax = plt.subplots(figsize=(7, 3.2))
ax.bar(range(len(items)), [v for _, v, _ in items], color=[c for *_, c in items]); ax.set_ylim(0.85, 0.98)
ax.set_xticks(range(len(items))); ax.set_xticklabels([n for n, *_ in items], fontsize=8)
for k, (_, v, _) in enumerate(items):
    ax.text(k, v + 0.002, f"{v:.3f}", ha="center", fontsize=8)
ax.set_ylabel("ROC-AUC, held-out years 2000/2008/2009/2015\n(cell-months, prev. 2.46%; truncated axis)")
save(fig, "FigD_B3_vs_nulls", pd.DataFrame([dict(model=n.replace("\n", " "), roc_auc=v) for n, v, _ in items]))

# Fig E -- MaxEnt training-size sensitivity
mx = br[br.experiment == "maxent_n"].copy(); mx["n"] = mx.train_rows
fig, ax = plt.subplots(1, 2, figsize=(8, 3))
for pop, col in (("all", C["mx"]), ("forest", "#053061")):
    s = mx[mx.population == pop].groupby("n").roc_auc.agg(["mean", "std"])
    ax[0].errorbar(s.index / 1e3, s["mean"], yerr=s["std"].fillna(0), marker="o", color=col, label=pop, capsize=2)
ax[0].set_xlabel("MaxEnt training rows (thousands)"); ax[0].set_ylabel("Test ROC-AUC"); ax[0].legend(title="population")
t = mx[mx.population == "all"].groupby("n").fit_sec.mean()
ax[1].loglog(t.index, t.values, "o-", color="k"); ax[1].set_xlabel("training rows"); ax[1].set_ylabel("fit time (s)")
slope = np.polyfit(np.log(t.index), np.log(t.values), 1)[0]; ax[1].set_title(f"fit time ~ n^{slope:.2f}")
save(fig, "FigE_maxent_sample_size", mx[["tag", "population", "n", "roc_auc", "ap", "fit_sec"]])

# Fig F -- Biswas permutation importance vs Biswas-style re-implementation (same method, same variables)
bs = json.load(open(os.path.join(RES, "biswas_reference", "BISWAS_STYLE_BASELINE.json")))
rep = bs["biswas_reported"]["permutation_importance_pct"]; ours = bs["replica_2020_presences_025deg"]["runs"][0]["permutation_importance_pct"]
names = list(rep.keys())
fig, ax = plt.subplots(figsize=(8, 4))
y = np.arange(len(names))
ax.barh(y + .2, [rep[n] for n in names], .4, label="Biswas et al. 2025 (reported)", color="#999999")
ax.barh(y - .2, [ours[n] for n in names], .4, label="Biswas-style re-implementation (this study's data)", color=C["mx"])
ax.set_yticks(y); ax.set_yticklabels(names); ax.invert_yaxis(); ax.set_xlabel("MaxEnt permutation importance (%)"); ax.legend(fontsize=8)
save(fig, "FigF_biswas_importance_comparison", pd.DataFrame(dict(variable=names, biswas_reported_pct=[rep[n] for n in names], reimplementation_pct=[ours[n] for n in names])))

# Fig G -- trained CDR-PINO term magnitudes
d = []
for c in cfgs:
    fp = os.path.join(RES, "cdr_pino", f"term_magnitudes_unified_A_{c}_s42.json")
    if os.path.exists(fp):
        s = json.load(open(fp))["summary"]
        d.append(dict(config=c, median_abs_dudt=s["dudt"]["median"], diffusion=s["diff"]["mean"], advection=s["adv"]["mean"],
                      reaction=s["react"]["mean"], rms_residual=s["resid"]["mean"]))
D = pd.DataFrame(d)
fig, ax = plt.subplots(figsize=(7, 3.2))
x = np.arange(len(D))
for k, (col, lab) in enumerate((("median_abs_dudt", "|du/dt| (median)"), ("diffusion", "|D lap u|"), ("advection", "|v.grad u|"), ("reaction", "|R|"), ("rms_residual", "RMS residual"))):
    ax.bar(x + (k - 2) * .16, D[col], .16, label=lab)
ax.set_yscale("log"); ax.set_xticks(x); ax.set_xticklabels(["none", "D", "D+A", "D+A+R"]); ax.legend(fontsize=7, ncol=2)
ax.set_ylabel("mean magnitude over cells x 265 months (log)"); ax.set_title("Trained CDR-PINO (Track A, seed 42): full-CDR residual terms")
save(fig, "FigG_cdr_term_magnitudes", D)

# Fig H -- final v2 susceptibility map (quantile classes)
mp = os.path.join(F, "maps", "Susceptibility_RF_v2_5class_quantile.tif")
if os.path.exists(mp):
    import rasterio
    with rasterio.open(mp) as s:
        a = s.read(1); b = s.bounds
    fig, ax = plt.subplots(figsize=(6, 6.5))
    from matplotlib.colors import ListedColormap
    im = ax.imshow(a, cmap=ListedColormap(["#1a9850", "#a6d96a", "#fee08b", "#f46d43", "#a50026"]), extent=(b.left, b.right, b.bottom, b.top), interpolation="nearest")
    cb = fig.colorbar(im, ax=ax, ticks=[1.4, 2.2, 3, 3.8, 4.6], shrink=.6); cb.ax.set_yticklabels(["Very low", "Low", "Moderate", "High", "Very high"])
    ax.set_title("Forest-fire susceptibility, RF v2 (quantile classes of a relative score)", fontsize=8); ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
    vals, cnt = np.unique(a[np.isfinite(a)], return_counts=True)
    save(fig, "FigH_final_map_RF_v2", pd.DataFrame(dict(class_=vals, pixels=cnt)))
print("figures:", sorted(os.listdir(FG)))
