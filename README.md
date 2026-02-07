# Spring 2026 DAEN — Flood Early Warning Decision-Support MVP

**Purpose**
Deliver an integrated decision-support + data Science/Data Analytics prototype for community flood early warning by turning public data into actionable, defensible insights. The MVP emphasizes a reusable Data-as-a-Service foundation and a mobile-friendly web dashboard (not a native app).

**Core Objectives**
- Curate, ingest, normalize, and document authoritative public datasets (e.g., USGS, NOAA, USACE, Census, agreed layers)
- Provide repeatable refresh mechanisms and provenance so future teams can extend the pipeline
- Implement explainable indicators and quality checks (data gaps, plausibility, thresholds, trend signals)
- Deliver a map-centric, responsive dashboard with stakeholder-driven views (Risk/Readiness, Response/Routes, Data Quality)
- Produce runbooks, architecture diagrams, and a reusable repository for handoff

**Scope**
- Data-as-a-Service layer with documented sources, refresh, and catalog
- Decision-support analytics (risk/readiness prioritization overlays)
- Web dashboard optimized for phone browsers
- Demo-ready storytelling for stakeholders

**Source Intelligence Structure**
- `sources/IMINT`: imagery intelligence used for PAB/CAI image products, geospatial interpretation, and visual change detection.
- `sources/MASINT`: measurement and signature intelligence from sensors and instrument-based streams used to monitor hazard and infrastructure signals.
- `sources/OSINT`: open-source intelligence including public datasets, bulletins, and openly available operational references.
- `sources/HUMINT`: field intelligence captured by instructors and students during site visits to risk zones or post-event areas to document risks, readiness, and resiliency conditions.
- Operational intent: combine these intelligence streams to support defensible situation awareness, planning, and response decisions.

**Out of Scope**
- Native mobile apps (iOS/Android)
- Hardware sensor design/build or embedded firmware
- Large-scale ML training requiring specialized GPU/MLOps
- 24/7 production deployment and monitoring

**Key Stakeholders**
- Instructor/PM authority: Isaac
- Partners/SMEs: Gilberto (continuity + stakeholder alignment), Melvin (mission + community narrative), Willie (data engineering + platform guardrails)
- Optional external demos: STAR-TIDES / USACE (only if scope allows)

**Operating Cadence (Target)**
- Agile sprints with weekly partner meeting
- Sequence: data inventory + requirements → pipeline + baseline dashboard → indices + prioritization → packaging + demo

**License Direction**
- Apache 2.0 (see `LICENSE`) to encourage broad participation and reuse across semesters and partner organizations.
- Rationale: permissive terms plus an explicit patent grant help reduce friction for contributors and downstream adopters while keeping the project easy to extend semester-over-semester.
