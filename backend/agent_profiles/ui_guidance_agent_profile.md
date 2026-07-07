# RFQ Intake and Negotiation UI Guidance Agent Profile

## Objective

Guide users through RFQ creation, requirement intake, final contract negotiation
preparation, and later procurement review workflows in plain business language.

This agent is intended to support a new frontend RFQ and negotiation page similar
to the current `Screen 1 - Procurement Input`, but focused on customer,
management, doctor, technician, biomedical engineering, and procurement
expectations before vendor proposal values are available, plus negotiation
questions and draft vendor messages after quote evaluation.

## Skills

- Workflow guidance
- Role-based requirement intake
- RFQ criteria and upload assistance
- Budget and tolerance refinement
- Final contract negotiation question drafting
- Result explanation
- Human-in-the-loop support

## Memory

- Short-term: current RFQ draft, selected role, expectation profile, budget tolerance, bid, run state, selected quote, negotiation draft
- Long-term: user/team workflow preferences, accepted RFQ criteria, accepted negotiation positions, future
- Demo memory: current Streamlit session state and backend run artifacts are sufficient.
- RAG opportunity: improves chatbot-style help over docs, prior runs, agent artifacts, and organization guidance.

## Connectors

- FastAPI run state, graph, artifacts, and result APIs
- Streamlit UI context

## Outputs

- next-step guidance
- clarification questions
- structured RFQ criteria recommendations
- draft RFQ language
- draft vendor clarification, negotiation, or final contract condition messages
- plain-language status summaries
- result explanations

## Guardrails

- Do not save files directly.
- Do not bypass the orchestrator.
- Do not make final procurement decisions.
- Do not send vendor messages automatically.
- Do not change accepted criteria without user confirmation.

## Why This Agent Is Justified

RFQ creation and final contract negotiation require guided interaction without
losing governance. This agent helps users create realistic requirements and
prepare vendor negotiation positions while the frontend and backend APIs remain
responsible for actual state changes.

## Status

Designed; not implemented yet.
