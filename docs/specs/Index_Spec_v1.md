# Index Spec v1 — GMU Disaster Decision Support Indices (Puerto Rico)

**Project:** GMU open-source class project (notebook-derived data + geospatial layers)  
**Goal:** Operational decision support for life safety, infrastructure continuity, utility resilience, emergency response, and recovery.

---

## 0. Design Principles

1. **Defensible:** Align to established risk/resilience concepts; every score is explainable.
2. **Operational:** Works pre/during/post event; supports escalation + prioritization.
3. **Transparent MVP:** Weighted sum baseline + optional AHP for eliciting weights.
4. **Confidence-aware:** Every index has a confidence score driven by data quality.
5. **Scale-aware:** Station-level → municipio-level aggregation with distance weighting.

---

## 1. Taxonomy: Four Indices

### 1.1 Risk Index (R)
**Question:** Where is harm most likely *if the hazard manifests*?  
**Core form:**
\[
R = H \times E \times V
\]
- **H (Hazard)**: intensity/likelihood from sensors + alerts
- **E (Exposure)**: people/assets in hazard footprint
- **V (Vulnerability)**: social + structural + access constraints

### 1.2 Resilience Index (Res)
**Question:** How well can the system absorb disruption and continue critical function?  
\[
Res = 100 - \sum_i w_i \cdot s_i \quad (\text{where } s_i \text{ are “fragility/weakness” scores})
\]

### 1.3 Response Readiness Index (RR)
**Question:** Can we respond fast/effectively if something happens now?  
\[
RR = 100 - \sum_i w_i \cdot s_i \quad (\text{where } s_i \text{ are “gaps/latency/constraints” scores})
\]

### 1.4 Recovery Capacity Index (RC)
**Question:** How quickly can essential services and livelihoods be restored?  
\[
RC = 100 - \sum_i w_i \cdot s_i \quad (\text{where } s_i \text{ are “recovery impediment” scores})
\]

---

## 2. Scoring & Normalization

### 2.1 Normalize each raw indicator to a 0–100 score
Let indicator value be \(x\) with bounds \(L, U\).

**If higher is worse (risk drivers):**
\[
s = 100 \cdot \mathrm{clip}\left(\frac{x - L}{U - L}, 0, 1\right)
\]

**If higher is better (capacity):**
\[
s = 100 \cdot \left(1 - \mathrm{clip}\left(\frac{x - L}{U - L}, 0, 1\right)\right)
\]

**Bounds policy (in order of preference):**
1. Agency/engineering thresholds when available (e.g., flood stages)
2. Robust percentiles (p05/p95) from Puerto Rico baseline window
3. Fixed domain bounds documented in assumptions

### 2.2 Combine indicators (MVP baseline)
\[
Index = \sum_i w_i \cdot s_i \quad;\quad \sum_i w_i = 1
\]

**Baseline method:** Weighted sum + stakeholder weight elicitation (AHP optional).  
**Advanced extension:** Bayesian/MCDA with uncertainty propagation once validation labels exist.

---

## 3. Indicator Taxonomy: Leading / Coincident / Lagging

- **Leading (Pre-event):** readiness posture, staging, warnings
- **Coincident (During-event):** routing, rescue prioritization, resource allocation
- **Lagging (Post-event):** restoration priority, after-action learning, recovery planning

Each indicator MUST declare:
- **Unit**
- **Directionality** (↑ worse / ↑ better)
- **Cadence** (refresh frequency)
- **Category** (leading/coincident/lagging)

---

## 4. Data Inputs (Notebook Outputs)

### 4.1 Time-series Feeds
**NOAA water levels (CO-OPS):**
- `station_id, t_utc, water_level, datum, qc_flag`

**NOAA station metadata (thresholds):**
- `station_id, lat, lon, minor_flood, moderate_flood, major_flood` (if available)

**USGS hydrology (NWIS):**
- `site_no, t_utc, discharge_00060, gage_height_00065, qc_flag`

