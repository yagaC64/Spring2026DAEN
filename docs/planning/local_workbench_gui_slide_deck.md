# PR Hazard and Readiness Analysis Workbench Slide Deck

**Audience:** GMU students, team members, and stakeholders  
**Purpose:** Explain why the new workbench was introduced, what it can do now, how to use it, and where it should go next.  
**Change window covered:** March 19, 2026 meeting guidance; March 26, 2026 baseline workbench implementation; April 2, 2026 workbench naming/positioning update; April 2, 2026 social adjustment factor implementation.

## Slide 1 — Title

**On-slide text**
- PR Hazard and Readiness Analysis Workbench
- Why We Added It, What It Does, and Where It Goes Next
- Spring 2026 DAEN / Puerto Rico Decision-Support MVP

**Talk track**
This workbench is not a separate project. It is a local analytical layer added on top of the existing notebook-first analytics pipeline so the team can inspect, validate, and explain current outputs through a single interactive surface.

## Slide 2 — Why Bring in a Workbench Now?

**On-slide text**
- The repo already had strong notebook outputs, but interaction was fragmented
- The team needed a practical local analysis surface for QA and demo support
- The March 19, 2026 meeting explicitly supported DuckDB + Streamlit for this stage
- The goal was low-cost, fast-start, local-first capability

**Talk track**
The reason for the workbench was not "because Streamlit is popular." It came from a practical gap: we had valuable outputs, but no single local workbench where a contributor or reviewer could quickly inspect ranked municipios, alerts, stations, terrain context, source readiness, and adjustment factors together. In the March 19 meeting, the client explicitly supported DuckDB and Streamlit for early-stage development because they are lightweight, low-cost, and aligned with an exploratory capstone phase.

## Slide 3 — Meeting Context Behind the Decision

**On-slide text**
- March 19, 2026: database options reviewed
- DuckDB approved as the current-stage analytical store
- Streamlit approved as an appropriate early-stage dashboard/workbench layer
- Snowflake and AWS remain future scaling options, not current defaults

**Talk track**
This is important for the audience: the workbench was not introduced as scope creep. It fits the meeting direction. William supported DuckDB for the current implementation stage and confirmed that DuckDB plus Streamlit is well-suited for early development. The team also discussed larger deployment options, but the approved near-term path was to stay low-friction and local-first until the stack is more validated.

## Slide 4 — What Changed in the Latest Repo Work

**On-slide text**
- March 26, 2026: DuckDB + Streamlit baseline added
- March 26, 2026: quickstart and planning notes documented
- April 2, 2026: renamed from "local prototype" to "local workbench"
- April 2, 2026: age adjustment factors implemented in canonical notebooks, DuckDB, and the workbench
- The rename clarified purpose: serious internal analysis surface, not a throwaway demo

**Talk track**
Four changes matter. First, the baseline was added in code. Second, the quickstart and assumptions were documented. Third, the language was tightened from "prototype" to "workbench," which better reflects how the tool should be used. Fourth, the social-adjustment path was implemented in canonical notebooks and surfaced in DuckDB and the workbench instead of living in a detached notebook copy.

## Slide 5 — What Problem the Workbench Solves

**On-slide text**
- Reduces friction for new contributors
- Turns scattered CSV/Parquet outputs into one browsable local interface
- Supports internal QA, explainability, and review
- Preserves notebook-first architecture instead of replacing it

**Talk track**
Before this workbench, the team had to open multiple outputs manually and mentally stitch them together. The workbench solves that by loading current curated outputs into a small analytical store and presenting them through one local app. It improves speed, consistency, and comprehension without forcing a migration away from notebooks.

## Slide 6 — Architecture in One Line

**On-slide text**
- Curated notebook outputs -> DuckDB baseline build -> reusable views -> Streamlit GUI
- Shared factor/config logic -> staged outputs -> DuckDB views -> inspectable workbench tables
- Public GitHub Pages dashboard remains unchanged
- Local/internal workbench is additive, not a replacement

**Talk track**
The architecture is deliberately simple. The workbench does not pull raw feeds directly. It rebuilds from the most stable curated outputs already produced by the notebooks. Those outputs are loaded into DuckDB tables, shaped into views, and then rendered through Streamlit. Shared factor logic now also lives in background Python modules so notebook math and workbench math stay aligned.

## Slide 7 — Why `run.sh` Matters

**On-slide text**
- One-command startup: `./run.sh up`
- Guided menu: `./run.sh`
- Built-in status, install, test, build, query, optimize, start, stop, logs
- Handles local `.venv`, smoke tests, baseline build, and clean app launch

**Talk track**
`run.sh` is the operational bridge between the repo and the workbench. It is not just a launcher. It creates or reuses the local virtual environment, checks dependencies, runs pytest smoke tests, rebuilds the DuckDB baseline, starts the Streamlit app, and can stop it cleanly. That makes the workbench usable by more than the person who originally built it.

## Slide 8 — What the Workbench Shows Today

**On-slide text**
- Municipio summary table
- Top-municipio priority chart
- Municipio map preview
- Station snapshot
- Alert snapshot
- Baseline source status
- Adjustment factor reference and age-overlay review

