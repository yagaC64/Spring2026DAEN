# Terrain Feature Pack v1

## Purpose

Terrain Feature Pack v1 adds municipio-aligned terrain and geographic indicators that can improve flood relevance and spatial accuracy without changing the existing scoring stack by default.

The design priorities are:

- explainable formulas
- local-first reproducibility
- public/script-friendly sources where practical
- graceful degradation when optional datasets are absent
- compatibility with the staged notebook pipeline already used in this repo

## Stage Placement

- Suggested notebook stage: `JupyterNotebooks/index_pipeline/02_feature_engineering/15_build_terrain_features_pr.ipynb`
- Output root: `outputs/index_pipeline/15_terrain/`
- Status: optional sidecar feature-engineering stage

This stage does not rewrite the current scoring flow. It produces terrain fields that are ready for future use in hazard and vulnerability logic.

## Minimum v1 Outputs

At minimum, the stage writes:

- `outputs/index_pipeline/15_terrain/municipio_terrain_features.csv`
- `outputs/index_pipeline/15_terrain/municipio_terrain_features.parquet`
- `outputs/index_pipeline/15_terrain/municipio_terrain_features.geojson`
- `outputs/index_pipeline/15_terrain/README.md`
- `outputs/index_pipeline/15_terrain/run_metadata.json`

## Expected Fields

Required output columns:

- `municipio_id`
- `municipio_name`
- `elevation_mean`
- `slope_mean`
- `slope_p90`
- `local_relief`
- `wetness_proxy`
- `distance_to_stream_km`
- `coastal_inundation_flag`
- `coastal_inundation_depth_mean`
- `soil_runoff_potential`
- `land_cover_runoff_modifier`
- `terrain_data_completeness`
- `terrain_confidence_score`
- `config_version`
- `run_timestamp_utc`

Implementation may include additional helper fields such as `municipio_key`.

## Source Strategy

| Theme | Preferred Source | Retrieval Mode | v1 Handling |
| --- | --- | --- | --- |
| Municipio boundaries | Census TIGER county boundaries filtered to Puerto Rico (`STATEFP=72`) | Script-retrievable | Automated fetch if local file absent |
| DEM / elevation | USGS 3DEP or NOAA DEM GeoTIFF / IMG | Usually manual download | Local-file discovery via config globs, recursive raster discovery |
| Streams | Local NHD or equivalent hydrography vector | Manual or project-provided | Optional local vector input with support for `.gpkg`, `.geojson`, `.shp`, `.zip`, and `.gdb` |
| Coastal inundation | NOAA Sea Level Rise Viewer rasters or polygons | Usually manual download | Optional local raster/vector input with support for `.tif`, `.img`, `.gpkg`, `.geojson`, `.shp`, `.zip`, and `.gdb` |
| Soil runoff potential | gSSURGO / SSURGO-derived local layers | Usually manual download | Optional local vector/raster input, including common FileGDB packaging |
| Land cover runoff modifier | NOAA C-CAP or equivalent raster | Manual download | Optional local raster input with auto-detection for C-CAP and NLCD-style class codes |

## Local Data Discovery

All terrain inputs are discovered through `config/terrain_spec_v1.yaml`.

Expected staging root:

- `data/staging/terrain/`

Expected subfolders:

- `data/staging/terrain/boundaries/`
- `data/staging/terrain/dem/`
- `data/staging/terrain/streams/`
- `data/staging/terrain/coastal/`
- `data/staging/terrain/soils/`
- `data/staging/terrain/land_cover/`

The implementation does not hardcode user-specific paths. It resolves relative glob patterns from the repo root.

The guided notebook also exposes a source-inventory step before execution so users can confirm which files were discovered and which remaining steps are still manual.

## CRS Assumptions

- Working CRS: `EPSG:32161`
- Reason: projected CRS appropriate for Puerto Rico/Virgin Islands local distance and area work
- Municipio boundaries and optional vector inputs are reprojected to the working CRS before area/distance calculations
- Rasters are processed in their native CRS when possible, but are read through a projected view when needed for terrain derivatives

## Feature Definitions

### 1. Elevation Mean

- Definition: mean DEM value within municipio polygon
- Unit: meters above datum of source DEM

### 2. Slope Mean

- Definition: mean slope derived from DEM
- Method: slope from horizontal and vertical DEM gradients
- Unit: degrees

