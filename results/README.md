# Audit results (2026-09-24/25)

Start with **`FULL_METHODOLOGY_AUDIT.md`**. No historical project file was modified; everything the
audit produced is in this folder.

| Deliverable (brief item) | Location |
|---|---|
| 1 FULL_METHODOLOGY_AUDIT.md | `./` |
| 2 BISWAS_REFERENCE_AUDIT.md | `biswas_reference/` |
| 3 BISWAS_VS_CURRENT_COMPARISON.md | `./` (contribution matrix + manuscript Table X) |
| 4–6 BISWAS_FEATURE_PARITY / DATA_SOURCE_COMPARISON / RESULT_COMPARISON.csv | `biswas_reference/` |
| 7 CONTRIBUTION_DECOMPOSITION.csv | `final/` |
| 8 GAP_CLOSURE_MATRIX.csv | `audit/` |
| 9 NUMERICAL_RECALCULATION_AUDIT.csv | `audit/` |
| 10 EQUATION_CODE_AUDIT.csv | `audit/` |
| 11 MANUSCRIPT_NUMBER_AUDIT.csv | `audit/` |
| 12 BISWAS_CLAIM_AUDIT.csv | `audit/` |
| 13 EXPERIMENT_REGISTRY.csv | `final/` (raw log: `audit/experiment_registry.jsonl`) |
| 14 METHODOLOGY_CHANGELOG.md | `./` |
| 15 DATA_PROVENANCE.md | `audit/` |
| 16 REPRODUCIBILITY_REPORT.md | `./` |
| 17–23 FINAL_RESULTS, FINAL_METRICS, SEED_LEVEL_RESULTS, ABLATION_RESULTS, GENERALIZATION_RESULTS, SENSITIVITY_RESULTS, FINAL_FEATURE_DICTIONARY | `final/` |
| 24 FINAL_MODEL_CONFIGURATION.json | `final/` |
| 25 FINAL_CHECKPOINT_MANIFEST.csv | `final/` |
| 26–27 FIGURE_DATA / TABLE_DATA | `final/` (figures in `final/figures/`) |
| 28 FINAL_MANUSCRIPT_NUMBERS.md | `./` and `manuscript_ready/` |

Other folders:

| Folder | Contents |
|---|---|
| `historical/` | artefact hashes |
| `recalculated/` | R1–R7 raw-data recalculations, the v2 feature table, and feature sets. The `R4_ndvi/tmp` and `R5_lst/tmp` scratch arrays are ~39 GB and can be regenerated |
| `baseline/` | classical models: predictions, importance, paired tests |
| `cdr_pino/` | reproduction, unified runs (checkpoints, predictions), term magnitudes |
| `ablation/`, `generalization/`, `sensitivity/` | the corresponding tables |
| `final/maps/` | v2 susceptibility GeoTIFFs |
| `code/` | every script used |
| `logs/` | run logs |
