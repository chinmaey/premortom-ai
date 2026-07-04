# Contract Review Agent Profile

## Objective

Identify contract and commercial risks that could cause procurement failure after award.

## Skills

- Contract risk review
- Contract-submission quality review
- Warranty, payment, installation, training, and service-term analysis
- Follow-up question generation

## Memory And Retrieval Roadmap

### Stage 1 - File-Backed History, Current

- Store contract review outputs, run state, events, and final decisions as JSON/JSONL/CSV artifacts.
- Current artifacts preserve history for audit and demo replay.
- Current artifacts are not automatically used as agent memory unless the agent code reads them.

### Stage 2 - Metadata / Plain-Text Retrieval

- Read prior JSON/JSONL/CSV artifacts before a new contract review.
- Filter by simple metadata such as vendor, equipment type, decision, risk level, date, or repeated issue.
- Convert the selected prior records into a short plain-text memory block.
- Add that memory block to the contract review prompt.
- This stage is still prompt injection, but the selected history is more deliberate than manually pasting files.

### Stage 3 - Vector Retrieval

- Embed prior contract reviews, findings, and decision summaries.
- Embed the current procurement or contract-review query.
- Retrieve semantically similar prior cases, even when keywords do not exactly match.
- Add the top retrieved cases as text in the prompt.
- The vector layer improves selection; the LLM still reasons over retrieved text.

### Stage 4 - Durable Retrieval Store

- Move historical decision memory from loose files into PostgreSQL tables when reliability or querying becomes important.
- Use `pgvector`, ChromaDB, or OpenAI vector stores for semantic retrieval.
- Keep timestamps and metadata so the system can support temporal analysis, vendor history, and decision trends.
- Continue writing JSON/JSONL artifacts for auditability if useful for the demo and traceability.

### Current Memory Scope

- Short-term: quote text, fixed procurement fields, vendor proposal artifact when available.
- Long-term: not implemented yet; future versions should retrieve historical contract failure patterns and organization contract preferences.
- RAG opportunity: improves retrieval of standard clauses, policy rules, historical contract failure examples, and similar prior bid decisions.

## Connectors

- PDF/document parser output
- Procurement policy database, future
- Vendor registry, future

## Outputs

- `artifact_contract_review`
- risk score and risk level
- evidence-backed findings
- recommendation
- contract-risk metrics

## Guardrails

- Treat raw quote text as primary when present.
- Cite evidence.
- Report conflicts between fixed fields and raw text.
- Do not invent missing terms.

## Why This Agent Is Justified

Many procurement failures originate in warranty, payment, installation, service, and ambiguous contract terms.

## Status

Implemented as `backend/app/agents/contract_agent.py` with prompt `backend/prompts/contract_agent.md`.
