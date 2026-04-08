# Spring 2026 DAEN — Flood Early Warning Decision-Support MVP

**Official Repository:** [`yagaC64/Spring2026DAEN`](https://github.com/yagaC64/Spring2026DAEN)
**Live Dashboard:** [`yagac64.github.io/Spring2026DAEN`](https://yagac64.github.io/Spring2026DAEN/)

**Purpose**
Deliver an integrated decision-support + data Science/Data Analytics prototype for community flood early warning by turning public data into actionable, defensible insights. The MVP emphasizes a reusable Data-as-a-Service foundation and a mobile-friendly web dashboard (not a native app).

**Core Objectives**
- Curate, ingest, normalize, and document authoritative public datasets (e.g., USGS, NOAA, USACE, Census, agreed layers)
- Provide repeatable refresh mechanisms and provenance so future teams can extend the pipeline
- Implement explainable indicators and quality checks (data gaps, plausibility, thresholds, trend signals)
- Deliver a map-centric, responsive dashboard with stakeholder-driven views (Risk/Readiness, Response/Routes, Data Quality)
- Produce runbooks, architecture diagrams, and a reusable repository for handoff

**Scope**
- Data-as-a-Service layer with documented sources, refresh, and catalog
- Decision-support analytics (risk/readiness prioritization overlays)
- Web dashboard optimized for phone browsers
- Demo-ready storytelling for stakeholders

**Quick Local Start**
- After cloning, run `./run.sh up` for the fastest local workbench startup path.
- That workflow creates or reuses a repo-local Python virtual environment at `.venv`, checks and installs the baseline requirements, runs pytest smoke tests, rebuilds the local DuckDB baseline, and starts the local Streamlit workbench.
- `./run.sh` without arguments opens an interactive menu for the same workflow plus status, query, and stop utilities.
- After startup, the runner can offer to open the local app in the default browser automatically. Inside the Streamlit app, a `Quit Local App` button is available for clean local shutdown.
- To stop the local app cleanly and free port `8501` for other tools, run `./run.sh stop`. If you need a different port, set `STREAMLIT_PORT` before launch.
- This baseline uses a standard repo-local Python virtual environment, not `uv`. That is intentional here: it keeps the setup lightweight, explicit, and compatible with the current notebook-first repo style.

**Notebook Catalog**
| Notebook | Purpose | ArcGIS Dependency |
| --- | --- | --- |
| `JupyterNotebooks/nws-alerts-sync.ipynb` | Pull active NWS alerts for Puerto Rico and export local analysis outputs. | Optional (`USE_ARCGIS=1`) |
| `JupyterNotebooks/nws-forecast-sync.ipynb` | Pull NWS point forecast data for configured PR coordinates and export local outputs. | Optional (`USE_ARCGIS=1`) |
| `JupyterNotebooks/usgs-earthquakes-sync.ipynb` | Pull recent USGS earthquake events for PR-focused filtering and export local outputs. | Optional (`USE_ARCGIS=1`) |
| `JupyterNotebooks/usgs-water-sync.ipynb` | Pull USGS daily water observations (OGC API), normalize with codetables, and export tabular/geospatial outputs. | Optional (`USE_ARCGIS=1`) |
| `JupyterNotebooks/census-risk-features-pr.ipynb` | Build PR demographic risk features (municipio, ZIP/ZCTA, and town coordinates) from Census APIs. | Not required |
| `JupyterNotebooks/index_pipeline/02_feature_engineering/15_build_terrain_features_pr.ipynb` | Guided terrain workflow for Puerto Rico: inspect discovered sources, stage manual downloads, and build municipio-aligned terrain indicators from DEM, coastal, soil, land-cover, and optional stream inputs with graceful fallbacks. | Not required |
| `JupyterNotebooks/noaa-pr-waterlevel-hydrograph.ipynb` | Build a resilient, algorithmic PR NOAA water-level workflow (live catalog, no hardwired station dependency) and export comprehensive products: `outputs/noaa_pr/noaa_pr_waterlevel_comprehensive.html`, `outputs/noaa_pr/noaa_pr_water_levels_timeseries.csv`, `outputs/noaa_pr/noaa_pr_station_summary.csv`. | Not required |

**Execution Notes**
- Default mode is local (no ArcGIS account required).
- ArcGIS publishing/sync is enabled only when `USE_ARCGIS=1` plus the corresponding layer ID environment variable is set.
- GitHub Pages publishes from `index.html`, which redirects to `noaa_pr_waterlevel_comprehensive.html`.
- Most pipeline outputs are written to local `outputs/` folders under `JupyterNotebooks/` unless intentionally promoted for publication.
- Terrain Feature Pack v1 stages local inputs under `data/staging/terrain/` and writes local reviewable outputs to `outputs/index_pipeline/15_terrain/`.
- The terrain CLI supports pre-run inspection with `python3 scripts/terrain/terrain_feature_pack.py --inspect-only` so users can see what was discovered before running the full stage.

## Repository Tree

```text
.
├── app/                                # Local Streamlit prototype shell
├── .github/workflows/                  # GitHub Pages deployment workflow
├── config/                             # Versioned executable configuration
├── data/                               # Local/project data staging
│   └── local/duckdb/                   # Local DuckDB workbench artifacts
├── docs/
│   ├── meetings/                       # Approved publishable meeting records
│   ├── planning/                       # Scope, requirements, and planning docs
│   ├── research/                       # Research stacks and question banks
│   └── specs/                          # Index specs and implementation playbooks
├── JupyterNotebooks/
│   ├── index_pipeline/                 # Staged index/scoring notebook pipeline
│   ├── *.ipynb                         # Source ingest and analysis notebooks
│   └── outputs/                        # Local/generated notebook outputs
├── noaa_pr_waterlevel_comprehensive.html  # Published dashboard artifact
├── index.html                          # GitHub Pages landing redirect
├── outputs/                            # Local/generated exports and artifacts
├── run.sh                              # Local DuckDB + Streamlit prototype runner
├── scripts/                            # Reusable local pipeline/support scripts
├── sql/                                # Sample DuckDB baseline queries
├── sources/
│   ├── HUMINT/
│   ├── IMINT/
│   ├── MASINT/
│   └── OSINT/
└── README.md
```

For a docs-only breakdown, see `docs/README.md`.

## Index Configuration Skeleton (Executable Spec)

- `config/index_spec_v1.yaml` is the versioned configuration skeleton that translates the written index spec into notebook-loadable parameters.
- It centralizes bounds, weights, alert mappings, threshold bands, phase rules, spatial aggregation settings, and confidence scoring factors.
- Intended use: notebooks in `JupyterNotebooks/index_pipeline/` load this file instead of hardcoding scoring logic constants in multiple places.
- Outcome: consistent runs, easier audits, simpler tuning, and cleaner semester-to-semester handoff.

## Terrain Feature Pack v1

- `docs/specs/terrain_feature_pack_v1.md` defines the terrain feature scope, formulas, source strategy, CRS assumptions, limitations, and downstream integration guidance.
- `config/terrain_spec_v1.yaml` versions terrain source globs, feature parameters, quality scoring, and output defaults.
- `JupyterNotebooks/index_pipeline/02_feature_engineering/15_build_terrain_features_pr.ipynb` is the guided local-first terrain stage notebook for inspection, pacing, and execution.
- `scripts/terrain/terrain_feature_pack.py` contains the reusable Python implementation for notebook or CLI execution.
- Current automation focuses on source discovery, staging-folder setup, support for `.zip` / `.gdb` / `.img` local inputs, and land-cover profile auto-detection.
- Intended outputs: `outputs/index_pipeline/15_terrain/municipio_terrain_features.{csv,parquet,geojson}` plus run metadata and a local data dictionary.

## Social Adjustment Factors v1

- `config/social_adjustments_v1.yaml` versions optional social-adjustment settings. The current default-on overlay adds age-sensitive adjustment points using children under 5 and adults 65+.
- `scripts/factors/social_adjustments.py` is the shared background module used by canonical notebooks and the local workbench.
- `JupyterNotebooks/census-risk-features-pr.ipynb` now pulls the required ACS age fields into the canonical census feature outputs instead of relying on a detached notebook copy.
- `JupyterNotebooks/index_pipeline/02_feature_engineering/10_build_exposure_vulnerability_features.ipynb` applies the configured overlay and writes:
  - `JupyterNotebooks/outputs/index_pipeline/10_features/municipio_exposure_vulnerability_features.csv`
  - `JupyterNotebooks/outputs/index_pipeline/10_features/municipio_adjustment_factors.csv`
  - `JupyterNotebooks/outputs/index_pipeline/10_features/adjustment_factor_reference.csv`
- The local workbench surfaces the same factor reference and municipio adjustment outputs through DuckDB so the adjustment logic is inspectable outside the notebooks.

## PR Hazard and Readiness Analysis Workbench (Local-Only Prototype)

### Current State

This repository is currently not centered on a formal DuckDB database layer or a deployed Streamlit application. The current MVP remains notebook-first, local-first by default, driven by curated public-data ingest and staged analytics notebooks, and publicly surfaced through the existing GitHub Pages dashboard flow.

For the local workbench, the recommended path after cloning is:

```bash
./run.sh up
```

That command checks or installs local requirements, runs pytest smoke tests, rebuilds the local DuckDB starter database, and brings the local Streamlit workbench up.

### Why Add This Workbench?

A lightweight DuckDB + Streamlit workbench helps future contributors start from a practical local analysis surface instead of starting from zero. The intent is to complement the current architecture by adding:

- a small local analytical store
- a repeatable loader from current curated outputs
- starter views and queries for QA and exploration
- and a minimal Streamlit shell for local interactive analysis

### What This Workbench Is

This workbench is intended to be:

- local-first
- additive
- lightweight
- easy to rebuild from current outputs
- and suitable for extension by future contributors

### What This Workbench Is Not

This workbench is not:

- a replacement for the current GitHub Pages public dashboard
- a full production deployment
- a complete migration away from the notebook-first workflow
- or a claim that all project outputs are already normalized into a database schema

### Starter Scope in This Repo

- Local DuckDB convention: `data/local/duckdb/spring2026daen_baseline.duckdb`
- Loader script: `scripts/build_duckdb_baseline.py`
- Starter local app: `app/streamlit_app.py`
- Sample SQL: `sql/duckdb_baseline_queries.sql`
- Assumptions and open questions: `docs/planning/duckdb_streamlit_baseline_notes.md`

Current baseline ingestion targets the most stable local curated outputs currently available:

- `JupyterNotebooks/outputs/index_pipeline/30_scoring/municipio_indices_scored.csv`
- `JupyterNotebooks/outputs/index_pipeline/50_products/priority_actions.csv`
- `JupyterNotebooks/outputs/index_pipeline/01_ingest/flood_station_latest_features.csv`
- `JupyterNotebooks/outputs/index_pipeline/01_ingest/nws_alerts_enriched.csv`
- `outputs/index_pipeline/15_terrain/municipio_terrain_features.parquet` or `.csv`
- `outputs/noaa_pr/noaa_pr_station_summary.csv`

GeoJSON outputs are inventoried for future map-friendly extensions but are not yet loaded into a spatial database schema.

### Public vs Local Workbench

- Public today: the current GitHub Pages dashboard flow remains the official public-facing surface.
- Local/internal workbench: the DuckDB database and Streamlit app are intended for local analytical exploration, QA, and future extension.

### Quickstart

1. Clone the repository.
2. Run `./run.sh up`.
3. Let the runner create or reuse `.venv`, install requirements if needed, run pytest smoke tests, build the local DuckDB baseline, and launch the local workbench.
4. Use `./run.sh` later for the interactive menu, status checks, rebuilds, queries, optimization, and clean stop actions.

```bash
./run.sh up
```

For a guided local menu, use:

```bash
./run.sh
```

If you want the underlying steps directly, they are still available:

```bash
./run.sh install
./run.sh test
./run.sh build
./run.sh start
./run.sh stop
```

### Known Gaps and Next Extensions

- The baseline currently focuses on a small set of stable outputs rather than the full notebook estate.
- The app is a local workbench shell, not a production deployment target.
- GeoJSON sources are inventoried rather than modeled spatially in DuckDB.
- Natural next candidates for expansion include age, transport/no-vehicle, housing fragility, income/poverty, and future terrain pilot outputs.

## Index Formula Overview (`JupyterNotebooks/index_pipeline/`)

This section documents the implemented formulas used in the staged pipeline at `JupyterNotebooks/index_pipeline/`, including the rationale, operational use, and output artifact.

1. **Linear normalization (0-100)**
- **Formula:** `score = clip((x - low) / (high - low), 0, 1) * 100`
- **Rationale:** Put different sensor units/scales into a common index scale.
- **Use:** `01_ingest_hazard/01_ingest_flood_hazard_feeds.ipynb` (`normalize_linear`).
- **Outcome:** `exceed_score`, `rise_score` fields used in flood hazard scoring.

2. **Flood rise-rate signal**
- **Formula:** `rise_rate_per_hour = (latest_water_level - previous_water_level) / delta_hours`
- **Rationale:** Capture how quickly water conditions are changing, not only current level.
- **Use:** `01_ingest_hazard/01_ingest_flood_hazard_feeds.ipynb`.
- **Outcome:** `rise_rate_per_hour` and normalized `rise_score` in `outputs/index_pipeline/01_ingest/flood_station_latest_features.csv`.

3. **Flood stage exceedance signal**
- **Formula:** `exceed_ratio = (latest_water_level - minor_stage) / (major_stage - minor_stage)` (when thresholds are present)
- **Rationale:** Express present level relative to operational flood stage thresholds.
- **Use:** `01_ingest_hazard/01_ingest_flood_hazard_feeds.ipynb`.
- **Outcome:** `exceed_ratio` and normalized `exceed_score` in station-level flood features.

4. **Station sensor flood hazard**
- **Formula:** `sensor_hazard_score = mean(exceed_score, rise_score)` (NaN-safe)
- **Rationale:** Balance "how high" and "how fast rising" into one station hazard score.
- **Use:** `01_ingest_hazard/01_ingest_flood_hazard_feeds.ipynb`.
- **Outcome:** `sensor_hazard_score` per station.

5. **NWS alert override and final flood hazard**
- **Formula:** `flood_hazard_final = max(sensor_hazard_score, nws_global_alert_score)` with alert mapping `Flood Watch=40`, `Flood Warning=70`, `Flash Flood Warning=100` (severity fallback map included)
- **Rationale:** Ensure authoritative warnings can raise risk posture even if station telemetry under-represents emerging conditions.
- **Use:** `01_ingest_hazard/01_ingest_flood_hazard_feeds.ipynb`.
- **Outcome:** `flood_hazard_final` in station features; `nws_alerts_enriched.csv` as supporting evidence.

6. **Robust percentile normalization for social features**
- **Formula:** `score = clip((x - p05) / (p95 - p05), 0, 1) * 100` (invert when higher is better)
- **Rationale:** Reduce sensitivity to outliers while keeping comparability across municipios.
- **Use:** `02_feature_engineering/10_build_exposure_vulnerability_features.ipynb` (`robust_score`).
- **Outcome:** Standardized social/exposure component scores in `outputs/index_pipeline/10_features/municipio_exposure_vulnerability_features.csv`.

7. **Vulnerability composite**
- **Formula:** `vulnerability_score = 0.35*poverty_score + 0.25*transport_constraint_score + 0.15*housing_fragility_score + 0.25*(100 - income_capacity_score)`
- **Rationale:** Combine socioeconomic and mobility stressors into one explainable vulnerability factor.
- **Use:** `02_feature_engineering/10_build_exposure_vulnerability_features.ipynb`.
- **Outcome:** `vulnerability_score` used directly in risk and priority calculations.

8. **Optional age adjustment overlay**
- **Formula:** `score_age_vulnerability = 0.4*score_child_vulnerability + 0.6*score_elderly_vulnerability`; `age_adjustment_points = score_age_vulnerability/100 * 12`; `vulnerability_score_adjusted = clip(vulnerability_score_base + age_adjustment_points, 0, 100)`
- **Rationale:** Add an explainable overlay for age-sensitive populations without rewriting the core staged scoring architecture.
- **Use:** `config/social_adjustments_v1.yaml` plus `scripts/factors/social_adjustments.py`, applied in `02_feature_engineering/10_build_exposure_vulnerability_features.ipynb`.
- **Outcome:** Transparent base-vs-adjusted vulnerability fields and a separate municipio adjustment table.

9. **Resilience baseline proxy**
- **Formula:** `resilience_capacity_score = 0.45*income_capacity_score + 0.30*(100 - transport_constraint_score) + 0.25*(100 - housing_fragility_score)`
- **Rationale:** Estimate local capacity to absorb and recover from disruption.
- **Use:** `02_feature_engineering/10_build_exposure_vulnerability_features.ipynb`.
- **Outcome:** `resilience_capacity_score` feeding `resilience_index`, readiness, and recovery formulas.

10. **Municipio flood aggregation (distance-weighted + local override)**
- **Formula:** `w = exp(-distance_km / 25.0)`; `weighted_flood = weighted_average(flood_hazard_final, w)`; `flood_hazard_muni = max(weighted_flood, local_max_within_12km, nws_global_alert_score)`
- **Rationale:** Blend nearby station influence while preserving worst-case local conditions and active alerts.
- **Use:** `02_feature_engineering/20_build_municipio_hazard_features.ipynb`.
- **Outcome:** `flood_hazard_muni` per municipio.

11. **Earthquake municipio hazard proxy**
- **Formula:** `depth_factor = 1 / (1 + depth_km/70)`; `recency_factor = exp(-age_hours/168)`; `intensity_raw = magnitude / log1p(distance_km) * depth_factor * recency_factor`; `earthquake_hazard_score = robust_to_0_100(intensity_raw)`
- **Rationale:** Prioritize stronger, closer, shallower, and more recent events.
- **Use:** `02_feature_engineering/20_build_municipio_hazard_features.ipynb`.
- **Outcome:** `earthquake_hazard_score`; then `hazard_combined = max(flood_hazard_muni, earthquake_hazard_score)`.

12. **Risk index (multiplicative core)**
- **Formula:** `risk_index_raw = (hazard_combined/100) * (exposure_score/100) * (vulnerability_score/100) * 100`
- **Rationale:** High risk emerges when hazard, exposure, and vulnerability are jointly elevated.
- **Use:** `03_scoring/30_score_operational_indices.ipynb`.
- **Outcome:** `risk_index_raw` in `outputs/index_pipeline/30_scoring/municipio_indices_scored.csv`.

12. **Response and recovery operational indices**
- **Formula (Response Readiness):** `0.45*(100 - hazard) + 0.35*resilience_capacity + 0.20*(100 - vulnerability)`
- **Formula (Recovery Capacity):** `0.50*resilience_capacity + 0.25*(100 - exposure) + 0.25*(100 - vulnerability)`
- **Rationale:** Capture actionable posture for immediate response and near-term restoration.
- **Use:** `03_scoring/30_score_operational_indices.ipynb`.
- **Outcome:** `response_readiness_index`, `recovery_capacity_index`, and `resilience_index`.

13. **Phase-aware priority index**
- **Formula:** `priority_index = w_risk*risk_index_raw + w_rr*(100 - response_readiness_index) + w_rc*(100 - recovery_capacity_index)` with weights by phase (`PRE`, `DURING`, `POST`)
- **Rationale:** Shift emphasis based on incident phase instead of fixed weighting all the time.
- **Use:** `03_scoring/30_score_operational_indices.ipynb`.
- **Outcome:** `priority_index` and `phase` fields per municipio.

14. **Confidence scoring and confidence-adjusted priority**
- **Formula (confidence):** `confidence_score = 0.35*freshness + 0.25*completeness + 0.25*validity + 0.15*crosscheck`
- **Formula (adjusted priority):** `priority_index_conf_adj = confidence_0_1*priority_index + (1 - confidence_0_1)*baseline_median_priority`
- **Rationale:** Prevent unstable/noisy feed conditions from over-driving final prioritization.
- **Use:** `03_scoring/30_score_operational_indices.ipynb`.
- **Outcome:** Stable `priority_index_conf_adj` and auditable `confidence_score`.

15. **Priority banding and hard-red overrides**
- **Formula:** Bands from adjusted priority: `>=85 Red`, `>=70 Orange`, `>=50 Yellow`, else `Green`; hard override to `Red` if `nws_global_alert_score >= 95` or `flood_hazard_muni >= 90`
- **Rationale:** Convert scores into operationally interpretable escalation tiers.
- **Use:** `03_scoring/30_score_operational_indices.ipynb`.
- **Outcome:** `priority_band` for downstream products in `outputs/index_pipeline/50_products/priority_actions.csv` and `index_priority_overview.html`.

**End-to-end aggregation summary:** the pipeline ingests hazard feeds, normalizes and engineers station/municipio features, factors those features through phase-aware and confidence-aware formulas, generates final operational indices and priority bands, and writes reproducible artifacts that are review-ready and can be shipped to `main`.

## Best Practices for Reusable Decision-Support Repos

Use this pattern in future repos so notebooks, specs, and outputs stay aligned and reproducible.

1. **Keep the written spec and executable config separate but linked**
- Store the narrative design in `docs/specs/` and the runnable parameter skeleton in `config/`.
- Reference each file from the other so updates do not drift silently.

2. **Treat weights, bounds, and thresholds as versioned configuration**
- Do not scatter constants across notebooks.
- Put alert mappings, phase weights, confidence factors, and band cutoffs in one YAML/JSON file.

3. **Use stable keys and clear naming**
- Prefer machine-stable keys (for example `risk_during`, `hazard_flood_station`) and human-readable descriptions.
- Keep names consistent across spec, config, notebooks, and output columns.

4. **Make assumptions explicit in config comments**
- Document placeholder feeds, fallback behavior, and policy choices directly in the config file.
- This prevents future teams from confusing design intent with final production logic.

5. **Separate raw ingest, feature engineering, scoring, validation, and products**
- Preserve stage boundaries (`01_ingest`, `10_features`, `20_features`, `30_scoring`, etc.) so each step can be rerun and inspected independently.
- Write explicit artifacts between stages for traceability.

6. **Prefer explainable formulas before advanced models**
- Start with weighted sums, overrides, and confidence adjustment.
- Add advanced methods only after validation labels and backtesting baselines are in place.

7. **Add confidence and override logic as first-class design elements**
- Operational scoring should always account for data freshness/completeness/validity and authoritative alerts.
- Treat confidence adjustment and hard overrides as part of the index contract, not afterthoughts.

8. **Pin reproducibility metadata in outputs**
- Record run timestamps, source pull times, phase, and config version in derived outputs whenever possible.
- This makes comparisons across runs defensible.

9. **Design for handoff from day one**
- Assume the next team did not attend your meetings.
- Keep runbooks, config files, example outputs, and spec language clean enough for immediate reuse.

10. **Tune with evidence, not intuition**
- Change thresholds/weights through documented backtesting or scenario tests.
- Log what changed, why it changed, and what metric improved.

**Source Intelligence Structure**
- `sources/IMINT`: imagery intelligence used for PAB/CAI image products, geospatial interpretation, and visual change detection.
- `sources/MASINT`: measurement and signature intelligence from sensors and instrument-based streams used to monitor hazard and infrastructure signals.
- `sources/OSINT`: open-source intelligence including public datasets, bulletins, and openly available operational references.
- `sources/HUMINT`: field intelligence captured by instructors and students during site visits to risk zones or post-event areas to document risks, readiness, and resiliency conditions.
- Operational intent: combine these intelligence streams to support defensible situation awareness, planning, and response decisions.

**Out of Scope**
- Native mobile apps (iOS/Android)
- Hardware sensor design/build or embedded firmware
- Large-scale ML training requiring specialized GPU/MLOps
- 24/7 production deployment and monitoring

**Key Stakeholders**
- Instructor/PM authority: Isaac
- Partners/SMEs: Gilberto (continuity + stakeholder alignment), Melvin (mission + community narrative), Willie (data engineering + platform guardrails)
- Optional external demos: STAR-TIDES / USACE (only if scope allows)

**Operating Cadence (Target)**
- Agile sprints with weekly partner meeting
- Sequence: data inventory + requirements → pipeline + baseline dashboard → indices + prioritization → packaging + demo

**License Direction**
- Apache 2.0 (see `LICENSE`) to encourage broad participation and reuse across semesters and partner organizations.
- Rationale: permissive terms plus an explicit patent grant help reduce friction for contributors and downstream adopters while keeping the project easy to extend semester-over-semester.
