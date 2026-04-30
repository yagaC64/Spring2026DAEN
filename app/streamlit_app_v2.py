"""
streamlit_app_v2.py
Puerto Rico Community Flood Early Warning System — Dashboard V2
Spring2026DAEN · Community Decision-Support Interface

Provides live decision support for emergency managers and community leaders
during flood events in Puerto Rico. Connects directly to a local DuckDB
pipeline database populated by the staged Jupyter notebook pipeline.

Tabs:
    Overview Map     — pydeck risk map of all 78 municipios
    Risk Rankings    — filterable priority table + Plotly bar chart
    Live Conditions  — active NWS alerts + NOAA water-level stations
    Ask the Data     — natural-language chatbot backed by live DuckDB data
    SQL Explorer     — read-only SELECT interface for ad-hoc analysis

Usage:
    streamlit run app/streamlit_app_v2.py

Environment:
    SPRING2026DAEN_DUCKDB_PATH  (optional) override the default DuckDB path
"""

from __future__ import annotations

import difflib
import json
import os
import re
import signal
import threading
import time
from pathlib import Path

import duckdb
import pandas as pd
import pydeck as pdk
import streamlit as st

try:
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False


# ---------------------------------------------------------------------------
# Map tile providers — CARTO free tiles (no Mapbox token required)
# ---------------------------------------------------------------------------
CARTO_DARK     = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"
CARTO_VOYAGER  = "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json"
CARTO_POSITRON = "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"

# Default map centre — geographic centroid of Puerto Rico
PR_LAT  = 18.22
PR_LON  = -66.59
PR_ZOOM = 7.8

# ---------------------------------------------------------------------------
# Risk tier thresholds
# These score boundaries define the four priority bands used throughout the
# pipeline, the dashboard, and all recommended-action outputs.
# ---------------------------------------------------------------------------
TIER_HIGH     = 33.0   # priority_index_conf_adj >= 33  → High
TIER_ELEVATED = 23.0   # >= 23 and < 33                → Elevated
TIER_MODERATE = 18.0   # >= 18 and < 23                → Monitor
                       # < 18                           → Low

# Visual metadata for each risk tier (colours, labels, emojis)
TIER_META: dict[str, dict] = {
    "High":     {"rgb": [239, 68,  68,  230], "emoji": "🔴", "hex": "#ef4444", "label": "High Priority"},
    "Elevated": {"rgb": [249, 115, 22,  210], "emoji": "🟠", "hex": "#f97316", "label": "Elevated"},
    "Monitor":  {"rgb": [234, 179,  8,  190], "emoji": "🟡", "hex": "#eab308", "label": "Monitor"},
    "Low":      {"rgb": [34,  197, 94,  160], "emoji": "🟢", "hex": "#22c55e", "label": "Low"},
}

# ---------------------------------------------------------------------------
# Theme palettes — dark and light variants
# Each key maps to a CSS colour token used in the inline-HTML sections.
# ---------------------------------------------------------------------------
PALETTE: dict[str, dict[str, str]] = {
    "dark": {
        "bg":         "#080d18",
        "card":       "#0d1526",
        "card2":      "#111d33",
        "border":     "#1e3050",
        "text":       "#e2e8f0",
        "muted":      "#64748b",
        "accent":     "#3b82f6",
        "divider":    "#1a2845",
        "input_bg":   "#0d1526",
        "plot_bg":    "#080d18",
        "plot_paper": "#080d18",
        "plot_font":  "#e2e8f0",
        "plot_grid":  "#1e3050",
    },
    "light": {
        "bg":         "#f8fafc",
        "card":       "#ffffff",
        "card2":      "#f1f5f9",
        "border":     "#cbd5e1",
        "text":       "#0f172a",
        "muted":      "#64748b",
        "accent":     "#2563eb",
        "divider":    "#e2e8f0",
        "input_bg":   "#ffffff",
        "plot_bg":    "#ffffff",
        "plot_paper": "#ffffff",
        "plot_font":  "#0f172a",
        "plot_grid":  "#e2e8f0",
    },
}

# Quick-question shortcuts shown above the chat input on the Ask the Data tab
QUICK_QUESTIONS: list[str] = [
    "Which areas need help most?",
    "Any active flood alerts?",
    "Most vulnerable communities?",
    "Where should teams be deployed?",
    "Which areas face earthquake risk?",
    "Give me an overall snapshot",
]

# Navigation guide text shown below each tab name in the sidebar
TAB_INFO: dict[str, str] = {
    "🗺️ Overview Map": (
        "Interactive map of Puerto Rico. Each circle is a municipio — color = risk level, "
        "size = population. Use the toggles above the map to add label and heatmap layers. "
        "Click the dropdown to see detailed metrics."
    ),
    "⚠️ Risk Rankings": (
        "Full ranked list of all 78 municipios. Filter by risk level, read plain-English "
        "explanations of what drives each score, and use the slider to control chart depth."
    ),
    "🌊 Live Conditions": (
        "Current NWS weather alerts and water-level readings from 6 active flood monitoring "
        "stations. Each station shows current level vs minor/moderate/major flood thresholds."
    ),
    "💬 Ask the Data": (
        "Natural-language assistant backed by live DuckDB data. Ask about any municipio, "
        "risk level, vulnerability, alerts, or earthquake exposure. No API key needed."
    ),
    "🔍 SQL Explorer": (
        "Direct SQL access to the DuckDB pipeline. Choose from preset queries or write "
        "your own SELECT. Results are downloadable as CSV."
    ),
}

# Chatbot intent keywords — each intent maps to (keyword, weight) pairs.
# Scores are additive; the highest-scoring intent wins.
INTENTS: dict[str, list[tuple[str, float]]] = {
    "top_priority": [
        ("risk", 2.0), ("priority", 2.5), ("danger", 2.0), ("urgent", 2.0),
        ("worst", 1.8), ("help", 1.5), ("top", 1.5), ("highest", 2.0),
        ("most at risk", 3.0), ("need help", 2.5), ("attention", 1.5),
    ],
    "alerts": [
        ("alert", 3.0), ("warning", 2.5), ("watch", 2.0), ("advisory", 2.5),
        ("nws", 2.0), ("flood watch", 3.0), ("active", 1.5),
    ],
    "vulnerability": [
        ("vulnerable", 3.0), ("poverty", 2.5), ("poor", 2.0), ("income", 2.0),
        ("vehicle", 2.0), ("community", 1.5), ("people", 1.5), ("housing", 2.0),
    ],
    "actions": [
        ("deploy", 2.5), ("team", 2.0), ("resource", 2.0), ("send", 2.0),
        ("action", 2.5), ("recommend", 2.5), ("what to do", 3.0), ("response", 2.0),
    ],
    "stations": [
        ("station", 3.0), ("water level", 3.0), ("gauge", 2.5), ("river", 2.0),
        ("rising", 2.0), ("water", 1.5), ("tide", 2.0), ("sensor", 2.0),
    ],
    "earthquake": [
        ("earthquake", 3.0), ("seismic", 3.0), ("quake", 3.0), ("tremor", 2.5),
    ],
    "flood": [
        ("flood", 2.5), ("rain", 2.0), ("rainfall", 2.0), ("surge", 2.0),
    ],
    "snapshot": [
        ("snapshot", 3.0), ("overview", 2.5), ("summary", 2.5),
        ("how many", 2.0), ("total", 2.0), ("status", 1.5),
    ],
}


# ===========================================================================
# UTILITY FUNCTIONS
# ===========================================================================

def find_repo_root(start: Path | None = None) -> Path:
    """Walk parent directories to find the repo root (contains README.md + JupyterNotebooks)."""
    probe = (start or Path.cwd()).resolve()
    for candidate in [probe, *probe.parents]:
        if (candidate / "README.md").exists() and (candidate / "JupyterNotebooks").exists():
            return candidate
    return probe


def load_view(con: duckdb.DuckDBPyConnection, query: str) -> pd.DataFrame:
    """Execute a SELECT query and return a DataFrame, or an empty DataFrame on error."""
    try:
        return con.execute(query).df()
    except duckdb.Error:
        return pd.DataFrame()


def risk_tier(score: float) -> str:
    """Map a numeric priority score to its tier label (High / Elevated / Monitor / Low)."""
    if score >= TIER_HIGH:
        return "High"
    if score >= TIER_ELEVATED:
        return "Elevated"
    if score >= TIER_MODERATE:
        return "Monitor"
    return "Low"


def t_emoji(tier: str) -> str:
    """Return the coloured circle emoji for a risk tier."""
    return TIER_META.get(tier, {}).get("emoji", "⚪")


def t_hex(tier: str) -> str:
    """Return the hex colour string for a risk tier."""
    return TIER_META.get(tier, {}).get("hex", "#888888")


def t_rgb(tier: str) -> list[int]:
    """Return the RGBA list for a risk tier (used by pydeck layers)."""
    return TIER_META.get(tier, {}).get("rgb", [128, 128, 128, 180])


def t_label(tier: str) -> str:
    """Return the human-readable label for a risk tier."""
    return TIER_META.get(tier, {}).get("label", tier)


def fmt(val, dec: int = 1, prefix: str = "", suffix: str = "") -> str:
    """Format a numeric value with optional prefix/suffix; returns 'n/a' on failure."""
    try:
        return f"{prefix}{float(val):.{dec}f}{suffix}"
    except (TypeError, ValueError):
        return "n/a"


def pct(val) -> str:
    """Format a decimal fraction as a percentage string (e.g. 0.35 → '35.0%')."""
    try:
        return f"{float(val) * 100:.1f}%"
    except (TypeError, ValueError):
        return "n/a"


def why_risk(row: pd.Series) -> str:
    """
    Generate a plain-English explanation of what drives a municipio's risk score.
    Returns a ' · ' separated list of contributing factors, or a generic fallback.
    """
    parts = []
    hazard    = float(row.get("hazard_combined")          or 0)
    eq_score  = float(row.get("earthquake_hazard_score")  or 0)
    vuln      = float(row.get("vulnerability_score")      or 0)
    readiness = float(row.get("response_readiness_index") or 0)

    if hazard >= 80:
        parts.append("Extreme flood hazard")
    elif hazard >= 60:
        parts.append("High flood hazard")

    if eq_score >= 50:
        parts.append("High seismic risk")
    elif eq_score >= 25:
        parts.append("Moderate seismic risk")

    if vuln >= 60:
        parts.append("Highly vulnerable population")
    elif vuln >= 45:
        parts.append("Elevated vulnerability")

    if readiness <= 30:
        parts.append("Low response readiness")

    return " · ".join(parts) if parts else "Multiple compounding factors"


