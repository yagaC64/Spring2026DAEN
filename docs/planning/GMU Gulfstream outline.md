1) What / So what / Why / How / Who
What
A Spring 2026 DAEN capstone delivering an Integrated Decision-Support + UX/UI prototype for community flood early warning, centered on:
    • Data-as-a-Service (clean, documented, reusable data access layer)
    • Risk/readiness + response decision-support (indices, prioritization, overlays)
    • A mobile-friendly web dashboard (not native iOS/Android)
So what
    • Converts scattered public sensor feeds + GIS layers into actionable, defensible decision cues for communities and partners.
    • Produces a reusable pipeline + catalog + playbook that can be extended semester-over-semester.
    • Creates credible output for stakeholders (Gulfstream/C-RASC/USACE/STAR-TIDES) without requiring hardware work by students.
Why now
    • Capstone timeline is short (12 build weeks); scope must be locked early.
    • You’re at a crossroads: multiple prior efforts exist, but the “glue” (integration + continuity) is the missing piece.
    • PR deployments + USACE interest means you want an MVP that can be shown, not just talked about.
How
    • Agile scrum sprints with weekly partner meeting.
    • Start with data inventory + requirements, then pipeline + baseline dashboards, then indices + prioritization, then packaging + demo.
    • Keep the deliverable open-source friendly (Apache 2.0) and built on public data.
Who
    • Instructor/PM authority: Isaac (capstone delivery owner)
    • Partners/SMEs: Gilberto (domain + stakeholder + continuity), Melvin (mission + community + deployment narrative), Willie (data engineering + platform integration + technical guardrails)
    • Students (Team): execution of pipeline, analytics, UI, documentation
    • Optional external influence: Linton/STAR-TIDES & USACE demos (only if it doesn’t pull scope)

2) The meeting outcome you want in 30 minutes
By the end, you want these locked:
    1. Recurring meeting cadence: Thu 11:00 ET confirmed + who must attend
    2. Scope statement: “data-as-a-service + decision-support dashboard (mobile-friendly web), no native mobile app, no hardware build”
    3. Workstreams: either 1 team with 2 subteams or 2 teams with clean separation
    4. Data access plan: where the datasets live + how students access them + continuity plan
    5. Week-1 deliverables: what the team produces before next partner meeting
If you lock those, you win.

3) Topics to discuss (ordered, with “what to say”)
A) Confirm scope boundaries (do this early)
Say:
    • “We want a mobile-friendly dashboard experience, not native app development.”
    • “Hardware is out of capstone scope; students work on public data feeds + any sensor outputs we provide.”
B) Define the MVP deliverables in plain language
MVP =
    • A working data pipeline (ETL/ELT) that pulls/normalizes selected feeds
    • A data catalog + schema + provenance notes
    • A decision-support dashboard showing risk/readiness and response overlays
    • A minimal risk prioritization index (transparent + explainable)
C) Decide: 1 team vs 2 teams
Offer Isaac an easy choice:
Option 1: One team, two subteams (recommended default)
    • Subteam A: Data pipeline + validation + catalog
    • Subteam B: UX/UI dashboard + decision cues + “playbook views”
Option 2: Two full teams (only if they truly need to place 12 students)
    • Team 1: Risk/readiness indicators + prioritization (indices + reliability)
    • Team 2: Response planning overlays (routes, comms, logistics layers + UI)
Key guardrail to say:
    • “We’ll make artifacts non-overlapping so nobody becomes a passenger.”
D) Data inventory + continuity plan (your leadership moment)
This is where you can look the most “program-manager sharp.”
Say:
    • “We’ll provide a structured dataset pack + source list, and we’ll define a storage location so future semesters don’t lose data.”
    • “We’ll treat prior GitHub repos as the baseline, but we won’t assume prior datasets exist unless found.”
Propose a simple continuity plan:
    • Create a “Capstone Data Pack” (versioned zip or bucket) containing:
        ◦ curated extracts (small/medium size)
        ◦ scripts to refresh from authoritative sources
        ◦ README + schema + data dictionary
