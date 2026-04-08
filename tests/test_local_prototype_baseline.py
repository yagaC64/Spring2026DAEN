from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import duckdb
import pandas as pd

from scripts.build_duckdb_baseline import build_duckdb_baseline


REPO_ROOT = Path(__file__).resolve().parents[1]


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)


def _make_temp_repo(tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True)
    (repo_root / "README.md").write_text("# temp repo\n")
    (repo_root / "JupyterNotebooks").mkdir(parents=True)

    _write_csv(
        repo_root / "JupyterNotebooks/outputs/index_pipeline/30_scoring/municipio_indices_scored.csv",
        [
            {
                "municipio": "San Juan",
                "municipio_key": "san juan",
                "latitude": 18.426281,
                "longitude": -66.062495,
                "hazard_combined": 60.0,
                "flood_hazard_muni": 60.0,
                "earthquake_hazard_score": 9.4,
                "exposure_score": 100.0,
                "vulnerability_score": 58.8,
                "resilience_index": 34.8,
                "response_readiness_index": 38.4,
                "recovery_capacity_index": 27.7,
                "risk_index_raw": 35.2,
                "priority_index": 46.8,
                "priority_index_conf_adj": 46.2,
                "confidence_score": 97.7,
                "confidence_0_1": 0.97,
                "priority_band": "Green",
                "phase": "DURING",
            }
        ],
    )
    _write_csv(
        repo_root / "JupyterNotebooks/outputs/index_pipeline/50_products/priority_actions.csv",
        [
            {
                "rank": 1,
                "municipio": "San Juan",
                "priority_band": "Green",
                "priority_index_conf_adj": 46.2,
                "hazard_combined": 60.0,
                "flood_hazard_muni": 60.0,
                "earthquake_hazard_score": 9.4,
                "vulnerability_score": 58.8,
                "response_readiness_index": 38.4,
                "recovery_capacity_index": 27.7,
                "confidence_score": 97.7,
                "recommended_actions": "Increase responder readiness",
            }
        ],
    )
    _write_csv(
        repo_root / "JupyterNotebooks/outputs/index_pipeline/01_ingest/flood_station_latest_features.csv",
        [
            {
                "station_id": "9755371",
                "station_name": "San Juan",
                "shefcode": "SJUP4",
                "lat": 18.45,
                "lon": -66.11,
                "latest_time_utc": "2026-03-26T20:00:00Z",
                "latest_water_level": 0.2,
                "rise_rate_per_hour": 0.1,
                "minor": 6.66,
                "moderate": 7.63,
                "major": 8.86,
                "exceed_ratio": 0.0,
                "exceed_score": 0.0,
                "rise_score": 15.0,
                "sensor_hazard_score": 15.0,
                "nws_global_alert_score": 60.0,
                "flood_hazard_final": 60.0,
                "catalog_pull_utc": "2026-03-26T20:00:10Z",
            }
        ],
    )
    _write_csv(
        repo_root / "JupyterNotebooks/outputs/index_pipeline/01_ingest/nws_alerts_enriched.csv",
        [
            {
                "id": "alert-1",
                "event": "Flood Watch",
                "severity": "Moderate",
                "urgency": "Expected",
                "certainty": "Likely",
                "headline": "Flood Watch issued",
                "sent": "2026-03-26T20:00:00Z",
                "onset": "2026-03-26T20:00:00Z",
                "ends": "2026-03-27T08:00:00Z",
                "status": "Actual",
                "area_desc": "San Juan",
                "ugc_list": "PRZ001",
                "alert_score": 60.0,
            }
        ],
    )
    _write_csv(
        repo_root / "outputs/index_pipeline/15_terrain/municipio_terrain_features.csv",
        [
            {
                "municipio_id": "72001",
                "municipio_name": "San Juan",
                "municipio_key": "san_juan",
                "elevation_mean": 12.0,
                "slope_mean": 3.5,
                "slope_p90": 7.0,
                "local_relief": 20.0,
                "wetness_proxy": 1.2,
                "distance_to_stream_km": 2.0,
                "coastal_inundation_flag": 1.0,
                "coastal_inundation_depth_mean": 0.3,
                "soil_runoff_potential": 0.7,
                "land_cover_runoff_modifier": 0.6,
                "terrain_data_completeness": 100.0,
                "terrain_confidence_score": 100.0,
                "config_version": "1.0",
                "run_timestamp_utc": "2026-03-26T20:00:00Z",
            }
        ],
    )
    _write_csv(
        repo_root / "JupyterNotebooks/outputs/index_pipeline/10_features/municipio_adjustment_factors.csv",
        [
            {
                "municipio": "San Juan",
                "municipio_key": "san_juan",
                "municipio_slug": "san_juan",
                "child_under_5_population": 1200.0,
                "elderly_65_plus_population": 3400.0,
                "child_rate": 0.08,
                "elderly_65_plus_rate": 0.22,
                "age_dependency_rate": 0.30,
                "score_child_vulnerability": 55.0,
                "score_elderly_vulnerability": 78.0,
                "score_age_vulnerability": 68.8,
                "age_adjustment_points": 8.3,
                "age_adjustment_enabled": True,
                "vulnerability_score_base": 58.8,
                "vulnerability_score_adjusted": 67.1,
                "adjustment_config_version": "1.0",
            }
        ],
    )
    _write_csv(
        repo_root / "outputs/noaa_pr/noaa_pr_station_summary.csv",
        [
            {
                "station_id": "9755371",
                "station_name": "San Juan",
                "latest_time_utc": "2026-03-26T20:00:00Z",
                "latest_value": 0.21,
                "latest_quality": "p",
                "lat": 18.45,
                "lon": -66.11,
                "minor": 6.66,
                "moderate": 7.63,
                "major": 8.86,
                "obs_count": 10,
                "peak_value": 0.58,
                "mean_value": 0.28,
            }
        ],
    )
    (repo_root / "outputs/index_pipeline/15_terrain/municipio_terrain_features.geojson").write_text(
        '{"type":"FeatureCollection","features":[]}\n'
    )
    (repo_root / "outputs/noaa_pr/noaa_pr_latest_station.geojson").write_text(
        '{"type":"FeatureCollection","features":[]}\n'
    )
    return repo_root


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def test_build_duckdb_baseline_from_curated_outputs(tmp_path: Path) -> None:
    repo_root = _make_temp_repo(tmp_path)
    db_path = repo_root / "data/local/duckdb/test_baseline.duckdb"

    summary = build_duckdb_baseline(repo_root=repo_root, db_path=db_path)

    assert db_path.exists()
    assert set(summary["loaded_sources"]) == {
        "municipio_indices",
        "priority_actions",
        "flood_station_latest",
        "nws_alerts_enriched",
        "terrain_features",
        "municipio_adjustment_factors",
        "noaa_station_summary",
    }

    con = duckdb.connect(str(db_path), read_only=True)
    assert con.execute("SELECT COUNT(*) FROM vw_municipio_risk_summary").fetchone()[0] == 1
    top_row = con.execute(
        "SELECT municipio, recommended_actions, terrain_data_completeness, age_adjustment_points FROM vw_municipio_risk_summary"
    ).fetchone()
    assert top_row[0] == "San Juan"
    assert "Increase responder readiness" in top_row[1]
    assert float(top_row[2]) == 100.0
    assert float(top_row[3]) == 8.3
    con.close()


def test_streamlit_app_starts_with_override_db_path(tmp_path: Path) -> None:
    repo_root = _make_temp_repo(tmp_path)
    db_path = repo_root / "data/local/duckdb/test_baseline.duckdb"
    build_duckdb_baseline(repo_root=repo_root, db_path=db_path)

    port = _free_port()
    env = os.environ.copy()
    env["SPRING2026DAEN_DUCKDB_PATH"] = str(db_path)
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(REPO_ROOT / "app/streamlit_app.py"),
            "--server.headless",
            "true",
            "--server.port",
            str(port),
        ],
        cwd=str(REPO_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        deadline = time.time() + 20
        last_output = ""
        while time.time() < deadline:
            if proc.poll() is not None:
                if proc.stdout is not None:
                    last_output = proc.stdout.read()
                raise AssertionError(f"Streamlit exited early.\n{last_output}")
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}", timeout=1) as response:
                    body = response.read().decode("utf-8", errors="ignore")
                    assert "Streamlit" in body or response.status == 200
                    return
            except (urllib.error.URLError, TimeoutError):
                time.sleep(0.5)
        if proc.stdout is not None:
            last_output = proc.stdout.read()
        raise AssertionError(f"Streamlit did not become reachable in time.\n{last_output}")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=10)
