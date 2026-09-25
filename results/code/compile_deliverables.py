"""Compile the tabular audit deliverables from the result files (no hand-entered metrics)."""
import glob
import hashlib
import json
import os
import shutil
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from audit_common import RES, ROOT  # noqa: E402

F = os.path.join(RES, "final")
os.makedirs(F, exist_ok=True)
for d in ("FIGURE_DATA", "TABLE_DATA"):
    os.makedirs(os.path.join(F, d), exist_ok=True)
M = pd.read_csv(os.path.join(RES, "baseline", "CLASSICAL_METRICS.csv"))
S = pd.read_csv(os.path.join(RES, "cdr_pino", "SUMMARY_cdr_unified.csv"))
SEED = pd.read_csv(os.path.join(RES, "cdr_pino", "SEED_LEVEL_RESULTS_cdr.csv"))
FOR = pd.read_csv(os.path.join(RES, "cdr_pino", "FOREST_POPULATION_cdr.csv"))
PA = pd.read_csv(os.path.join(RES, "baseline", "PAIRED_trackA.csv"))
PB = pd.read_csv(os.path.join(RES, "baseline", "PAIRED_B1_B2.csv")) if os.path.exists(os.path.join(RES, "baseline", "PAIRED_B1_B2.csv")) else pd.DataFrame()
PP = pd.read_csv(os.path.join(RES, "ablation", "PAIRED_physics_vs_nophys.csv"))
PG = pd.read_csv(os.path.join(RES, "generalization", "PAIRED_cdr_vs_classical_same_cells.csv"))
BS = json.load(open(os.path.join(RES, "biswas_reference", "BISWAS_STYLE_BASELINE.json")))

# ---------------------------------------------------------------- FINAL_METRICS (every model x track x population)
rows = []
cls = M.copy()
cls["family"] = "classical"
for exp, g in cls.groupby("experiment"):
    for (tag, pop), s in g.groupby(["tag", "population"]):
        rows.append(dict(track=exp, model=tag, population=pop, n_units=len(s), n_test=int(s.n.sum()), prevalence=s.prevalence.mean(),
                         roc_auc=s.roc_auc.mean(), roc_auc_sd_units=s.roc_auc.std(ddof=0) if len(s) > 1 else np.nan,
                         ap=s.ap.mean(), brier=s.brier.mean(), ece=s.ece.mean(), precision=s.precision.mean(),
                         recall_sensitivity=s.recall_sensitivity.mean(), specificity=s.specificity.mean(), f1=s.f1.mean(),
                         threshold_rule="max-F1 on validation" if s.precision.notna().any() else "none (no validation split)",
                         grid="1 km" if not exp.startswith("bridge12") else "12 km (CDR-PINO cells)"))
for _, r in S.iterrows():
    fr = FOR[(FOR.track == r.track) & (FOR.config == r.config)]
    rows.append(dict(track=f"CDR_{r.track}", model=f"CDR-PINO_{r.config}", population="all", n_units=r.n_runs, prevalence=r.prevalence,
                     roc_auc=r.auc_mean, roc_auc_sd_units=r.auc_sd_across_seeds, ap=r.ap_mean, grid="12 km (CDR-PINO cells)",
                     threshold_rule="n/a (ranking metrics only)"))
    if len(fr):
        rows.append(dict(track=f"CDR_{r.track}", model=f"CDR-PINO_{r.config}", population="forest", n_units=len(fr),
                         prevalence=fr.forest_prev.mean(), roc_auc=fr.forest_auc.mean(), roc_auc_sd_units=fr.groupby("seed").forest_auc.mean().std(ddof=1),
                         ap=fr.forest_ap.mean(), grid="12 km (CDR-PINO cells)", threshold_rule="n/a"))
bsum = BS["replica_2020_presences_025deg"]["summary"]
rows.append(dict(track="Biswas-style 0.25 deg", model="MaxEnt LQHP beta1 (REIMPLEMENTATION)", population="presence vs background",
                 n_units=10, roc_auc=bsum["test_auc_mean"], roc_auc_sd_units=bsum["test_auc_sd"], grid="0.25 deg"))
