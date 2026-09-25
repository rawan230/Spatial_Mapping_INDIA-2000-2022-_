"""Insert a document-specific 'Audit update (2026-09-25)' block at the top of each root document.
Only statements that actually occur in a document are listed for it (regex-matched). Idempotent:
a document that already carries the block is skipped. Originals are in
_Archive_Unwanted_2026-09-25/pre_audit_document_snapshots/."""
import glob
import os
import re

ROOT = r"D:\FOREST FIRE MAPPING(INDIA)"
MARK = "<!-- AUDIT-UPDATE-2026-09-25 -->"
RULES = [
    (r"0\.9576|beats? (it|Biswas)", "**'Replicates Biswas's MaxEnt and beats it (0.9576 vs 0.879)'**: 0.9576 cannot be traced to any output, and the comparison is not valid (different population, predictors, labels and AUC definition). A Biswas-style reimplementation gives **0.893 ± 0.009** vs their 0.879 (moderately comparable)."),
    (r"temporal generali[sz]ation[^.]*(strong|advantage)|one clear generali", "**'Temporal generalisation (B3) is strong / CDR-PINN's advantage'**: withdrawn. Leak-free B3 is 0.893 (3 seeds), which is **below** covariate-free persistence baselines on the same cell-months (0.908; seasonal 0.930). RF with monthly covariates reaches 0.972."),
    (r"0\.602|0\.6017|each mechanism contributes|term-ablation", "**Term ablation (0.602 / 0.924 / 0.940)**: historical single-seed, fixed-budget runs, with no no-physics arm. Under one validated protocol with 3 seeds: **no physics 0.945, diffusion 0.924, diff + adv 0.939, full 0.939** (Track A). No physics configuration beats no physics on any track."),
    (r"B3 [ΔD]elta|physics[- ]vs[- ]no[- ]physics|no accuracy advantage", "**Physics vs no physics**: confirmed and extended (3 seeds, paired tests). Full − none: −0.006 (A, p < 0.02 for every seed), CI including 0 (B1, B2), −0.011 (B3)."),
    (r"same fold scheme|Track B1 exactly|0\.9498|0\.950\s*±", "**'RF 0.950 vs CDR 0.751 on the same fold scheme'**: not the same folds, grid, label or features. On CDR-PINO's own cells, splits and covariates, RF scores **0.974** (B1), 0.959 (B2) and 0.980 (A), vs CDR-PINO 0.719 / 0.570 / 0.939."),
    (r"0\.7510|0\.6187|0\.8960|0\.9398", "**CDR-PINO historical numbers** (0.9398, 0.7510 ± 0.0182, 0.6187 ± 0.0680, 0.8960) reproduce bit-exactly. Under the unified protocol (3 seeds), full CDR scores 0.939 / 0.719 / 0.570 / 0.893 (A / B1 / B2 / B3), and Track A and B1–B3 were separate models trained under different protocols."),
    (r"elevation dominat|near-total elevation|elevation over-reliance", "**Elevation dominance**: specific to CDR-PINO's 7-covariate model. With the full predictor set, removing terrain changes AUC by −0.0001; Biswas also ranks elevation low (2.4%)."),
    (r"Fisher", "**'Fisher–KPP reaction'**: a misnomer. The reaction ρσ(u)(1−σ(u)) acts on the logit u, which is equivalent to ds/dt = ρs²(1−s)² for s = σ(u)."),
    (r"size-matched|[Nn]egative supervision", "**'Size-matched negative sampling'**: not implemented. The data loss is a pos-weighted BCE over all training cells."),
    (r"w_i\s*←|gradient-norm-balanced", "**Loss-weight formula**: the code uses w_i ← 0.9 w_i + 0.1 · mean‖∇L‖/‖∇L_i‖ every 5 windows, not the multiplicative form stated."),
    (r"zero-shot|resolution[- ]independen|instance-wise", "**Zero-shot super-resolution, resolution independence and instance-wise fine-tuning**: not evaluated. Present them as future work only."),
    (r"national scalar|relative humidity \(derived\)", "**'Specific humidity is only a national scalar'**: incorrect. Specific humidity is a per-pixel predictor (v1 and v2); derived RH is an additional predictor."),
    (r"9\.86", "**'National forest cover 9.86–10.43%'**: computed over the download rectangle. For India only it is **18.3–19.3%**."),
    (r"0\.8322", "**Moran's I 0.8322**: reproduced, but 67% of the cells were row-mean-filled non-India cells. India-only (8×8 block means): **I = 0.9456**."),
    (r"147,206|3,731,210|1,063,120|234,318|2,545,287", "**Mann–Kendall significance counts**: reproduce, but the tests are invalid (MK on a smoothed or seasonal series). Seasonal Kendall + FDR gives NDVI 3,552,278 greening / 72,305 browning; LST day 2,435,163 cooling; night 2,080,747 warming; DTR 3,273,301 narrowing."),
    (r"636 raw|multiple-testing noise", "**'Air-temperature trend is multiple-testing noise'**: an artefact of MK on seasonal data. Seasonal Kendall gives 9,988 of 29,056 pixels FDR-significant."),
    (r"round\(\(lat|round\(\(lon", "**Fire rasterisation rule `round((lat−f)/e)`**: displaces 74.9% of points by one pixel (it rounds against the edge). The correct rule is `floor`. Correcting it raises RF AUC by +0.006 (all) / +0.011 (forest)."),
    (r"55 trainable|55 features|59 columns", "**Feature count**: the v1 parquet has **57** features (61 columns). v2 has 55 (a different set)."),
    (r"0\.01°|0\.01 deg|~0\.01", "**Grid spacing** is 1/120° (≈0.93 km), not 0.01°."),
    (r"anomaly[_ ]mean|anomaly-mean", "**Anomaly-mean features** (climate, LST, NDVI) are degenerate: with a 2001–2020 baseline they equal the residue of the 26 out-of-baseline months. v2 replaces them with climatological levels."),
    (r"LandCover_22Class|22-class|22 class", "**22 land-cover fractions** come from the 2020 map, inside the label window. v2 uses the 2001 map; the measured leakage effect is small."),
    (r"0\.9704|0\.9598", "**RF 0.9704 / MaxEnt 0.9598** reproduce exactly (v1, all pixels). v2: RF 0.975 all / **0.897 forest pixels** (the primary population, because forest fraction alone gives AUC 0.91)."),
    (r"150,000|150k", "**MaxEnt 150k subsample**: sensitivity from 50k to 500k gives AUC 0.964 → 0.969 (all) and 0.855 → 0.872 (forest); fit time grows as about n^1.6."),
    (r"-46\.9|−46\.9", "**−46.9 m elevation**: located at the Neyveli open-cast lignite mines; most likely real terrain, not an SRTM artefact."),
    (r"not preserved in the tracked", "**'Burned-area script not preserved'**: out of date. The scripts are tracked (commit 5b2c316)."),
]
done = []
for p in sorted(glob.glob(os.path.join(ROOT, "*.md"))):
    name = os.path.basename(p)
    if name in ("CLAUDE.md", "STUDY_METHODOLOGY_AND_GAPS.md"):
        continue
    txt = open(p, encoding="utf-8").read()
    if MARK in txt:
        continue
    hits = [msg for pat, msg in RULES if re.search(pat, txt, flags=re.I)]
    block = [MARK, "> ### Audit update (2026-09-25)",
             "> A full end-to-end audit recalculated every step from raw data and re-ran every model (`results/FULL_METHODOLOGY_AUDIT.md`).",
             "> Take paper numbers **only** from `results/FINAL_MANUSCRIPT_NUMBERS.md`. The pre-update copy of this file is in",
             f"> `_Archive_Unwanted_2026-09-25/pre_audit_document_snapshots/{name}`. Statements in this document superseded by the audit:",
             ">"]
    if hits:
        block += [f"> - {h}" for h in hits]
    else:
        block += ["> - No specific numbers in this document were superseded. Note the audit-wide conclusions: no physics configuration improves accuracy under controlled comparison; forest pixels are the primary evaluation population."]
    block += [MARK, ""]
    lines = txt.split("\n")
    ins = 1 if lines and lines[0].startswith("#") else 0
    new = "\n".join(lines[:ins] + ([""] if ins else []) + block + lines[ins:])
    open(p, "w", encoding="utf-8").write(new)
    done.append((name, len(hits)))
for n, k in done:
    print(f"{k:2d} superseded statements flagged  {n}")
