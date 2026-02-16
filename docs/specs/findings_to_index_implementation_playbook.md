# Findings to Index Implementation Playbook

## Purpose

Translate research findings into:
- explicit index formulas,
- reproducible dataframe features,
- notebook implementation steps for the GMU decision-support stack.

This playbook is implementation-focused and designed for class handoff/reuse.

## 1) Core Index Formulas

### 1.1 Risk Index (R)

\[
R_m = H_m \times E_m \times V_m
\]

- `H_m`: hazard score (flood or earthquake) for municipio `m`
- `E_m`: exposure score (population/assets in hazard influence area)
- `V_m`: vulnerability score (social + access + fragility)

### 1.2 Resilience Index (Res)

\[
Res_m = \sum_i w_i \cdot C_{m,i}
\quad\text{with}\quad \sum_i w_i = 1
\]

- `C_{m,i}` are continuity/capacity features (power, water, roads, health, telecom, etc.)

### 1.3 Response Readiness Index (RR)

\[
RR_m = \sum_i w_i \cdot RR_{m,i}
\]

- readiness features include route reliability, shelter reach, resource proximity, comms reach.

### 1.4 Recovery Capacity Index (RC)

\[
RC_m = \sum_i w_i \cdot RC_{m,i}
\]

- recovery features include utility restoration velocity, healthcare access restoration, school reopening, housing habitability proxy.

## 2) Standard Normalization Layer

For any raw indicator `x` with bounds `[L, U]`:

- if higher = worse:
\[
s = 100 \cdot clip\left(\frac{x-L}{U-L}, 0, 1\right)
\]

- if higher = better:
\[
s = 100 \cdot \left(1 - clip\left(\frac{x-L}{U-L}, 0, 1\right)\right)
\]

Use engineering thresholds when available; otherwise use robust local baselines (example: p05/p95).

## 3) Dataframe Feature Mapping

## 3.1 Flood hazard features (station-level)

| Feature | Source DataFrame | Raw Formula | Notes |
| --- | --- | --- | --- |
| `wl_exceed_ratio` | NOAA water levels + station thresholds | `(wl - minor) / (major - minor)` | Clamp to `[0,1+]`; null-safe if thresholds missing |
| `wl_rise_rate` | NOAA water levels | `delta(wl) / delta(hours)` | Compute over rolling window (example: 30-60 min) |
| `nws_alert_score` | NWS alerts | Watch=40, Warning=70, Flash Flood Warning=100 | Use max active severity per municipio/time |
| `hazard_flood_station` | Derived | `max(weighted(wl_exceed_ratio, wl_rise_rate), nws_alert_score)` | Supports hard override behavior |

## 3.2 Municipio aggregation features

| Feature | Source DataFrame | Raw Formula | Notes |
| --- | --- | --- | --- |
| `hazard_flood_muni` | station hazard + station-municipio distances | weighted mean by `exp(-d/lambda)` | allow in-municipio worst-station override |
| `exposure_population` | Census/ACS | population in influence zone (count or %) | normalize to score |
| `vuln_svi` | SVI | `svi_overall * 100` | keep year-consistent comparisons |
| `vuln_access` | Census + roads | no-vehicle + route constraints composite | explicit weighting required |

## 3.3 Response and recovery features

| Feature | Source | Raw Formula | Cadence |
| --- | --- | --- | --- |
| `route_reliability` | roads + hazard footprint | share of viable routes to critical facilities | hourly |
| `resource_proximity` | facilities + travel model | median travel time to hotspots | hourly |
| `utility_restore_velocity` | utility restoration feed | `delta(restored_pct)/delta(day)` | daily |
| `health_access_restore` | health facilities + travel model | delta travel-time vs baseline | daily |

## 4) Notebook Implementation Plan

## 4.1 Foundation notebooks (already in repo)

- `JupyterNotebooks/noaa-pr-waterlevel-hydrograph.ipynb`
- `JupyterNotebooks/nws-alerts-sync.ipynb`
- `JupyterNotebooks/usgs-water-sync.ipynb`
- `JupyterNotebooks/usgs-earthquakes-sync.ipynb`
- `JupyterNotebooks/census-risk-features-pr.ipynb`

## 4.2 New index notebooks (recommended)

1. `JupyterNotebooks/index-feature-engineering-pr.ipynb`
   - Merge normalized outputs from source notebooks.
   - Build station-level and municipio-level engineered features.
2. `JupyterNotebooks/index-scoring-pr.ipynb`
   - Apply normalization, weighting, and phase-specific logic.
   - Produce `Risk`, `Resilience`, `Response Readiness`, `Recovery Capacity`.
3. `JupyterNotebooks/index-validation-pr.ipynb`
   - Backtest against historical event periods and outcome proxies.
   - Report rank correlation, precision/recall for high-priority municipios.

## 4.3 Output artifacts (recommended)

- `outputs/index/municipio_index_timeseries.csv`
- `outputs/index/station_hazard_timeseries.csv`
- `outputs/index/index_confidence_scores.csv`
- `outputs/index/index_validation_report.md`

## 5) Phase-Based Dynamic Weighting

Define phase and weight vectors explicitly:

- Pre-event: emphasize vulnerability/readiness
- During-event: emphasize hazard/access constraints
- Post-event: emphasize continuity/recovery velocity

Represent as a versioned table in notebook config:

| Phase | `w_H` | `w_E` | `w_V` | `w_Res` | `w_RR` | `w_RC` |
| --- | --- | --- | --- | --- | --- | --- |
| Pre | ... | ... | ... | ... | ... | ... |
| During | ... | ... | ... | ... | ... | ... |
| Post | ... | ... | ... | ... | ... | ... |

## 6) Confidence and Data Quality Integration

Per-observation/source confidence:

\[
Conf = 0.35F + 0.25C + 0.25V + 0.15X
\]

- `F`: freshness
- `C`: completeness
- `V`: validity
- `X`: cross-source consistency

Confidence-adjusted score:

\[
Index^* = Conf \cdot Index + (1-Conf)\cdot Index_{baseline}
\]

## 7) Decision-Support Explainability Template

For each high-priority municipio, generate:

1. Top hazard drivers
2. Top vulnerability drivers
3. Top continuity/response constraints
4. Confidence tier
5. Recommended phase-specific actions

## 8) Definition of Done (per index release)

- Formula definitions documented and versioned.
- Feature dictionary complete (source, unit, direction, cadence).
- Notebook pipeline reproducible from raw pull to scored outputs.
- Confidence scoring enabled.
- Validation report produced with known-event backtest.
- Explainability summary produced for top-priority municipios.
