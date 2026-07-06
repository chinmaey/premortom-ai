---
type: ranking-policy
title: Quote Ranking Policy
description: Ranking guidance for comparing reviewed quotes within one bid.
resource: bid_recommender_agent
status: draft
tags:
  - ranking
  - shortlist
  - quote-comparison
---

# Quote Ranking Policy

The core ranking should be deterministic and auditable.

Prefer quotes that combine:

- Lower contract risk.
- Fewer hard blockers.
- Clearer warranty, installation, commissioning, training, and service terms.
- Lower ambiguity or conflict between fixed fields and raw quote text.
- Better alignment with management criteria and weights when available.
- Stronger evidence quality.

Do not select a quote only because it has the lowest risk score if it has an
unresolved blocker that makes award unsafe.

The LLM may improve explanation language, but it should not silently change the
winner, ranked quote list, shortlist, or score components.