def sev_color(severity: str) -> str:
    """Map an NWS severity label to a hex colour for visual coding."""
    return {
        "Extreme":  "#ef4444",
        "Severe":   "#f97316",
        "Moderate": "#eab308",
        "Minor":    "#22c55e",
    }.get(severity, "#94a3b8")


def request_shutdown(delay: float = 1.5) -> None:
    """Send SIGTERM to this process after a short delay so the UI can update first."""
    if st.session_state.get("_shutdown"):
        return
    st.session_state["_shutdown"] = True

    def _kill():
        time.sleep(delay)
        os.kill(os.getpid(), signal.SIGTERM)

    threading.Thread(target=_kill, daemon=True).start()


# ===========================================================================
# CHATBOT — Weighted intent scoring + fuzzy municipio matching
# ===========================================================================

def _intent(query: str) -> str:
    """
    Score a user query against each intent keyword set.
    Returns the highest-scoring intent name, or 'unknown' if nothing matches.
    """
    q = query.lower()
    scores = {k: 0.0 for k in INTENTS}
    for intent, keywords in INTENTS.items():
        for kw, weight in keywords:
            if kw in q:
                scores[intent] += weight
    best = max(scores, key=lambda k: scores[k])
    return best if scores[best] > 0 else "unknown"


def _fuzzy_muni(query: str, municipios: list[str]) -> str | None:
    """
    Try to match a municipio name (or close variant) anywhere in the query.
    Handles accented characters and partial token matches via difflib.
    Returns the matched municipio name, or None if no match is found.
    """
    q = query.lower()
    # Normalise accented characters for comparison
    accent_table = str.maketrans("áéíóúüñÁÉÍÓÚÜÑ", "aeiouunAEIOUUN")
    q_plain = q.translate(accent_table)

    # Exact substring match (with and without accents)
    for m in municipios:
        m_plain = m.lower().translate(accent_table)
        if m.lower() in q or m_plain in q_plain:
            return m

    # Token-level fuzzy match for longer words (avoids false positives on short tokens)
    for token in re.findall(r"\b\w+\b", q_plain):
        if len(token) < 4:
            continue
        muni_plain = [m.lower().translate(accent_table) for m in municipios]
        hits = difflib.get_close_matches(token, muni_plain, n=1, cutoff=0.82)
        if hits:
            return municipios[muni_plain.index(hits[0])]

    return None


def _q(con: duckdb.DuckDBPyConnection, sql: str, params: list | None = None) -> pd.DataFrame:
    """Execute a parameterised query and return a DataFrame."""
    return con.execute(sql, params or []).df()


# -- Chatbot response generators --------------------------------------------

def _resp_top(con, n: int = 5) -> str:
    """Return a ranked list of the top-n highest-priority municipios."""
    df = _q(con, (
        f"SELECT municipio, priority_index_conf_adj, hazard_combined, "
        f"vulnerability_score, recommended_actions "
        f"FROM vw_priority_ranking ORDER BY overall_rank LIMIT {n}"
    ))
    if df.empty:
        return "No priority data available."
    lines = [f"📊 **Top {n} highest-priority municipios right now:**\n"]
    for _, row in df.iterrows():
        tier   = risk_tier(row["priority_index_conf_adj"])
        action = str(row.get("recommended_actions") or "Monitor").split("|")[0].strip()
        lines.append(
            f"{t_emoji(tier)} **{row['municipio']}** — "
            f"Score `{row['priority_index_conf_adj']:.1f}` · "
            f"Hazard `{row['hazard_combined']:.0f}` · "
            f"Vulnerability `{row['vulnerability_score']:.0f}`  \n  👉 *{action}*"
        )
    lines.append("\n💡 *See the Risk Rankings tab for the full list.*")
    return "\n\n".join(lines)


def _resp_alerts(con) -> str:
    """Return a summary of active NWS weather alerts."""
    df = _q(con, "SELECT event, severity, area_desc, sent, ends FROM vw_alerts_summary")
    if df.empty:
        return "✅ **No active NWS alerts** for Puerto Rico right now."
    lines = [f"⚠️ **{len(df)} active NWS alert(s):**\n"]
    for _, row in df.iterrows():
        lines.append(
            f"**{row['event']}** ({row.get('severity', '?')})  \n"
            f"  📍 {str(row.get('area_desc', ''))[:100]}  \n"
            f"  ⏰ Expires `{str(row.get('ends', ''))[:16]}`"
        )
    return "\n\n".join(lines)


def _resp_vuln(con, n: int = 5) -> str:
    """Return the most vulnerable communities ranked by vulnerability score."""
    df = _q(con, (
        f"SELECT municipio, vulnerability_score, poverty_rate, no_vehicle_rate, population "
        f"FROM vw_vulnerability_breakdown ORDER BY vulnerability_score DESC LIMIT {n}"
    ))
    if df.empty:
        return "No vulnerability data."
    lines = [f"🏘️ **Top {n} most vulnerable communities:**\n"]
    for _, row in df.iterrows():
        lines.append(
            f"🔴 **{row['municipio']}** — Vulnerability `{row['vulnerability_score']:.0f}/100`  \n"
            f"  👥 Pop: **{int(row.get('population', 0)):,}** · "
            f"Poverty: **{pct(row.get('poverty_rate'))}** · "
            f"No vehicle: **{pct(row.get('no_vehicle_rate'))}**"
        )
    return "\n\n".join(lines)


def _resp_actions(con, n: int = 5) -> str:
    """Return recommended response actions for the top-priority municipios."""
    df = _q(con, (
        f"SELECT municipio, priority_index_conf_adj, recommended_actions "
        f"FROM vw_priority_ranking ORDER BY overall_rank LIMIT {n}"
    ))
    if df.empty:
        return "No action data."
    lines = ["📋 **Recommended actions for top areas:**\n"]
    for _, row in df.iterrows():
        actions = " · ".join(
            a.strip()
            for a in str(row.get("recommended_actions", "Monitor")).split("|")
            if a.strip()
        )
        lines.append(
            f"{t_emoji(risk_tier(row['priority_index_conf_adj']))} **{row['municipio']}**: {actions}"
        )
    return "\n\n".join(lines)


def _resp_stations(con) -> str:
    """Return water monitoring station statuses."""
    df = _q(con, (
        "SELECT station_name, latest_water_level, rise_rate_per_hour, flood_hazard_final "
        "FROM vw_station_water_summary ORDER BY flood_hazard_final DESC NULLS LAST"
    ))
    if df.empty:
        return "No station data."
    lines = [f"🌊 **{len(df)} water monitoring stations active:**\n"]
    for _, row in df.iterrows():
        hazard = float(row.get("flood_hazard_final", 0) or 0)
        rate   = float(row.get("rise_rate_per_hour",  0) or 0)
        trend  = "↑ Rising" if rate > 0.05 else ("↓ Falling" if rate < -0.05 else "→ Stable")
        status = "🔴" if hazard >= 70 else ("🟡" if hazard >= 50 else "🟢")
        wl     = row.get("latest_water_level")
        wl_str = f"{float(wl):.2f} ft" if wl else "n/a"
        lines.append(f"{status} **{row['station_name']}** — Level: `{wl_str}` {trend}")
    return "\n\n".join(lines)


def _resp_eq(con, n: int = 5) -> str:
    """Return the municipios with the highest earthquake hazard scores."""
    df = _q(con, (
        f"SELECT municipio, earthquake_hazard_score, hazard_combined "
        f"FROM vw_hazard_breakdown ORDER BY earthquake_hazard_score DESC LIMIT {n}"
    ))
    if df.empty:
        return "No earthquake data."
    lines = [f"🌍 **Top {n} areas by earthquake hazard:**\n"]
    for _, row in df.iterrows():
        eq  = float(row.get("earthquake_hazard_score", 0) or 0)
        lbl = "🔴 High" if eq >= 60 else ("🟠 Moderate" if eq >= 30 else "🟢 Low")
        lines.append(f"{lbl} **{row['municipio']}** — EQ score: `{eq:.0f}/100`")
    return "\n\n".join(lines)


def _resp_flood(con, n: int = 5) -> str:
    """Return the municipios with the highest flood hazard scores."""
    df = _q(con, (
        f"SELECT municipio, flood_hazard_muni, nws_global_alert_score "
        f"FROM vw_hazard_breakdown ORDER BY flood_hazard_muni DESC LIMIT {n}"
    ))
    if df.empty:
        return "No flood data."
    lines = [f"🌊 **Top {n} areas by flood hazard:**\n"]
    for _, row in df.iterrows():
        lines.append(
            f"🔴 **{row['municipio']}** — "
            f"Flood: `{float(row.get('flood_hazard_muni', 0)):.0f}/100` · "
            f"NWS: `{float(row.get('nws_global_alert_score', 0)):.0f}`"
        )
    return "\n\n".join(lines)