FM = pd.DataFrame(rows)
FM.to_csv(os.path.join(F, "FINAL_METRICS.csv"), index=False)

# ---------------------------------------------------------------- FINAL_RESULTS (headline table)
def g(track, model, pop):
    s = FM[(FM.track == track) & (FM.model == model) & (FM.population == pop)]
    return (float(s.roc_auc.iloc[0]), float(s.ap.iloc[0]) if s.ap.notna().any() else np.nan) if len(s) else (np.nan, np.nan)
head = []
for label, track, model in [("RF v2 (55)", "trackA", "RF_v2"), ("RF Biswas-15", "trackA", "RF_biswas15"), ("MaxEnt v2", "trackA", "MaxEnt_v2"),
                            ("MaxEnt Biswas-15 (LQHP)", "trackA", "MaxEnt_biswas15_LQHP"), ("RF v1 historical label (repro split)", "repro", "RF_v1_histlabel_80_20"),
                            ("RF v2 B1", "B1", "RF_v2"), ("RF v2 B2", "B2", "RF_v2"), ("RF Biswas-15 B1", "B1", "RF_biswas15"),
                            ("RF v2 unseen years (static)", "B3static", "RF_v2"), ("Persistence null unseen years (1 km)", "B3static", "persistence_null_everburned_trainyears")]:
    a, ap = g(track, model, "all"); fa, fap = g(track, model, "forest")
    head.append(dict(result=label, grid="1 km", auc_all=a, ap_all=ap, auc_forest=fa, ap_forest=fap))
for tr in ("A", "B1", "B2", "B3"):
    for cfg in ("nophys", "full"):
        a, ap = g(f"CDR_{tr}", f"CDR-PINO_{cfg}", "all"); fa, fap = g(f"CDR_{tr}", f"CDR-PINO_{cfg}", "forest")
        head.append(dict(result=f"CDR-PINO {cfg} {tr} (3 seeds)", grid="12 km", auc_all=a, ap_all=ap, auc_forest=fa, ap_forest=fap))
for tr, mdl in (("bridge12_A", "RF_cdr7"), ("bridge12_B1", None), ("bridge12_B2", None), ("bridge12_B3", "null_climatological_frequency"),
                ("bridge12_B3", "null_seasonal_frequency"), ("bridge12_B3", "RF_monthly_cdr7_month")):
    if mdl is None:
        s = M[(M.experiment == tr) & M.tag.str.startswith("RF_cdr7_")]
        for pop in ("all", "forest"):
            pass
        head.append(dict(result=f"RF on CDR covariates {tr.split('_')[1]}", grid="12 km",
                         auc_all=s[s.population == "all"].roc_auc.mean(), ap_all=s[s.population == "all"].ap.mean(),
                         auc_forest=s[s.population == "forest"].roc_auc.mean(), ap_forest=s[s.population == "forest"].ap.mean()))
    else:
        a, ap = g(tr, mdl, "all"); fa, fap = g(tr, mdl, "forest")
        head.append(dict(result=f"{mdl} {tr.split('_')[1]}", grid="12 km", auc_all=a, ap_all=ap, auc_forest=fa, ap_forest=fap))
head.append(dict(result="Biswas-style reimplementation (0.25 deg, 2020 presences) test AUC", grid="0.25 deg", auc_all=bsum["test_auc_mean"]))
head.append(dict(result="Biswas et al. 2025 REPORTED test AUC (not comparable)", grid="0.25 deg", auc_all=0.879))
pd.DataFrame(head).to_csv(os.path.join(F, "FINAL_RESULTS.csv"), index=False)

