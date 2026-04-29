# Puerto Rico Census Boundary Sources

This note records official U.S. Census Bureau reference pages and direct download links for Puerto Rico TIGER/Line boundary layers that may be useful for future class work.

## Purpose

Use this note as a quick reference when the project needs:

- official Puerto Rico administrative boundary downloads
- a canonical landing page for TIGER/Line vintages
- finer-than-municipio Puerto Rico boundary layers for analysis or mapping

These links are useful as source references even when the repo does not yet ingest these layers directly.

## Verified Sources

Verified on April 10, 2026:

- `https://www2.census.gov/geo/tiger/TIGER2025/COUSUB/tl_2025_72_cousub.zip` returned `200 OK`
- `https://www2.census.gov/geo/tiger/TIGER2025/SUBBARRIO/tl_2025_72_subbarrio.zip` returned `200 OK`

## Source Table

| Source | Official page | Direct download | Use in this repo | Notes |
| --- | --- | --- | --- | --- |
| TIGER/Line landing page | [TIGER/Line Shapefiles landing page](https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html) | n/a | Canonical discovery page for current and prior TIGER vintages. Useful when a notebook or spec needs an official Census landing reference instead of a hardcoded ZIP only. | Best starting point when a future class needs to update a vintage year. |
| Puerto Rico county subdivision | n/a | [2025 COUSUB ZIP](https://www2.census.gov/geo/tiger/TIGER2025/COUSUB/tl_2025_72_cousub.zip) | Candidate boundary layer when class work needs Puerto Rico county subdivision geography rather than municipio-only geography. | TIGER uses `COUSUB` for county subdivisions. In Puerto Rico, this is a useful reference for minor civil division-style analysis below county-equivalent scale. |
| Puerto Rico subbarrio catalog entry | [Data.gov catalog page](https://catalog.data.gov/dataset/tiger-line-shapefile-current-state-puerto-rico-subbarrio-subminor-civil-division) | n/a | Catalog-style reference page for discoverability, metadata, and provenance notes. | Good citation target when documenting source provenance in README/spec notes. |
| Puerto Rico subbarrio | n/a | [2025 SUBBARRIO ZIP](https://www2.census.gov/geo/tiger/TIGER2025/SUBBARRIO/tl_2025_72_subbarrio.zip) | Candidate fine-grained Puerto Rico boundary layer for neighborhood-scale pilots, local overlays, or future higher-resolution workbench maps. | Census technical documentation describes subbarrios in Puerto Rico as legally defined subdivisions of barrios and barrios-pueblo. They do not exist everywhere and do not necessarily cover an entire minor civil division where present. |

## Recommended Use by Layer

### 1. TIGER/Line Landing Page

Use this when the repo needs:

- an official Census Bureau landing page in docs or specs
- a way to discover newer TIGER vintages
- a citation that is more stable than pasting only a direct ZIP

### 2. COUSUB (`tl_2025_72_cousub.zip`)

Use this when the repo needs:

- a Puerto Rico administrative boundary layer below county-equivalent scale
- an intermediate geography that is finer than municipio-only work
- a reference layer for future joins, map overlays, or pilot feature engineering

Project fit:

- likely useful for future staged notebooks or workbench views when the class wants more spatial detail than municipio centroids
- useful to keep documented even if not yet loaded into DuckDB

### 3. SUBBARRIO Catalog Page

Use this when the repo needs:

- a public catalog citation page for provenance
- a metadata-oriented reference that classmates can read before downloading
- a human-readable source page in issues, PRs, or docs

### 4. SUBBARRIO (`tl_2025_72_subbarrio.zip`)

Use this when the repo needs:

- finer Puerto Rico boundaries than county subdivision
- neighborhood-scale pilot mapping where available
- future map layers or risk analysis pilots that require more local spatial resolution

Project fit:

- a good candidate for optional future workbench overlays
- a better fit for selective pilots than for assuming statewide complete coverage

## Practical Guidance for the Class

- Prefer citing the landing page or catalog page in docs, then include the direct ZIP for reproducible download.
- Keep the vintage year explicit in docs so future classes can update links intentionally.
- Do not assume these layers should replace municipio boundaries everywhere. They are best treated as optional finer-resolution references until a specific pipeline stage adopts them.
- If these files are added to the repo later, store only lightweight metadata or staged derivatives unless the class explicitly wants raw shapefile assets committed.

## Notes for Future Integration

Possible future uses in `Spring2026DAEN`:

- richer Puerto Rico boundary reference notes in specs
- optional higher-resolution map layers in the local workbench
- exploratory joins for localized hazard, readiness, or demographic overlays
- pilot notebook work that tests finer-than-municipio spatial aggregation