def _resp_snapshot(con) -> str:
    """Return a high-level system snapshot (counts, totals, averages)."""
    n_munis     = con.execute("SELECT COUNT(*) FROM baseline_municipio_indices").fetchone()[0]
    n_alerts    = con.execute("SELECT COUNT(*) FROM baseline_nws_alerts").fetchone()[0]
    n_stations  = con.execute("SELECT COUNT(*) FROM baseline_flood_station_latest").fetchone()[0]
    n_high      = con.execute(
        f"SELECT COUNT(*) FROM baseline_municipio_indices "
        f"WHERE priority_index_conf_adj >= {TIER_HIGH}"
    ).fetchone()[0]
    n_elevated  = con.execute(
        f"SELECT COUNT(*) FROM baseline_municipio_indices "
        f"WHERE priority_index_conf_adj >= {TIER_ELEVATED} "
        f"  AND priority_index_conf_adj < {TIER_HIGH}"
    ).fetchone()[0]
    pop_at_risk = con.execute(
        f"SELECT COALESCE(SUM(ev.population), 0) "
        f"FROM baseline_municipio_indices mi "
        f"JOIN baseline_exposure_vulnerability ev ON mi.municipio_slug = ev.municipio_slug "
        f"WHERE mi.priority_index_conf_adj >= {TIER_ELEVATED}"
    ).fetchone()[0]
    avg_ready   = con.execute(
        "SELECT ROUND(AVG(response_readiness_index), 1) FROM baseline_municipio_indices"
    ).fetchone()[0]

    return (
        f"📊 **Puerto Rico Flood EWS — Current Snapshot:**\n\n"
        f"- 🗺️ **{n_munis}** municipios tracked\n"
        f"- 🔴 **{n_high}** High priority · 🟠 **{n_elevated}** Elevated\n"
        f"- 👥 **~{int(pop_at_risk):,}** people in elevated-or-higher risk zones\n"
        f"- ⚠️ **{n_alerts}** active NWS alerts\n"
        f"- 🌊 **{n_stations}** water stations online\n"
        f"- 📈 Average island-wide readiness: **{avg_ready}/100**"
    )


def _resp_profile(con, name: str) -> str:
    """Return a detailed risk profile for a specific municipio."""
    df = _q(con, """
        SELECT
            m.municipio, m.priority_index_conf_adj, m.hazard_combined,
            m.flood_hazard_muni, m.earthquake_hazard_score,
            m.vulnerability_score, m.response_readiness_index,
            m.recovery_capacity_index, m.recommended_actions,
            v.population, v.poverty_rate, v.no_vehicle_rate, v.median_income
        FROM vw_municipio_risk_summary m
        LEFT JOIN vw_vulnerability_breakdown v ON m.municipio_slug = v.municipio_slug
        WHERE LOWER(m.municipio) LIKE ?
    """, [f"%{name.lower()}%"])

    if df.empty:
        return f"No data found for '{name}'. Try a different spelling or partial name."

    row     = df.iloc[0]
    tier    = risk_tier(row["priority_index_conf_adj"])
    actions = " · ".join(
        a.strip()
        for a in str(row.get("recommended_actions", "Monitor")).split("|")
        if a.strip()
    )
    return (
        f"{t_emoji(tier)} **{row['municipio']}** — {t_label(tier)}\n\n"
        f"| Metric | Value |\n|---|---|\n"
        f"| Priority Score      | `{row['priority_index_conf_adj']:.1f}/100` |\n"
        f"| Hazard (combined)   | `{row['hazard_combined']:.0f}/100` |\n"
        f"| Flood Hazard        | `{row['flood_hazard_muni']:.0f}/100` |\n"
        f"| Earthquake Risk     | `{row['earthquake_hazard_score']:.0f}/100` |\n"
        f"| Vulnerability       | `{row['vulnerability_score']:.0f}/100` |\n"
        f"| Response Readiness  | `{row['response_readiness_index']:.0f}/100` |\n"
        f"| Population          | **{int(row.get('population', 0) or 0):,}** |\n"
        f"| Poverty Rate        | **{pct(row.get('poverty_rate'))}** |\n"
        f"| Median Income       | **${int(row.get('median_income') or 0):,}** |\n\n"
        f"👉 **Actions:** {actions}"
    )


def _resp_help() -> str:
    """Return the chatbot welcome / help message."""
    return (
        "👋 **Welcome to Ask the Data!**\n\n"
        "I can answer questions about Puerto Rico flood risk, vulnerability, "
        "and response readiness using the live pipeline data.\n\n"
        "Try asking:\n"
        "- *Which areas need help most?*\n"
        "- *Tell me about Ponce* (any municipio name)\n"
        "- *Most vulnerable communities?*\n"
        "- *Active flood alerts?*\n"
        "- *Earthquake risk areas?*\n"
        "- *Give me an overall snapshot*\n\n"
        "💡 *I understand typos, accents, and partial names too.*"
    )


def process_query(query: str, con, municipios: list[str]) -> str:
    """
    Route a natural-language query to the appropriate response function.
    First tries municipio name matching; falls back to keyword intent scoring.
    """
    if len(query.strip()) < 3:
        return _resp_help()

    matched_muni = _fuzzy_muni(query, municipios)
    if matched_muni:
        return _resp_profile(con, matched_muni)

    intent = _intent(query)
    handlers = {
        "top_priority":  _resp_top,
        "alerts":        _resp_alerts,
        "vulnerability": _resp_vuln,
        "actions":       _resp_actions,
        "stations":      _resp_stations,
        "earthquake":    _resp_eq,
        "flood":         _resp_flood,
        "snapshot":      _resp_snapshot,
    }
    return handlers.get(intent, lambda _: _resp_help())(con)


# ===========================================================================
# MAP BUILDERS
# ===========================================================================

def build_risk_map(
    df: pd.DataFrame,
    map_style: str,
    show_labels: bool = False,
    show_heat: bool = False,
) -> pdk.Deck:
    """
    Build a pydeck map of municipio risk circles.

    Each circle is sized proportionally to population and coloured by risk tier.
    Optional heatmap and municipality label overlays can be enabled.
    """
    layers = []

    if show_heat:
        layers.append(pdk.Layer(
            "HeatmapLayer",
            data=df,
            get_position=["longitude", "latitude"],
            get_weight="priority_index_conf_adj",
            radiusPixels=55,
            intensity=1.2,
            threshold=0.05,
            opacity=0.55,
        ))

    layers.append(pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position=["longitude", "latitude"],
        get_fill_color="color_rgb",
        get_radius="radius",
        radius_min_pixels=5,
        radius_max_pixels=17,
        pickable=True,
        opacity=0.90,
        stroked=True,
        get_line_color=[255, 255, 255, 120],
        line_width_min_pixels=1,
    ))

    if show_labels:
        layers.append(pdk.Layer(
            "TextLayer",
            data=df,
            get_position=["longitude", "latitude"],
            get_text="municipio",
            get_size=11,
            get_color=[255, 255, 255, 220],
            get_anchor="'middle'",
            get_alignment_baseline="'bottom'",
            get_pixel_offset=[0, -14],
            pickable=False,
        ))

    return pdk.Deck(
        layers=layers,
        initial_view_state=pdk.ViewState(
            latitude=PR_LAT, longitude=PR_LON, zoom=PR_ZOOM, pitch=0
        ),
        map_style=map_style,
        tooltip={
            "html": (
                "<b style='font-size:14px;font-family:Inter,sans-serif'>{municipio}</b><br/>"
                "<span style='color:#94a3b8'>Risk:</span> <b>{tier}</b><br/>"
                "<span style='color:#94a3b8'>Priority:</span> {score_label}<br/>"
                "<span style='color:#94a3b8'>Hazard:</span> {hazard_label}<br/>"
                "<span style='color:#94a3b8'>Vulnerability:</span> {vuln_label}<br/>"
                "<span style='color:#94a3b8'>Population:</span> {pop_label}"
            ),
            "style": {
                "backgroundColor": "#080d18",
                "color":           "#e2e8f0",
                "fontSize":        "13px",
                "fontFamily":      "Inter,sans-serif",
                "borderRadius":    "8px",
                "padding":         "12px",
                "border":          "1px solid #1e3050",
            },
        },
    )


def build_station_map(df: pd.DataFrame, map_style: str) -> pdk.Deck:
    """
    Build a pydeck map of NOAA water monitoring stations.
    Stations are coloured by flood hazard score and labelled by name.
    """
    layers = [
        pdk.Layer(
            "ScatterplotLayer",
            data=df,
            get_position=["longitude", "latitude"],
            get_fill_color="color_rgb",
            get_radius=7000,
            radius_min_pixels=10,
            radius_max_pixels=20,
            pickable=True,
            opacity=0.92,
            stroked=True,
            get_line_color=[255, 255, 255, 200],
            line_width_min_pixels=2,
        ),
        pdk.Layer(
            "TextLayer",
            data=df,
            get_position=["longitude", "latitude"],
            get_text="station_name",
            get_size=11,
            get_color=[255, 255, 255, 200],
            get_anchor="'middle'",
            get_alignment_baseline="'bottom'",
            get_pixel_offset=[0, -16],
            pickable=False,
        ),
    ]
    return pdk.Deck(
        layers=layers,
        initial_view_state=pdk.ViewState(
            latitude=PR_LAT, longitude=PR_LON, zoom=7.6, pitch=0
        ),
        map_style=map_style,
        tooltip={
            "html": (
                "<b>{station_name}</b><br/>"
                "Level: {wl_str}<br/>"
                "Trend: {trend}<br/>"
                "Hazard: {haz_label}"
            ),
            "style": {
                "backgroundColor": "#080d18",
                "color":           "#e2e8f0",
                "fontSize":        "13px",
                "fontFamily":      "Inter,sans-serif",
                "borderRadius":    "8px",
                "padding":         "10px",
            },
        },
    )


# ===========================================================================
# APPLICATION ENTRY POINT
# ===========================================================================

# Locate the repo root and derive the default DuckDB path
REPO_ROOT  = find_repo_root()
DEFAULT_DB = REPO_ROOT / "data" / "local" / "duckdb" / "spring2026daen_baseline.duckdb"