# ---------------------------------------------------------------- SEED_LEVEL_RESULTS
seed_rows = SEED[["tag", "track", "config", "seed", "test_auc", "test_ap", "val_auc", "best_epoch", "epochs_run", "train_time_sec", "test_prevalence", "c_adv"]].copy()
seed_rows["family"] = "CDR-PINO"
mx = M[M.experiment == "maxent_n"].copy()
mx["seed"] = mx.tag.str.extract(r"seed(\d+)").astype(float); mx["family"] = "MaxEnt sample-size"
bs = pd.DataFrame(BS["replica_2020_presences_025deg"]["runs"])[["seed", "train_auc", "test_auc", "n_train_presence", "n_test_presence", "n_background"]]
bs["family"] = "Biswas-style reimplementation"
pd.concat([seed_rows, mx[["tag", "family", "seed", "population", "roc_auc", "ap", "train_rows", "fit_sec"]], bs], ignore_index=True).to_csv(
    os.path.join(F, "SEED_LEVEL_RESULTS.csv"), index=False)

# ---------------------------------------------------------------- ABLATION_RESULTS
ab = S[S.track.isin(["A", "B1", "B2", "B3"])].copy()
pp = PP.copy()
pp["diff"] = pp.delong_diff.fillna(pp.get("blockboot_diff"))
agg = pp.groupby(["track", "config"]).agg(mean_paired_diff_vs_nophys=("diff", "mean"), min_diff=("diff", "min"), max_diff=("diff", "max")).reset_index()
ab = ab.merge(agg, on=["track", "config"], how="left")
ab.to_csv(os.path.join(F, "ABLATION_RESULTS.csv"), index=False)
PP.to_csv(os.path.join(F, "TABLE_DATA", "paired_physics_vs_nophys_per_seed.csv"), index=False)

# ---------------------------------------------------------------- GENERALIZATION_RESULTS
gen = FM[FM.track.isin(["B1", "B2", "B3static", "bridge12_B1", "bridge12_B2", "bridge12_B3", "CDR_B1", "CDR_B2", "CDR_B3", "CDR_B3orig"])]
gen.to_csv(os.path.join(F, "GENERALIZATION_RESULTS.csv"), index=False)
PG.to_csv(os.path.join(F, "TABLE_DATA", "paired_cdr_vs_classical_same_cells.csv"), index=False)
if len(PB):
    PB.to_csv(os.path.join(F, "TABLE_DATA", "paired_B1_B2_blockbootstrap.csv"), index=False)

# ---------------------------------------------------------------- SENSITIVITY_RESULTS
sens = []
base = PA[(PA.model_A == "RF_v2")].set_index(["model_B", "population"])
for mb, what in (("RF_v2_lst005", "LST level at 0.05 deg (MOD11C3-resolution proxy)"), ("RF_v2_slopezt", "Slope: Zevenbergen-Thorne vs Horn"),
                 ("RF_v2_slope025", "Slope from 0.25 deg DEM"), ("RF_v2_minus_trends", "Remove Seasonal-Kendall/Sen trend group"),
                 ("RF_v2_minus_landcover", "Remove land-cover group"), ("RF_v2_minus_terrain", "Remove terrain group")):
    for pop in ("all", "forest"):
        if (mb, pop) in base.index:
            r = base.loc[(mb, pop)]
            sens.append(dict(factor=what, population=pop, baseline_auc=r.auc_A, variant_auc=r.auc_B, delta_variant_minus_baseline=-r["diff"],
                             ci95=f"[{-r.ci95_hi:.4f}, {-r.ci95_lo:.4f}]", test="paired DeLong, identical test pixels"))
for lab, what in (("RF_v2_label_conf30", "FIRMS confidence >= 30"), ("RF_v2_label_type0", "FIRMS type == 0"), ("RF_v2_label_conf30_type0", "confidence >= 30 and type == 0")):
    for pop in ("all", "forest"):
        v = M[(M.experiment == "trackA") & (M.tag == lab) & (M.population == pop)]; b0 = M[(M.experiment == "trackA") & (M.tag == "RF_v2") & (M.population == pop)]
        sens.append(dict(factor=f"Label filter: {what}", population=pop, baseline_auc=float(b0.roc_auc.iloc[0]), variant_auc=float(v.roc_auc.iloc[0]),
                         delta_variant_minus_baseline=float(v.roc_auc.iloc[0] - b0.roc_auc.iloc[0]), test="unpaired (different target labels)"))
