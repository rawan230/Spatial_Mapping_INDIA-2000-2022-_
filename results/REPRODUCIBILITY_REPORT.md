# Reproducibility Report

## 1. What was reproduced, and how exactly

| Result | Historical | Re-run | Agreement |
|---|---|---|---|
| Forest-fire point set | 541,545 | 541,545 | identical set |
| FLDAS 14 features | parquet | from 266 raw NetCDF | r = 1.000000, max diff ≤ 8.5e-5 |
| Land cover 2020 (22 classes), forest 2001 | parquet | from raw LCCS | max diff 0.0 |
| NDVI F1–F4, F7 | GeoTIFFs | from 266 raw months | r ≥ 0.99999999, max diff ≤ 1.2e-6 |
| NDVI F6 (MK) | GeoTIFF | re-run | r = 0.99999998 |
| LST MK τ; anomaly means | parquet | from 1,013 composites | exact; anomaly means exact under composite-weighted climatology |
| Terrain; distances | parquet | from DEM / OSM | r ≥ 0.99999 (aspect 0.9986, wraparound) |
| RF Track A (v1) | 0.9704 / 0.7011 | 0.9704 / 0.7011 | exact |
| MaxEnt Track A (v1) | 0.9598 / 0.6275 | 0.9598 / 0.6275 | exact |
| RF spatial CV (v1) | 0.9459 / 0.9527 / 0.9508 | same | exact |
| CDR-PINO Track A | 0.9398 / 0.9223 | same | bit-exact |
| CDR-PINO B1 / B2 / B3 | 0.7510 ± 0.0182 / 0.6187 ± 0.0680 / 0.8960 | same, fold by fold | bit-exact |
| Historical term ablation (full CDR row) | 0.9397 | — | **not reproducible from a checkpoint**: file overwritten by the Track A checkpoint |

## 2. Determinism

- **CDR-PINO:** given the same stacks, seed and GPU (RTX PRO 4500, torch 2.11.0+cu128), training was
  bit-reproducible in this environment. Seed variation (3 seeds) is 0.001–0.013 AUC SD depending on
  the track (`final/SEED_LEVEL_RESULTS.csv`).
- **RF:** deterministic to about 1e-15 (multi-threaded summation).
- **MaxEnt (elapid):** subsample seed SD ≤ 0.0004 AUC.

## 3. How to reproduce the audit

Environments: `wildfire_env` (NDVI R4), base anaconda3 (R1–R3, R5–R7, classical models, analysis) and
`cdr_pinn_env` (CDR-PINO). Run from `results/code/` in this order:

```
python recalc_01_fire_labels.py          # ~5 min
python recalc_02_fldas.py                # ~10 min
python recalc_03_lulc.py                 # ~2 min
wildfire_env python recalc_04_ndvi.py    # ~60 min (24 cores)
python recalc_05_lst.py                  # ~40 min
python recalc_06_terrain.py              # ~15 min
python recalc_07_access.py               # ~2.5 h (single-threaded vector ops)
python build_v2_table.py
cdr_pinn_env python repro_historical_cdr.py all   # ~45 min GPU
cdr_pinn_env python cdr_unified_runner.py         # ~7 h GPU (102 runs)
python models_classical.py repro|trackA|B1|B2|B3|B1hist|maxent_n   # ~16 h CPU in total
python bridge_12km.py ; python biswas_style_baseline.py
python analyze_classical.py ; python analyze_cdr.py
cdr_pinn_env python cdr_term_magnitudes.py <ckpt> <tag>
python compile_deliverables.py ; python make_feature_dictionary.py ; python make_final_map.py ; python make_figures.py
```

Unit tests: `trend_stats.py` (MK, Seasonal Kendall with ties, seasonal Sen, BH-FDR) and
`eval_utils.delong_paired` were checked against brute-force implementations; a CPU smoke test of the
unified CDR runner was run before the GPU run.

## 4. Remaining reproducibility risks

1. **OSM source location:** the source data lives in `C:\Users\Admin\Downloads\...`, outside the
   project; it should be moved or documented with checksums.
2. **Undocumented CDR environment:** `cdr_pinn_env` is not in CLAUDE.md, and the base env's torch is
   CPU-only.
3. **Burned-area validation:** it was not re-extracted from the raw MCD64A1 files in this audit;
   the correlations were recomputed from the saved annual series.
4. **SHAP** could not be computed (`shap` fails to import; its numba build needs NumPy ≤ 2.0).
5. **The Biswas comparison values** come from the user's PDF, which cannot be redistributed; the page
   numbers are given for verification.
