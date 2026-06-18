"""Agent 3 — Workforce Readiness Agent (LLM-only)."""
from __future__ import annotations

from ..models import AgentResult, ProcurementInput
from ..services.llm import has_api_key, run_agent_llm
from .base import clamp, risk_level

NAME = "Workforce Readiness Agent"
INSTRUCTIONS = """You are an operational-readiness analyst specialising in
public-sector procurement.

Assess the gap between trained operators/staff available versus required,
the presence of a hiring or training plan, training included in the contract,
and the likelihood the asset will be usable on arrival.

Return a JSON object with EXACTLY these keys:
{
  "risk_score": <integer 0-100>,
  "findings": ["specific finding 1", ...],
  "evidence": ["direct evidence from the input", ...],
  "reasoning": "narrative linking staff gaps to operational risk",
  "recommendation": "concrete action (hire X staff, mandate training, etc.)",
  "metrics": {
    "staff_readiness_pct": <integer 0-100, available/required × 100>,
    "operator_gap": <integer, required minus available; 0 if fully staffed>
  }
}

Scoring guidance:
- 0 operators available, >0 required → CRITICAL (score ≥ 80)
- Gap > 50% of required → HIGH (score 60-79)
- No training included in contract → +10 pts
- staff_readiness_pct = min(100, available / required × 100)"""


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
    metrics.setdefault("staff_readiness_pct", 50)
    metrics.setdefault(
        "operator_gap",
        max(0, data.technicians_required - data.technicians_available),
    )

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
        metrics={"staff_readiness_pct": 50, "operator_gap": 0},
    )