# Must be the very first Streamlit call in the script
st.set_page_config(
    page_title="PR Flood Early Warning System",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Session state initialisation
# These keys must exist before any widget that reads from them.
# ---------------------------------------------------------------------------
for _key, _default in [
    ("chat_history", None),
    ("sql_history",  []),
    ("_shutdown",    False),
]:
    if _key not in st.session_state:
        st.session_state[_key] = _default

# Seed the chat history with the welcome message on first load
if st.session_state.chat_history is None:
    st.session_state.chat_history = [{"role": "assistant", "content": _resp_help()}]


# ===========================================================================
# SIDEBAR
# The theme toggle lives here so the correct palette is known before the
# main CSS block is injected below.
# ===========================================================================
with st.sidebar:
    st.markdown(
        "<p style='font-family:Inter,sans-serif;font-size:20px;font-weight:700;"
        "margin:0;letter-spacing:-0.3px'>🌊 PR Flood EWS</p>"
        "<p style='font-family:Inter,sans-serif;font-size:12px;color:#64748b;margin:0'>"
        "Community Decision Support · Spring2026DAEN</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    # Dark / Light theme toggle — determines which palette tokens are used below
    is_dark   = st.toggle("🌑 Dark  /  ☀️ Light", value=True, key="dark_mode")
    C         = PALETTE["dark"] if is_dark else PALETTE["light"]
    MAP_STYLE = CARTO_DARK if is_dark else CARTO_VOYAGER

    st.divider()
    municipio_search = st.text_input("🔍 Find a municipio", placeholder="e.g. Ponce")
    st.divider()

    # Navigation guide — brief description of each tab
    st.markdown(
        f"<p style='font-family:Inter,sans-serif;font-size:12px;font-weight:600;"
        f"text-transform:uppercase;letter-spacing:0.5px;color:{C['muted']};margin-bottom:8px'>"
        f"Navigation Guide</p>",
        unsafe_allow_html=True,
    )
    for tab_name, tab_desc in TAB_INFO.items():
        st.markdown(
            f"<div style='margin-bottom:10px;padding:8px 10px;background:{C['card2']};"
            f"border-radius:6px;border-left:3px solid {C['border']}'>"
            f"<p style='font-family:Inter,sans-serif;font-size:12px;font-weight:600;"
            f"margin:0 0 3px 0;color:{C['text']}'>{tab_name}</p>"
            f"<p style='font-family:Inter,sans-serif;font-size:11px;color:{C['muted']};"
            f"margin:0;line-height:1.5'>{tab_desc}</p></div>",
            unsafe_allow_html=True,
        )

    st.divider()
    db_path  = Path(
        st.text_input("DuckDB path", str(DEFAULT_DB), label_visibility="collapsed")
    ).expanduser()
    quit_btn = st.button("⏹ Quit App", use_container_width=True)


# ===========================================================================
# GLOBAL CSS
# Injected after the theme toggle so the correct palette tokens are known.
#
# Key design decisions:
#  1. NEVER override <span> broadly — Streamlit's UI chrome (expander arrows,
#     selectbox caret, sidebar icons) uses plain <span>s with the Material
#     Icons font. Overriding span.font-family breaks those icons.
#  2. Toggle checkboxes are excluded from the input{} background rule so
#     BaseWeb's toggle track/thumb visuals are not disturbed.
#  3. Dropdown panels (BaseWeb menus) render in a DOM portal at the body root,
#     so they need standalone selectors — not scoped to .stApp.
# ===========================================================================
_shadow  = "0 1px 5px rgba(15,23,42,0.07)" if not is_dark else "0 1px 5px rgba(0,0,0,0.35)"
_code_bg = C["card2"]
_code_fg = C["text"]

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
@import url('https://fonts.googleapis.com/icon?family=Material+Icons|Material+Icons+Outlined');

/* -----------------------------------------------------------------------
   BASE — fonts and app background
   IMPORTANT: Do NOT override <span> or <button> broadly here.
   Streamlit UI chrome icons live in plain <span> elements and will break
   if font-family is overridden for all spans.
----------------------------------------------------------------------- */
html, body {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}}
p, h1, h2, h3, h4, h5, h6, li, td, th, label, textarea, select {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}}
[data-testid="stWidgetLabel"] p,
[data-testid="stMetricLabel"] p,
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] td,
[data-testid="stMarkdownContainer"] th,
.stMarkdown p, .stMarkdown li {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}}
.stTabs [data-baseweb="tab"] p,
.stTabs [data-baseweb="tab"] span[class] {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}}
/* Preserve Material Icons font for all Streamlit icon elements */
[data-testid="stIconMaterial"], .material-icons, span.material-icons {{
    font-family: 'Material Icons', 'Material Icons Outlined' !important;
}}

.stApp                 {{ background-color: {C['bg']} !important; }}
.main .block-container {{ background-color: {C['bg']} !important; padding-top: 1rem; }}

/* -----------------------------------------------------------------------
   HEADER / TOOLBAR
----------------------------------------------------------------------- */
header[data-testid="stHeader"] {{
    background-color: {C['card']} !important;
    border-bottom: 1px solid {C['border']} !important;
}}
header[data-testid="stHeader"] * {{ color: {C['text']} !important; }}
button[data-testid="baseButton-header"],
button[data-testid="baseButton-headerNoPadding"] {{
    color: {C['text']} !important;
    background: transparent !important;
}}

/* -----------------------------------------------------------------------
   SIDEBAR
----------------------------------------------------------------------- */
section[data-testid="stSidebar"] > div:first-child {{
    background-color: {C['card']} !important;
    border-right: 1px solid {C['border']} !important;
}}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label {{ color: {C['text']} !important; }}

/* -----------------------------------------------------------------------
   TEXT
----------------------------------------------------------------------- */
p, label, .stMarkdown, .stCaption, li {{ color: {C['text']} !important; }}
[data-testid="stMarkdownContainer"] span,
[data-testid="stCaptionContainer"] span,
[data-testid="stWidgetLabel"] span {{ color: {C['text']} !important; }}
h1, h2, h3, h4, h5, h6 {{ color: {C['text']} !important; }}
a {{ color: {C['accent']} !important; }}
code, .stCode code {{
    background: {_code_bg} !important;
    color: {_code_fg} !important;
    border: 1px solid {C['border']} !important;
    border-radius: 4px !important;
    padding: 1px 6px !important;
    font-size: 0.85em !important;
}}
pre, .stCode pre {{
    background: {_code_bg} !important;
    border: 1px solid {C['border']} !important;
    border-radius: 8px !important;
    color: {_code_fg} !important;
}}

/* -----------------------------------------------------------------------
   METRIC CARDS
----------------------------------------------------------------------- */
div[data-testid="stMetric"],
div[data-testid="metric-container"] {{
    background: {C['card']} !important;
    border: 1px solid {C['border']} !important;
    border-radius: 10px !important;
    padding: 14px 18px !important;
    box-shadow: {_shadow} !important;
}}
div[data-testid="stMetric"] [data-testid="stMetricLabel"] p,
div[data-testid="stMetric"] label,
div[data-testid="metric-container"] label {{
    color: {C['muted']} !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}}
div[data-testid="stMetric"] [data-testid="stMetricValue"],
div[data-testid="stMetric"] [data-testid="stMetricValue"] *,
div[data-testid="stMetricValue"],
div[data-testid="stMetricValue"] * {{
    color: {C['text']} !important;
    font-size: 24px !important;
    font-weight: 700 !important;
}}
div[data-testid="stMetric"] [data-testid="stMetricDelta"],
div[data-testid="stMetric"] [data-testid="stMetricDelta"] * {{
    font-size: 12px !important;
}}

/* -----------------------------------------------------------------------
   TABS
----------------------------------------------------------------------- */
.stTabs [data-baseweb="tab-list"] {{
    background: {C['card']} !important;
    border-bottom: 2px solid {C['border']} !important;
    border-radius: 8px 8px 0 0 !important;
    gap: 0 !important;
}}
.stTabs [data-baseweb="tab"] {{
    background: transparent !important;
    color: {C['muted']} !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 10px 18px !important;
    border-radius: 6px 6px 0 0 !important;
    border-bottom: 2px solid transparent !important;
}}
.stTabs [aria-selected="true"] {{
    color: {C['accent']} !important;
    border-bottom: 2px solid {C['accent']} !important;
    background: {C['bg']} !important;
    font-weight: 600 !important;
}}
.stTabs [data-baseweb="tab-panel"] {{
    background: {C['bg']} !important;
    padding-top: 1rem !important;
}}

/* -----------------------------------------------------------------------
   INPUTS — text fields, textareas, selectboxes
   Checkboxes and radios are explicitly excluded so toggle switch
   visuals are not overridden here (see TOGGLES section below).
----------------------------------------------------------------------- */
input:not([type="checkbox"]):not([type="radio"]),
textarea,
[data-testid="stTextArea"] textarea,
[data-testid="stTextInput"] input,
.stTextArea textarea,
.stTextInput input {{
    background: {C['input_bg']} !important;
    color: {C['text']} !important;
    border: 1px solid {C['border']} !important;
    border-radius: 7px !important;
}}
input:not([type="checkbox"]):not([type="radio"])::placeholder,
textarea::placeholder,
[data-testid="stTextArea"] textarea::placeholder {{ color: {C['muted']} !important; }}

/* Selectbox trigger */
.stSelectbox div[data-baseweb="select"] > div,
.stMultiSelect div[data-baseweb="select"] > div {{
    background: {C['input_bg']} !important;
    border: 1px solid {C['border']} !important;
    border-radius: 7px !important;
    color: {C['text']} !important;
}}
.stSelectbox [data-baseweb="select"] [data-baseweb="single-value"],
.stSelectbox [data-baseweb="select"] [class*="placeholder"] {{ color: {C['text']} !important; }}

/* Dropdown open panel — rendered in a DOM portal at the body root.
   Must use standalone selectors (not scoped to .stApp). */
[data-baseweb="popover"],
[data-baseweb="popover"] > div,
[data-baseweb="popover"] > div > div,
[data-baseweb="menu"],
[data-baseweb="list"] {{
    background: {C['card']} !important;
    border: 1px solid {C['border']} !important;
    border-radius: 8px !important;
    box-shadow: 0 4px 16px rgba(0,0,0,0.12) !important;
}}
[data-baseweb="option"],
[role="option"],
ul[data-baseweb="menu"] li {{ background: {C['card']} !important; color: {C['text']} !important; }}
[data-baseweb="option"]:hover,
[data-baseweb="option"][aria-selected="true"],
[role="option"]:hover,
[role="option"][aria-selected="true"] {{
    background: {C['card2']} !important;
    color: {C['accent']} !important;
}}
[data-baseweb="menu"] *,
[data-baseweb="list"] *,
[data-baseweb="popover"] p,
[data-baseweb="popover"] span:not([class*="icon"]) {{ color: {C['text']} !important; }}

