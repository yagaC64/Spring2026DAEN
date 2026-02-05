1) Scope
Project Title
Integrated UX/UI and Decision-Support Platform for Community Flood Early Warning Systems (Flood Sensor MVP)
In-Scope Objectives
The capstone team will deliver an analytics-driven decision-support MVP that integrates public flood-relevant data sources and presents actionable insights through a mobile-friendly web dashboard (not a native mobile app). The work will focus on:
    1. Data-as-a-Service foundation
        ◦ Identify, ingest, normalize, and document a curated set of authoritative, publicly available datasets (e.g., USGS, NOAA, USACE, Census, and other public layers as agreed).
        ◦ Provide repeatable refresh mechanisms and provenance documentation so future teams can continue without re-starting from scratch.
    2. Decision-support analytics
        ◦ Implement explainable indicators and quality checks (e.g., sensor/data gap detection, plausibility checks, baseline thresholds, trend indicators).
        ◦ Develop a risk/readiness prioritization view that can incorporate vulnerability signals (e.g., infrastructure fragility, community vulnerability proxies) alongside hazard indicators.
    3. UX/UI prototype for stakeholder use
        ◦ Deliver a map-centric dashboard with filters, layers, and a small set of stakeholder-driven “views” (e.g., “Readiness/Risk,” “Response/Routes,” “Data Quality”).
        ◦ Ensure the UI is usable from a phone browser (responsive layout) and supports demo-ready storytelling.
    4. Documentation and handoff
        ◦ Provide runbooks, architecture diagrams, and a documented repository suitable for reuse in subsequent semesters and partner operations.
Out of Scope (Explicit)
    • Native mobile application development (iOS/Android builds, app store packaging).
    • Hardware design/build (sensor fabrication, soldering, embedded firmware development).
    • Deep learning / high-scale model training requiring millions of labeled rows, specialized GPUs, or extensive MLOps infrastructure.
    • Operational deployment as a production service with 24/7 monitoring (capstone produces a prototype/MVP and documentation).
Assumptions
    • Data used is publicly accessible or shared by partners in a manner compatible with the capstone Terms of Service and open-source expectations.
    • Partners will provide weekly SME engagement and timely answers to domain questions.
    • Students will use GMU-supported compute environments (local laptops + optional GMU OpenStack/HPC), with external cloud usage constrained by availability/cost.
Key Constraints
    • 15-week course, with the first ~12 weeks for development; scope must fit that timeline.
    • Deliverables produced by students are expected to be open source (Apache 2.0) unless the program specifies otherwise.

2) Requirements
A) Partner Engagement Requirements
    1. Weekly Partner Meeting: 1-hour Zoom meeting each week with partners (SMEs) and the student team.
    2. POC Availability: Designate a primary partner POC (Willie) and backup POC (Gilberto or Melvin) for schedule continuity and fast clarifications.
    3. Response SLA: Partners respond to student questions/issues within 2 business days when feasible (especially data access blockers).
B) Data Requirements
    1. Source Register: Create a “Data Source Register” listing each dataset with:
        ◦ source/owner, URL/API, license terms, update cadence, spatial/temporal resolution, key fields/units, and known limitations.
    2. Curated Data Pack: Provide a minimal “seed dataset” (sample extracts) to allow development to start immediately, plus scripts/config to refresh from authoritative sources.
    3. Normalization: Define a consistent schema for time, location, units, and identifiers across sources (documented in a data dictionary).
    4. Provenance & Traceability: Every derived dataset must be reproducible and traceable to raw sources via scripts/notebooks and documentation.
C) Functional Requirements
Data Pipeline
    1. Ingest at least N agreed core sources (recommend 4–8) and produce normalized outputs.
    2. Automated refresh job or repeatable manual runbook that a new team can execute.
    3. Basic data quality checks, including:
        ◦ missing data/gap detection
        ◦ outlier detection (configurable thresholds)
        ◦ timestamp consistency and unit validation where possible
    4. Export/store results in accessible formats (e.g., CSV/Parquet/GeoJSON) and/or a simple service interface as feasible.
Analytics / Decision Support
5. Implement an initial Risk/Readiness Index v1 that is explainable and documented (not a black-box).
6. Implement a Data Reliability/Health view highlighting questionable readings, gaps, or sensor coverage limitations.
7. Provide prioritization logic that can incorporate vulnerability proxies (e.g., limited access routes, community vulnerability indicators) alongside hazard indicators.
UX/UI Dashboard
8. Deliver a map-centric dashboard with:
    • layer toggles
    • geographic filters
    • time filtering (where applicable)
    • at least 2–3 stakeholder “views” (e.g., Readiness, Response, Data Quality)
    9. Dashboard must be mobile-friendly via web browser (responsive layout) and usable on a phone screen.
    10. Provide a “demo script” or guided narrative enabling a 5–10 minute walkthrough.
D) Non-Functional Requirements
    1. Reproducibility: A new team should be able to clone the repo and run the pipeline using documented steps.
    2. Maintainability: Clear folder structure, README, and inline documentation for key modules/notebooks.
    3. Performance: Must handle the agreed dataset sizes within reasonable student compute limits; avoid unnecessary heavy dependencies.
    4. Security/Privacy:
        ◦ Use public data or partner-approved datasets only.
        ◦ No PII or sensitive operational details unless explicitly approved and appropriately handled.
    5. Licensing: Code and documentation compatible with Apache 2.0 (or program-specified permissive license). Data licensing constraints must be documented.
E) Acceptance Criteria (Definition of Done)
The project is considered successful when:
    1. The pipeline can refresh data from sources and produce normalized outputs without manual “hero work.”
    2. The dashboard loads and supports a coherent decision-support story with documented assumptions.
    3. The risk/readiness indicators are explainable, documented, and demonstrated with at least one realistic scenario.
    4. The repository includes: architecture overview, data source register, runbook, and final report/presentation materials.
F) Risks and Mitigations (short list)
    • Risk: Data availability/coverage gaps (e.g., sparse soil saturation sensors).
Mitigation: Explicit “coverage limitations” view and data quality flags; prioritize explainable indicators.
    • Risk: Scope creep toward native app or hardware build.
Mitigation: Enforce “mobile-friendly web dashboard only” and “no hardware build” statements in all docs.
    • Risk: Lost continuity of datasets across semesters.
Mitigation: Establish a data pack + storage plan and scripted refresh workflow.
