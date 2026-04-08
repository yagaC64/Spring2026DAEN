from __future__ import annotations

import os
import signal
import sys
import threading
import time
from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).resolve().parent
EARLY_REPO_ROOT = APP_DIR.parent
if str(EARLY_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(EARLY_REPO_ROOT))

from scripts.factors.social_adjustments import (
    build_adjustment_factor_reference,
    load_social_adjustment_spec,
)


def find_repo_root(start: Path | None = None) -> Path:
    probe = (start or Path.cwd()).resolve()
    for candidate in [probe, *probe.parents]:
        if (candidate / "README.md").exists() and (candidate / "JupyterNotebooks").exists():
            return candidate
    return probe


def load_view(con: duckdb.DuckDBPyConnection, query: str) -> pd.DataFrame:
    try:
        return con.execute(query).df()
    except duckdb.Error:
        return pd.DataFrame()


def request_local_shutdown(delay_seconds: float = 1.5) -> None:
    if st.session_state.get("_shutdown_requested"):
        return
    st.session_state["_shutdown_requested"] = True

    def _shutdown() -> None:
        time.sleep(delay_seconds)
        os.kill(os.getpid(), signal.SIGTERM)

    threading.Thread(target=_shutdown, daemon=True).start()


def render_shutdown_notice() -> None:
    st.success(
        "Local app closed successfully. Any active DuckDB connection was released cleanly and the server is shutting down."
    )
    st.info("This page will stop responding in a moment. You can close this browser tab.")
    st.markdown(
        """
        <script>
        window.setTimeout(function() {
          try { window.close(); } catch (e) {}
        }, 1800);
        </script>
        """,
        unsafe_allow_html=True,
    )


REPO_ROOT = find_repo_root()
DEFAULT_DB_PATH = Path(
    os.environ.get(
        "SPRING2026DAEN_DUCKDB_PATH",
        str(REPO_ROOT / "data" / "local" / "duckdb" / "spring2026daen_baseline.duckdb"),
    )
).expanduser()
ADJUSTMENT_SPEC = load_social_adjustment_spec(REPO_ROOT)
ADJUSTMENT_REFERENCE_DF = build_adjustment_factor_reference(ADJUSTMENT_SPEC)

st.set_page_config(page_title="PR Hazard and Readiness Analysis Workbench", layout="wide")

st.title("PR Hazard and Readiness Analysis Workbench")
st.caption(
    "Local/internal workbench only. This app complements the notebook-first workflow and does not replace the "
    "current GitHub Pages public dashboard."
)

db_path_input = st.sidebar.text_input("DuckDB path", str(DEFAULT_DB_PATH))
db_path = Path(db_path_input).expanduser()

st.sidebar.markdown("### Filters")
top_n = st.sidebar.slider("Top municipios in chart", min_value=5, max_value=25, value=10, step=1)
st.sidebar.markdown("### Session")
quit_requested = st.sidebar.button(
    "Quit Local App",
    use_container_width=True,
    help="Close the local DuckDB connection cleanly and stop this local Streamlit server.",
)

if not db_path.exists():
    if quit_requested:
        render_shutdown_notice()
        request_local_shutdown()
        st.stop()
    st.warning(
        "DuckDB baseline not found yet. Build it first with `python scripts/build_duckdb_baseline.py`, "
        "then reload this app."
    )
    st.stop()