**NWS alerts:**
- `alert_id, event, severity, certainty, onset, ends, geometry, affected_zones`

### 4.2 Static / Slow-changing Layers
**Census/ACS:**
- `geoid, pop_total, age65plus_pct, disability_pct, income, housing_burden, limited_english_pct, no_vehicle_pct`

**SVI (preferred):**
- `geoid, svi_overall, svi_theme1..theme4`

**Critical infrastructure layers (points/lines/polygons):**
- hospitals, clinics, substations, water plants/intakes, telecom towers, roads/bridges, ports, airports, fire/police/EOCs, shelters

---

## 5. Flood Module (v1)

### 5.1 Station-level Flood Hazard \(H_f^{station}\)

**Option A (NOAA CO-OPS):**
- Stage exceedance ratio:
\[
x_{exc}=\frac{WL - WL_{minor}}{WL_{major}-WL_{minor}}
\]
- Stage rise rate:
\[
x_{rate}=\frac{WL_t - WL_{t-\Delta t}}{\Delta t}
\]

Combine:
\[
H_f^{station} = 0.6\cdot s(x_{exc}) + 0.4\cdot s(x_{rate})
\]

**Option B (USGS streamgage):**
\[
H_f^{station} = 0.5\cdot s(\text{gage height}) + 0.5\cdot s(\Delta Q/\Delta t)
\]

### 5.2 Alert Override (NWS)
Map alerts to a score \(s_{NWS}\) (example):
- Flood Watch = 40
- Flood Warning = 70
- Flash Flood Warning = 100

Final hazard:
\[
H_f^{final} = \max\left(H_f^{station},\ s_{NWS}\right)
\]

---

## 6. Earthquake Module (v1)

### 6.1 Event severity proxy per municipio
Let \(M\)=magnitude, \(d\)=km distance from epicenter to municipio centroid.

\[
x_{eq} = \frac{M}{\log(1+d)} \cdot g(depth)
\]

Normalize to \(H_{eq}\).  
Then compute:
\[
R_{eq} = H_{eq} \times E \times V
\]

(Advanced extension: replace proxy with modeled shaking/intensity if available.)

---

## 7. Exposure (E) & Vulnerability (V)

### 7.1 Exposure (E) — baseline
Examples:
- `pop_in_zone` or `%pop_in_zone` (hazard influence footprint)
- `critical_facilities_in_zone` count

Normalize to 0–100 where higher is worse.

### 7.2 Vulnerability (V) — baseline
Use SVI + access constraints + housing fragility proxy.

Suggested weights (MVP):
- SVI overall: 0.60
- Access constraints (no-vehicle %, road fragility): 0.25
- Housing fragility proxy: 0.15

\[
V = 0.60\cdot s(SVI) + 0.25\cdot s(Access) + 0.15\cdot s(Housing)
\]

---

## 8. Critical Infrastructure Continuity (ICS) for Resilience

Compute sector sub-scores per municipio, then:
\[
ICS = \sum_{sector} w_{sector}\cdot s_{sector}
\]

Suggested sector weights (editable):
- Hospitals 0.20
- Power 0.20
- Water 0.15
- Roads/Bridges 0.15
- Telecom 0.10
- Ports 0.08
- Airports 0.07
- Emergency facilities 0.05

Resilience index:
\[
Res = 100 - ICS
\]

---

## 9. Response Readiness (RR)

Core indicators (examples):
- Alert-to-action readiness (EOC/shelter staffing flags if available)
- Route reliability to shelters/critical facilities
- Resource proximity (travel time to hotspots)
- Communications reach proxy

\[
RR = 100 - \sum_i w_i\cdot s_i
\]

---

## 10. Recovery Capacity (RC)

Core indicators (examples):
- Utility restoration velocity: \(\Delta(\% restored)/\Delta t\)
- Healthcare access restoration (travel time vs baseline)
- School reopening (% operational)
- Housing habitability proxy

\[
RC = 100 - \sum_i w_i\cdot s_i
\]

