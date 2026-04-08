# Terrain Staging Area

This folder is reserved for local terrain inputs used by Terrain Feature Pack v1.

The guided driver for this workflow is:

- `JupyterNotebooks/index_pipeline/02_feature_engineering/15_build_terrain_features_pr.ipynb`

## Why This Folder Is Ignored

Terrain rasters and hydrography layers can be large and are often downloaded locally for notebook processing. The local `.gitignore` in this folder keeps those raw inputs out of Git while allowing this README to stay versioned.

## Expected Layout

- `data/staging/terrain/boundaries/`
- `data/staging/terrain/dem/`
- `data/staging/terrain/streams/`
- `data/staging/terrain/coastal/`
- `data/staging/terrain/soils/`
- `data/staging/terrain/land_cover/`

## Automation Status

Automated in v1:

- Puerto Rico municipio boundaries via Census TIGER fallback download
- staging subfolder creation
- recursive local source discovery
- support for common local download packaging such as `.zip`, `.gdb`, and raster `.img`
- land-cover profile auto-detection for NOAA C-CAP and NLCD Puerto Rico style class codes

Manual/local download expected in v1:

- DEM GeoTIFF from USGS 3DEP or NOAA DEM
- NOAA Sea Level Rise Viewer inundation raster/polygon exports
- gSSURGO / SSURGO soil layers
- NOAA C-CAP land-cover raster
- Optional stream network if not already curated by the team

## Expected Filenames / Globs

The stage discovers inputs through glob patterns defined in `config/terrain_spec_v1.yaml`.

Examples:

- `data/staging/terrain/dem/*.tif`
- `data/staging/terrain/dem/**/*.img`
- `data/staging/terrain/streams/*.gpkg`
- `data/staging/terrain/streams/**/*.zip`
- `data/staging/terrain/streams/**/*.gdb`
- `data/staging/terrain/coastal/*.tif`
- `data/staging/terrain/coastal/**/*.img`
- `data/staging/terrain/coastal/*.geojson`
- `data/staging/terrain/soils/*.gpkg`
- `data/staging/terrain/soils/**/*.gdb`
- `data/staging/terrain/land_cover/*.tif`
- `data/staging/terrain/land_cover/**/*.img`

## Manual Steps That Still Matter

1. Download the source data from the official portals into the matching subfolder under `data/staging/terrain/`.
2. Unzip archives only if you want to inspect contents manually. The stage can now read common zipped shapefile bundles directly.
3. For FileGDB soil or hydrography downloads, place the `.gdb` directory itself under the expected terrain subfolder.
4. Prefer NOAA C-CAP for land cover if you want the least-friction default mapping. NLCD Puerto Rico is also supported, but class mapping is profile-based.
5. Use the notebook inspection cell first. It will tell you what was discovered and which manual steps are still blocking a full terrain run.
