"""Agent 1 — Contract Risk Agent (LLM-only)."""
from __future__ import annotations

from ..models import AgentResult, ProcurementInput
from ..services.llm import has_api_key, run_agent_llm
from .base import clamp, risk_level

NAME = "Contract Risk Agent"
INSTRUCTIONS = """You are a public-procurement contract risk analyst.

Analyse the warranty clauses, advance payment terms, installation responsibility,
penalty/performance clauses, and training obligations of the procurement below.

Return a JSON object with EXACTLY these keys — no extras, no omissions:
{
  "risk_score": <integer 0-100; 0 = no risk, 100 = near-certain failure>,
  "findings": ["specific finding 1", "specific finding 2", ...],
  "evidence": ["direct quote or data point from the input", ...],
  "reasoning": "narrative explaining how you weighed each factor",
  "recommendation": "concrete action the procurement officer should take",
  "metrics": {
    "advance_released_cr": <float, advance payment amount in INR Crore>,
    "warranty_start": "<warranty start term as stated in the contract>"
  }
}

Scoring guidance:
- Warranty starting at delivery (before commissioning) → +30-40 pts
- Advance ≥ 50% with no bank guarantee → +20-30 pts
- Installation responsibility on buyer with no vendor penalty → +10 pts
- No training included → +5-10 pts
- Each mitigant present (commissioning-linked warranty, bank guarantee, etc.) → -10 pts"""


def analyze(data: ProcurementInput) -> AgentResult:
    if not has_api_key():
        return _offline_result()

    result = run_agent_llm(
        name=NAME,
        instructions=INSTRUCTIONS,
        user_payload=data.model_dump_json(),
    )
    if result is None:
        raise RuntimeError(f"{NAME}: LLM call failed — check your API key.")

    score = clamp(float(result.get("risk_score", 50)))
    metrics = result.get("metrics") or {}
    # Ensure required downstream keys exist
    if "advance_released_cr" not in metrics:
        metrics["advance_released_cr"] = round(
            data.contract_value_cr * data.advance_payment_pct / 100, 2
        )
    if "warranty_start" not in metrics:
        metrics["warranty_start"] = data.warranty_start.value

    return AgentResult(
        agent=NAME,
        risk_score=round(score),
        risk_level=risk_level(score),
        findings=result.get("findings") or [],
        evidence=result.get("evidence") or [],
        reasoning=result.get("reasoning") or "",
        recommendation=result.get("recommendation") or "",
        metrics=metrics,
    )


def _offline_result() -> AgentResult:
    return AgentResult(
        agent=NAME,
        status="offline",
        risk_score=50,
        risk_level=risk_level(50),
        findings=["Offline mode — no API key set. Add OPENAI_API_KEY or ANTHROPIC_API_KEY to enable analysis."],
        evidence=[],
        reasoning="No analysis performed in offline mode.",
        recommendation="Configure an API key to enable agentic analysis.",
        metrics={"advance_released_cr": 0.0, "warranty_start": "unknown"},
    )