E) Define “success” in Week 12
Ask Isaac to agree to 3 acceptance criteria:
    1. “Data refresh is repeatable” (one-click runbook)
    2. “Dashboard tells a story” (risk + response cues; not just maps)
    3. “Documentation is handoff-ready” (future teams can pick up)

4) Proposed top-level project plan (12 build weeks)
Here’s a clean sprint sequence that matches DAEN reality.
Sprint 0 (Week 1): Alignment + inventory
Deliverables
    • MVP scope + user stories
    • Data inventory + access credentials/links
    • Repo setup + issue board
    • Architecture sketch (pipeline → store → service → dashboard)
Dependencies
    • You provide: list of authoritative sources + any existing links/repos + sample datasets
Sprint 1 (Weeks 2–3): Data foundation
Deliverables
    • ETL skeleton (pull + normalize + store)
    • Basic QA checks (missing data, outliers, gaps)
    • Data catalog v1 (fields, units, cadence)
Sprint 2 (Weeks 4–5): Map + baseline dashboard
Deliverables
    • Baseline dashboard: layers + filters + time-series widgets
    • “Known-good” minimal story: a few counties/areas as reference
Sprint 3 (Weeks 6–7): Indicators and prioritization
Deliverables
    • Risk/readiness index v1 (explainable, not deep learning)
    • Reliability flags (sensor gaps, inconsistent readings)
    • Prioritization logic (vulnerability + single-point-of-failure infra ideas)
Sprint 4 (Weeks 8–9): Response decision support
Deliverables
    • Response overlays: evacuation constraints, comms lines, “where help goes first”
    • Scenario views: “heavy rainfall event” / “river rise” simple cases
Sprint 5 (Weeks 10–12): Packaging + demo readiness
Deliverables
    • Final report + slides + recorded demo
    • Runbook (“how to refresh data, rerun pipeline”)
    • Public GitHub repo polish (Apache 2.0 compatible)

5) Proposed deliverables list (executive-friendly)
Use these as your “contract” bullets.
    1. Project charter (scope, users, success metrics)
    2. Data Source Register (authoritative sources + refresh cadence)
    3. Data Catalog / Dictionary
    4. ETL Pipeline + QA checks
    5. Decision-Support Dashboard (mobile-friendly web)
    6. Risk/Readiness Index v1 (transparent, explainable)
    7. Response Support Views (routes/comms/logistics overlays)
    8. Runbook + Handoff Guide
    9. Final presentation + poster-ready visuals

6) Your “leadership navigation” cheat sheet
Things to say that signal confidence
    • “Let’s lock MVP boundaries now so the team can sprint.”
    • “We’ll keep it explainable—no deep learning required.”
    • “Our priority is repeatability and handoff so future semesters build forward.”
Things to avoid (scope grenades)
    • “Native mobile app”
    • “We’ll do tensors / deep learning”
    • “We need custom hardware in the loop”
    • “We’ll integrate everything everywhere”
Questions to ask Isaac that make you look like the grown-up
    1. “Do you prefer one team with subteams or two teams with separate repos?”
    2. “Where should the data live for continuity (OpenStack/on-prem/HPC storage)?”
    3. “What format do you want for weekly updates—demo-first or slide-first?”
    4. “Any constraints on GIS tooling (ArcGIS vs open stack) for students?”

7) Micro-agenda for today’s 30-minute kickoff (tight)
    1. 2 min – intros + confirm recurring meeting schedule
    2. 5 min – MVP scope + boundaries (no native app, no hardware)
    3. 8 min – workstreams + proposed sprint plan
    4. 10 min – data access + continuity storage decision
    5. 5 min – Week-1 tasks + next meeting agenda

8) Your Week-1 ask to the student team (simple and powerful)
Assign them “Day 1 wins”:
    • Create repo + backlog issues (10–15)
    • Create data source register (top 6–10 sources)
    • Build “hello world ETL” that pulls one source and stores normalized output
    • Draft dashboard wireframe (even boxes-on-a-slide is fine)
