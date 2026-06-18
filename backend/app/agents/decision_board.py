"""Agent 7 - Decision Board Agent (consolidator)."""
from __future__ import annotations

from statistics import mean
from typing import Dict, List

from ..models import AgentResult, Decision, ProcurementInput

NAME = "Decision Board Agent"

# Relative influence of each specialist on the overall risk score.
WEIGHTS: Dict[str, float] = {
    "Infrastructure Readiness Agent": 0.26,
    "Contract Risk Agent": 0.18,
    "Workforce Readiness Agent": 0.18,
    "Financial Exposure Agent": 0.20,
    "Historical Intelligence Agent": 0.18,
}


def consolidate(
    data: ProcurementInput,
    results: List[AgentResult],
) -> dict:
    by_name = {r.agent: r for r in results}

    # Weighted overall risk score.
    num, den = 0.0, 0.0
    for r in results:
        w = WEIGHTS.get(r.agent, 0.1)
        num += w * r.risk_score
        den += w
    overall = round(num / den) if den else round(mean(r.risk_score for r in results))

    hist = by_name.get("Historical Intelligence Agent")
    infra = by_name.get("Infrastructure Readiness Agent")
    fin = by_name.get("Financial Exposure Agent")

    failure_probability = round(
        0.55 * overall
        + 0.45 * (hist.metrics.get("failure_probability_pct", overall) if hist else overall)
    )
    failure_probability = min(99, max(1, failure_probability))

    predicted_delay = (
        infra.metrics.get("predicted_delay_months", 8.0) if infra else 8.0
    )
    projected_loss = fin.metrics.get("projected_loss_cr", 0.0) if fin else 0.0

    # Decision thresholds.
    critical_count = sum(1 for r in results if r.risk_score >= 80)
    if overall >= 70 or critical_count >= 2:
        decision = Decision.NO_GO
    elif overall >= 45:
        decision = Decision.GO_WITH_CONDITIONS
    else:
        decision = Decision.GO

    # Confidence: how strongly the agents agree (low variance => high confidence).
    scores = [r.risk_score for r in results]
    spread = max(scores) - min(scores) if scores else 0
    confidence = round(max(60.0, 96 - spread * 0.6))

    # Failure mode + conditions.
    failure_mode = _failure_mode(data, by_name)
    conditions = _conditions(data, by_name, decision)

    evidence = _evidence(by_name)
    outcomes = _outcomes(predicted_delay, projected_loss, data, by_name)

    return {
        "overall_risk_score": overall,
        "failure_probability_pct": failure_probability,
        "confidence_pct": confidence,
        "predicted_delay_months": predicted_delay,
        "projected_financial_loss_cr": projected_loss,
        "recommended_decision": decision,
        "predicted_failure_mode": failure_mode,
        "supporting_evidence": evidence,
        "predicted_outcomes": outcomes,
        "conditions": conditions,
    }


def _failure_mode(data: ProcurementInput, by_name) -> str:
    infra = by_name.get("Infrastructure Readiness Agent")
    if infra and infra.risk_score >= 70:
        return "Equipment delivered before site readiness."
    if data.technicians_available == 0 and data.technicians_required > 0:
        return "Asset commissioned without trained operators."
    return "Value committed ahead of verified readiness."


def _evidence(by_name) -> List[str]:
    out: List[str] = []
    for agent in (
        "Infrastructure Readiness Agent",
        "Contract Risk Agent",
        "Workforce Readiness Agent",
        "Financial Exposure Agent",
        "Historical Intelligence Agent",
    ):
        r = by_name.get(agent)
        if r and r.findings:
            out.append(r.findings[0])
    return out


def _outcomes(delay, loss, data: ProcurementInput, by_name) -> List[str]:
    infra = by_name.get("Infrastructure Readiness Agent")
    delay_range = (
        infra.metrics.get("delay_range") if infra else f"{int(delay)} months"
    )
    fin = by_name.get("Financial Exposure Agent")
    annual_idle = fin.metrics.get("annual_idle_cost_cr") if fin else None
    outcomes = [
        f"Installation delay: {delay_range}",
        f"Projected financial loss: ₹{loss:.2f} Cr",
    ]
    if annual_idle:
        outcomes.append(f"Idle asset exposure: ₹{annual_idle:.2f} Cr / year")
    if data.warranty_start.value == "On Delivery":
        outcomes.append(
            f"Warranty loss: ~{int(delay)} months of coverage consumed while idle"
        )
    outcomes.append("High probability of underutilisation")
    return outcomes


def _conditions(data: ProcurementInput, by_name, decision: Decision) -> List[str]:
    if decision == Decision.GO:
        return ["Proceed with standard milestone monitoring."]
    conditions: List[str] = []
    if data.construction_completion_pct < 95:
        conditions.append("Facility readiness reaches 95%.")
    if data.electrical_readiness.value != "Approved":
        conditions.append("Electrical readiness completed and energised.")
    if data.regulatory_approval_status.value != "Approved":
        conditions.append("All regulatory/safety approvals completed.")
    if data.technicians_available < data.technicians_required:
        conditions.append("Required technicians hired and certified.")
    if data.warranty_start.value != "On Commissioning":
        conditions.append("Warranty revised to start at commissioning date.")
    if data.advance_payment_pct > 20:
        conditions.append("Advance reduced to <=20% against a bank guarantee.")
    return conditions or ["Address all flagged agent findings before approval."]
