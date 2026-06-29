# Bid Recommendation Agent Profile

## Objective

Compare all quotes within a bid and recommend the best quote or shortlist.

## Skills

- Quote ranking
- Multi-agent signal synthesis
- Tradeoff explanation
- Winner and shortlist recommendation

## Memory

- Short-term: current bid, quote reviews, proposal intelligence, criteria, dataset labels for evaluation
- Long-term: historical decision outcomes and reviewer preferences, future
- Demo memory: `dataset.csv`, `metadata.json`, and run artifacts are sufficient.
- RAG opportunity: strongly improves retrieval of past decisions, company preferences, reviewer feedback, and similar bid outcomes.

## Connectors

- Vendor proposal artifacts
- Contract review artifacts
- Cost, compliance, vendor-risk, and market-research agents, future

## Outputs

- `artifact_bid_recommendation`
- winner
- ranked quotes
- rationale
- feedback and negotiation points

## Guardrails

- Compare quotes within the same bid only.
- Separate evidence from judgment.
- Explain why weaker quotes were downgraded.

## Why This Agent Is Justified

Procurement decisions require comparing multiple vendor proposals, not merely reviewing one quote in isolation.

## Status

Partially implemented as deterministic ranking placeholder in the orchestrator.
