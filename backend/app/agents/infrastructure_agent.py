"""Agent 2 — Infrastructure Readiness Agent (LLM-only)."""
from __future__ import annotations

from ..models import AgentResult, ProcurementInput
from ..services.llm import has_api_key, run_agent_llm
from .base import clamp, risk_level

NAME = "Infrastructure Readiness Agent"
INSTRUCTIONS = """You are a site-readiness and civil-works engineer specialising
in public-sector infrastructure procurement.

Evaluate construction completion percentage, electrical/power readiness,
regulatory and safety approvals (radiation clearance, fire NOC, etc.), and
any other installation prerequisites mentioned in the procurement below.

Return a JSON object with EXACTLY these keys:
{
  "risk_score": <integer 0-100>,
  "findings": ["specific finding 1", ...],
  "evidence": ["direct evidence from the input", ...],
  "reasoning": "narrative of how site readiness translates to installation risk",
  "recommendation": "concrete gate conditions before accepting delivery",
  "metrics": {
    "readiness_pct": <integer 0-100, composite site readiness>,
    "construction_pct": <integer 0-100, civil works completion>,
    "predicted_delay_months": <float, expected installation delay>,
    "delay_range": "<low>-<high> months"
  }
}

Scoring guidance:
- Construction < 80% → installation impossible → CRITICAL (score ≥ 80)
- Each major approval pending (electrical, regulatory) → +20-25 pts
- Construction gap (100 - pct) × 0.8 is a reasonable base score
- predicted_delay_months: civil gap drives ~0.1 months per 1% gap;
  each pending approval adds 1-2.5 months"""


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
    # Ensure required downstream keys exist with safe defaults
    metrics.setdefault("readiness_pct", 50)
    metrics.setdefault("construction_pct", data.construction_completion_pct)
    metrics.setdefault("predicted_delay_months", 8.0)
    delay = float(metrics["predicted_delay_months"])
    metrics.setdefault(
        "delay_range",
        f"{max(1, round(delay - 2))}-{round(delay + 1)} months",
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
        metrics={
            "readiness_pct": 50,
            "construction_pct": 50,
            "predicted_delay_months": 8.0,
            "delay_range": "6-9 months",
        },
    )
