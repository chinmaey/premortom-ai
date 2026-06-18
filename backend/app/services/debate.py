"""Generate the simulated multi-agent debate (Screen 3)."""
from __future__ import annotations

from typing import Dict, List

from ..models import AgentResult, DebateTurn


def build_debate(results: List[AgentResult]) -> List[DebateTurn]:
    by_name: Dict[str, AgentResult] = {r.agent: r for r in results}
    turns: List[DebateTurn] = []

    infra = by_name.get("Infrastructure Readiness Agent")
    if infra:
        readiness = infra.metrics.get(
            "construction_pct", infra.metrics.get("readiness_pct", "?")
        )
        delay_range = infra.metrics.get("delay_range", "several months")
        turns.append(
            DebateTurn(
                agent="Infrastructure Agent",
                statements=[
                    f"Facility readiness is only {readiness}%.",
                    "Installation is impossible until civil and electrical works close.",
                    f"Predicted installation delay: {delay_range}.",
                ],
            )
        )

    contract = by_name.get("Contract Risk Agent")
    if contract:
        turns.append(
            DebateTurn(
                agent="Contract Agent",
                statements=[
                    f"Warranty begins at {contract.metrics.get('warranty_start', 'delivery')}.",
                    "Coverage loss is expected while the asset sits idle.",
                ],
            )
        )

    fin = by_name.get("Financial Exposure Agent")
    if fin:
        advance = fin.metrics.get("advance_cr", 0)
        turns.append(
            DebateTurn(
                agent="Financial Agent",
                statements=[
                    f"₹{advance:.2f} Crore released before a usable asset exists.",
                    f"Projected loss of ₹{fin.metrics.get('projected_loss_cr', 0):.2f} Crore.",
                ],
            )
        )

    workforce = by_name.get("Workforce Readiness Agent")
    if workforce:
        gap = workforce.metrics.get("operator_gap", 0)
        turns.append(
            DebateTurn(
                agent="Workforce Agent",
                statements=[
                    f"{gap} operators short - no one to run the equipment."
                    if gap
                    else "Staffing is adequate.",
                    "Equipment likely idle even after installation.",
                ],
            )
        )

    hist = by_name.get("Historical Intelligence Agent")
    if hist:
        turns.append(
            DebateTurn(
                agent="Historical Agent",
                statements=[
                    f"Comparable projects averaged "
                    f"{hist.metrics.get('avg_delay_months', '?')} months of delay.",
                    f"Failure probability from precedent: "
                    f"{hist.metrics.get('failure_probability_pct', '?')}%.",
                ],
            )
        )

    return turns
