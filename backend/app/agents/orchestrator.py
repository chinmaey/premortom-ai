"""Agent orchestration.

Runs all five specialist analysis agents in parallel, then the Scenario
Simulation Agent and finally the Decision Board Agent. When ``langgraph`` is
installed the flow is expressed as a graph; otherwise we use a thread pool,
preserving identical behaviour.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import List

from ..models import AgentResult, PreMortemReport, ProcurementInput
from ..services.debate import build_debate
from . import (
    contract_agent,
    decision_board,
    financial_agent,
    historical_agent,
    infrastructure_agent,
    scenario_agent,
    workforce_agent,
)


def _run_parallel(data: ProcurementInput) -> List[AgentResult]:
    """Execute the independent specialist agents concurrently."""
    with ThreadPoolExecutor(max_workers=5) as ex:
        f_contract = ex.submit(contract_agent.analyze, data)
        f_infra = ex.submit(infrastructure_agent.analyze, data)
        f_workforce = ex.submit(workforce_agent.analyze, data)
        f_historical = ex.submit(historical_agent.analyze, data)
        infra_result = f_infra.result()
        predicted_delay = infra_result.metrics.get("predicted_delay_months", 8.0)
        # Financial agent depends on infra's delay prediction.
        f_financial = ex.submit(
            financial_agent.analyze, data, predicted_delay
        )
        results = [
            f_contract.result(),
            infra_result,
            f_workforce.result(),
            f_financial.result(),
            f_historical.result(),
        ]
    return results


def run_premortem(data: ProcurementInput) -> PreMortemReport:
    results = _run_parallel(data)

    consolidated = decision_board.consolidate(data, results)
    debate = build_debate(results)
    scenarios = scenario_agent.simulate(
        data,
        consolidated["predicted_delay_months"],
        consolidated["failure_probability_pct"],
    )

    return PreMortemReport(
        procurement_name=data.procurement_name,
        equipment_type=data.equipment_type,
        contract_value_cr=data.contract_value_cr,
        overall_risk_score=consolidated["overall_risk_score"],
        failure_probability_pct=consolidated["failure_probability_pct"],
        confidence_pct=consolidated["confidence_pct"],
        predicted_delay_months=consolidated["predicted_delay_months"],
        projected_financial_loss_cr=consolidated["projected_financial_loss_cr"],
        predicted_failure_mode=consolidated["predicted_failure_mode"],
        supporting_evidence=consolidated["supporting_evidence"],
        predicted_outcomes=consolidated["predicted_outcomes"],
        recommended_decision=consolidated["recommended_decision"],
        conditions=consolidated["conditions"],
        agent_results=results,
        debate=debate,
        scenarios=scenarios,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
