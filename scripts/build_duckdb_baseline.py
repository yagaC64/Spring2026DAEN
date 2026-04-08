#!/usr/bin/env python3
"""Build a local DuckDB workbench database from curated Spring2026DAEN outputs."""

from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable


try:
    import duckdb
    import pandas as pd
except ImportError as exc:  # pragma: no cover - friendly runtime guard
    raise SystemExit(
        "Missing dependency for DuckDB baseline. Install requirements with "
        "`pip install -r requirements.txt` before running this script."
    ) from exc


def find_repo_root(start: Path | None = None) -> Path:
    probe = (start or Path.cwd()).resolve()
    for candidate in [probe, *probe.parents]:
        if (candidate / "README.md").exists() and (candidate / "JupyterNotebooks").exists():
            return candidate
    return probe


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    value = value.lower().replace("&", "and")
    value = "".join(ch if ch.isalnum() else "_" for ch in value)
    return "_".join(part for part in value.split("_") if part)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def first_existing_path(repo_root: Path, candidates: list[str]) -> Path | None:
    for candidate in candidates:
        path = repo_root / candidate
        if path.exists():
            return path
    return None


def load_frame(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix == ".parquet":
        return pd.read_parquet(path)
    raise ValueError(f"Unsupported tabular baseline source format: {path.suffix}")


def ensure_columns(frame: pd.DataFrame, expected_columns: list[str]) -> pd.DataFrame:
    for column in expected_columns:
        if column not in frame.columns:
            frame[column] = pd.NA
    return frame


def transform_municipio_indices(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    frame["municipio_slug"] = frame["municipio"].map(slugify)
    return ensure_columns(
        frame,
        [
            "municipio",
            "municipio_slug",
            "municipio_key",
            "latitude",
            "longitude",
            "hazard_combined",
            "flood_hazard_muni",
            "earthquake_hazard_score",
            "exposure_score",
            "vulnerability_score",
            "resilience_index",
            "response_readiness_index",
            "recovery_capacity_index",
            "risk_index_raw",
            "priority_index",
            "priority_index_conf_adj",
            "confidence_score",
            "confidence_0_1",
            "priority_band",
            "phase",
        ],
    )


def transform_priority_actions(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    frame["municipio_slug"] = frame["municipio"].map(slugify)
    return ensure_columns(
        frame,
        [
            "rank",
            "municipio",
            "municipio_slug",
            "priority_band",
            "priority_index_conf_adj",
            "hazard_combined",
            "flood_hazard_muni",
            "earthquake_hazard_score",
            "vulnerability_score",
            "response_readiness_index",
            "recovery_capacity_index",
            "confidence_score",
            "recommended_actions",
        ],
    )


def transform_flood_station_latest(frame: pd.DataFrame) -> pd.DataFrame:
    return ensure_columns(
        frame.copy(),
        [
            "station_id",
            "station_name",
            "shefcode",
            "lat",
            "lon",
            "latest_time_utc",
            "latest_water_level",
            "rise_rate_per_hour",
            "minor",
            "moderate",
            "major",
            "exceed_ratio",
            "exceed_score",
            "rise_score",
            "sensor_hazard_score",
            "nws_global_alert_score",
            "flood_hazard_final",
            "catalog_pull_utc",
        ],
    )


def transform_nws_alerts(frame: pd.DataFrame) -> pd.DataFrame:
    return ensure_columns(
        frame.copy(),
        [
            "id",
            "event",
            "severity",
            "urgency",
            "certainty",
            "headline",
            "sent",
            "onset",
            "ends",
            "status",
            "area_desc",
            "ugc_list",
            "alert_score",
        ],
    )


def transform_terrain_features(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    if "municipio_name" in frame.columns:
        frame["municipio_slug"] = frame["municipio_name"].map(slugify)
    elif "municipio_key" in frame.columns:
        frame["municipio_slug"] = frame["municipio_key"].map(slugify)
    else:
        frame["municipio_slug"] = pd.NA
    return ensure_columns(
        frame,
        [
            "municipio_id",
            "municipio_name",
            "municipio_key",
            "municipio_slug",
            "elevation_mean",
            "slope_mean",
            "slope_p90",
            "local_relief",
            "wetness_proxy",
            "distance_to_stream_km",
            "coastal_inundation_flag",
            "coastal_inundation_depth_mean",
            "soil_runoff_potential",
            "land_cover_runoff_modifier",
            "terrain_data_completeness",
            "terrain_confidence_score",
            "config_version",
            "run_timestamp_utc",
        ],
    )


def transform_municipio_adjustment_factors(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    if "municipio_slug" not in frame.columns:
        if "municipio_key" in frame.columns:
            frame["municipio_slug"] = frame["municipio_key"]
        elif "municipio" in frame.columns:
            frame["municipio_slug"] = frame["municipio"].map(slugify)
        else:
            frame["municipio_slug"] = pd.NA
    return ensure_columns(
        frame,
        [
            "municipio",
            "municipio_key",
            "municipio_slug",
            "child_under_5_population",
            "elderly_65_plus_population",
            "child_rate",
            "elderly_65_plus_rate",
            "age_dependency_rate",
            "score_child_vulnerability",
            "score_elderly_vulnerability",
            "score_age_vulnerability",
            "age_adjustment_points",
            "age_adjustment_enabled",
            "vulnerability_score_base",
            "vulnerability_score_adjusted",
            "adjustment_config_version",
        ],
    )


def transform_noaa_station_summary(frame: pd.DataFrame) -> pd.DataFrame:
    return ensure_columns(
        frame.copy(),
        [
            "station_id",
            "station_name",
            "latest_time_utc",
            "latest_value",
            "latest_quality",
            "lat",
            "lon",
            "minor",
            "moderate",
            "major",
            "obs_count",
            "peak_value",
            "mean_value",
        ],
    )


EMPTY_SCHEMAS: dict[str, dict[str, str]] = {
    "baseline_municipio_indices": {
        "municipio": "string",
        "municipio_slug": "string",
        "municipio_key": "string",
        "latitude": "float64",
        "longitude": "float64",
        "hazard_combined": "float64",
        "flood_hazard_muni": "float64",
        "earthquake_hazard_score": "float64",
        "exposure_score": "float64",
        "vulnerability_score": "float64",
        "resilience_index": "float64",
        "response_readiness_index": "float64",
        "recovery_capacity_index": "float64",
        "risk_index_raw": "float64",
        "priority_index": "float64",
        "priority_index_conf_adj": "float64",
        "confidence_score": "float64",
        "confidence_0_1": "float64",
        "priority_band": "string",
        "phase": "string",
    },
    "baseline_priority_actions": {
        "rank": "Int64",
        "municipio": "string",
        "municipio_slug": "string",
        "priority_band": "string",
        "priority_index_conf_adj": "float64",
        "hazard_combined": "float64",
        "flood_hazard_muni": "float64",
        "earthquake_hazard_score": "float64",
        "vulnerability_score": "float64",
        "response_readiness_index": "float64",
        "recovery_capacity_index": "float64",
        "confidence_score": "float64",
        "recommended_actions": "string",
    },
    "baseline_flood_station_latest": {
        "station_id": "string",
        "station_name": "string",
        "shefcode": "string",
        "lat": "float64",
        "lon": "float64",
        "latest_time_utc": "string",
        "latest_water_level": "float64",
        "rise_rate_per_hour": "float64",
        "minor": "float64",
        "moderate": "float64",
        "major": "float64",
        "exceed_ratio": "float64",
        "exceed_score": "float64",
        "rise_score": "float64",
        "sensor_hazard_score": "float64",
        "nws_global_alert_score": "float64",
        "flood_hazard_final": "float64",
        "catalog_pull_utc": "string",
    },
    "baseline_nws_alerts": {
        "id": "string",
        "event": "string",
        "severity": "string",
        "urgency": "string",
        "certainty": "string",
        "headline": "string",
        "sent": "string",
        "onset": "string",
        "ends": "string",
        "status": "string",
        "area_desc": "string",
        "ugc_list": "string",
        "alert_score": "float64",
    },
    "baseline_terrain_features": {
        "municipio_id": "string",
        "municipio_name": "string",
        "municipio_key": "string",
        "municipio_slug": "string",
        "elevation_mean": "float64",
        "slope_mean": "float64",
        "slope_p90": "float64",
        "local_relief": "float64",
        "wetness_proxy": "float64",
        "distance_to_stream_km": "float64",
        "coastal_inundation_flag": "float64",
        "coastal_inundation_depth_mean": "float64",
        "soil_runoff_potential": "float64",
        "land_cover_runoff_modifier": "float64",
        "terrain_data_completeness": "float64",
        "terrain_confidence_score": "float64",
        "config_version": "string",
        "run_timestamp_utc": "string",
    },
    "baseline_municipio_adjustment_factors": {
        "municipio": "string",
        "municipio_key": "string",
        "municipio_slug": "string",
        "child_under_5_population": "float64",
        "elderly_65_plus_population": "float64",
        "child_rate": "float64",
        "elderly_65_plus_rate": "float64",
        "age_dependency_rate": "float64",
        "score_child_vulnerability": "float64",
        "score_elderly_vulnerability": "float64",
        "score_age_vulnerability": "float64",
        "age_adjustment_points": "float64",
        "age_adjustment_enabled": "boolean",
        "vulnerability_score_base": "float64",
        "vulnerability_score_adjusted": "float64",
        "adjustment_config_version": "string",
    },
    "baseline_noaa_station_summary": {
        "station_id": "string",
        "station_name": "string",
        "latest_time_utc": "string",
        "latest_value": "float64",
        "latest_quality": "string",
        "lat": "float64",
        "lon": "float64",
        "minor": "float64",
        "moderate": "float64",
        "major": "float64",
        "obs_count": "Int64",
        "peak_value": "float64",
        "mean_value": "float64",
    },
}


def empty_frame(schema_name: str) -> pd.DataFrame:
    schema = EMPTY_SCHEMAS[schema_name]
    return pd.DataFrame({column: pd.Series(dtype=dtype) for column, dtype in schema.items()})


@dataclass(frozen=True)
class BaselineSource:
    name: str
    table_name: str | None
    description: str
    candidates: list[str]
    file_type: str
    role: str
    transform: Callable[[pd.DataFrame], pd.DataFrame] | None = None


BASELINE_SOURCES: list[BaselineSource] = [
    BaselineSource(
        name="municipio_indices",
        table_name="baseline_municipio_indices",
        description="Current municipio-level scored outputs from the staged index pipeline.",
        candidates=["JupyterNotebooks/outputs/index_pipeline/30_scoring/municipio_indices_scored.csv"],
        file_type="csv",
        role="load_table",
        transform=transform_municipio_indices,
    ),
    BaselineSource(
        name="priority_actions",
        table_name="baseline_priority_actions",
        description="Current ranked municipio action recommendations for operational review.",
        candidates=["JupyterNotebooks/outputs/index_pipeline/50_products/priority_actions.csv"],
        file_type="csv",
        role="load_table",
        transform=transform_priority_actions,
    ),
    BaselineSource(
        name="flood_station_latest",
        table_name="baseline_flood_station_latest",
        description="Latest station-level flood feature outputs from the ingest stage.",
        candidates=["JupyterNotebooks/outputs/index_pipeline/01_ingest/flood_station_latest_features.csv"],
        file_type="csv",
        role="load_table",
        transform=transform_flood_station_latest,
    ),
    BaselineSource(
        name="nws_alerts_enriched",
        table_name="baseline_nws_alerts",
        description="Current enriched NWS alert outputs suitable for alert summary views.",
        candidates=["JupyterNotebooks/outputs/index_pipeline/01_ingest/nws_alerts_enriched.csv"],
        file_type="csv",
        role="load_table",
        transform=transform_nws_alerts,
    ),
    BaselineSource(
        name="terrain_features",
        table_name="baseline_terrain_features",
        description="Terrain Feature Pack v1 municipio outputs for terrain-sidecar analysis.",
        candidates=[
            "outputs/index_pipeline/15_terrain/municipio_terrain_features.parquet",
            "outputs/index_pipeline/15_terrain/municipio_terrain_features.csv",
        ],
        file_type="parquet_or_csv",
        role="load_table",
        transform=transform_terrain_features,
    ),
    BaselineSource(
        name="municipio_adjustment_factors",
        table_name="baseline_municipio_adjustment_factors",
        description="Municipio-level optional adjustment outputs, including age-based overlays, from stage 10.",
        candidates=["JupyterNotebooks/outputs/index_pipeline/10_features/municipio_adjustment_factors.csv"],
        file_type="csv",
        role="load_table",
        transform=transform_municipio_adjustment_factors,
    ),
    BaselineSource(
        name="noaa_station_summary",
        table_name="baseline_noaa_station_summary",
        description="Current NOAA station summary outputs for water-level overview screens.",
        candidates=[
            "outputs/noaa_pr/noaa_pr_station_summary.csv",
            "JupyterNotebooks/outputs/noaa_pr/noaa_pr_station_summary.csv",
        ],
        file_type="csv",
        role="load_table",
        transform=transform_noaa_station_summary,
    ),
    BaselineSource(
        name="terrain_geojson",
        table_name=None,
        description="Terrain municipio GeoJSON retained for future map-friendly extensions.",
        candidates=["outputs/index_pipeline/15_terrain/municipio_terrain_features.geojson"],
        file_type="geojson",
        role="inventory_only",
    ),
    BaselineSource(
        name="noaa_latest_station_geojson",
        table_name=None,
        description="Latest NOAA station GeoJSON retained for future map-friendly extensions.",
        candidates=[
            "outputs/noaa_pr/noaa_pr_latest_station.geojson",
            "JupyterNotebooks/outputs/noaa_pr/noaa_pr_latest_station.geojson",
        ],
        file_type="geojson",
        role="inventory_only",
    ),
]


def write_table(con: duckdb.DuckDBPyConnection, table_name: str, frame: pd.DataFrame) -> None:
    con.register("incoming_frame", frame)
    con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM incoming_frame")
    con.unregister("incoming_frame")


def create_views(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        """
        CREATE OR REPLACE VIEW vw_municipio_risk_summary AS
        SELECT
            mi.municipio,
            mi.municipio_slug,
            mi.phase,
            COALESCE(pa.priority_band, mi.priority_band) AS priority_band,
            mi.priority_index_conf_adj,
            mi.hazard_combined,
            mi.flood_hazard_muni,
            mi.earthquake_hazard_score,
            mi.exposure_score,
            mi.vulnerability_score,
            mi.response_readiness_index,
            mi.recovery_capacity_index,
            mi.confidence_score,
            maf.vulnerability_score_base,
            maf.vulnerability_score_adjusted,
            maf.score_age_vulnerability,
            maf.age_adjustment_points,
            maf.age_adjustment_enabled,
            maf.adjustment_config_version,
            mi.latitude,
            mi.longitude,
            pa.rank AS priority_rank,
            pa.recommended_actions,
            tf.elevation_mean,
            tf.slope_mean,
            tf.local_relief,
            tf.wetness_proxy,
            tf.terrain_data_completeness,
            tf.terrain_confidence_score
        FROM baseline_municipio_indices AS mi
        LEFT JOIN baseline_priority_actions AS pa
            ON mi.municipio_slug = pa.municipio_slug
        LEFT JOIN baseline_terrain_features AS tf
            ON mi.municipio_slug = tf.municipio_slug
        LEFT JOIN baseline_municipio_adjustment_factors AS maf
            ON mi.municipio_slug = maf.municipio_slug
        """
    )
    con.execute(
        """
        CREATE OR REPLACE VIEW vw_station_water_summary AS
        SELECT
            fs.station_id,
            COALESCE(ns.station_name, fs.station_name) AS station_name,
            fs.shefcode,
            COALESCE(ns.lat, fs.lat) AS latitude,
            COALESCE(ns.lon, fs.lon) AS longitude,
            fs.latest_time_utc,
            fs.latest_water_level,
            fs.rise_rate_per_hour,
            fs.flood_hazard_final,
            fs.nws_global_alert_score,
            ns.obs_count,
            ns.peak_value,
            ns.mean_value,
            ns.latest_value AS noaa_latest_value
        FROM baseline_flood_station_latest AS fs
        LEFT JOIN baseline_noaa_station_summary AS ns
            ON CAST(fs.station_id AS VARCHAR) = CAST(ns.station_id AS VARCHAR)
        """
    )
    con.execute(
        """
        CREATE OR REPLACE VIEW vw_alerts_summary AS
        SELECT
            event,
            severity,
            urgency,
            certainty,
            alert_score,
            sent,
            ends,
            area_desc,
            headline
        FROM baseline_nws_alerts
        ORDER BY alert_score DESC NULLS LAST, sent DESC NULLS LAST
        """
    )
    con.execute(
        """
        CREATE OR REPLACE VIEW vw_terrain_summary AS
        SELECT
            municipio_name,
            municipio_slug,
            elevation_mean,
            slope_mean,
            slope_p90,
            local_relief,
            wetness_proxy,
            distance_to_stream_km,
            coastal_inundation_flag,
            soil_runoff_potential,
            land_cover_runoff_modifier,
            terrain_data_completeness,
            terrain_confidence_score,
            run_timestamp_utc
        FROM baseline_terrain_features
        """
    )
    con.execute(
        """
        CREATE OR REPLACE VIEW vw_vulnerability_adjustments AS
        SELECT
            municipio,
            municipio_key,
            municipio_slug,
            child_under_5_population,
            elderly_65_plus_population,
            child_rate,
            elderly_65_plus_rate,
            age_dependency_rate,
            score_child_vulnerability,
            score_elderly_vulnerability,
            score_age_vulnerability,
            age_adjustment_points,
            age_adjustment_enabled,
            vulnerability_score_base,
            vulnerability_score_adjusted,
            adjustment_config_version
        FROM baseline_municipio_adjustment_factors
        ORDER BY age_adjustment_points DESC NULLS LAST, municipio
        """
    )
    con.execute(
        """
        CREATE OR REPLACE VIEW vw_baseline_source_status AS
        SELECT
            name,
            role,
            file_type,
            status,
            row_count,
            loaded_path,
            description
        FROM baseline_source_inventory
        ORDER BY
            CASE status
                WHEN 'loaded' THEN 1
                WHEN 'inventory_only' THEN 2
                WHEN 'missing' THEN 3
                ELSE 4
            END,
            name
        """
    )


def build_duckdb_baseline(repo_root: Path, db_path: Path) -> dict[str, object]:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    run_timestamp = utc_now()
    inventory_rows: list[dict[str, object]] = []

    with duckdb.connect(str(db_path)) as con:
        for source in BASELINE_SOURCES:
            chosen_path = first_existing_path(repo_root, source.candidates)
            row: dict[str, object] = {
                "name": source.name,
                "role": source.role,
                "file_type": source.file_type,
                "description": source.description,
                "loaded_path": str(chosen_path.relative_to(repo_root)) if chosen_path else None,
                "row_count": 0,
                "status": "missing",
                "run_timestamp_utc": run_timestamp,
            }

            if chosen_path is None:
                if source.table_name is not None:
                    write_table(con, source.table_name, empty_frame(source.table_name))
                inventory_rows.append(row)
                continue

            if source.role == "inventory_only":
                row["status"] = "inventory_only"
                inventory_rows.append(row)
                continue

            frame = load_frame(chosen_path)
            if source.transform is not None:
                frame = source.transform(frame)
            write_table(con, source.table_name, frame)
            row["status"] = "loaded"
            row["row_count"] = int(len(frame))
            inventory_rows.append(row)

        inventory = pd.DataFrame(inventory_rows)
        write_table(con, "baseline_source_inventory", inventory)
        create_views(con)

    summary = {
        "run_timestamp_utc": run_timestamp,
        "db_path": str(db_path.relative_to(repo_root)),
        "loaded_sources": [row["name"] for row in inventory_rows if row["status"] == "loaded"],
        "missing_sources": [row["name"] for row in inventory_rows if row["status"] == "missing"],
        "inventory_only_sources": [row["name"] for row in inventory_rows if row["status"] == "inventory_only"],
    }
    summary_path = db_path.with_name("duckdb_baseline_build_summary.json")
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the local DuckDB workbench database from current curated outputs.")
    parser.add_argument("--repo-root", default=None, help="Optional repo-root override.")
    parser.add_argument(
        "--db-path",
        default=None,
        help="Optional local DuckDB output path. Defaults to data/local/duckdb/spring2026daen_baseline.duckdb",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = find_repo_root(Path(args.repo_root).resolve()) if args.repo_root else find_repo_root()
    db_path = (
        Path(args.db_path).resolve()
        if args.db_path
        else repo_root / "data" / "local" / "duckdb" / "spring2026daen_baseline.duckdb"
    )
    summary = build_duckdb_baseline(repo_root=repo_root, db_path=db_path)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