---

## 11. Station → Municipio Aggregation

For municipio \(m\) and stations \(j\), distance-weighted hazard:
\[
H_m = \frac{\sum_j e^{-d_{jm}/\lambda}\cdot H_j}{\sum_j e^{-d_{jm}/\lambda}}
\]
- \(\lambda\) default: 15 km (tune by basin scale)
- Optional worst-case override: if station in municipio, allow `max()` with weighted mean.

---

## 12. Dynamic Weighting by Phase

Define phase based on alert state:
- **Pre-event:** focus vulnerability + readiness
- **During-event:** focus hazard + access
- **Post-event:** focus continuity + recovery velocity

Example weights for Risk components:
- Pre: \(w_H=0.35,\ w_E=0.25,\ w_V=0.40\)
- During: \(w_H=0.55,\ w_E=0.20,\ w_V=0.25\)

---

## 13. Threshold Bands (Green/Yellow/Orange/Red)

### 13.1 Quantile bands (default)
- Green: 0–50
- Yellow: 50–70
- Orange: 70–85
- Red: 85–100

### 13.2 Hard overrides (authoritative signals)
- Flash Flood Warning ⇒ Red
- “Major flood” threshold exceeded ⇒ Orange/Red (policy-set)

---

## 14. Uncertainty, Data Quality, and Confidence

### 14.1 Per-observation quality factors (0–1)
- **Freshness (F):** time since last update
- **Completeness (C):** missingness in recent window
- **Validity (V):** range/unit checks + QC flags
- **Cross-check (X):** consistency with nearby feeds / alert state

\[
Conf = 0.35F + 0.25C + 0.25V + 0.15X
\]

### 14.2 Confidence-adjusted index
\[
Index^* = Conf\cdot Index + (1-Conf)\cdot Index_{baseline}
\]
Where `Index_baseline` is last known good or baseline median.

---

## 15. Explainability Template (Required Output)

For any municipio score, provide:
1. **Top drivers** (3–5 indicators with contributions \(w_i s_i\))
2. **Alert context** (active watches/warnings)
3. **Confidence** (Conf + why it’s low/high)
4. **Recommended actions** (phase-aware)

---

## 16. Validation & Backtesting (v1 Plan)

1. Select 3–5 historical hazard events affecting PR.
2. Recompute indices over time; compare “red” rankings to outcomes:
   - outage duration proxies
   - shelter demand / accessibility constraints
   - known impacted municipios (qualitative if needed)
3. Metrics:
   - rank correlation (Spearman) between Risk and outcome proxy
   - stability under synthetic feed dropouts (20–40%)
   - false escalation review (cases where red did not align with impact)

---

## 17. Deliverables (v1 MVP)

- `index_inputs/` normalized dataframes + provenance fields
- `index_engine/` scoring + aggregation functions/notebooks
- `index_outputs/` municipio-level time series + station panels + confidence
- `docs/specs/Index_Spec_v1.md` (this file)
- Dashboard:
  - Municipio choropleth + confidence overlay
  - Station trend sparklines + threshold badges
  - “Why this is red” panel + action checklist

---

## 18. Assumptions (Declare in README)

- Bounds \(L,U\) chosen from thresholds or robust percentiles.
- SVI used as relative vulnerability; year-to-year comparisons handled cautiously.
- Where direct restoration KPIs are absent, use proxies and label them clearly.
- Hazard footprint approximation used until hydrodynamic models are integrated.

---

## 19. Configuration Knobs (YAML/JSON)

- Indicator bounds (L/U)
- Indicator weights (per index + per phase)
- Distance decay \(\lambda\)
- Alert-to-score mapping
- Band thresholds
- Confidence factor thresholds

---

## 20. Roadmap (Semester)

**Weeks 1–6:** Flood Risk MVP + confidence + explainability  
**Weeks 7–10:** Backtesting + bands tuning + response overlays  
**Weeks 11–15:** Earthquake module + dynamic weighting + fairness checks

---
