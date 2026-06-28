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
from ..services import bid_outputs, document_parser, input_bids
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


def run_bid_evaluation(run_id: str, bid_id: str, quote_ids: List[str]) -> None:
    """Evaluate a bid run and persist status for the UI.

    This is the first backend skeleton for the bid workflow. It uses the
    existing Contract Risk Agent for per-quote review and ranks lower-risk
    quotes higher. Later, the Bid Recommender Agent can replace the ranking
    logic while keeping the same run-state API.
    """
    try:
        bid_outputs.set_running(run_id)
        bid_outputs.update_agent(
            run_id,
            "bid_recommender",
            "running",
            "Preparing quote review plan",
        )
        quote_rows = input_bids.get_quote_rows(bid_id, quote_ids)
        reviews = []

        for quote in quote_rows:
            quote_id = quote["quote_id"]
            bid_outputs.update_quote(run_id, quote_id, "running")
            bid_outputs.update_agent(
                run_id,
                "contract_review",
                "running",
                f"Reviewing {quote_id}",
            )
            pdf_path = input_bids.SAMPLES_DIR / quote["pdf_path"]
            content = pdf_path.read_bytes()
            text = document_parser.extract_text(pdf_path.name, content)
            data = ProcurementInput(
                procurement_name=quote.get("procurement_name") or bid_id,
                equipment_type=quote.get("equipment_type") or "Medical Equipment",
                raw_document_text=text,
            )
            result = contract_agent.analyze(data)
            review = {
                "quote_id": quote_id,
                "vendor_name": quote.get("vendor_name", ""),
                "risk_score": result.risk_score,
                "risk_level": result.risk_level.value,
                "findings": result.findings,
                "recommendation": result.recommendation,
            }
            reviews.append(review)
            bid_outputs.update_quote(
                run_id,
                quote_id,
                "completed",
                vendor_name=quote.get("vendor_name", ""),
                risk_score=result.risk_score,
            )

        bid_outputs.update_agent(
            run_id,
            "decision_logic",
            "running",
            "Ranking reviewed quotes",
        )
        ranked = sorted(reviews, key=lambda item: item["risk_score"])
        winner = ranked[0] if ranked else {}
        result = {
            "run_id": run_id,
            "bid_id": bid_id,
            "status": "completed",
            "winner": winner,
            "ranked_quotes": ranked,
            "feedback": [
                "Initial demo ranking uses lower contract risk as better.",
                "Bid Recommender Agent logic can replace this ranking later.",
            ],
        }
        bid_outputs.complete_run(run_id, result)
    except Exception as exc:
        bid_outputs.fail_run(run_id, str(exc))
