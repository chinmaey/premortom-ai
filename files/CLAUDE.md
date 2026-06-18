# CLAUDE.md — PreMortem AI (project context for Claude Code)

You are continuing work on **PreMortem AI**, a hackathon project. Read this
file fully before acting. The human is new to agentic AI frameworks, is on a
tight deadline (~48h), and uses the Anthropic (Claude) API — NOT OpenAI.
Prefer small, reviewable diffs. Keep the offline rule-based fallback intact at
every step (it's the "runs with no API key" demo safety net).

## What the product is
A pre-decision auditor for procurement. A user submits a proposal/contract
BEFORE approval; several specialist agents each investigate a risk dimension,
they debate, and a Decision Board issues GO / GO-WITH-CONDITIONS / NO-GO with
evidence and a projected financial loss.

## Architecture (already built)
- `backend/` FastAPI. Entry: `app/main.py`. Schemas: `app/models.py`.
- `app/agents/`: contract, infrastructure, workforce, financial, historical,
  scenario, decision_board, plus `orchestrator.py` (runs the 5 specialists,
  then scenario, then board).
- `app/services/`: `llm.py` (LLM wrapper), `historical_data.py` (KB +
  retrieval), `document_parser.py`, `report.py` (PDF/Word/JSON), `debate.py`.
- `frontend/` Streamlit 6-screen UI (`app.py`, `charts.py`, `api_client.py`).

## Honest diagnosis (the two real problems)
1. **It is not actually agentic yet.** The "agents" are deterministic
   if/else scoring functions. The LLM, if present, only runs AFTER the rule
   engine and overwrites the JSON with prose — delete it and behavior is
   identical. There is NO tool use, NO reasoning loop, NO external data. The
   pitch promises "live vendor intelligence, market data, litigation signals"
   — none of that exists in code.
2. **It only handles one scenario.** `ProcurementInput` is hardcoded to
   medical-equipment + site-readiness (warranty_start, construction_pct,
   electrical_readiness, technicians_*). Defaults ARE the AIIMS MRI case. The
   historical KB is 6 hardcoded medical projects. Any input pattern-matches
   back to "equipment delivered before site ready," so every run feels the
   same.

The fix for both is the same: shift from "fixed form → fixed scores" toward
"document + context → Claude reasoning with real tools."

## Model + cost conventions
- Claude API only. `ANTHROPIC_API_KEY` in `.env`. It's pay-as-you-go and
  separate from the human's Claude Pro chat subscription.
- Default per-agent model: `claude-haiku-4-5-20251001` (cheap, runs 5x/analysis).
- Use `claude-sonnet-4-6` ONLY for the Decision Board synthesis + debate.
- Set the model via the `CLAUDE_MODEL` env var; don't hardcode per file.
- Always degrade gracefully to the rule-based path on any API/tool failure.

## Task list (do in order, smallest diffs first)

### Task A — Swap LLM wrapper to Claude  [STATUS: DONE if llm.py uses `anthropic`]
- `backend/app/services/llm.py` should import `anthropic`, expose the same
  `has_api_key()` and `run_agent_llm(name, instructions, user_payload,
  temperature)` interface, key off `ANTHROPIC_API_KEY`, and prefill the
  assistant turn with "{" for reliable JSON.
- `backend/requirements.txt`: remove `openai*` lines, add `anthropic>=0.40.0`.
- Verify with: `python -c "from app.services.llm import run_agent_llm;
  print(run_agent_llm(name='t', instructions='You are a test.',
  user_payload='Return JSON with key ok set to true.'))"`

### Task B — Give the historical/vendor agent REAL tool use  [DO THIS NEXT]
Goal: make one agent genuinely agentic and deliver the pitch's differentiator.
- Add Claude tool use (the `tools=[...]` param on `client.messages.create`,
  with a `web_search` tool, plus a tool-result loop) so the agent can look up
  the vendor name + "debarment / litigation / blacklist" and the equipment +
  "price benchmark."
- Real, queryable signals worth wiring in: SAM.gov exclusions (US debarred
  vendors), World Bank debarred-firms list.
- Fold findings into the existing `AgentResult` (findings/evidence/reasoning).
- MUST fall back to today's keyword/rule behavior if the tool call fails.

### Task C — Generalize the input so it's not MRI-only
- Keep the structured `ProcurementInput` fields OPTIONAL.
- Add a path: when `raw_document_text` is present, an extraction agent uses
  Claude to pull the risk variables from free text, so a non-medical contract
  (e.g. an IT/software or construction deal) works end-to-end.
- `document_parser.py` already extracts text; route it through the new agent.

### Task D — Make scoring reasoning-driven for ≥2 agents
- For the contract + financial agents, let Claude judge severity, using the
  current rule score as a prior/sanity bound (clamp to plausible range).
- Keep the pure rule engine as the offline fallback.

## Data sources (for the historical KB + validation)
- Real failures: CAG of India audit reports; CPP Portal (eprocure.gov.in); GeM;
  World Bank procurement datasets.
- Vendor risk: SAM.gov exclusions; World Bank debarred firms.
- Validation: generate ~10 varied synthetic procurement packages (one clear
  NO-GO, one clean GO, one GO-WITH-CONDITIONS, plus non-medical cases) to prove
  it isn't single-use.

## Definition of done for the demo
Running a software-vendor contract (not just the MRI sample) produces a
sensible, DIFFERENT report, with at least one finding that came from a live
tool lookup. That single beat answers both "must leverage agentic AI" and
"it's not just ChatGPT."