for pop in ("all", "forest"):
    s = M[(M.experiment == "maxent_n") & (M.population == pop)].copy(); s["n"] = s.train_rows
    for n, gg in s.groupby("n"):
        sens.append(dict(factor=f"MaxEnt training rows = {int(n):,}", population=pop, variant_auc=gg.roc_auc.mean(),
                         variant_auc_sd_seeds=gg.roc_auc.std(ddof=1) if len(gg) > 1 else np.nan, fit_sec=gg.fit_sec.mean(), n_seeds=len(gg)))
R4 = json.load(open(os.path.join(RES, "recalculated", "R4_ndvi", "R4_report.json")))
R5 = json.load(open(os.path.join(RES, "recalculated", "R5_lst", "R5_report.json")))
R6 = json.load(open(os.path.join(RES, "recalculated", "R6_terrain", "R6_report.json")))
sens += [dict(factor="NDVI QA Good-only vs Good+Marginal (F1 correlation)", value=R4["F1_qa01_vs_qa0_corr"], note=f"pixel-months lost: {R4['frac_missing_pixel_months_qa0']:.3f} vs {R4['frac_missing_pixel_months_qa01']:.3f}"),
         dict(factor="NDVI 2007-03/04 QA gap fix (F1 correlation hist vs v2)", value=R4["F1_hist_vs_v2_corr"], note=f"max abs change {R4['F1_hist_vs_v2_max_abs_diff']:.3f}"),
         dict(factor="CVSI k* under historical / corrected / training-only labels", value=str(R4["F7_kstar"])),
         dict(factor="theta* under historical / corrected / training-only labels", value=str(R4["F9_theta"])),
         dict(factor="LST day level spatial variance retained at 0.05 deg", value=R5["day_variance_retained_at_0.05deg"]),
         dict(factor="LST night level spatial variance retained at 0.05 deg", value=R5["night_variance_retained_at_0.05deg"]),
         dict(factor="Slope single-feature AUC Horn / ZT / 1 km DEM / 0.25 deg DEM", value=f"{R6['slope_algorithm_sensitivity']['single_feature_auc_horn']:.4f} / {R6['slope_algorithm_sensitivity']['single_feature_auc_zt']:.4f} / {R6['slope_algorithm_sensitivity']['single_feature_auc_slope_from_1km_dem']:.4f} / {R6['slope_algorithm_sensitivity']['single_feature_auc_slope_from_025deg_dem']:.4f}"),
         dict(factor="B3 terminal-label leakage (full CDR, leaky - leak-free, mean of 3 seeds)", value=float(S[(S.track == "B3orig") & (S.config == "full")].auc_mean.iloc[0] - S[(S.track == "B3") & (S.config == "full")].auc_mean.iloc[0]))]
R1 = json.load(open(os.path.join(RES, "recalculated", "R1_fire_labels", "R1_report.json")))
sens.append(dict(factor="Boundary: points in state vs country vs GADM polygon", value=str(R1["boundary_sensitivity_points_in_bbox"]), note=str(R1["boundary_sensitivity_disagreement"])))
pd.DataFrame(sens).to_csv(os.path.join(F, "SENSITIVITY_RESULTS.csv"), index=False)

# ---------------------------------------------------------------- CONTRIBUTION_DECOMPOSITION
cd = []
def pa(a, b, pop):
    s = PA[(PA.model_A == a) & (PA.model_B == b) & (PA.population == pop)]
    return s.iloc[0] if len(s) else None
steps = [("B1: Biswas-15 predictors + MaxEnt", "trackA", "MaxEnt_biswas15_LQHP"), ("B1b: Biswas-15 predictors + RF", "trackA", "RF_biswas15"),
         ("B2: current (v2) predictors + MaxEnt", "trackA", "MaxEnt_v2"), ("B3: current (v2) predictors + RF", "trackA", "RF_v2"),
         ("CDR covariates (5 static) + RF, 1 km", "trackA", "RF_cdr7static")]
