# Backend Design

This document defines the backend API, storage layout, and service boundaries for the bid and quote workflow. The agentic architecture and agent responsibilities are described separately in `High_level_Agent_architecture_v3.md`.

## Goals

The backend should support a demo-safe workflow where the UI can:

1. Create a bid or request-for-quote container.
2. Upload vendor quote PDFs.
3. Scan generated quote folders created by the synthetic data script.
4. Start a bid evaluation run.
5. Poll run status for realtime-style UI updates.
6. Fetch the final recommendation, analysis outputs, telemetry, and report artifacts.

The first implementation should avoid a database and use CSV/JSON files for demo persistence.

## Process Boundaries

The application has two server processes:

```text
Browser
  -> Streamlit UI server
    -> FastAPI backend server
      -> input registry services
      -> orchestrator
      -> agents
      -> output store
```

Roles:

- Browser is the client of Streamlit.
- Streamlit is the client of FastAPI.
- FastAPI is the backend server and source of truth for bid inputs, run state, and outputs.
- FastAPI is also the client of LLM providers through the centralized LLM service.

The UI should not call agents directly. It should call FastAPI endpoints.

## Storage Layout

Inputs and outputs must remain separate.

### Input Storage

Inputs are stored under:

```text
files/input/samples/
```

Structure:

```text
files/input/samples/
  bids_database.csv
  metadata.json
  manifest.csv
  coverage.csv
  bids/
    BID-001/
      BID-001-Q01.pdf
      BID-001-Q02.pdf
    BID-002/
      BID-002-Q01.pdf
```

Purpose:

- Store uploaded and generated vendor quote PDFs.
- Track bid and quote metadata.
- Keep generated experiment metadata, manifest, coverage, and ground truth files.

PDFs should not be stored in CSV or in a database. The CSV stores metadata only.

### Output Storage

Agent outputs and decisions are stored under:

```text
files/output/
```

Recommended structure:

```text
files/output/
  bid_runs/
    runs_database.csv
    RUN-001/
      run_state.json
      events.jsonl
      contract_review_agent_quote_reviews.json
      bid_recommender_agent_decision_result.json
      telemetry.json
      report.json
      report.pdf
```

Outputs belong to a run, not only to a bid, because the same bid can be evaluated multiple times with different prompts, models, quote subsets, or agent logic.

## CSV Registries

### bids_database.csv

Path:

```text
files/input/samples/bids_database.csv
```

Purpose:

- Operational registry for bid and quote inputs.
- Includes both manually uploaded quotes and scanned generated quote PDFs.
- Used by FastAPI endpoints to list bids and quotes without requiring a database.

Suggested columns:

```text
bid_id
quote_id
vendor_name
equipment_type
procurement_name
source
status
pdf_path
original_filename
created_at
updated_at
```

Example rows:

```csv
bid_id,quote_id,vendor_name,equipment_type,procurement_name,source,status,pdf_path,original_filename,created_at,updated_at
BID-101,,,,MRI Machine,MRI Procurement,upload,created,,,,2026-06-27T10:00:00Z,2026-06-27T10:00:00Z
BID-101,BID-101-Q01,MedNova Healthcare,MRI Machine,MRI Procurement,upload,uploaded,bids/BID-101/BID-101-Q01.pdf,quote.pdf,2026-06-27T10:01:00Z,2026-06-27T10:01:00Z
```

`source` values:

- `upload`: created through the FastAPI upload endpoint.
- `scan`: discovered by scanning `files/input/samples/bids/`.
- `generated`: optionally used later for rows imported directly from generated metadata.

`status` values:

- `created`
- `uploaded`
- `discovered`
- `ready`
- `error`

### runs_database.csv

Path:

```text
files/output/bid_runs/runs_database.csv
```

Purpose:

- Operational registry for evaluation runs.
- Allows the UI to list previous runs and compare outputs.

Suggested columns:

```text
run_id
bid_id
status
quote_count
winner_quote_id
decision_result_path
started_at
completed_at
created_by
llm_provider
model
```

`status` values:

- `queued`
- `running`
- `completed`
- `failed`
- `cancelled`

## Backend Services

### Input Bid Registry Service

Suggested module:

```text
backend/app/services/input_bids.py
```

Responsibilities:

- Create bid IDs.
- Create bid folders.
- Save uploaded quote PDFs.
- Assign quote IDs.
- Maintain `bids_database.csv`.
- Scan `files/input/samples/bids/` for generated quote PDFs.
- List bids and quotes for API endpoints.

This is deterministic bookkeeping and should not be implemented as an AI agent.

### Bid Output Store Service

Suggested module:

```text
backend/app/services/bid_outputs.py
```

Responsibilities:

- Create run IDs.
- Create run output folders.
- Maintain `runs_database.csv`.
- Write `run_state.json`.
- Append `events.jsonl`.
- Write `contract_review_agent_quote_reviews.json`.
- Write `bid_recommender_agent_decision_result.json`.
- Write `telemetry.json`.
- Write final report artifacts.

This service provides durable output files that can be used for evaluation.

## Input APIs

### Create Bid

```text
POST /bids
```

Request:

```json
{
  "procurement_name": "MRI Procurement",
  "equipment_type": "MRI Machine"
}
```

Response:

```json
{
  "bid_id": "BID-101",
  "status": "created",
  "storage_path": "files/input/samples/bids/BID-101"
}
```

Behavior:

- Creates `files/input/samples/bids/{bid_id}/`.
- Adds a bid-level row to `bids_database.csv`.

### List Bids

```text
GET /bids
```

Response:

```json
{
  "bids": [
    {
      "bid_id": "BID-101",
      "procurement_name": "MRI Procurement",
      "equipment_type": "MRI Machine",
      "quote_count": 2,
      "status": "created"
    }
  ]
}
```

### Upload Quote PDF

```text
POST /bids/{bid_id}/quotes
```

Multipart fields:

```text
file = vendor_quote.pdf
vendor_name = MedNova Healthcare
```

Response:

```json
{
  "bid_id": "BID-101",
  "quote_id": "BID-101-Q01",
  "vendor_name": "MedNova Healthcare",
  "pdf_path": "bids/BID-101/BID-101-Q01.pdf",
  "status": "uploaded"
}
```

Behavior:

- Saves the PDF to `files/input/samples/bids/{bid_id}/{quote_id}.pdf`.
- Adds a quote-level row to `bids_database.csv`.
- Does not update `coverage.csv` immediately.

### List Quotes For Bid

```text
GET /bids/{bid_id}/quotes
```

Response:

```json
{
  "bid_id": "BID-101",
  "quotes": [
    {
      "quote_id": "BID-101-Q01",
      "vendor_name": "MedNova Healthcare",
      "pdf_path": "bids/BID-101/BID-101-Q01.pdf",
      "status": "uploaded"
    }
  ]
}
```

### Scan Input Folder

```text
POST /input/scan
```

Behavior:

- Scans `files/input/samples/bids/`.
- Finds `BID-*` folders.
- Finds `BID-*-Q*.pdf` files.
- Adds missing rows to `bids_database.csv`.

Response:

```json
{
  "bids_indexed": 100,
  "quotes_indexed": 2000,
  "new_bids": 0,
  "new_quotes": 20
}
```

## Evaluation APIs

### Start Bid Run

```text
POST /bid-runs
```

Request:

```json
{
  "bid_id": "BID-101",
  "quote_ids": ["BID-101-Q01", "BID-101-Q02"]
}
```

Response:

```json
{
  "run_id": "RUN-001",
  "bid_id": "BID-101",
  "status": "queued",
  "output_path": "files/output/bid_runs/RUN-001"
}
```

Behavior:

- Creates a run folder.
- Adds a row to `runs_database.csv`.
- Starts orchestrator execution in the background.
- Returns quickly so the UI can begin polling.

### Get Run State

```text
GET /bid-runs/{run_id}/state
```

Response:

```json
{
  "run_id": "RUN-001",
  "bid_id": "BID-101",
  "status": "running",
  "current_step": "contract_review",
  "quotes": [
    {
      "quote_id": "BID-101-Q01",
      "vendor_name": "MedNova Healthcare",
      "status": "completed",
      "risk_score": 68
    },
    {
      "quote_id": "BID-101-Q02",
      "vendor_name": "BudgetMed Systems",
      "status": "running",
      "risk_score": null
    }
  ],
  "agents": {
    "bid_recommender": {
      "status": "running",
      "message": "Comparing submitted quotes"
    },
    "contract_review": {
      "status": "running",
      "message": "Reviewing BID-101-Q02"
    }
  }
}
```

Behavior:

- Reads current run state from memory or `run_state.json`.
- Does not block on agent execution.

### Get Run Events

```text
GET /bid-runs/{run_id}/events?since=0
```

Response:

```json
{
  "run_id": "RUN-001",
  "events": [
    {
      "id": 1,
      "timestamp": "2026-06-27T10:00:00Z",
      "type": "run_started",
      "run_id": "RUN-001",
      "bid_id": "BID-101"
    }
  ],
  "next_since": 1
}
```

Events are read from:

```text
files/output/bid_runs/{run_id}/events.jsonl
```

This endpoint can power incremental polling and can later be reused for SSE or WebSocket.

### Get Final Result

```text
GET /bid-runs/{run_id}/result
```

Response:

```json
{
  "run_id": "RUN-001",
  "bid_id": "BID-101",
  "status": "completed",
  "winner": {
    "quote_id": "BID-101-Q01",
    "vendor_name": "MedNova Healthcare",
    "score": 84.2
  },
  "ranked_quotes": [],
  "feedback": [],
  "output_files": {
    "bid_recommender_agent": "files/output/bid_runs/RUN-001/bid_recommender_agent_decision_result.json",
    "contract_review_agent": "files/output/bid_runs/RUN-001/contract_review_agent_quote_reviews.json",
    "report": "files/output/bid_runs/RUN-001/report.json"
  }
}
```

### List Runs For Bid

```text
GET /bids/{bid_id}/runs
```

Response:

```json
{
  "bid_id": "BID-101",
  "runs": [
    {
      "run_id": "RUN-001",
      "status": "completed",
      "winner_quote_id": "BID-101-Q01",
      "completed_at": "2026-06-27T10:05:00Z"
    }
  ]
}
```

## Output Artifact Access For UI Screens

The UI should not read output files directly from the filesystem. Streamlit should access run artifacts through FastAPI endpoints so the storage location can change later without rewriting the UI.

Current primary endpoint:

```text
GET /bid-runs/{run_id}/result
```

This returns the final recommendation and includes `output_files` references for traceability.

Recommended future artifact endpoint:

```text
GET /bid-runs/{run_id}/artifacts/{artifact_name}
```

Supported artifact names should map to files as follows:

```text
state
  -> files/output/bid_runs/{run_id}/run_state.json

events
  -> files/output/bid_runs/{run_id}/events.jsonl

contract_review_agent
  -> files/output/bid_runs/{run_id}/contract_review_agent_quote_reviews.json

bid_recommender_agent
  -> files/output/bid_runs/{run_id}/bid_recommender_agent_decision_result.json

report
  -> files/output/bid_runs/{run_id}/report.json

telemetry
  -> files/output/bid_runs/{run_id}/telemetry.json
```

For the first implementation, the UI can use the existing state/result endpoints:

```text
GET /bid-runs/{run_id}/state
GET /bid-runs/{run_id}/events?since=N
GET /bid-runs/{run_id}/result
```

Later, add the artifact endpoint only if the UI needs to display raw agent outputs independently from the final result response.

### Screen 1: Procurement Input

Purpose:

- Create or select a bid.
- Upload or scan quote PDFs.
- Start a bid evaluation run.

Backend access:

```text
POST /bids
GET  /bids
POST /bids/{bid_id}/quotes
GET  /bids/{bid_id}/quotes
POST /input/scan
POST /bid-runs
```

Output files used:

```text
None directly.
```

This screen should use input registry APIs and then store `bid_id` and `run_id` in Streamlit session state.

### Screen 2: Agent Investigation Board

Purpose:

- Show per-agent findings.
- Show quote-by-quote contract review results.
- Show agent status and evidence.

Backend access:

```text
GET /bid-runs/{run_id}/state
GET /bid-runs/{run_id}/result
```

Primary output artifact:

```text
contract_review_agent_quote_reviews.json
```

Recommended UI mapping:

- Contract Review Agent cards should read from `contract_review_agent_quote_reviews.json`.
- Each quote review should show `quote_id`, `vendor_name`, `risk_score`, `risk_level`, findings, and recommendation.
- Agent status cards should read from `run_state.json` through `GET /bid-runs/{run_id}/state`.

### Screen 3: Agent Debate Room

Purpose:

- Show discussion, disagreements, and reasoning between agents.

Backend access:

```text
GET /bid-runs/{run_id}/result
GET /bid-runs/{run_id}/events?since=N
```

Current output artifact:

```text
bid_recommender_agent_decision_result.json
```

Future output artifacts:

```text
agent_debate.json
decision_board_agent_consensus.json
```

Recommended UI mapping:

- For the first bid workflow, show recommender feedback and ranking rationale from `bid_recommender_agent_decision_result.json`.
- When a dedicated debate/decision-board step is added, write it to separate agent-named files and expose them through the artifact endpoint.

### Screen 4: Executive Dashboard

Purpose:

- Show the bid-level winner, ranked quotes, risk distribution, status, and telemetry.

Backend access:

```text
GET /bid-runs/{run_id}/state
GET /bid-runs/{run_id}/result
```

Primary output artifact:

```text
bid_recommender_agent_decision_result.json
```

Supporting output artifacts:

```text
contract_review_agent_quote_reviews.json
telemetry.json
```

Recommended UI mapping:

- Winner and ranked quote table should read from `bid_recommender_agent_decision_result.json`.
- Quote risk charts should read from `ranked_quotes` and/or `contract_review_agent_quote_reviews.json`.
- Agent runtime, connection status, and graph state should read from `run_state.json` through `GET /bid-runs/{run_id}/state`.
- Token, model, latency, and cost metrics should read from `telemetry.json` when implemented.

