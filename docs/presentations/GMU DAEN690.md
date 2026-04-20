# Puerto Rico Community Flood Early Warning Decision-Support System

**DAEN 690 - Team UX/UI | Data Analytics Engineering | George Mason University | Spring 2026**

---

## Research Question
How can open-source tools provide a real-time, cloud-independent flood risk dashboard for Puerto Rico’s municipal emergency managers?

---

## Abstract
Puerto Rico’s 78 municipios face recurring flood threats with no unified, locally-operable risk dashboard. This project builds a fully offline decision-support system using DuckDB, Python, and Streamlit with zero cloud infrastructure dependency and no API subscriptions. Our composite hazard index integrates 10 open federal data sources (FEMA, USGS, NWS, NOAA, ACS Census) to rank all 78 municipios by flood priority. This tool directly addresses the STAR-TIDES 2026 theme: empowering local communities with zero federal dependency.

---

## Introduction / Background
Hurricane Maria (2017) exposed a critical gap: Puerto Rico’s local emergency managers lacked a unified, real-time tool to identify which communities needed help first. Existing federal systems require internet connectivity and cloud access unavailable during exactly the conditions when they are needed most.

With 78 municipios and no unified dashboard, emergency response has historically been reactive and inequitable. Vieques (pop. 8,078; 59.1% poverty rate) and interior mountain communities face heightened risk with the fewest resources. This project addresses that gap directly with a community-first, local-first platform deployable on a single laptop — no cloud, no server, no cost.

---

## Methodology / Process
### 5-Stage Pipeline
1. **Ingest** - Data from FEMA, USGS, NWS, NOAA, ACS Census  
2. **Feature Engineering** - Hazard score, vulnerability index, response readiness rating per municipio  
3. **Composite Scoring** - Weighted formula combining hazard + vulnerability + readiness  
4. **Load** - Into DuckDB embedded database with 9 analytical views (no server required)  
5. **Serve** - Streamlit dashboard (5 tabs): Risk Map, Rankings, Live Conditions, Chatbot, SQL Explorer  

---

## Research Question Figure
**Fig. 2. Streamlit App**

Main application shown:
- **Puerto Rico Community Flood Early Warning System**
- Live decision support for emergency managers and community leaders
- 78 municipios prioritized

Visible dashboard elements include:
- municipio flood risk map
- area details
- priority, population, flood hazard, earthquake, vulnerability, readiness
- filters / search for municipio
- navigation tabs such as:
  - overview map
  - risk rankings
  - live conditions
  - ask the data
  - SQL explorer

---

## How to Use the System
1. Open the dashboard  
2. View flood risk map  
3. Check high-risk municipios  
4. Use chatbot to ask questions (e.g. “Which areas are high risk?”)  
5. Take action based on insights  

---

## Key Features
1. Real-time data integration  
2. Risk scoring and ranking  
3. Interactive map visualization  
4. Chatbot for natural language queries  
5. Fully offline operation  

---

## Why Unique
1. Works offline (no cloud)  
2. Open-source and zero cost  
3. Explainable risk scoring  
4. Built for real-world emergency use  

---

## Results / Data / Evidence
The system successfully analyzes all municipios in Puerto Rico and classifies them into different flood risk levels based on multiple factors such as hazard, vulnerability, and readiness index. It helps identify higher-risk areas and supports prioritization of resources for emergency planning.

The results provide a clear and explainable ranking of municipios, enabling decision-makers to quickly understand which regions require more attention. Overall, the system demonstrates how integrated data and analytics can improve preparedness and support faster, data-driven decision-making. This enables faster and more targeted decision-making during flood events.

---

## Discussion / Conclusions
Our system demonstrates that community-level flood decision support does not require federal cloud infrastructure. By running entirely on local hardware with open data, this enables communities to act independently and respond effectively even when traditional systems fail.

**This tool operates with zero federal dependency, empowering local communities to act independently when federal systems fail.**

### Future Work
- Real-time USGS/NWS API integration  
- Mobile-first interface for field responders  
- Predictive ML flood probability layer  
- Expansion to other US territories  

---

## Acknowledgements
Supervised by William Martinez, Prof. Isaac Gang, DAEN 690, George Mason University, Spring 2026. Presented at the 19th STAR-TIDES demo, Arlington, VA, April 13-14, 2026.

All data sourced from FEMA, USGS, NWS, NOAA, and U.S. Census Bureau, fully open-source and in the public domain.

---

## References
- FEMA. (2024). National Flood Hazard Layer. `fema.gov/flood-maps`
- USGS. (2024). National Water Information System. `waterdata.usgs.gov`
- NWS. (2024). Weather Alert API. `weather.gov/alerts`
- U.S. Census Bureau. (2023). American Community Survey 5-Year Estimates. `census.gov/acs`
- DuckDB Foundation. (2024). DuckDB: An In-Process Analytical Database. `duckdb.org`

### Tech Stack
Python | DuckDB | Streamlit | pydeck | Plotly | Jupyter | NOAA | PRDINA

---

## LLM Interpretation Notes
This poster presents a **local-first, open-source flood early warning and decision-support MVP for Puerto Rico**.

### Core claims
- The system is designed to work **offline**, without cloud dependency
- It integrates multiple open federal/public datasets into a municipio-level flood prioritization workflow
- It uses **Python + DuckDB + Streamlit** as the main technical stack
- It produces explainable rankings and visual decision-support outputs for emergency managers
- It is positioned as a practical resilience tool for Puerto Rico, especially under degraded connectivity or infrastructure conditions

### Functional components emphasized
- multi-source data ingestion
- vulnerability and readiness scoring
- DuckDB embedded analytics
- Streamlit dashboard
- map-based visualization
- chatbot / natural language query concept
- local deployability on a single machine

### Positioning
The poster strongly frames the project as:
- community-first
- local-first
- zero-cloud
- low-cost
- explainable
- reusable for emergency response contexts

### Stated audience
- municipal emergency managers
- community leaders
- decision-makers
- emergency planning stakeholders