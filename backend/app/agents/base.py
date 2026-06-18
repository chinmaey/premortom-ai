"""Shared helpers for specialist agents."""
from __future__ import annotations

from ..models import RiskLevel


def risk_level(score: float) -> RiskLevel:
    if score >= 80:
        return RiskLevel.CRITICAL
    if score >= 60:
        return RiskLevel.HIGH
    if score >= 35:
        return RiskLevel.MODERATE
    return RiskLevel.LOW


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))
