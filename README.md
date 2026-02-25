# Spring 2026 DAEN — Flood Early Warning Decision-Support MVP

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

**Notebook Catalog**
| Notebook | Purpose | ArcGIS Dependency |
| --- | --- | --- |
| `JupyterNotebooks/nws-alerts-sync.ipynb` | Pull active NWS alerts for Puerto Rico and export local analysis outputs. | Optional (`USE_ARCGIS=1`) |
| `JupyterNotebooks/nws-forecast-sync.ipynb` | Pull NWS point forecast data for configured PR coordinates and export local outputs. | Optional (`USE_ARCGIS=1`) |
| `JupyterNotebooks/usgs-earthquakes-sync.ipynb` | Pull recent USGS earthquake events for PR-focused filtering and export local outputs. | Optional (`USE_ARCGIS=1`) |
| `JupyterNotebooks/usgs-water-sync.ipynb` | Pull USGS daily water observations (OGC API), normalize with codetables, and export tabular/geospatial outputs. | Optional (`USE_ARCGIS=1`) |
| `JupyterNotebooks/census-risk-features-pr.ipynb` | Build PR demographic risk features (municipio, ZIP/ZCTA, and town coordinates) from Census APIs. | Not required |
| `JupyterNotebooks/noaa-pr-waterlevel-hydrograph.ipynb` | Build a resilient, algorithmic PR NOAA water-level workflow (live catalog, no hardwired station dependency) and export comprehensive products: `outputs/noaa_pr/noaa_pr_waterlevel_comprehensive.html`, `outputs/noaa_pr/noaa_pr_water_levels_timeseries.csv`, `outputs/noaa_pr/noaa_pr_station_summary.csv`. | Not required |

**Execution Notes**
- Default mode is local (no ArcGIS account required).
- ArcGIS publishing/sync is enabled only when `USE_ARCGIS=1` plus the corresponding layer ID environment variable is set.
- Most outputs are written to local `outputs/` folders under `JupyterNotebooks/`.

## Index Formula Overview (`PR-Risk-and-Resiliency/JupyterNotebooks/index_pipeline/`)

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

8. **Resilience baseline proxy**
- **Formula:** `resilience_capacity_score = 0.45*income_capacity_score + 0.30*(100 - transport_constraint_score) + 0.25*(100 - housing_fragility_score)`
- **Rationale:** Estimate local capacity to absorb and recover from disruption.
- **Use:** `02_feature_engineering/10_build_exposure_vulnerability_features.ipynb`.
- **Outcome:** `resilience_capacity_score` feeding `resilience_index`, readiness, and recovery formulas.

9. **Municipio flood aggregation (distance-weighted + local override)**
- **Formula:** `w = exp(-distance_km / 25.0)`; `weighted_flood = weighted_average(flood_hazard_final, w)`; `flood_hazard_muni = max(weighted_flood, local_max_within_12km, nws_global_alert_score)`
- **Rationale:** Blend nearby station influence while preserving worst-case local conditions and active alerts.
- **Use:** `02_feature_engineering/20_build_municipio_hazard_features.ipynb`.
- **Outcome:** `flood_hazard_muni` per municipio.

10. **Earthquake municipio hazard proxy**
- **Formula:** `depth_factor = 1 / (1 + depth_km/70)`; `recency_factor = exp(-age_hours/168)`; `intensity_raw = magnitude / log1p(distance_km) * depth_factor * recency_factor`; `earthquake_hazard_score = robust_to_0_100(intensity_raw)`
- **Rationale:** Prioritize stronger, closer, shallower, and more recent events.
- **Use:** `02_feature_engineering/20_build_municipio_hazard_features.ipynb`.
- **Outcome:** `earthquake_hazard_score`; then `hazard_combined = max(flood_hazard_muni, earthquake_hazard_score)`.

11. **Risk index (multiplicative core)**
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
