# QUORUM — Autonomous War Room // Roadmap Progress

> AI Startup Expert Council & Pressure-Test Engine
> Last Updated: 2026-10-11

---

## PHASE 1 — Backend Engine (COMPLETE)

| Component | Status | Notes |
|-----------|--------|-------|
| Expert Catalog Ingestion | DONE | 520+ mentors from EXPERT LIST.xlsx |
| Advice Library Ingestion | DONE | Batch 1 docx parsed to JSON |
| Expert Store | DONE | ExpertStore singleton, search, sector filter |
| Council Router | DONE | Sector detection, panel recommendation (15 experts) |
| Council Evaluator | DONE | 8-pillar scoring, critiques, roadmap, kill questions |
| Gemini Brain Adapter | DONE | Persona generation, follow-up chat |
| 3D Network Graph | DONE | Nodes + edges with 3D coords (Three.js-ready) |
| SSE Streaming Endpoint | DONE | /api/council/evaluate/stream |
| Document Parser | DONE | PDF, DOCX, TXT pitch deck support |
| FastAPI App | DONE | CORS, lifespan, static serving |

---

## PHASE 2 — UI Integration (COMPLETE)

| Screen | Route | Status | Notes |
|--------|-------|--------|-------|
| Idea Portal (SPA) | / | DONE | 4-stage SPA wired to backend |
| Brief Curation | /curation | DONE | Convene CTA wired, localStorage handoff |
| War Room Console | /war-room | DONE | Advance CTA wired, panel fetch |
| Council Theater | /theater | DONE | SSE stream + sync fallback |
| Council Report | /report | DONE | Auto-populates all metrics, chat, export |

### Data Flow: localStorage keys passed between pages
- quorum_brief — IdeaBrief from /api/ideas/analyze
- quorum_panel — ExpertProfile[] from /api/council/recommend-panel
- quorum_report — CouncilReport from /api/council/evaluate

---

## PHASE 3 — Test Suite (COMPLETE) — 5/5 PASSED

- test_store_and_catalog: PASSED
- test_router_and_brief_generation: PASSED
- test_council_evaluation_and_3d_network_graph: PASSED
- test_api_endpoints: PASSED (all routes 200 OK)
- test_ui_backend_wiring: PASSED (all 5 HTML wiring verified)

Run time: 27.51s

---

## How to Run

  Set PYTHONPATH=src
  python -m uvicorn quorum.api.main:app --host 127.0.0.1 --port 8000 --reload

  App URL: http://127.0.0.1:8000

---

## Next Phase Options

| Feature | Priority |
|---------|----------|
| Migrate to google.genai SDK (fix FutureWarning) | High |
| YouTube transcript harvesting pipeline | Medium |
| Additional expert batch distillation | Medium |
| PDF export | Low |
| Persistent session storage | Low |
