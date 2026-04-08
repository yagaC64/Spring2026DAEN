-- DuckDB workbench queries for local QA and exploration.

-- 1. Top municipios by confidence-adjusted priority.
SELECT
    municipio,
    phase,
    priority_band,
    priority_index_conf_adj,
    hazard_combined,
    vulnerability_score
FROM vw_municipio_risk_summary
ORDER BY priority_index_conf_adj DESC NULLS LAST
LIMIT 15;

-- 2. Source readiness and load status.
SELECT
    name,
    role,
    status,
    row_count,
    loaded_path
FROM vw_baseline_source_status;

-- 3. Station summary ordered by current flood signal.
SELECT
    station_id,
    station_name,
    latest_water_level,
    rise_rate_per_hour,
    flood_hazard_final,
    obs_count
FROM vw_station_water_summary
ORDER BY flood_hazard_final DESC NULLS LAST, latest_water_level DESC NULLS LAST;

-- 4. Terrain completeness review.
SELECT
    municipio_name,
    terrain_data_completeness,
    terrain_confidence_score,
    elevation_mean,
    slope_mean,
    wetness_proxy
FROM vw_terrain_summary
ORDER BY terrain_data_completeness DESC NULLS LAST, municipio_name;

-- 5. Active alert summary.
SELECT
    event,
    severity,
    alert_score,
    sent,
    ends,
    area_desc
FROM vw_alerts_summary
ORDER BY alert_score DESC NULLS LAST, sent DESC NULLS LAST;

-- 6. Optional age-adjustment overlay review.
SELECT
    municipio,
    score_age_vulnerability,
    age_adjustment_points,
    vulnerability_score_base,
    vulnerability_score_adjusted
FROM vw_vulnerability_adjustments
ORDER BY age_adjustment_points DESC NULLS LAST, municipio;
