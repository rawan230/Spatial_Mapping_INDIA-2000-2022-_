# Data Provenance

Audit date 2026-09-24. Every entry was checked against the raw files on disk, not against the
documentation. Paths are relative to `D:\FOREST FIRE MAPPING(INDIA)` unless stated.

## 1. Raw sources

| Source | Product / version | Files on disk (verified) | Native grid | Period used | Notes found by the audit |
|---|---|---|---|---|---|
| Fire points | MODIS C6.1 FIRMS archive, `fire_archive_M-C61_772720.csv` (218 MB) | 1 CSV, 2,804,373 rows | points | 2000-11-01 – 2022-12-15 | Stage counts reproduce exactly (R1). Terra 130,885 / Aqua 410,660 forest points; 495,301 day / 46,244 night |
| Land cover | ESA-CCI LCCS v2.0.7cds (≤2015), C3S v2.1.1 (2016–2022), area subset 37.5N/98.6E/6.67S/67.5W | 27 NetCDF (1992–1995, 2000–2022) | 300 m (1/360°) | yearly, 2000–2022 | No year in the study period uses the nearest-year fallback. Historical "forest cover 9.86–10.43%" is computed over the whole download rectangle (incl. neighbours and ocean), not over India |
| NDVI | MOD13A3.061 1 km monthly (AppEEARS GeoTIFF: NDVI, pixel_reliability, VI_Quality) | 310 + 310 + 310 files (309 NDVI months) | 1/120° (3641 × 3504), EPSG:4326 | 266 months, 2000-11 – 2022-12 | **2007-03 and 2007-04 have no pixel-reliability file** (a 2025-03 file was downloaded instead; 12 × 2025 reliability files present). Step 2 used those months unfiltered; the CDR-PINO stack dropped them entirely |
| LST | MOD11A2.061 8-day (LST_Day_1km, LST_Night_1km, QC_Day, QC_Night) | 1,015 Day / 1,014 Night / 1,016 QC_Day / 1,016 QC_Night | 1/120° (3781 × 3536), origin 68.06E/37.55N | 1,013 complete composites in period | **2001-06-26** has QC layers only; **2016-02-18** has no Night layer; both silently excluded. The first composite (2000-10-31) is outside the period |
| Climate | FLDAS_NOAH01_C_GL_M.001 (MERRA-2 + CHIRPS forcing) | 266 NetCDF, 2000-11 – 2022-12, none missing | 0.1° (335 × 315 crop; 29,056 India px) | 266 months | Units verified from file attributes (R2) |
| DEM | SRTMGL3 (3″) mosaic, `India_SRTMGL3_DEM_mosaic.tif` | 1 GeoTIFF, 1.28 GB | 1/1200° | static | 0 is ambiguous (sea level vs void); see R6 |
| DEM cross-check | GMTED2010 7.5″ tile 30N090E (mean/min/max/…) | 6 GeoTIFF | 7.5″ | static | Overlaps only NE India (≥30°N, ≥90°E) |
| Roads / rail / water | Geofabrik OSM free GeoPackages, 6 Indian zones, 2022 | 6 gpkg (8.3 GB) | vector | 2022 snapshot | Stored outside the project folder (`C:\Users\Admin\Downloads\Distance(Roads, Station)@INDIA\Extracted`) — a reproducibility risk |
| Boundary | `India_State_Boundary.shp` (37 polygons, no .prj, EPSG:3857 metres); GADM 4.1 level 0/1 (sensitivity only) | shp | vector | — | Boundary sensitivity in R1 |
| Burned area | MCD64A1.061 (validation only, not a predictor) | GeoTIFFs in `Burn Area Data @INDIA/` | 500 m | 2000–2022 | Script provenance flagged as a gap (Part II C4) |

## 2. Derived datasets and lineage

```
fire_archive CSV ──R1──> all_forest_fires_2000_2022.csv (541,545; reproduced exactly)
        │                      │
        │                      ├─ F10 raster (half-pixel-shifted rule, E01) ──> parquet fire_ever (v1 label)
        │                      └─ containing-pixel rule ─────────────────────> y_all (v2 label)
MOD13A3 ──R4──> F1..F9 (v1) / v2 NDVI features ─┐
MOD11A2 ──R5──> LST/DTR anomaly-mean, MK τ (v1) / levels, SK τ (v2) ─┤
FLDAS   ──R2──> anomaly-mean, MK τ (v1) / levels, SK τ, Sen (v2) ────┼─> Integrated_FireRisk_Pixels.parquet (v1, 57 features)
ESA-CCI ──R3──> 22-class fractions 2020 (v1) / 2001 (v2), forest_frac_2001 ┤    FEATURE_TABLE_v2.parquet (v2, 57 features)
SRTM    ──R6──> elevation, slope (Horn), aspect ─────────────────────┤
OSM     ──R7──> distance to roads / railways / waterways ────────────┘
                     │
                     └─ 256×256 CDR-PINO stack (cdr_pinn_monthly_stacks.npz):
                        NDVI + FLDAS re-read from raw at 12 km; terrain/access resampled;
                        fire_ever_frac from the v1 parquet label; monthly labels re-binned (correct rule)
```

## 3. Versions of record

| Artefact | SHA-256 (first 16) | Role |
|---|---|---|
| `all_forest_fires_2000_2022.csv` | ca09d1e7655cc04f | label source (reproduced bit-exactly as a set) |
| `Integrated_FireRisk_Pixels.parquet` | 23b5af30a59d8c3f | v1 feature table (4,161,009 × 61) |
| `cdr_pinn_monthly_stacks.npz` | ea7828a5651557c2 | CDR-PINO input (256 × 256 × 266) |
| `cdr_pinn_full_cdr_standard_protocol.pt` | 9e4cfd45ddd05ae5 | Track A checkpoint (byte-identical to `cdr_pinn_full_cdr.pt`: the ablation's full-CDR checkpoint was overwritten) |

Step-repository commits at audit time: Step 1 `a01fadb`, Step 2 `1c274d6`, Step 3 `7e5d870`,
Step 4 `4dbe755`, Step 5a `e48a4a9`, Step 5b `c74ab6b`, Steps 6–7 `3fcc34c`, Step 8 `cd1d298`,
root `fb0d8aa`. All repositories were clean (no uncommitted changes).

## 4. Environments actually used

| Env | Python | Key versions | Used for |
|---|---|---|---|
| `wildfire_env` | 3.10.20 | torch 2.11.0+cu128, cupy 14.1.1, esda 2.7.0, libpysal 4.13 | Steps 1–3, 6 (the Step 6 notebook kernelspec is `wildfire_env`, not `firerisk-anaconda3` as CLAUDE.md states); audit R4 |
| base `anaconda3` (`firerisk-anaconda3`) | 3.12.7 | **torch 2.12.1+cpu (no CUDA)**, sklearn 1.9.0, elapid 1.0.4 | Steps 4, 5, 7; audit R1–R3, R5–R7, classical models |
| `cdr_pinn_env` | 3.11.15 | torch 2.11.0+cu128, CUDA 12.8 | **All CDR-PINO training (undocumented in CLAUDE.md)**; audit reproduction and unified runs |