for name, tr, mdl in steps:
    a, ap = g(tr, mdl, "all"); fa, fap = g(tr, mdl, "forest")
    cd.append(dict(configuration=name, grid="1 km", population_note="4.16M pixels, prevalence 6.45% (all) / 1.20M forest pixels, 22.4%",
                   auc_all=a, auc_forest=fa, ap_all=ap, ap_forest=fap))
for tag, name in (("RF_cdr7", "CDR covariates (9, static summaries) + RF"), ("MaxEnt_cdr7", "CDR covariates + MaxEnt"), ("LogReg_cdr7", "CDR covariates + LogReg"),
                  ("RF_v2agg", "v2 predictors aggregated + RF")):
    a, ap = g("bridge12_A", tag, "all"); fa, fap = g("bridge12_A", tag, "forest")
    cd.append(dict(configuration=name, grid="12 km", population_note="CDR-PINO cells, Track A split, prevalence 42%", auc_all=a, auc_forest=fa, ap_all=ap, ap_forest=fap))
for cfg, name in (("nophys", "B4: CDR-PINO without physics"), ("diff", "B5: CDR-PINO + diffusion"), ("diffadv", "B6: + diffusion + advection"), ("full", "B7: full CDR-PINO")):
    a, ap = g("CDR_A", f"CDR-PINO_{cfg}", "all"); fa, fap = g("CDR_A", f"CDR-PINO_{cfg}", "forest")
    cd.append(dict(configuration=name, grid="12 km", population_note="CDR-PINO cells, Track A split, prevalence 42%; mean of 3 seeds", auc_all=a, auc_forest=fa, ap_all=ap, ap_forest=fap))
CD = pd.DataFrame(cd)
eff = [("Model family (RF - MaxEnt), Biswas-15, 1 km", pa("RF_biswas15", "MaxEnt_biswas15_LQHP", "all"), pa("RF_biswas15", "MaxEnt_biswas15_LQHP", "forest")),
       ("Model family (RF - MaxEnt), v2, 1 km", pa("RF_v2", "MaxEnt_v2", "all"), pa("RF_v2", "MaxEnt_v2", "forest")),
       ("Added predictors/engineering (v2 - Biswas-15), RF", pa("RF_v2", "RF_biswas15", "all"), pa("RF_v2", "RF_biswas15", "forest")),
       ("Added predictors (v2 - Biswas-15), MaxEnt", pa("MaxEnt_v2", "MaxEnt_biswas15_LQHP", "all"), pa("MaxEnt_v2", "MaxEnt_biswas15_LQHP", "forest")),
       ("Predictor restriction (v2 - CDR 5 static), RF", pa("RF_v2", "RF_cdr7static", "all"), pa("RF_v2", "RF_cdr7static", "forest"))]
for name, ra, rf in eff:
    CD = pd.concat([CD, pd.DataFrame([dict(configuration=f"EFFECT: {name}", grid="1 km", auc_all=ra["diff"] if ra is not None else np.nan,
                                           auc_forest=rf["diff"] if rf is not None else np.nan,
                                           population_note=f"paired DeLong 95% CI all [{ra.ci95_lo:.4f},{ra.ci95_hi:.4f}], forest [{rf.ci95_lo:.4f},{rf.ci95_hi:.4f}]" if ra is not None else "")])])
ph = PP.groupby(["track", "config"]).apply(lambda s: pd.Series(dict(d=s.delong_diff.fillna(s.blockboot_diff).mean()))).reset_index()
for _, r in ph.iterrows():
    CD = pd.concat([CD, pd.DataFrame([dict(configuration=f"EFFECT: physics ({r.config} - nophys), CDR track {r.track}", grid="12 km", auc_all=r.d,
                                           population_note="mean of 3 per-seed paired differences (DeLong for A/B3, block bootstrap for B1/B2)")])])
