"""Plotly visualizations for the PreMortem dashboard."""
from __future__ import annotations

from typing import List

import plotly.graph_objects as go


RISK_COLORS = {
    "LOW": "#16a34a",
    "MODERATE": "#eab308",
    "HIGH": "#f97316",
    "CRITICAL": "#dc2626",
}


def risk_gauge(score: float) -> go.Figure:
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            number={"suffix": "/100", "font": {"size": 40}},
            title={"text": "Overall Risk Score"},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1},
                "bar": {"color": "#0f172a"},
                "steps": [
                    {"range": [0, 35], "color": "#bbf7d0"},
                    {"range": [35, 60], "color": "#fef08a"},
                    {"range": [60, 80], "color": "#fed7aa"},
                    {"range": [80, 100], "color": "#fecaca"},
                ],
                "threshold": {
                    "line": {"color": "#dc2626", "width": 4},
                    "thickness": 0.75,
                    "value": score,
                },
            },
        )
    )
    fig.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=10))
    return fig


def agent_contribution_bar(agents: List[dict]) -> go.Figure:
    names = [a["agent"].replace(" Agent", "") for a in agents]
    scores = [a["risk_score"] for a in agents]
    colors = [RISK_COLORS.get(a["risk_level"], "#64748b") for a in agents]
    fig = go.Figure(
        go.Bar(
            x=scores,
            y=names,
            orientation="h",
            marker_color=colors,
            text=scores,
            textposition="outside",
        )
    )
    fig.update_layout(
        title="Agent Risk Contributions",
        xaxis=dict(range=[0, 100], title="Risk Score"),
        height=320,
        margin=dict(l=10, r=10, t=50, b=10),
    )
    return fig


def agent_radar(agents: List[dict]) -> go.Figure:
    names = [a["agent"].replace(" Agent", "") for a in agents]
    scores = [a["risk_score"] for a in agents]
    fig = go.Figure(
        go.Scatterpolar(
            r=scores + [scores[0]],
            theta=names + [names[0]],
            fill="toself",
            line_color="#dc2626",
            fillcolor="rgba(220,38,38,0.25)",
        )
    )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        title="Multi-Agent Consensus",
        height=360,
        margin=dict(l=30, r=30, t=50, b=30),
    )
    return fig


def risk_heatmap(agents: List[dict]) -> go.Figure:
    names = [a["agent"].replace(" Agent", "") for a in agents]
    scores = [a["risk_score"] for a in agents]
    fig = go.Figure(
        go.Heatmap(
            z=[scores],
            x=names,
            y=["Risk"],
            colorscale=[
                [0.0, "#16a34a"],
                [0.35, "#eab308"],
                [0.6, "#f97316"],
                [0.8, "#dc2626"],
                [1.0, "#7f1d1d"],
            ],
            zmin=0,
            zmax=100,
            text=[scores],
            texttemplate="%{text}",
            showscale=True,
        )
    )
    fig.update_layout(
        title="Procurement Risk Heatmap",
        height=200,
        margin=dict(l=10, r=10, t=50, b=10),
    )
    return fig


def scenario_timeline(scenarios: List[dict]) -> go.Figure:
    names = [s["name"] for s in scenarios]
    timelines = [s["timeline_months"] for s in scenarios]
    losses = [s["financial_impact_cr"] for s in scenarios]
    fig = go.Figure()
    fig.add_trace(
        go.Bar(name="Delay (months)", x=names, y=timelines, marker_color="#3b82f6")
    )
    fig.add_trace(
        go.Bar(
            name="Financial Impact (Cr)",
            x=names,
            y=losses,
            marker_color="#ef4444",
            yaxis="y2",
        )
    )
    fig.update_layout(
        title="Failure Timeline & Financial Simulation",
        yaxis=dict(title="Delay (months)"),
        yaxis2=dict(title="Loss (Cr)", overlaying="y", side="right"),
        barmode="group",
        height=360,
        margin=dict(l=10, r=10, t=50, b=10),
    )
    return fig


def whatif_curve(delays: List[float], losses: List[float]) -> go.Figure:
    fig = go.Figure(
        go.Scatter(
            x=delays,
            y=losses,
            mode="lines+markers",
            line=dict(color="#dc2626", width=3),
            fill="tozeroy",
            fillcolor="rgba(220,38,38,0.15)",
        )
    )
    fig.update_layout(
        title="What-If: Financial Loss vs Delay",
        xaxis_title="Installation Delay (months)",
        yaxis_title="Projected Loss (Cr)",
        height=320,
        margin=dict(l=10, r=10, t=50, b=10),
    )
    return fig