con: duckdb.DuckDBPyConnection | None = None
try:
    con = duckdb.connect(str(db_path), read_only=True)

    if quit_requested:
        con.close()
        con = None
        render_shutdown_notice()
        request_local_shutdown()
        st.stop()

    municipio_df = load_view(con, "SELECT * FROM vw_municipio_risk_summary")
    alerts_df = load_view(con, "SELECT * FROM vw_alerts_summary")
    stations_df = load_view(con, "SELECT * FROM vw_station_water_summary")
    source_status_df = load_view(con, "SELECT * FROM vw_baseline_source_status")
    adjustments_df = load_view(con, "SELECT * FROM vw_vulnerability_adjustments")

    phase_options = sorted(
        [value for value in municipio_df.get("phase", pd.Series(dtype="string")).dropna().unique().tolist()]
    )
    selected_phases = st.sidebar.multiselect("Phase", options=phase_options, default=phase_options)

    band_options = sorted(
        [value for value in municipio_df.get("priority_band", pd.Series(dtype="string")).dropna().unique().tolist()]
    )
    selected_bands = st.sidebar.multiselect("Priority band", options=band_options, default=band_options)

    municipio_search = st.sidebar.text_input("Municipio contains", "")

    filtered_municipios = municipio_df.copy()
    if selected_phases:
        filtered_municipios = filtered_municipios[filtered_municipios["phase"].isin(selected_phases)]
    if selected_bands:
        filtered_municipios = filtered_municipios[filtered_municipios["priority_band"].isin(selected_bands)]
    if municipio_search.strip():
        filtered_municipios = filtered_municipios[
            filtered_municipios["municipio"].fillna("").str.contains(municipio_search.strip(), case=False)
        ]

    metric_cols = st.columns(5)
    metric_cols[0].metric("Filtered municipios", f"{len(filtered_municipios):,}")
    metric_cols[1].metric(
        "Mean adj. priority",
        f"{filtered_municipios['priority_index_conf_adj'].mean():.1f}" if not filtered_municipios.empty else "n/a",
    )
    metric_cols[2].metric("Alerts loaded", f"{len(alerts_df):,}")
    metric_cols[3].metric("Stations loaded", f"{len(stations_df):,}")
    metric_cols[4].metric(
        "Mean age adj. points",
        f"{adjustments_df['age_adjustment_points'].mean():.1f}" if not adjustments_df.empty else "n/a",
    )

    top_municipio = (
        filtered_municipios.sort_values("priority_index_conf_adj", ascending=False).head(1)["municipio"].iloc[0]
        if not filtered_municipios.empty
        else "n/a"
    )
    st.markdown(f"**Current top municipio in this filtered view:** `{top_municipio}`")

    left_col, right_col = st.columns([1.2, 1])

    with left_col:
        st.subheader("Municipio Summary Table")
        table_columns = [
            "municipio",
            "phase",
            "priority_band",
            "priority_index_conf_adj",
            "hazard_combined",
            "vulnerability_score",
            "response_readiness_index",
            "terrain_data_completeness",
            "recommended_actions",
        ]
        available_columns = [column for column in table_columns if column in filtered_municipios.columns]
        st.dataframe(
            filtered_municipios[available_columns].sort_values("priority_index_conf_adj", ascending=False),
            use_container_width=True,
            hide_index=True,
        )

    with right_col:
        st.subheader("Top Municipios by Adjusted Priority")
        if filtered_municipios.empty:
            st.info("No municipios match the current filters.")
        else:
            chart_df = (
                filtered_municipios.sort_values("priority_index_conf_adj", ascending=False)
                .head(top_n)[["municipio", "priority_index_conf_adj"]]
                .set_index("municipio")
            )
            st.bar_chart(chart_df)

    if {"latitude", "longitude"}.issubset(filtered_municipios.columns):
        map_df = filtered_municipios[["municipio", "latitude", "longitude"]].dropna().rename(
            columns={"latitude": "lat", "longitude": "lon"}
        )
        if not map_df.empty:
            st.subheader("Municipio Map Preview")
            st.map(map_df[["lat", "lon"]])

    station_col, alert_col = st.columns(2)

    with station_col:
        st.subheader("Station Snapshot")
        if stations_df.empty:
            st.info("No station summary view is available in the current baseline build.")
        else:
            station_cols = [
                "station_id",
                "station_name",
                "latest_water_level",
                "rise_rate_per_hour",
                "flood_hazard_final",
                "obs_count",
            ]
            station_cols = [column for column in station_cols if column in stations_df.columns]
            st.dataframe(
                stations_df[station_cols].sort_values("flood_hazard_final", ascending=False),
                use_container_width=True,
                hide_index=True,
            )

    with alert_col:
        st.subheader("Alert Snapshot")
        if alerts_df.empty:
            st.info("No alert summary view is available in the current baseline build.")
        else:
            alert_cols = ["event", "severity", "alert_score", "sent", "ends", "area_desc"]
            alert_cols = [column for column in alert_cols if column in alerts_df.columns]
            st.dataframe(alerts_df[alert_cols], use_container_width=True, hide_index=True)

    with st.expander("Baseline Source Status"):
        if source_status_df.empty:
            st.info("Source status view is unavailable.")
        else:
            st.dataframe(source_status_df, use_container_width=True, hide_index=True)

    with st.expander("Adjustment Factors and Age Overlay"):
        st.caption("Shared factor settings used by the staged notebooks and the local workbench.")
        st.dataframe(ADJUSTMENT_REFERENCE_DF, use_container_width=True, hide_index=True)
        if adjustments_df.empty:
            st.info("No municipio adjustment output is currently loaded into the local DuckDB workbench.")
        else:
            adjustment_columns = [
                "municipio",
                "child_rate",
                "elderly_65_plus_rate",
                "score_age_vulnerability",
                "age_adjustment_points",
                "vulnerability_score_base",
                "vulnerability_score_adjusted",
                "adjustment_config_version",
            ]
            adjustment_columns = [column for column in adjustment_columns if column in adjustments_df.columns]
            st.dataframe(
                adjustments_df[adjustment_columns],
                use_container_width=True,
                hide_index=True,
            )
finally:
    if con is not None:
        con.close()
