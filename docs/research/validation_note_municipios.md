# Validation Note — Selected Municipios

**Project:** GMU Flood Early Warning Decision-Support Platform — Puerto Rico  
**Municipios reviewed:** Salinas, Mayagüez, San Juan  
**Purpose:** Cross-check whether the dashboard/workbench risk outputs are directionally believable against publicly available historical and contextual sources.  
**Method:** Open-source review using FEMA, NOAA, NWS, USGS, and public reporting relevant to flood exposure and vulnerability in Puerto Rico.

---

## What "directionally believable" means

This note does **not** claim the dashboard scores are precise or fully validated against historical labels. The narrower goal is to test whether the relative output patterns make sense:

- if the model flags a municipio as high concern, is there public evidence that supports that concern?
- if the model shows a readiness offset, is that consistent with what is known publicly about capacity and infrastructure?

If yes, the model is at least pointing in a defensible direction.

---

## Salinas

**Why this municipio matters:**  
Salinas is on Puerto Rico's south coast, with exposure to coastal flooding, low-lying terrain, and socially vulnerable populations. It was also called out as a pilot municipio in class/client discussion.

**What public sources suggest:**
- FEMA maps place parts of the municipio in Special Flood Hazard Areas along the southern coastal plain.
- South-coast communities experienced significant flooding and long-duration disruption during Hurricane Maria (2017).
- Low elevation and surface-water accumulation risk make heavy-rain flood impacts plausible.
- Public vulnerability indicators for the area support concern around poverty, access constraints, and evacuation difficulty.

**Assessment:**  
Flagging Salinas as high concern is directionally consistent with known geography, historical flood exposure, and social vulnerability context.

---

## Mayagüez

**Why this municipio matters:**  
Mayagüez combines urban, riverine, and coastal exposure on the west side of Puerto Rico and was treated as a meaningful pilot municipio for hazard review.

**What public sources suggest:**
- The Río Yagüez corridor has a documented flood history affecting the urban core.
- FEMA flood mapping places portions of the municipio in higher-risk flood zones.
- The broader west-side hazard picture includes compounding stress from the 2020 earthquake sequence, which matters for infrastructure and recovery considerations even when the immediate focus is flooding.
- Public vulnerability indicators do not place Mayagüez among the least-constrained municipios, which supports a moderate-to-high concern posture rather than a low-risk one.

**Assessment:**  
Scoring Mayagüez as moderate-to-high concern is directionally believable given its river exposure, flood-zone presence, and multi-hazard context.

---

## San Juan

**Why this municipio matters:**  
San Juan is the capital, the most populous municipio, and a useful check on whether the model can reflect both **high exposure** and **higher relative capacity** at the same time.

**What public sources suggest:**
- San Juan has well-documented urban flooding in low-lying neighborhoods during heavy rainfall, even outside named storms.
- Hurricane Maria produced severe flooding impacts in and around the metro area.
- San Juan also has comparatively stronger hospital, government, and emergency infrastructure than many rural municipios.
- High population density and built-up exposure support elevated concern even when readiness is stronger than elsewhere.

**Assessment:**  
An output showing elevated concern with some readiness offset is directionally consistent with San Juan's profile: high exposure, recurring urban flood issues, and stronger institutional capacity than many other municipios.

---

## Overall Conclusion

Across these three review points, the outputs appear **directionally believable** based on public evidence:

- **Salinas:** high concern is consistent with south-coast flood geography and vulnerability context.
- **Mayagüez:** moderate-to-high concern is consistent with river corridor flooding and broader hazard exposure.
- **San Juan:** elevated concern with stronger readiness context fits a dense urban municipio with recurring flood issues and greater institutional capacity.

This note should be treated as a **qualitative plausibility check**, not as final empirical validation. A stronger future validation path would include event-based backtesting against specific historical cases such as Hurricane Maria and other documented flood episodes.

---

## Reference Pointers

- FEMA Flood Map Service Center: `msc.fema.gov`
- NOAA CO-OPS: `api.tidesandcurrents.noaa.gov`
- NWS San Juan Weather Forecast Office: `weather.gov/sju`
- USGS National Water Information System: `waterdata.usgs.gov`
- CDC/ATSDR Social Vulnerability Index: `atsdr.cdc.gov/place-health/php/svi`
