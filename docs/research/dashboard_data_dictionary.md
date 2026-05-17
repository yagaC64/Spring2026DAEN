# Dashboard Data Dictionary

**Project:** GMU Flood Early Warning Decision-Support Platform — Puerto Rico  
**Reference basis:** Index Spec v1 plus the recorded notebook/workbench handoff implementation in this repository  
**Purpose:** Define the main scored fields shown in the local workbench and related dashboard discussion materials without forcing reviewers to reconstruct the scoring flow from notebook code alone.

---

## Score Range

Current scored fields are normalized to a **0-100 scale** unless noted otherwise.

- Higher is worse for hazard, exposure, vulnerability, and priority-style fields.
- Higher is better for resilience, readiness, and recovery-capacity fields.
- `confidence_0_1` is the exception: it is stored on a **0-1 scale** as the normalized confidence value derived from `confidence_score`.

---

## Priority Band

The current scored outputs classify each municipio into a color band using the **confidence-adjusted priority score**.

| Band | Score Range | Meaning |
|---|---:|---|
| Green | 0-49.99 | Low concern |
| Yellow | 50-69.99 | Elevated; monitor closely |
| Orange | 70-84.99 | High; consider pre-positioning resources |
| Red | 85-100 | Critical; immediate action warranted |

**Current implementation note:**
- bands are assigned from `priority_index_conf_adj`
- hard red override is applied when `nws_global_alert_score >= 95` or `flood_hazard_muni >= 90`

---

## Hazard Fields

**`hazard_combined`**  
What it measures: overall hazard level after combining hazard inputs into a normalized municipio-level score.

**`flood_hazard_muni`**  
What it measures: municipio-level flood hazard derived from flood-related inputs.

**`earthquake_hazard_score`**  
What it measures: municipio-level earthquake hazard contribution used in the broader hazard picture.

**Main data sources:** NOAA CO-OPS, USGS NWIS, NWS alerts, and the earthquake ingest path used by the staged notebook pipeline.

---

## Exposure Score

**`exposure_score`**  
What it measures: the concentration of people or assets exposed to the hazard footprint.

In the conceptual risk equation, exposure is the **E** term.

---

## Vulnerability Score

**`vulnerability_score`**  
What it measures: how susceptible the population is to harm from a flood or related disruptive event.

The repository’s written design and staged feature engineering emphasize:
- social vulnerability inputs
- transport/access constraints such as no-vehicle households
- housing fragility proxies
- poverty and income-related stressors

This field is the **V** term in the conceptual risk equation.

---

## No-Vehicle Households

**What it means:** Percentage of households in a municipio without access to a private vehicle, typically sourced from Census / ACS-derived inputs.

**Why it matters:** Households without vehicles face greater evacuation and access constraints during flood events, which is why this factor matters operationally in vulnerability review.

---

## Poverty and Income Context

**Poverty-related indicators** capture the share of the population experiencing direct economic hardship.  
**Income-related indicators** capture broader earning capacity.

Both matter because they describe different dimensions of vulnerability rather than duplicating the same idea.

---

## Resilience, Readiness, and Recovery Fields

**`resilience_index`**  
What it measures: retained capacity or system strength relative to fragility-style inputs.

**`response_readiness_index`**  
What it measures: how ready the municipio is to respond effectively right now.

**`recovery_capacity_index`**  
What it measures: how well the municipio can recover or restore function after disruption.

These fields are part of the operational scoring path and help shape priority, but they are not all “risk” in the narrow hazard-times-exposure-times-vulnerability sense.

---

## Risk Index vs Priority Index

**`risk_index_raw`**  
Formula:

`risk_index_raw = (hazard_combined / 100) * (exposure_score / 100) * (vulnerability_score / 100) * 100`

This is the repository’s implemented multiplicative **risk concept**, corresponding to the familiar `H × E × V` framing from Index Spec v1.

**Important distinction:** the current ranked operational output is **not** driven by `risk_index_raw` alone.

**`priority_index`**  
What it measures: phase-aware operational priority that combines:
- raw risk
- lower response readiness
- lower recovery capacity

The weights vary by phase (`PRE`, `DURING`, `POST`) in the scoring notebook.

**`priority_index_conf_adj`**  
What it measures: the confidence-adjusted version of `priority_index`.

This is the field currently used for:
- ranking municipios in the scored outputs
- assigning `priority_band`
- driving the main workbench table/chart ordering

---

## Confidence Fields

**`confidence_score`**  
What it measures: overall confidence in the scored output, based on data freshness, completeness, validity, and cross-check logic.

Stored range: **0-100**

**`confidence_0_1`**  
What it measures: normalized confidence derived from `confidence_score / 100`

Stored range: **0-1**

**Operational use:** confidence is used to adjust `priority_index` into `priority_index_conf_adj`, reducing overconfidence when input quality is weaker.

---

## Data Sources Summary

| Field family | Typical source |
|---|---|
| Water level / flood thresholds | NOAA CO-OPS API |
| Stream discharge / gage height | USGS NWIS |
| Flood alerts | NWS CAP / alerts API |
| Population, housing, income, vehicles | US Census / ACS |
| Social vulnerability context | CDC/ATSDR SVI and related census-derived features |
| Infrastructure / facilities context | Curated GIS layers and derived features |

---

## Reviewer Note

This dictionary is meant to support handoff and review of the repository’s recorded scoring/workbench state. Where the conceptual index specification and the implemented operational scoring path differ, this note prioritizes the **implemented handoff state** so future contributors are not misled about what the repository currently does.
