# 🛡️ PreMortem AI

### Predicting Public Procurement Failures Before They Happen

> *"Don't analyze failures after they happen. Predict them before approval."*

PreMortem AI is a full-stack **Agentic AI** platform that predicts procurement
and project failures **before approval** by simulating a structured AI
PreMortem review. Multiple specialist agents analyse the contract,
infrastructure readiness, workforce readiness, financial exposure and
historical outcomes, debate their findings, and a Decision Board Agent issues a
**GO / GO WITH CONDITIONS / NO-GO** recommendation.

The flagship demo recreates the **AIIMS MRI procurement failure** — where ₹72 Cr
of equipment sat unused because infrastructure, installation planning, operators
and warranty timing were never aligned — and shows that AI could have flagged a
**NO-GO before public funds were committed**.

---

## Architecture

```
Streamlit UI  ──HTTP──►  FastAPI backend  ──►  Agent Orchestrator (parallel)
 (Python)                                         ├─ Contract Risk Agent
                                                  ├─ Infrastructure Readiness Agent
                                                  ├─ Workforce Readiness Agent
                                                  ├─ Financial Exposure Agent
                                                  ├─ Historical Intelligence Agent  ──► ChromaDB
                                                  ├─ Scenario Simulation Agent
                                                  └─ Decision Board Agent (consolidator)
```

| Layer       | Technology |
|-------------|------------|
| Frontend    | **Streamlit** (Python UI), Plotly |
| Backend     | **FastAPI** |
| Agents      | **OpenAI Agents SDK / GPT-5.5** (with deterministic offline fallback) |
| Workflow    | Parallel orchestration (LangGraph-compatible) |
| Vector DB   | **ChromaDB** + OpenAI embeddings |
| Documents   | **PyPDF**, python-docx |
| Reports     | **ReportLab** (PDF), python-docx (Word), JSON |
| Database    | **PostgreSQL** (via docker-compose) |
| Deployment  | **Docker + Docker Compose** |

> 💡 **No API key? No problem.** Every agent has a rule-based engine, so the
> full demo runs offline and deterministically. Add `OPENAI_API_KEY` to switch
> to LLM-authored agentic reasoning automatically.

---

## Screens

1. **Procurement Input** — enter data or upload a document (auto-fills fields).
2. **Agent Investigation Board** — live agent cards with status, risk score, evidence, reasoning.
3. **Agent Debate Room** — simulated multi-agent debate + consensus.
4. **Executive Dashboard** — risk gauge, heatmap, radar, agent contributions, scenario timeline.
5. **PreMortem Report** — executive report with PDF / Word / JSON export.
6. **★ Bonus Lab** — Digital Twin What-If simulator & failure-loss sensitivity curve.

---

## Quick Start

### Option A — Docker (recommended)

```bash
cd premortem-ai
cp .env.example .env          # optionally add OPENAI_API_KEY
docker compose up --build
```

- UI:      http://localhost:8501
- API docs: http://localhost:8000/docs

### Option B — Local (two terminals)

**Backend**
```bash
cd premortem-ai/backend
python -m venv .venv && . .venv/Scripts/activate   # Windows
# source .venv/bin/activate                         # macOS/Linux
pip install -r requirements.txt
export OKF_MEMORY_ROOT="$PWD/agent_profiles/contract_agent_profile"  # macOS/Linux
# set OKF_MEMORY_ROOT=%CD%\agent_profiles\contract_agent_profile   # Windows cmd
uvicorn app.main:app --reload --port 8000
```

Backend HTTP API:

- Base URL: http://localhost:8000
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

**Frontend**
```bash
cd premortem-ai/frontend
pip install -r requirements.txt
streamlit run app.py
```

The backend and frontend load `../.env` automatically for local runs. Values
already exported in your shell or provided by Docker still take precedence.
`OKF_MEMORY_ROOT` enables the contract agent's durable memory bundle during
backend runs. If it is omitted, the app still runs with the normal offline/LLM
fallback behavior.

Open http://localhost:8501, click **Load AIIMS MRI demo**, then **Run PreMortem**.

---

## Demo: Expected Output (AIIMS MRI)

| Metric | Value |
|--------|-------|
| Overall Risk Score | ~88/100 |
| Failure Probability | ~91% |
| Predicted Failure Mode | Equipment delivered before site readiness |
| Recommended Decision | **NO-GO** |

**Conditions for approval:** facility readiness ≥95%, approvals completed,
technicians hired, warranty revised to commissioning date.

---

## API

| Method | Path | Description |
|--------|------|-------------|
| GET  | `/health` | Service status + mode (agentic/offline) |
| GET  | `/sample` | AIIMS MRI demo input |
| POST | `/analyze` | Run full PreMortem, returns report JSON |
| POST | `/upload` | Parse uploaded PDF/DOCX/TXT |
| POST | `/report/{pdf\|docx\|json}` | Export the report |

---

## References

- [OKF SPEC.md](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)

---

## Project Layout

```
premortem-ai/
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI endpoints
│   │   ├── models.py           # Pydantic schemas
│   │   ├── agents/             # 7 specialist agents + orchestrator
│   │   └── services/           # llm, historical_data, debate, document_parser, report
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app.py                  # Streamlit 6-screen UI
│   ├── charts.py               # Plotly visualizations
│   ├── api_client.py
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```