### Screen 5: PreMortem Report

Purpose:

- Show the final human-readable decision package.
- Support JSON/PDF/DOCX exports.

Backend access:

```text
GET  /bid-runs/{run_id}/result
POST /report/{fmt}
```

Current primary output artifact:

```text
bid_recommender_agent_decision_result.json
```

Future report artifacts:

```text
report.json
report.pdf
report.docx
```

Recommended UI mapping:

- For the first bid workflow, build the report screen from the final result endpoint.
- When bid-level report generation is implemented, write `report.json`, `report.pdf`, and `report.docx` into the run folder and expose them through export endpoints.

### Bonus Lab: What-If / Digital Twin

Purpose:

- Re-run or simulate changed procurement conditions.
- Compare original result with modified assumptions.

Backend access:

```text
POST /bid-runs
GET  /bid-runs/{run_id}/state
GET  /bid-runs/{run_id}/result
GET  /bids/{bid_id}/runs
```

Primary output artifacts:

```text
bid_recommender_agent_decision_result.json
contract_review_agent_quote_reviews.json
```

Recommended UI mapping:

- Create a new run for each what-if scenario instead of overwriting the original run.
- Compare two `run_id` values side by side.
- Use `GET /bids/{bid_id}/runs` to list previous runs for the same bid.
- Later, add scenario-specific output files such as `scenario_simulation_agent_results.json`.

## UI Polling Model

For the first implementation, use REST polling instead of WebSocket.

Flow:

```text
1. Streamlit sends POST /bid-runs.
2. FastAPI returns run_id immediately.
3. Streamlit polls GET /bid-runs/{run_id}/state every 0.5-1 second.
4. FastAPI returns current run state.
5. Streamlit redraws graph, status, telemetry, and quote progress.
6. When status is completed, Streamlit calls GET /bid-runs/{run_id}/result.
```

REST polling is preferred for the demo because Streamlit is naturally request/rerun oriented and agent events are low frequency. The event model should still be designed so SSE or WebSocket can be added later.

## Event-Driven Updates Later

The current design should remain modular enough to switch from polling to event-driven updates later.

The important design rule is:

```text
Orchestrator writes state/events once.
API delivery method can change independently.
```

Internal backend flow:

```text
orchestrator
  -> updates run_state.json
  -> appends events.jsonl
  -> updates in-memory RunState if available
```

Current delivery:

```text
Streamlit polls GET /bid-runs/{run_id}/state
Streamlit optionally polls GET /bid-runs/{run_id}/events?since=N
```

Future delivery:

```text
SSE endpoint streams the same events from events.jsonl or in-memory event queue.
WebSocket endpoint streams the same events and optionally receives live commands.
```

Recommended later endpoint for one-way event delivery:

```text
GET /bid-runs/{run_id}/events/stream
```

Use SSE first if the UI only needs server-to-client updates such as:

- agent started
- agent completed
- quote review completed
- decision completed
- telemetry updated
- run failed
- run completed

Use WebSocket only if the UI later needs two-way live interaction during a run, such as:

- pause
- cancel
- resume
- approve a step
- add human feedback
- ask an agent a follow-up question

TODO:

- Add an SSE endpoint backed by the existing run event log.
- Add reconnect support using the last event ID.
- Keep `GET /state` as the reliable snapshot endpoint even after SSE is added.
- Add WebSocket only if human-in-the-loop commands become part of the demo.

## Coverage CSV

`coverage.csv` remains experiment coverage for generated/evaluation data.

For the demo:

- Uploading a quote updates `bids_database.csv`.
- Scanning generated folders updates `bids_database.csv`.
- `coverage.csv` does not need to update on every upload.

Later, add:

```text
POST /input/coverage/rebuild
```

to rebuild coverage from `metadata.json` plus registered quote inputs.

## Implementation Order

1. Create `backend/app/services/input_bids.py`.
2. Create `backend/app/services/bid_outputs.py`.
3. Add FastAPI input endpoints:
   - `POST /bids`
   - `GET /bids`
   - `POST /bids/{bid_id}/quotes`
   - `GET /bids/{bid_id}/quotes`
   - `POST /input/scan`
4. Add run output endpoints:
   - `POST /bid-runs`
   - `GET /bid-runs/{run_id}/state`
   - `GET /bid-runs/{run_id}/events`
   - `GET /bid-runs/{run_id}/result`
   - `GET /bids/{bid_id}/runs`
5. Update `frontend/api_client.py`.
6. Add Streamlit bid creation and quote upload screens.
7. Wire orchestrator and agents after input/output plumbing works.