**Talk track**
The current workbench is intentionally focused. It centers on the municipio risk summary, then adds operational side views for stations, alerts, data readiness, and adjustment-factor review. This makes it useful for both storytelling and QA. It is already joining recommended actions and terrain completeness into the municipio view, which is important because it begins to show how multiple workstreams meet in one interface.

## Slide 9 — Core Interaction Capabilities

**On-slide text**
- Filter by phase
- Filter by priority band
- Search by municipio
- See mean adjusted priority and top municipio in current view
- Inspect age-adjustment factors against scored municipio rows
- Quit the local app cleanly from the sidebar

**Talk track**
This is a functional workbench, not just a static page. Users can filter by operational phase and priority band, search for a municipio, review metric cards, inspect the ranked table and chart together, and cross-check the current age overlay through the factor tables. The clean quit path also matters because the workbench is local and should release the DuckDB connection and port cleanly.

## Slide 10 — Data the Workbench Already Fuses

**On-slide text**
- Scored municipio indices
- Ranked priority actions
- Flood station latest features
- Enriched NWS alerts
- Terrain feature outputs
- NOAA station summary
- Optional social-adjustment outputs

**Talk track**
The workbench is valuable because it is not only showing one file. It is combining the municipio scoring outputs, action recommendations, station hazard outputs, alert summaries, terrain features, NOAA station summaries, and optional social-adjustment outputs into a joined local analytical surface. That is the beginning of a real decision-support workbench.

## Slide 11 — Demo Play-by-Play

**On-slide text**
- Start with `./run.sh up`
- Show the browser launch and local app title
- Filter the municipio list by phase and band
- Open one municipio story from score to actions
- Cross-check with stations, alerts, and source status

**Talk track**
For the demo, start by showing that the app is simple to launch. Then move into one filtered municipio example. Explain the adjusted priority score, show recommended actions, point out terrain completeness if present, and then validate the picture through station and alert snapshots. End by showing source status to reinforce that this GUI is also a QA surface.

## Slide 12 — What the Workbench Is Not

**On-slide text**
- Not the public dashboard replacement
- Not a production deployment target
- Not a full database migration of the repo
- Not a substitute for notebooks or peer review

**Talk track**
This slide is important because it prevents misinterpretation. The workbench is local/internal. The GitHub Pages dashboard remains the public-facing surface. The notebooks remain the primary analytics engine. The workbench is there to accelerate local analysis, validation, handoff, and future integration.

## Slide 13 — Why This Direction Is Good Engineering

**On-slide text**
- Low-cost and low-friction
- Rebuilds from current stable outputs
- Easier onboarding for future semesters
- Encourages reproducible local analysis
- Scales later without forcing premature cloud complexity

**Talk track**
The engineering value is that this solution meets the project where it is. It improves usability now, does not overcommit the team to a cloud architecture, and still leaves the door open for future scaling. That is a better capstone decision than trying to jump too early into a heavier production stack.

## Slide 14 — Direction of the Workbench

**On-slide text**
- Expand more curated notebook outputs into DuckDB
- Add stronger map layers beyond centroid preview
- Bring in more vulnerability and terrain drivers
- Make config-driven scoring easier to inspect in the GUI
- Expand the factor framework beyond age into other social overlays where justified
- Keep public and local surfaces clearly separated

**Talk track**
The next direction should be disciplined expansion. The team should promote additional curated outputs, improve map fidelity, expose more scoring drivers, and eventually reflect configuration-driven scoring more directly in the workbench. The new age overlay shows the correct pattern: shared config, shared Python, staged outputs, and workbench visibility. But the separation of concerns should remain clear: local workbench for internal analysis, public dashboard for outward communication.

## Slide 15 — Closing Message

**On-slide text**
- The workbench was added for a practical reason
- It complements the notebook pipeline and current dashboard
- It already improves usability, QA, and demo readiness
- It is the right local-first bridge toward a more integrated future stack

**Talk track**
The main message to leave with the audience is that the workbench is not cosmetic. It is a practical local analysis layer that improves accessibility to the current analytics, aligns with stakeholder guidance, and creates a cleaner path for future contributors.

## Appendix — Source Anchors for Presenter

- Meeting rationale: `docs/meetings/MOM (Mar 19).docx`
- Workbench assumptions: `docs/planning/duckdb_streamlit_baseline_notes.md`
- Local runner: `run.sh`
- Streamlit workbench: `app/streamlit_app.py`
- DuckDB loader/views: `scripts/build_duckdb_baseline.py`
- Shared factor logic: `scripts/factors/social_adjustments.py`
- Sample queries: `sql/duckdb_baseline_queries.sql`
- Smoke tests: `tests/test_local_prototype_baseline.py`, `tests/test_social_adjustments.py`
- Public/local positioning and quickstart: `README.md`

## Presenter Shortcut

If time is short, use this 5-slide compressed path:

1. Slides 2-4 for why it was added and what changed
2. Slides 6-8 for architecture and capabilities
3. Slide 11 for demo play-by-play
4. Slide 12 for scope guardrails
5. Slide 14 for next direction