### 3. Slope P90

- Definition: 90th percentile of slope values within municipio
- Use: captures steep terrain tails better than a simple mean

### 4. Local Relief

- Definition: municipio max DEM minus municipio min DEM
- Unit: meters

### 5. Wetness Proxy

v1 uses an explainable local topographic wetness proxy rather than a full hydrologic flow accumulation model.

Formula:

- `local_depression = max(local_mean_elevation - elevation, 0)`
- `wetness_proxy_raw = local_depression / tan(max(slope_deg, min_slope_deg))`

Interpretation:

- higher values indicate flatter areas that are lower than their nearby surroundings
- this is a screening proxy, not a full hydraulic model

### 6. Distance to Stream

v1 method:

- nearest distance from municipio centroid to nearest stream geometry

Unit:

- kilometers

Why:

- simple, explainable, and robust when a stream vector is available

Known limitation:

- centroid distance is less precise than a full municipio-wide mean distance-to-stream surface

### 7. Coastal Inundation

Raster mode:

- zonal mean inundation depth from local NOAA SLR or equivalent raster

Vector mode:

- municipio overlap with inundation polygon footprint

Fields:

- `coastal_inundation_flag`
- `coastal_inundation_depth_mean`

### 8. Soil Runoff Potential

Preferred v1 mapping:

- Hydrologic Soil Group A -> `0.10`
- B -> `0.35`
- C -> `0.70`
- D -> `1.00`

Combined groups such as `A/D` are mapped by averaging component scores.

### 9. Land Cover Runoff Modifier

Land-cover classes are mapped to runoff-modifier scores through a config table.

Interpretation:

- higher values indicate surfaces or cover types more likely to increase runoff intensity
- exact mapping is versioned in config for auditability

## Aggregation Method

- Raster-derived features use polygon zonal statistics at municipio level
- Soil vector overlays use area-weighted means
- Stream distance uses centroid-to-nearest-stream distance
- All municipio outputs include run timestamp and config version

## Missing Data Behavior

Optional datasets do not hard-fail the stage.

Instead, the implementation:

- logs a warning
- leaves affected fields as null
- records missing source information in `run_metadata.json`
- lowers completeness and confidence scores accordingly

## Manual Download vs Automation Notes

Fully or mostly script-retrievable in v1:

- Puerto Rico municipio boundaries from Census TIGER

Expected manual/local download in v1:

- DEM GeoTIFF or IMG tiles from USGS 3DEP or NOAA DEM sources
- NOAA SLR coastal rasters/polygons
- gSSURGO / SSURGO soil data
- NOAA C-CAP or NLCD Puerto Rico land-cover rasters
- project-approved stream vectors if not already curated

Automation added to reduce friction in v1:

- automatic staging-folder creation
- recursive source discovery beneath each terrain subfolder
- zipped shapefile support
- FileGDB support for common hydrography and soil deliveries
- raster IMG support for common NOAA/USGS downloads
- land-cover mapping profile auto-detection
- `inspect_terrain_inputs()` and notebook inspection cells for pre-run validation

## Example Future Integration

Terrain outputs are intentionally optional in scoring v1. A future terrain modifier can normalize and blend selected fields into the existing hazard or vulnerability logic.

Example only:

- `terrain_modifier_score = 0.30*norm(local_relief) + 0.25*norm(slope_p90) + 0.20*norm(wetness_proxy) + 0.15*norm(distance_to_stream_km, invert=true) + 0.10*norm(soil_runoff_potential)`

This example is documented for future integration but is not automatically inserted into current scoring notebooks.

## Known Limitations

- Wetness is a simplified terrain proxy, not a full hydrologic routing model
- Distance-to-stream is centroid-based in v1
- Coastal metrics depend heavily on local availability of NOAA inundation products
- Soil and land-cover quality depend on local source currency, schema, and coverage
- DEM resolution and datum differences can materially affect slope and relief results
- Some portals still require manual user-driven download choices even though the notebook can now auto-discover and read more of the resulting files

## Definition of Done

Terrain Feature Pack v1 is complete when:

- the notebook/script runs locally when terrain inputs are present
- outputs are generated reproducibly
- missing optional sources fail gracefully with warnings
- docs are sufficient for a new student team to rerun the stage