gb = PG[PG.classical == "RF_cdr7"]
if len(gb):
    CD = pd.concat([CD, pd.DataFrame([dict(configuration="EFFECT: model structure (full CDR-PINO - RF on same covariates/cells), Track A", grid="12 km",
                                           auc_all=gb[gb.cdr.str.startswith("A_full")].delong_diff.mean(), population_note="paired DeLong, 3 seeds")])])
CD.to_csv(os.path.join(F, "CONTRIBUTION_DECOMPOSITION.csv"), index=False)

# ---------------------------------------------------------------- EXPERIMENT_REGISTRY (classical + CDR)
reg = [json.loads(l) for l in open(os.path.join(RES, "audit", "experiment_registry.jsonl"), encoding="utf-8")]
er = []
for i, r in enumerate(reg):
    er.append(dict(EXPERIMENT_ID=f"CL{i:04d}", DATE=r["date"], PURPOSE=r["experiment"], REFERENCE_BASELINE="Biswas-15" if "biswas" in r["tag"] else "",
                   DATASET="FEATURE_TABLE_v2.parquet" if not r["experiment"].startswith("bridge12") else "cdr_pinn_monthly_stacks.npz (+v2 aggregated)",
                   FEATURE_VERSION=r.get("features"), CODE_COMMIT=r.get("root_commit"), MODEL=r.get("model"), ARCHITECTURE="",
                   HYPERPARAMETERS=json.dumps(r.get("hyperparameters")), SEED=r.get("subsample_seed", 42), TRAIN_SPLIT=r.get("split"),
                   VALIDATION_SPLIT="block-carved" if r["experiment"] in ("B1", "B2") else ("v2 random 15%" if r["experiment"] == "trackA" else ""),
                   TEST_SPLIT=r.get("split"), METRICS=json.dumps({p: {k: m.get(k) for k in ("roc_auc", "ap", "prevalence", "n")} for p, m in r["metrics"].items()}),
                   RUNTIME=r.get("fit_sec"), CHECKPOINT="not saved (sklearn/elapid models refit deterministically)",
                   OUTPUT=f"results/baseline/predictions/{r['experiment']}__{r['tag']}*.npz", STATUS="complete", NOTES=r.get("note", "")))
for f in sorted(glob.glob(os.path.join(RES, "cdr_pino", "unified", "track_*.json"))):
    js = json.load(open(f))
    for r in js["results"]:
        er.append(dict(EXPERIMENT_ID=f"CDR_{r['tag']}", DATE=js["meta"]["audit_date"], PURPOSE=f"CDR-PINO unified {r['tag'].split('_')[0]}",
                       DATASET="cdr_pinn_monthly_stacks.npz", FEATURE_VERSION="7 CDR covariates", CODE_COMMIT=js["meta"]["code_commit"][:7],
                       MODEL=f"CDR-PINO/{r['config']}", ARCHITECTURE="FNO2d width32 L4 modes16x16 + D/v/rho heads; 1,054,613 params",
                       HYPERPARAMETERS=json.dumps(js["meta"]["protocol"]), SEED=r["seed"], TRAIN_SPLIT=r["tag"], VALIDATION_SPLIT="see protocol",
                       TEST_SPLIT=r["tag"], METRICS=json.dumps(dict(test_auc=r["test_auc"], test_ap=r["test_ap"], val_auc=r["val_auc"], prevalence=r["test_prevalence"])),
                       RUNTIME=r["train_time_sec"], CHECKPOINT=r.get("checkpoint"), OUTPUT=f"results/cdr_pino/unified/pred_{r['tag']}.npz", STATUS="complete", NOTES=""))
for f in ("repro_validation_tracks_b1_b2_b3.json",):
    js = json.load(open(os.path.join(RES, "cdr_pino", "reproduction", f)))
    for tr, lst in js["results"].items():
        for r in lst:
            er.append(dict(EXPERIMENT_ID=f"REPRO_{r['tag']}", PURPOSE="historical CDR reproduction", MODEL="CDR-PINN historical", SEED=42,
                           METRICS=json.dumps(dict(roc_auc=r["roc_auc"], ap=r["ap"])), RUNTIME=r["train_time_sec"], STATUS="complete (bit-exact)"))