/* -----------------------------------------------------------------------
   BUTTONS
----------------------------------------------------------------------- */
[data-testid="stButton"] button,
[data-testid="stBaseButton-secondary"],
.stButton > button {{
    background: {C['card2']} !important;
    color: {C['text']} !important;
    border: 1px solid {C['border']} !important;
    border-radius: 7px !important;
    font-weight: 500 !important;
    transition: all 0.15s ease !important;
    box-shadow: {_shadow} !important;
}}
[data-testid="stButton"] button:hover,
.stButton > button:hover {{
    border-color: {C['accent']} !important;
    color: {C['accent']} !important;
    box-shadow: 0 0 0 2px {C['accent']}33 !important;
}}
[data-testid="stBaseButton-primary"],
button[kind="primary"] {{
    background: {C['accent']} !important;
    color: #ffffff !important;
    border: none !important;
}}

/* -----------------------------------------------------------------------
   DATAFRAME / TABLE
----------------------------------------------------------------------- */
.stDataFrame, [data-testid="stDataFrame"] {{
    border: 1px solid {C['border']} !important;
    border-radius: 8px !important;
    background: {C['card']} !important;
    box-shadow: {_shadow} !important;
    overflow: hidden !important;
}}
[data-testid="stDataFrame"] th,
[data-testid="stDataFrame"] thead tr th {{
    background: {C['card2']} !important;
    color: {C['text']} !important;
    border-bottom: 2px solid {C['border']} !important;
    font-weight: 600 !important;
}}
[data-testid="stDataFrame"] td {{
    background: {C['card']} !important;
    color: {C['text']} !important;
    border-bottom: 1px solid {C['divider']} !important;
}}
[data-testid="stDataFrame"] tr:hover td {{ background: {C['card2']} !important; }}

/* -----------------------------------------------------------------------
   INFO / WARNING / SUCCESS / ERROR BANNERS
----------------------------------------------------------------------- */
[data-testid="stAlert"],
div.element-container div[role="alert"] {{
    background: {C['card2']} !important;
    border: 1px solid {C['border']} !important;
    border-radius: 8px !important;
}}
[data-testid="stAlert"] p,
[data-testid="stAlert"] span {{ color: {C['text']} !important; }}

/* -----------------------------------------------------------------------
   EXPANDERS
----------------------------------------------------------------------- */
[data-testid="stExpander"],
.stExpander {{
    border: 1px solid {C['border']} !important;
    border-radius: 8px !important;
    background: {C['card']} !important;
    box-shadow: {_shadow} !important;
    overflow: hidden !important;
}}
[data-testid="stExpander"] summary,
.stExpander summary {{ color: {C['text']} !important; background: {C['card']} !important; }}
[data-testid="stExpander"] summary:hover,
.stExpander summary:hover {{ background: {C['card2']} !important; }}
[data-testid="stExpanderDetails"] {{ background: {C['card']} !important; }}

/* -----------------------------------------------------------------------
   SLIDER
----------------------------------------------------------------------- */
.stSlider label {{ color: {C['muted']} !important; }}
.stSlider [data-baseweb="slider"] [data-testid="stTickBarMin"],
.stSlider [data-baseweb="slider"] [data-testid="stTickBarMax"] {{ color: {C['muted']} !important; }}

/* -----------------------------------------------------------------------
   TOGGLE SWITCHES
   Streamlit builds toggles from BaseWeb's Checkbox in switch mode.
   We target [role="switch"] for the track background and its child
   div for the thumb so both on/off states are visually clear.
----------------------------------------------------------------------- */
.stToggle label, .stCheckbox label {{ color: {C['text']} !important; }}
/* Track — off state */
[data-testid="stToggle"] [role="switch"],
[data-testid="stCheckbox"] [role="checkbox"] {{
    background: {C['border']} !important;
    border-color: {C['border']} !important;
}}
/* Track — on state */
[data-testid="stToggle"] [role="switch"][aria-checked="true"],
[data-testid="stCheckbox"] [role="checkbox"][aria-checked="true"] {{
    background: {C['accent']} !important;
    border-color: {C['accent']} !important;
}}
/* Thumb — always white */
[data-testid="stToggle"] [role="switch"] > div,
[data-testid="stToggle"] [role="switch"] > span,
[data-testid="stCheckbox"] [role="checkbox"] > div {{
    background: #ffffff !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.25) !important;
}}

/* -----------------------------------------------------------------------
   CHAT MESSAGES AND INPUT
----------------------------------------------------------------------- */
[data-testid="stChatMessage"],
.stChatMessage {{
    background: {C['card']} !important;
    border: 1px solid {C['border']} !important;
    border-radius: 10px !important;
    box-shadow: {_shadow} !important;
}}
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] span,
[data-testid="stChatMessageContent"] p,
[data-testid="stChatMessageContent"] span {{ color: {C['text']} !important; }}
[data-testid="stChatInput"] {{
    background: {C['card']} !important;
    border: 1px solid {C['border']} !important;
    border-radius: 10px !important;
}}
[data-testid="stChatInputTextArea"] {{
    background: {C['card']} !important;
    color: {C['text']} !important;
    border: none !important;
}}

/* -----------------------------------------------------------------------
   PYDECK AND PLOTLY WRAPPERS
----------------------------------------------------------------------- */
[data-testid="stDeckGlJsonChart"],
.stDeckGlJsonChart {{
    border: 1px solid {C['border']} !important;
    border-radius: 10px !important;
    overflow: hidden !important;
    box-shadow: {_shadow} !important;
}}
[data-testid="stPlotlyChart"] {{
    border: 1px solid {C['border']} !important;
    border-radius: 10px !important;
    overflow: hidden !important;
    box-shadow: {_shadow} !important;
    background: {C['card']} !important;
}}

/* -----------------------------------------------------------------------
   POPOVER / TOOLTIP
----------------------------------------------------------------------- */
[data-testid="stPopover"] > div,
div[role="tooltip"] {{
    background: {C['card']} !important;
    border: 1px solid {C['border']} !important;
    border-radius: 8px !important;
    color: {C['text']} !important;
    box-shadow: {_shadow} !important;
}}

