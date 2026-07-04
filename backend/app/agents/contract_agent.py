"""Agent 1 — Contract Risk Agent (LLM-only)."""
from __future__ import annotations

from ..models import AgentResult, ProcurementInput
from ..services.llm import has_api_key, run_agent_llm
from ..services.okf_memory import select_okf_memory
from ..services.prompts import load_prompt
from .base import clamp, risk_level

NAME = "Contract Risk Agent"
BASE_INSTRUCTIONS = load_prompt("contract_agent")


def analyze(data: ProcurementInput) -> AgentResult:
    if not has_api_key():
        return _offline_result()

    instructions = _build_instructions(data)
    result = run_agent_llm(
        name=NAME,
        instructions=instructions,
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


def _build_instructions(data: ProcurementInput) -> str:
    query_text = "\n".join(
        [
            data.procurement_name,
            data.equipment_type,
            data.installation_responsibility,
            data.raw_document_text or "",
        ]
    )
    okf_memory = select_okf_memory(query_text)
    if not okf_memory:
        return BASE_INSTRUCTIONS
    return (
        f"{BASE_INSTRUCTIONS}\n\n"
        "# OKF long-term memory selected for this review\n"
        f"{okf_memory}\n"
    )
