# Quorum (Expert Council) 🏛️⚡

> **An AI platform where anyone submits an idea and receives a brutally honest, multi-expert evaluation drawn from the published principles, warnings, and heuristics of 700+ real industry leaders.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![Google Gemini Flash](https://img.shields.io/badge/AI%20Engine-Gemini%202.5%20Flash-4285F4.svg)](https://aistudio.google.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🌟 Vision & Overview

Millions of founders and students have ideas but lack direct access to world-class domain practitioners. Traditional feedback is either politely unhelpful (friends and family) or prohibitively expensive (consultants and selective incubators).

**Quorum** solves this by assembling a virtual council of iconic operators, founders, and investors (e.g., *Paul Graham, Michael Seibel, Jensen Huang, Dalton Caldwell, Tobi Lütke, Melanie Perkins, Sam Altman*):
- **Grounded Wisdom:** Digital brains are constructed strictly from verifiable public talks, books, essays, shareholder letters, and interviews.
- **Zero Sugar-Coating:** Personas are instructed to uncover hidden risks, flawed unit economics, and weak wedges before praising potential.
- **8-Pillar Weighted Scoring:** Market Demand, Differentiation, Feasibility, Financial Viability, Execution Risk, Legal Safety, Market Timing, and Defensibility.
- **Cinematic 3D Network Graph:** Exports spherical/orbital 3D coordinates `(x, y, z)` and tension telemetry for sci-fi network visualizers (Three.js / WebGL / Google Stitch).

---

## 🚀 Key Features

1. **Free for All (High Token Allowance)**:
   - Uses **Google Gemini 2.5 / 2.0 Flash** via the free API tier. Enjoy high RPM/TPM and a 1M+ token context window without spending a dollar.
   - Built-in graceful offline simulation mode allows running tests or local evaluations even without an API key.

2. **Digital Document Ingestion**:
   - Ingests pitches via raw text, PDF pitch decks, and Word (`.docx`) business plans.
   - Speech-to-text dependencies have been eliminated for a lightweight, instant installation footprint.

3. **700+ Curated Experts across 19+ Sectors**:
   - Spanning *Technology & Software, AI/ML, Telecom, Deep Tech & Space, Manufacturing, E-commerce, Fintech, FMCG, Fashion & Beauty, Healthcare, Agritech*, and more.
   - Pre-compiled in-memory index (`src/quorum/data/expert_catalog.json`) loads in under 30ms.

4. **Deliberation Theater (Server-Sent Events)**:
   - Real-time streaming endpoints deliver live telemetry as experts deliberate in parallel.

5. **3D Cinematic Visualizer Ready**:
   - Evaluated reports include a `network_graph` payload with node coordinates `(x, y, z)`, animation pulses, and edge tension indices ready for Google Stitch or WebGL renderers.

6. **1-on-1 Interactive Follow-Up**:
   - Founders can cross-examine any individual expert with follow-up questions directly grounded in their documented heuristics.

---

## 🛠️ Quickstart (1 Minute Setup)

### 1. Clone & Set Up Environment
```bash
git clone https://github.com/your-username/quorum.git
cd quorum

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux / macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Your API Key
Copy the template `.env.example` to `.env`:
```bash
cp .env.example .env
```
Open `.env` and paste your free Google Gemini API key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```
*(Get your free API key at [Google AI Studio](https://aistudio.google.com/))*

### 3. Start the Backend Server
```bash
python -m uvicorn quorum.api.main:app --reload --port 8000
```
Visit the interactive Swagger API documentation at:  
👉 **http://localhost:8000/docs**

---

## 🧪 Run Automated Tests

Quorum comes with an end-to-end test suite verifying ingestion, routing, Gemini evaluation, 3D graph synthesis, and API routes:

```bash
pytest tests/ -v
```

---

## 📡 API Reference (Ready for Google Stitch)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check & count of active expert profiles |
| `GET` | `/api/sectors` | Lists all 19 sectors and expert counts |
| `GET` | `/api/experts` | Search and filter 700+ expert profiles |
| `POST` | `/api/ideas/analyze` | Normalizes text pitch into a structured `IdeaBrief` |
| `POST` | `/api/ideas/upload-and-analyze` | Uploads PDF/DOCX files and creates an `IdeaBrief` |
| `POST` | `/api/council/recommend-panel` | Returns curated panel of domain and functional experts |
| `POST` | `/api/council/evaluate` | Synchronous evaluation generating full `CouncilReport` |
| `POST` | `/api/council/evaluate/stream` | Server-Sent Events (SSE) stream for live deliberation UI |
| `POST` | `/api/council/expert-chat` | Interactive 1-on-1 Q&A with any expert persona |

### Sample Evaluation Response (`CouncilReport`)
```json
{
  "id": "rep_a1b2c3d4",
  "title": "QuikD2C AI",
  "overall_score": 7.1,
  "verdict_label": "Promising",
  "consensus_percentage": 84.5,
  "pillar_scores": {
    "market_demand": 7.4,
    "differentiation": 5.8,
    "feasibility": 8.0,
    "financial_viability": 6.2,
    "execution_risk": 6.0,
    "regulatory_legal_risk": 8.5,
    "market_timing": 7.2,
    "defensibility_scale": 5.2
  },
  "top_warnings": [
    {
      "warning": "High customer acquisition cost in this market",
      "severity": "Critical",
      "experts_count": 5,
      "flagged_by": ["Paul Graham", "Michael Seibel", "Dalton Caldwell"]
    }
  ],
  "kill_questions": [
    {
      "question": "Who wants this so urgently that they would use a broken prototype?",
      "raised_by": "Paul Graham",
      "rationale": "Highlighted by Paul Graham as a decisive make-or-break hurdle."
    }
  ],
  "network_graph": {
    "nodes": [
      {
        "id": "core_idea",
        "label": "QuikD2C AI",
        "category": "idea",
        "radius": 24.0,
        "coords": { "x": 0.0, "y": 0.0, "z": 0.0 }
      }
    ],
    "edges": [...]
  }
}
```

---

## 🎨 Google Stitch Frontend Architecture

When creating your UI in **Google Stitch**:
1. **Screen 1 (Submission):** Form with text pitch and file uploader bound to `POST /api/ideas/analyze` or `/api/ideas/upload-and-analyze`.
2. **Screen 2 (Panel Curation):** Grid of cards bound to `POST /api/council/recommend-panel`.
3. **Screen 3 (Deliberation Theater):** Connects to `POST /api/council/evaluate/stream` to animate live progress.
4. **Screen 4 (Executive Dashboard):** Renders the 8 pillar scorecards, kill questions, top warnings, and the **3D Force/Orbital Graph** using the `coords` in `network_graph`.
5. **Screen 5 (Expert Dossier & Chat):** Click any expert card to open their drawer and chat via `POST /api/council/expert-chat`.

---

## 📄 License
MIT License. Built for founders, students, and operators worldwide.