pd.DataFrame(er).to_csv(os.path.join(F, "EXPERIMENT_REGISTRY.csv"), index=False)

# ---------------------------------------------------------------- FINAL_CHECKPOINT_MANIFEST
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()
man = []
for p in sorted(glob.glob(os.path.join(ROOT, "Physics_Informed_FireRisk_Model", "CDR_PINN_Data", "*.pt"))) + \
         sorted(glob.glob(os.path.join(RES, "cdr_pino", "reproduction", "*.pt"))) + sorted(glob.glob(os.path.join(RES, "cdr_pino", "unified", "ckpt_*.pt"))):
    import torch
    ck = torch.load(p, map_location="cpu", weights_only=False)
    res = ck.get("result", {}) if isinstance(ck, dict) else {}
    man.append(dict(path=os.path.relpath(p, ROOT), sha256=sha(p), size_bytes=os.path.getsize(p), config=res.get("config"),
                    embedded_test_auc=res.get("test_roc_auc", res.get("test_auc", res.get("held_out_roc_auc"))),
                    epochs=res.get("n_epochs_run", res.get("epochs_run", res.get("n_epochs"))), best_epoch=res.get("best_epoch"), seed=res.get("seed"),
                    n_params=sum(v.numel() for v in ck["model_state"].values()) if isinstance(ck, dict) and "model_state" in ck else None))
MAN = pd.DataFrame(man)
dup = MAN.groupby("sha256").path.apply(list)
MAN["identical_to"] = MAN.sha256.map(lambda h: "; ".join(x for x in dup[h]) if len(dup[h]) > 1 else "")
MAN.to_csv(os.path.join(F, "FINAL_CHECKPOINT_MANIFEST.csv"), index=False)

# ---------------------------------------------------------------- FINAL_MODEL_CONFIGURATION
from models_classical import RF_HP, MX_HIST, MX_BISWAS
meta = json.load(open(os.path.join(RES, "cdr_pino", "unified", "meta.json")))
cfg = dict(random_forest=RF_HP, maxent_v2=dict(**MX_HIST, library="elapid 1.0.4", train_rows=150000, class_weights=100, transform="cloglog"),
           maxent_biswas_style=dict(**MX_BISWAS, max_iter=10000, background="all valid 0.25 deg cells (<10,000)", presence_split="75/25, 10 seeds"),
           cdr_pino=dict(meta["protocol"], architecture="FNO2d lift 8->32, 4 x (SpectralConv 16x16 + 1x1 skip, GELU), proj 32->32->1; D_net 2-12-12-1 tanh; rho_net 4-12-12-1 tanh; c_adv scalar",
                         n_params=1054613, loss="adaptive-balanced sum of data (pos-weighted BCE + LSE terminal), PDE residual MSE, BC |grad u|^2 on boundary ring, IC (identically 0)",
                         physics_configs=["nophys", "diff", "diffadv", "full"], seeds=[42, 43, 44], environment=f"cdr_pinn_env, torch {meta['torch']}, {meta['gpu']}"),
           splits=dict(trackA_1km="stratified 65/15/20 by corrected label, random_state=42", B1="3 folds, CDR-PINO 2 deg block permutation (seed 42), block-carved validation",
                       B2="6 KMeans regions on 12 km valid cells (random_state 42); 1 km pixels by nearest centroid", B3="held-out years 2000, 2008, 2009, 2015"),
           labels=dict(primary="containing-pixel rasterisation of 541,545 forest-fire points (fire_ever)", populations=["all valid pixels", "forest pixels (forest_frac_2001 > 0)"]))
json.dump(cfg, open(os.path.join(F, "FINAL_MODEL_CONFIGURATION.json"), "w"), indent=1)
print("compiled:", sorted(os.listdir(F)))
