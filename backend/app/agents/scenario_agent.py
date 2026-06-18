"""Agent 6 - Scenario Simulation Agent."""
from __future__ import annotations

from typing import List

from ..models import ProcurementInput, ScenarioOutcome
from .financial_agent import ANNUAL_IDLE_RATE

NAME = "Scenario Simulation Agent"


def simulate(
    data: ProcurementInput,
    predicted_delay_months: float,
    failure_probability: float,
) -> List[ScenarioOutcome]:
    asset = data.contract_value_cr

    def loss_for(delay: float) -> float:
        return round(asset * ANNUAL_IDLE_RATE * (delay / 12.0), 2)

    best_delay = max(1.0, predicted_delay_months * 0.4)
    worst_delay = predicted_delay_months * 1.6

    best = ScenarioOutcome(
        name="Best Case",
        timeline_months=round(best_delay, 1),
        financial_impact_cr=loss_for(best_delay),
        operational_impact="Fast-tracked readiness; limited idle period and "
        "high eventual utilisation.",
        probability_pct=round(max(5.0, 100 - failure_probability) * 0.4, 0),
    )
    expected = ScenarioOutcome(
        name="Expected Case",
        timeline_months=round(predicted_delay_months, 1),
        financial_impact_cr=loss_for(predicted_delay_months),
        operational_impact="Installation delayed pending civil, electrical and "
        "regulatory closure; asset idle through the gap.",
        probability_pct=round(failure_probability, 0),
    )
    worst = ScenarioOutcome(
        name="Worst Case",
        timeline_months=round(worst_delay, 1),
        financial_impact_cr=loss_for(worst_delay),
        operational_impact="Prolonged idleness, warranty expiry before go-live "
        "and chronic underutilisation of the asset.",
        probability_pct=round(max(5.0, failure_probability - 25), 0),
    )
    return [best, expected, worst]