/* -----------------------------------------------------------------------
   DIVIDERS, SCROLLBARS, FOOTER
----------------------------------------------------------------------- */
hr {{ border-color: {C['divider']} !important; opacity: 1 !important; }}
::-webkit-scrollbar       {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: {C['bg']}; }}
::-webkit-scrollbar-thumb {{ background: {C['border']}; border-radius: 3px; }}
::-webkit-scrollbar-thumb:hover {{ background: {C['muted']}; }}
footer, footer * {{ color: {C['muted']} !important; background: {C['bg']} !important; }}
</style>
""", unsafe_allow_html=True)


# ===========================================================================
# DATABASE GUARD
# Show an error and stop early if the DuckDB baseline has not been built yet.
# ===========================================================================
if not db_path.exists():
    if quit_btn:
        request_shutdown()
        st.stop()
    st.error(
        "⚠️ DuckDB baseline not found. "
        "Run `python scripts/build_duckdb_baseline.py` then reload."
    )
    st.stop()


con: duckdb.DuckDBPyConnection | None = None
try:
    con = duckdb.connect(str(db_path), read_only=True)

    if quit_btn:
        con.close()
        con = None
        request_shutdown()
        st.stop()

    # -----------------------------------------------------------------------
    # DATA LOADING
    # All views are loaded upfront into DataFrames so individual tab sections
    # can read from memory without reopening the connection mid-render.
    # -----------------------------------------------------------------------
    muni_df     = load_view(con, "SELECT * FROM vw_municipio_risk_summary")
    vuln_df     = load_view(con, "SELECT * FROM vw_vulnerability_breakdown")
    hazard_df   = load_view(con, "SELECT * FROM vw_hazard_breakdown")
    ranking_df  = load_view(con, "SELECT * FROM vw_priority_ranking")
    stations_df = load_view(con, "SELECT * FROM vw_station_water_summary")
    alerts_df   = load_view(con, "SELECT * FROM vw_alerts_summary")
    source_df   = load_view(con, "SELECT * FROM vw_baseline_source_status")

    # Flat list of municipio names used by the chatbot for fuzzy matching
    municipio_names = muni_df["municipio"].dropna().tolist() if not muni_df.empty else []

    # Enrich muni_df with derived display columns used across all tabs
    if not muni_df.empty:
        muni_df["tier"]         = muni_df["priority_index_conf_adj"].map(risk_tier)
        muni_df["color_rgb"]    = muni_df["tier"].map(t_rgb)
        muni_df["score_label"]  = muni_df["priority_index_conf_adj"].map(lambda x: f"{x:.1f}/100")
        muni_df["hazard_label"] = muni_df["hazard_combined"].map(lambda x: f"{x:.0f}/100")
        muni_df["vuln_label"]   = muni_df["vulnerability_score"].map(lambda x: f"{x:.0f}/100")

        # Merge population from vulnerability table for map circle sizing
        if not vuln_df.empty:
            muni_df = muni_df.merge(
                vuln_df[["municipio_slug", "population"]],
                on="municipio_slug", how="left",
            )
        else:
            muni_df["population"] = 0

        muni_df["population"] = muni_df["population"].fillna(0)
        max_pop = max(muni_df["population"].max(), 1)
        # Power scaling keeps small municipios visible while large ones stand out
        muni_df["radius"]    = ((muni_df["population"] / max_pop) ** 0.45 * 5500 + 2000).astype(int)
        muni_df["pop_label"] = muni_df["population"].map(lambda x: f"{int(x):,}")

        # Apply optional sidebar search filter
        if municipio_search.strip():
            muni_df = muni_df[
                muni_df["municipio"].str.contains(municipio_search.strip(), case=False, na=False)
            ]

    # -----------------------------------------------------------------------
    # KPI COMPUTATION
    # Values used in the header metrics row and top-priority banner.
    # -----------------------------------------------------------------------
    n_high        = int((muni_df["tier"] == "High").sum())     if not muni_df.empty else 0
    n_elevated    = int((muni_df["tier"] == "Elevated").sum()) if not muni_df.empty else 0
    top_muni      = (
        muni_df.sort_values("priority_index_conf_adj", ascending=False)["municipio"].iloc[0]
        if not muni_df.empty else "n/a"
    )
    pop_at_risk   = (
        int(muni_df[muni_df["tier"].isin(["High", "Elevated"])]["population"].sum())
        if not muni_df.empty and "population" in muni_df.columns else 0
    )
    avg_readiness = muni_df["response_readiness_index"].mean() if not muni_df.empty else 0
    max_hazard    = muni_df["hazard_combined"].max()           if not muni_df.empty else 0

    # Read the pipeline build timestamp from the JSON summary file
    build_summary_path = REPO_ROOT / "data" / "local" / "duckdb" / "duckdb_baseline_build_summary.json"
    data_ts = "Unknown"
    if build_summary_path.exists():
        raw_ts  = json.loads(build_summary_path.read_text()).get("run_timestamp_utc", "")
        data_ts = raw_ts[:16].replace("T", " ") + " UTC" if raw_ts else "Unknown"

    # -----------------------------------------------------------------------
    # PAGE HEADER
    # -----------------------------------------------------------------------
    st.markdown(
        f"<h1 style='font-family:Inter,sans-serif;font-size:26px;font-weight:700;"
        f"color:{C['text']};margin-bottom:2px;letter-spacing:-0.5px'>"
        f"🌊 Puerto Rico Community Flood Early Warning System</h1>"
        f"<p style='font-family:Inter,sans-serif;font-size:13px;color:{C['muted']};margin-top:0'>"
        f"Live decision support for emergency managers and community leaders &nbsp;·&nbsp; "
        f"78 municipios monitored &nbsp;·&nbsp; "
        f"Pipeline: <code>{data_ts}</code></p>",
        unsafe_allow_html=True,
    )

    # Six KPI metrics across the top of the page
    col_people, col_high, col_elevated, col_alerts, col_readiness, col_stations = st.columns(6)
    col_people.metric(
        "👥 People at Risk", f"{pop_at_risk:,}",
        help="Population in High or Elevated priority zones",
    )
    col_high.metric("🔴 High Priority", n_high, help=f"Score ≥ {TIER_HIGH}")
    col_elevated.metric("🟠 Elevated", n_elevated, help=f"Score {TIER_ELEVATED}–{TIER_HIGH}")
    col_alerts.metric("⚠️ Active Alerts", len(alerts_df))
    col_readiness.metric(
        "📈 Avg Readiness", f"{avg_readiness:.0f}/100",
        help="Island-wide average response readiness",
    )
    col_stations.metric("🌊 Stations Online", len(stations_df))

    # Top-priority highlight banner
    st.markdown(
        f"<div style='background:{C['card']};border:1px solid {C['border']};"
        f"border-left:4px solid #ef4444;padding:9px 16px;border-radius:8px;"
        f"margin:8px 0 16px 0;font-family:Inter,sans-serif'>"
        f"📍 <b style='color:{C['text']}'>Highest-priority area right now:</b> "
        f"<code style='background:{C['card2']};padding:2px 8px;border-radius:5px;"
        f"font-size:14px;color:#ef4444'>{top_muni}</code>"
        f"<span style='color:{C['muted']};margin-left:16px;font-size:13px'>"
        f"Max hazard score: <b>{max_hazard:.0f}/100</b></span></div>",
        unsafe_allow_html=True,
    )

    # -----------------------------------------------------------------------
    # TABS
    # -----------------------------------------------------------------------
    tab_map, tab_rank, tab_live, tab_chat, tab_sql = st.tabs([
        "🗺️ Overview Map",
        "⚠️ Risk Rankings",
        "🌊 Live Conditions",
        "💬 Ask the Data",
        "🔍 SQL Explorer",
    ])

    # =======================================================================
    # TAB 1 — Overview Map
    # Pydeck scatter map with per-municipio risk circles.
    # Right panel shows drill-down details for the selected municipio.
    # =======================================================================
    with tab_map:
        map_col, detail_col = st.columns([2.2, 1])

        with map_col:
            st.markdown(
                f"<h4 style='font-family:Inter,sans-serif;color:{C['text']};margin-bottom:4px'>"
                f"Puerto Rico — Municipal Flood Risk Map</h4>"
                f"<p style='font-size:12px;color:{C['muted']};margin-top:0'>"
                f"🔴 High &nbsp;🟠 Elevated &nbsp;🟡 Monitor &nbsp;🟢 Low &nbsp;·&nbsp;"
                f"Circle size = population &nbsp;·&nbsp; Hover for details</p>",
                unsafe_allow_html=True,
            )

            # Layer toggles — optional map overlays
            toggle_labels_col, toggle_heat_col, _ = st.columns([1, 1, 3])
            show_labels = toggle_labels_col.toggle("🏷️ Labels",  value=False, key="map_labels")
            show_heat   = toggle_heat_col.toggle("🌡️ Heatmap", value=False, key="map_heat")

            if not muni_df.empty:
                deck      = build_risk_map(muni_df, MAP_STYLE, show_labels, show_heat)
                map_event = st.pydeck_chart(
                    deck,
                    on_select="rerun",
                    selection_mode="single-object",
                    use_container_width=True,
                    height=460,
                )
            else:
                st.info("No municipio data available.")
                map_event = None

        with detail_col:
            st.markdown(
                f"<h4 style='font-family:Inter,sans-serif;color:{C['text']};margin-bottom:8px'>"
                f"📍 Area Details</h4>",
                unsafe_allow_html=True,
            )

            # Pre-select the municipio clicked on the map (if any)
            selected_muni = None
            if map_event and hasattr(map_event, "selection"):
                selection_objects = getattr(map_event.selection, "objects", {})
                if selection_objects:
                    first_layer = next(iter(selection_objects.values()), [])
                    if first_layer:
                        selected_muni = first_layer[0].get("municipio")

            muni_names  = sorted(muni_df["municipio"].dropna().tolist()) if not muni_df.empty else []
            default_idx = muni_names.index(selected_muni) if selected_muni in muni_names else 0
            chosen = st.selectbox(
                "Select municipio",
                options=muni_names,
                index=default_idx,
                label_visibility="collapsed",
            )

            if chosen and not muni_df.empty:
                row_df = muni_df[muni_df["municipio"] == chosen]
                if not row_df.empty:
                    r     = row_df.iloc[0]
                    tier  = r["tier"]
                    color = t_hex(tier)

                    # Tier badge header
                    st.markdown(
                        f"<div style='border-left:4px solid {color};padding:10px 14px;"
                        f"background:{C['card']};border-radius:8px;margin-bottom:10px'>"
                        f"<span style='font-size:20px'>{t_emoji(tier)}</span> "
                        f"<b style='font-size:17px;color:{color};font-family:Inter,sans-serif'>"
                        f"{chosen}</b><br/>"
                        f"<span style='color:{C['muted']};font-size:12px'>{t_label(tier)}</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

                    # Score metrics in a 2×3 grid
                    score_col1, score_col2 = st.columns(2)
                    score_col1.metric("Priority",     f"{r['priority_index_conf_adj']:.1f}")
                    score_col2.metric("Population",   f"{int(r.get('population', 0)):,}")
                    score_col3, score_col4 = st.columns(2)
                    score_col3.metric("Flood Hazard", f"{r.get('flood_hazard_muni', 0):.0f}/100")
                    score_col4.metric("Earthquake",   f"{r.get('earthquake_hazard_score', 0):.0f}/100")
                    score_col5, score_col6 = st.columns(2)
                    score_col5.metric("Vulnerability", f"{r.get('vulnerability_score', 0):.0f}/100")
                    score_col6.metric("Readiness",     f"{r.get('response_readiness_index', 0):.0f}/100")

                    # Plain-English risk explanation
                    st.markdown(
                        f"<div style='background:{C['card2']};padding:8px 12px;"
                        f"border-radius:6px;font-size:12px;color:{C['muted']};margin-top:6px'>"
                        f"⚠️ {why_risk(r)}</div>",
                        unsafe_allow_html=True,
                    )

                    # Recommended actions
                    st.markdown(
                        f"<b style='color:{C['text']}'>👉 Actions:</b>",
                        unsafe_allow_html=True,
                    )
                    for action in str(r.get("recommended_actions", "Monitor")).split("|"):
                        if action.strip():
                            st.markdown(f"- {action.strip()}")

                    # Additional vulnerability context
                    if not vuln_df.empty:
                        vrow_df = vuln_df[vuln_df["municipio"] == chosen]
                        if not vrow_df.empty:
                            v = vrow_df.iloc[0]
                            st.markdown(
                                f"<div style='font-size:12px;color:{C['muted']};margin-top:6px'>"
                                f"Poverty: <b>{pct(v.get('poverty_rate'))}</b> · "
                                f"No vehicle: <b>{pct(v.get('no_vehicle_rate'))}</b> · "
                                f"Income: <b>${int(v.get('median_income') or 0):,}</b></div>",
                                unsafe_allow_html=True,
                            )

        # Top-5 priority cards row
        st.divider()
        st.markdown(
            f"<h4 style='font-family:Inter,sans-serif;color:{C['text']}'>"
            f"🏆 Top 5 Areas Needing Attention</h4>",
            unsafe_allow_html=True,
        )
        top5_df = (
            muni_df.sort_values("priority_index_conf_adj", ascending=False).head(5)
            if not muni_df.empty else pd.DataFrame()
        )
        if not top5_df.empty:
            for card_col, (_, r) in zip(st.columns(5), top5_df.iterrows()):
                color = t_hex(r["tier"])
                card_col.markdown(
                    f"<div style='border:1px solid {color};border-top:3px solid {color};"
                    f"border-radius:10px;padding:12px;background:{C['card']};text-align:center'>"
                    f"<div style='font-size:22px'>{t_emoji(r['tier'])}</div>"
                    f"<div style='font-weight:600;font-size:14px;color:{C['text']};margin:4px 0'>"
                    f"{r['municipio']}</div>"
                    f"<div style='color:{C['muted']};font-size:11px'>"
                    f"Score: {r['priority_index_conf_adj']:.1f}</div>"
                    f"<div style='color:{C['muted']};font-size:11px'>"
                    f"Pop: {int(r.get('population', 0)):,}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

    # =======================================================================
    # TAB 2 — Risk Rankings
    # Filterable ranked table of all 78 municipios + Plotly bar chart.
    # =======================================================================
    with tab_rank:
        st.markdown(
            f"<h4 style='font-family:Inter,sans-serif;color:{C['text']}'>"
            f"⚠️ Risk Rankings — All 78 Municipios</h4>",
            unsafe_allow_html=True,
        )

        tier_filter = st.selectbox(
            "Filter by risk level",
            ["All Levels", "🔴 High", "🟠 Elevated", "🟡 Monitor", "🟢 Low"],
            key="tier_flt",
        )

        rank_df = muni_df.copy() if not muni_df.empty else pd.DataFrame()

        # Apply tier filter when a specific level is selected
        if not rank_df.empty and tier_filter != "All Levels":
            tier_label_map = {
                "🔴 High":     "High",
                "🟠 Elevated": "Elevated",
                "🟡 Monitor":  "Monitor",
                "🟢 Low":      "Low",
            }
            rank_df = rank_df[rank_df["tier"] == tier_label_map.get(tier_filter, "")]

        if rank_df.empty:
            st.info("No municipios match this filter.")
        else:
            rank_df = rank_df.sort_values(
                "priority_index_conf_adj", ascending=False
            ).reset_index(drop=True)
            rank_df["Rank"]          = rank_df.index + 1
            rank_df["Risk Level"]    = rank_df["tier"].map(lambda t: f"{t_emoji(t)} {t_label(t)}")
            rank_df["Why High Risk"] = rank_df.apply(why_risk, axis=1)
            rank_df["Action"]        = (
                rank_df.get("recommended_actions", pd.Series("Monitor"))
                .fillna("Monitor")
                .map(lambda x: str(x).split("|")[0].strip())
            )
            display_df = rank_df[
                ["Rank", "municipio", "Risk Level", "priority_index_conf_adj",
                 "Why High Risk", "Action"]
            ].rename(columns={
                "municipio":                 "Municipio",
                "priority_index_conf_adj":   "Score",
            })
            st.dataframe(display_df, use_container_width=True, hide_index=True, height=380)

        # What drives risk? explainer cards
        st.divider()
        st.markdown(
            f"<h4 style='font-family:Inter,sans-serif;color:{C['text']}'>ℹ️ What Drives Risk?</h4>",
            unsafe_allow_html=True,
        )
        explainer_items = [
            ("🌊", "Flood Hazard",
             "Water-level sensors + NWS alerts. Reflects active or imminent flood risk.",
             "#ef4444"),
            ("🏘️", "Vulnerable People",
             "Poverty + no-vehicle households + housing quality. Higher = harder to evacuate.",
             "#f97316"),
            ("🚑", "Response Readiness",
             "Access to hospitals, shelters, services. Lower = slower rescue & recovery.",
             "#22c55e"),
        ]
        for exp_col, (icon, title, desc, border_color) in zip(st.columns(3), explainer_items):
            exp_col.markdown(
                f"<div style='background:{C['card']};border-left:3px solid {border_color};"
                f"padding:12px;border-radius:8px'>"
                f"<b style='color:{C['text']}'>{icon} {title}</b><br/>"
                f"<span style='color:{C['muted']};font-size:13px'>{desc}</span></div>",
                unsafe_allow_html=True,
            )

        # Priority score bar chart (requires Plotly)
        if not rank_df.empty and HAS_PLOTLY:
            st.divider()
            max_n   = max(len(rank_df), 6)
            chart_n = st.slider("Municipios in chart", 5, max_n, min(20, max_n), key="rank_slider")
            chart_df = rank_df.head(chart_n).sort_values("priority_index_conf_adj", ascending=True)

            fig = px.bar(
                chart_df,
                x="priority_index_conf_adj",
                y="municipio",
                color="tier",
                orientation="h",
                color_discrete_map={
                    "High":     "#ef4444",
                    "Elevated": "#f97316",
                    "Monitor":  "#eab308",
                    "Low":      "#22c55e",
                },
                labels={
                    "priority_index_conf_adj": "Priority Score",
                    "municipio":               "",
                    "tier":                    "Risk Level",
                },
                title=f"Top {chart_n} Municipios — Priority Score",
                height=max(380, chart_n * 22),
            )
            fig.update_layout(
                margin=dict(l=0, r=10, t=40, b=0),
                legend_title="Risk",
                paper_bgcolor=C["plot_paper"],
                plot_bgcolor=C["plot_bg"],
                font=dict(family="Inter, sans-serif", color=C["plot_font"]),
                xaxis=dict(gridcolor=C["plot_grid"]),
                yaxis=dict(gridcolor=C["plot_grid"]),
                legend=dict(
                    bgcolor=C["plot_paper"],
                    bordercolor=C["plot_grid"],
                    borderwidth=1,
                    font=dict(color=C["plot_font"]),
                ),
            )
            st.plotly_chart(fig, use_container_width=True)

    # =======================================================================
    # TAB 3 — Live Conditions
    # Active NWS alert cards + NOAA station gauge readings with progress bars.
    # =======================================================================
    with tab_live:
        st.markdown(
            f"<h4 style='font-family:Inter,sans-serif;color:{C['text']}'>🌊 Live Conditions</h4>",
            unsafe_allow_html=True,
        )

        # NWS Alerts section
        st.markdown(
            f"<b style='color:{C['text']}'>⚠️ Active NWS Alerts &nbsp;"
            f"<code>{len(alerts_df)}</code></b>",
            unsafe_allow_html=True,
        )
        if alerts_df.empty:
            st.success("✅ No active NWS alerts for Puerto Rico right now.")
        else:
            for _, alert_row in alerts_df.iterrows():
                severity    = str(alert_row.get("severity", "Unknown"))
                alert_color = sev_color(severity)
                expires     = str(alert_row.get("ends", ""))[:16]
                area        = str(alert_row.get("area_desc", "PR"))[:140]
                st.markdown(
                    f"<div style='border-left:4px solid {alert_color};background:{C['card']};"
                    f"padding:12px 16px;margin-bottom:8px;border-radius:8px;"
                    f"border:1px solid {C['border']}'>"
                    f"<div style='display:flex;justify-content:space-between'>"
                    f"<b style='color:{C['text']};font-size:15px'>"
                    f"{alert_row.get('event', 'Alert')}</b>"
                    f"<span style='color:{alert_color};font-weight:600;font-size:13px'>"
                    f"{severity}</span></div>"
                    f"<div style='color:{C['muted']};font-size:13px;margin-top:4px'>📍 {area}</div>"
                    f"<div style='color:{C['muted']};font-size:12px;margin-top:3px'>"
                    f"⏰ Expires: {expires}</div></div>",
                    unsafe_allow_html=True,
                )

        st.divider()

        # Water monitoring stations section
        st.markdown(
            f"<b style='color:{C['text']}'>🌊 Water Monitoring Stations &nbsp;"
            f"<code>{len(stations_df)} online</code></b>",
            unsafe_allow_html=True,
        )
        if stations_df.empty:
            st.info("No station data available.")
        else:
            # Build the station map (stations with valid coordinates only)
            station_map_df = stations_df.dropna(subset=["latitude", "longitude"]).copy()
            if not station_map_df.empty:
                station_map_df["haz"]       = station_map_df["flood_hazard_final"].fillna(0)
                station_map_df["tier"]      = station_map_df["haz"].map(
                    lambda x: "High" if x >= 70 else ("Elevated" if x >= 50 else "Monitor")
                )
                station_map_df["color_rgb"] = station_map_df["tier"].map(t_rgb)
                station_map_df["wl_str"]    = station_map_df["latest_water_level"].map(
                    lambda x: f"{x:.2f} ft" if x is not None else "n/a"
                )
                station_map_df["haz_label"] = station_map_df["haz"].map(lambda x: f"{x:.0f}/100")
                station_map_df["trend"]     = station_map_df["rise_rate_per_hour"].map(
                    lambda r: "↑ Rising" if (r or 0) > 0.05 else (
                        "↓ Falling" if (r or 0) < -0.05 else "→ Stable"
                    )
                )
                st.pydeck_chart(
                    build_station_map(station_map_df, MAP_STYLE),
                    use_container_width=True,
                    height=300,
                )

            # Per-station reading cards with flood threshold progress bars
            st.markdown(
                f"<b style='color:{C['text']};font-size:13px'>"
                f"Station Readings vs Flood Thresholds:</b>",
                unsafe_allow_html=True,
            )
            for _, stn in stations_df.sort_values("flood_hazard_final", ascending=False).iterrows():
                haz_score = float(stn.get("flood_hazard_final", 0) or 0)
                wl        = stn.get("latest_water_level")
                rate      = float(stn.get("rise_rate_per_hour", 0) or 0)
                minor     = stn.get("minor")
                moderate  = stn.get("moderate")
                major     = stn.get("major")
                trend     = "↑ Rising" if rate > 0.05 else ("↓ Falling" if rate < -0.05 else "→ Stable")
                stn_color = "#ef4444" if haz_score >= 70 else ("#eab308" if haz_score >= 50 else "#22c55e")
                icon      = "🔴" if haz_score >= 70 else ("🟡" if haz_score >= 50 else "🟢")
                wl_str    = f"{float(wl):.2f} ft" if wl is not None else "No reading"
                minor_str = f"{float(minor):.2f} ft" if minor is not None else "n/a"

                threshold_html = ""
                if moderate is not None:
                    threshold_html += f"<span>🟠 Moderate: <b>{float(moderate):.2f} ft</b></span>"
                if major is not None:
                    threshold_html += f"<span>🔴 Major: <b>{float(major):.2f} ft</b></span>"

                st.markdown(
                    f"<div style='background:{C['card']};border:1px solid {C['border']};"
                    f"border-left:4px solid {stn_color};border-radius:8px;"
                    f"padding:12px 16px;margin-bottom:10px'>"
                    f"<div style='display:flex;justify-content:space-between'>"
                    f"<b style='color:{C['text']}'>{icon} {stn.get('station_name', 'Station')}</b>"
                    f"<span style='color:{C['muted']};font-size:12px'>"
                    f"Hazard score: {haz_score:.0f}/100</span></div>"
                    f"<div style='display:flex;gap:20px;margin-top:6px;font-size:13px;color:{C['text']}'>"
                    f"<span>💧 Level: <b>{wl_str}</b></span>"
                    f"<span>📈 {trend}</span>"
                    f"<span>⚠️ Minor flood at: <b>{minor_str}</b></span>"
                    f"{threshold_html}"
                    f"</div></div>",
                    unsafe_allow_html=True,
                )
                # Progress bar: how close is the current level to minor flood stage?
                if wl is not None and minor is not None and float(minor) > 0:
                    pct_of_minor = min(float(wl) / float(minor), 1.0)
                    st.progress(
                        pct_of_minor,
                        text=f"{pct_of_minor * 100:.1f}% of minor flood stage ({minor_str})",
                    )

        st.divider()
        st.markdown(
            f"<div style='background:{C['card']};border:1px solid {C['border']};"
            f"border-left:3px solid #22c55e;padding:12px 16px;border-radius:8px;"
            f"color:{C['muted']};font-size:13px'>"
            f"🗻 <b style='color:{C['text']}'>Terrain Analysis — Coming Soon</b> · "
            f"Elevation, slope, wetness and runoff data is being collected for high-risk municipios.</div>",
            unsafe_allow_html=True,
        )

    # =======================================================================
    # TAB 4 — Ask the Data (natural-language chatbot)
    # Weighted intent scoring + fuzzy municipio name matching.
    # Backed by live DuckDB data — no external API required.
    # =======================================================================
    with tab_chat:
        st.markdown(
            f"<h4 style='font-family:Inter,sans-serif;color:{C['text']}'>💬 Ask the Data</h4>"
            f"<p style='color:{C['muted']};font-size:13px'>"
            f"Natural-language assistant backed by live DuckDB pipeline data. "
            f"Weighted intent scoring + fuzzy municipio matching. No external API required.</p>",
            unsafe_allow_html=True,
        )

        # Quick-question shortcut buttons
        st.markdown(
            f"<b style='color:{C['text']};font-size:13px'>Quick questions:</b>",
            unsafe_allow_html=True,
        )
        qq_cols = st.columns(3)
        for i, question in enumerate(QUICK_QUESTIONS):
            if qq_cols[i % 3].button(question, key=f"qq_{i}", use_container_width=True):
                st.session_state.chat_history.append({"role": "user", "content": question})
                with st.spinner("Querying data..."):
                    answer = process_query(question, con, municipio_names)
                st.session_state.chat_history.append({"role": "assistant", "content": answer})

        st.divider()

        # Chat history display
        with st.container(height=460):
            for msg in st.session_state.chat_history:
                avatar = "🤖" if msg["role"] == "assistant" else "👤"
                with st.chat_message(msg["role"], avatar=avatar):
                    st.markdown(msg["content"])

        # Free-text chat input
        user_input = st.chat_input("Ask about any municipio, risk, alerts, or vulnerability...")
        if user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            with st.spinner("Querying live data..."):
                answer = process_query(user_input, con, municipio_names)
            st.session_state.chat_history.append({"role": "assistant", "content": answer})
            st.rerun()

        # Clear button and usage hint
        clear_col, hint_col = st.columns([1, 5])
        if clear_col.button("🗑️ Clear chat"):
            st.session_state.chat_history = [{"role": "assistant", "content": _resp_help()}]
            st.rerun()
        hint_col.caption(
            "💡 Try: *'Tell me about Bayamón'*, *'earthquake risk'*, "
            "*'most vulnerable'*, *'active alerts'*"
        )

    # =======================================================================
    # TAB 5 — SQL Explorer
    # Read-only SELECT interface to the DuckDB baseline for ad-hoc analysis.
    # =======================================================================
    with tab_sql:
        st.markdown(
            f"<h4 style='font-family:Inter,sans-serif;color:{C['text']}'>🔍 SQL Explorer</h4>"
            f"<p style='color:{C['muted']};font-size:13px'>"
            f"Read-only SELECT access to the DuckDB baseline. "
            f"Pick a preset or write your own query. Results download as CSV.</p>",
            unsafe_allow_html=True,
        )

        # Expandable reference list of all views and base tables
        with st.expander("📋 Available views & tables", expanded=False):
            try:
                objects_df = con.execute("""
                    SELECT table_name AS name, table_type AS type
                    FROM information_schema.tables
                    WHERE table_schema = 'main'
                    ORDER BY table_type DESC, table_name
                """).df()
                if not objects_df.empty:
                    views  = objects_df[objects_df["type"] == "VIEW"]["name"].tolist()
                    tables = objects_df[objects_df["type"] == "BASE TABLE"]["name"].tolist()
                    view_col, table_col = st.columns(2)
                    with view_col:
                        st.markdown("**Views** *(use for analysis):*")
                        for v in views:
                            st.markdown(f"- `{v}`")
                    with table_col:
                        st.markdown("**Base tables:**")
                        for t in tables:
                            st.markdown(f"- `{t}`")
            except Exception:
                st.info("Could not list tables.")

        # Preset SQL query templates
        PRESETS: dict[str, str] = {
            "— Choose a preset —": "",
            "Top 10 priority municipios": (
                "SELECT municipio, priority_index_conf_adj AS score,\n"
                "       hazard_combined, vulnerability_score, recommended_actions\n"
                "FROM vw_priority_ranking\n"
                "ORDER BY overall_rank LIMIT 10"
            ),
            "Most vulnerable communities": (
                "SELECT municipio, vulnerability_score, poverty_rate,\n"
                "       no_vehicle_rate, population\n"
                "FROM vw_vulnerability_breakdown\n"
                "ORDER BY vulnerability_score DESC LIMIT 15"
            ),
            "Active NWS alerts": (
                "SELECT event, severity, alert_score, area_desc, sent, ends\n"
                "FROM vw_alerts_summary\n"
                "ORDER BY alert_score DESC"
            ),
            "Station levels vs thresholds": (
                "SELECT station_name, latest_water_level,\n"
                "       rise_rate_per_hour, minor, moderate, major, flood_hazard_final\n"
                "FROM vw_station_water_summary\n"
                "ORDER BY flood_hazard_final DESC"
            ),
            "Population by risk tier": (
                "SELECT\n"
                "  CASE\n"
                "    WHEN mi.priority_index_conf_adj >= 33 THEN '🔴 High'\n"
                "    WHEN mi.priority_index_conf_adj >= 23 THEN '🟠 Elevated'\n"
                "    WHEN mi.priority_index_conf_adj >= 18 THEN '🟡 Monitor'\n"
                "    ELSE '🟢 Low'\n"
                "  END AS risk_tier,\n"
                "  COUNT(*) AS municipios,\n"
                "  CAST(SUM(ev.population) AS BIGINT) AS total_population\n"
                "FROM baseline_municipio_indices mi\n"
                "JOIN baseline_exposure_vulnerability ev"
                "  ON mi.municipio_slug = ev.municipio_slug\n"
                "GROUP BY 1 ORDER BY 3 DESC"
            ),
            "Hazard breakdown (flood + earthquake)": (
                "SELECT municipio, hazard_combined, flood_hazard_muni,\n"
                "       earthquake_hazard_score, nws_global_alert_score\n"
                "FROM vw_hazard_breakdown\n"
                "ORDER BY hazard_combined DESC LIMIT 15"
            ),
            "Pipeline source status": (
                "SELECT name, status, row_count, file_type, description\n"
                "FROM vw_baseline_source_status"
            ),
        }

        def _on_preset_change() -> None:
            """Push the selected preset SQL into the sql_input session state key."""
            chosen_preset = st.session_state.get("sql_preset", "")
            preset_sql    = PRESETS.get(chosen_preset, "")
            if preset_sql:
                st.session_state["sql_input"] = preset_sql

        st.selectbox(
            "⚡ Preset queries",
            list(PRESETS.keys()),
            key="sql_preset",
            on_change=_on_preset_change,
        )

        # Seed the textarea with a default query on the first visit
        if "sql_input" not in st.session_state:
            st.session_state["sql_input"] = "SELECT * FROM vw_municipio_risk_summary LIMIT 20"

        sql_input = st.text_area("SQL Query", height=150, key="sql_input")

        run_col, download_col = st.columns([1, 4])
        if run_col.button("▶ Run", type="primary", use_container_width=True):
            # Only allow SELECT / WITH to prevent any write operations
            is_safe = (
                sql_input.strip().upper().startswith("SELECT")
                or sql_input.strip().upper().startswith("WITH")
            )
            if not is_safe:
                st.error("⛔ Only SELECT / WITH queries allowed in this read-only explorer.")
            else:
                try:
                    with st.spinner("Running..."):
                        result_df = con.execute(sql_input.strip()).df()
                    st.success(f"✅ {len(result_df):,} rows · {len(result_df.columns)} columns")
                    st.session_state.sql_history.append({
                        "sql":  sql_input.strip()[:80] + "…",
                        "rows": len(result_df),
                    })
                    st.dataframe(result_df, use_container_width=True, hide_index=True)
                    download_col.download_button(
                        "⬇ Download CSV",
                        data=result_df.to_csv(index=False).encode(),
                        file_name="query_result.csv",
                        mime="text/csv",
                    )
                except Exception as exc:
                    st.error(f"❌ **Query error:** `{exc}`")
                    st.markdown(
                        f"<div style='background:{C['card2']};padding:10px;border-radius:6px;"
                        f"border-left:3px solid #ef4444;font-size:13px;color:{C['muted']}'>"
                        f"💡 Check column and table names in the list above. "
                        f"Only SELECT / WITH are allowed.</div>",
                        unsafe_allow_html=True,
                    )

        # Query history (last 10 runs)
        if st.session_state.sql_history:
            with st.expander(
                f"🕐 Query history ({len(st.session_state.sql_history)})", expanded=False
            ):
                for entry in reversed(st.session_state.sql_history[-10:]):
                    st.markdown(
                        f"<code style='font-size:12px;color:{C['muted']}'>{entry['sql']}</code>"
                        f" — {entry['rows']} rows",
                        unsafe_allow_html=True,
                    )

        # Pipeline source status summary
        st.divider()
        with st.expander("🗂️ Pipeline Source Status", expanded=False):
            if not source_df.empty:
                source_df[""] = source_df["status"].map({
                    "loaded":         "✅",
                    "missing":        "❌",
                    "inventory_only": "📁",
                })
                st.dataframe(
                    source_df[["", "name", "status", "row_count", "file_type", "description"]],
                    use_container_width=True,
                    hide_index=True,
                )

finally:
    # Always close the DuckDB connection, even if an exception occurred above
    if con is not None:
        con.close()
