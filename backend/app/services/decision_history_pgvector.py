"""pgvector-backed decision history storage.

Decision history is kept separate from OKF agent memory. The full run snapshot
is stored for audit/replay, while compact text chunks are stored for later
similar-case retrieval.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import psycopg2
from psycopg2.extras import Json

from .okf_pgvector import VECTOR_DIMS, embed_text


EMBEDDING_METHOD = "local_hashing_vector_v1"


def store_bid_run_history(
    *,
    run_id: str,
    state: dict[str, Any],
    result: dict[str, Any],
    run_dir: Path,
) -> bool:
    """Store a completed bid run in decision history.

    Returns True when stored. If ``DATABASE_URL`` is missing or the database is
    unavailable, the caller should catch the exception and continue.
    """
    snapshot = _build_snapshot(run_id, state, result, run_dir)
    decision_id = run_id
    winner = result.get("winner") or {}
    procurement_title = _procurement_title(state, result, snapshot)
    risk_score = winner.get("risk_score")
    risk_level = winner.get("risk_level", "")
    recommendation = winner.get("recommendation") or result.get("rationale", "")
    findings = winner.get("findings") or []

    chunks = _build_chunks(
        decision_id=decision_id,
        run_id=run_id,
        bid_id=str(result.get("bid_id") or state.get("bid_id") or ""),
        procurement_title=procurement_title,
        result=result,
        snapshot=snapshot,
    )

    with _connect() as conn:
        with conn.cursor() as cur:
            _ensure_schema(cur)
            cur.execute(
                """
                INSERT INTO decision_history (
                  id,
                  run_id,
                  bid_id,
                  procurement_title,
                  winning_quote_id,
                  winning_vendor,
                  risk_score,
                  risk_level,
                  recommendation,
                  findings,
                  snapshot,
                  embedding_method
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                  bid_id = EXCLUDED.bid_id,
                  procurement_title = EXCLUDED.procurement_title,
                  winning_quote_id = EXCLUDED.winning_quote_id,
                  winning_vendor = EXCLUDED.winning_vendor,
                  risk_score = EXCLUDED.risk_score,
                  risk_level = EXCLUDED.risk_level,
                  recommendation = EXCLUDED.recommendation,
                  findings = EXCLUDED.findings,
                  snapshot = EXCLUDED.snapshot,
                  embedding_method = EXCLUDED.embedding_method,
                  updated_at = now()
                """,
                (
                    decision_id,
                    run_id,
                    str(result.get("bid_id") or state.get("bid_id") or ""),
                    procurement_title,
                    str(winner.get("quote_id") or ""),
                    str(winner.get("vendor_name") or ""),
                    risk_score,
                    str(risk_level),
                    str(recommendation),
                    Json(findings),
                    Json(snapshot),
                    EMBEDDING_METHOD,
                ),
            )
            cur.execute(
                "DELETE FROM decision_history_chunks WHERE decision_id = %s",
                (decision_id,),
            )
            for chunk in chunks:
                cur.execute(
                    """
                    INSERT INTO decision_history_chunks (
                      id,
                      decision_id,
                      run_id,
                      bid_id,
                      chunk_type,
                      content,
                      metadata,
                      embedding,
                      embedding_method
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s::vector, %s)
                    """,
                    (
                        chunk["id"],
                        decision_id,
                        run_id,
                        str(result.get("bid_id") or state.get("bid_id") or ""),
                        chunk["chunk_type"],
                        chunk["content"],
                        Json(chunk["metadata"]),
                        _vector_literal(embed_text(chunk["content"])),
                        EMBEDDING_METHOD,
                    ),
                )
        conn.commit()
    return True


def _connect():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured")
    return psycopg2.connect(database_url)


def _ensure_schema(cur) -> None:
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS decision_history (
          id text PRIMARY KEY,
          run_id text NOT NULL UNIQUE,
          bid_id text NOT NULL DEFAULT '',
          procurement_title text NOT NULL DEFAULT '',
          winning_quote_id text NOT NULL DEFAULT '',
          winning_vendor text NOT NULL DEFAULT '',
          risk_score numeric,
          risk_level text NOT NULL DEFAULT '',
          recommendation text NOT NULL DEFAULT '',
          findings jsonb NOT NULL DEFAULT '[]'::jsonb,
          snapshot jsonb NOT NULL,
          embedding_method text NOT NULL DEFAULT '',
          created_at timestamptz NOT NULL DEFAULT now(),
          updated_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    cur.execute(
        f"""
        CREATE TABLE IF NOT EXISTS decision_history_chunks (
          id text PRIMARY KEY,
          decision_id text NOT NULL REFERENCES decision_history(id) ON DELETE CASCADE,
          run_id text NOT NULL,
          bid_id text NOT NULL DEFAULT '',
          chunk_type text NOT NULL,
          content text NOT NULL,
          metadata jsonb NOT NULL DEFAULT '{{}}'::jsonb,
          embedding vector({VECTOR_DIMS}) NOT NULL,
          embedding_method text NOT NULL DEFAULT '',
          created_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    cur.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_decision_history_run
        ON decision_history(run_id)
        """
    )
    cur.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_decision_history_chunks_decision
        ON decision_history_chunks(decision_id)
        """
    )


def _build_snapshot(
    run_id: str,
    state: dict[str, Any],
    result: dict[str, Any],
    run_dir: Path,
) -> dict[str, Any]:
    artifacts = {
        "run_state": state,
        "decision_result": result,
    }
    for key, filename in {
        "vendor_proposals": "vendor_proposal_agent_quote_intelligence.json",
        "contract_reviews": "contract_review_agent_quote_reviews.json",
    }.items():
        path = run_dir / filename
        if path.exists():
            artifacts[key] = _read_json(path)

    return {
        "run_id": run_id,
        "bid_id": result.get("bid_id") or state.get("bid_id") or "",
        "status": result.get("status") or state.get("status") or "",
        "artifacts": artifacts,
    }


def _build_chunks(
    *,
    decision_id: str,
    run_id: str,
    bid_id: str,
    procurement_title: str,
    result: dict[str, Any],
    snapshot: dict[str, Any],
) -> list[dict[str, Any]]:
    winner = result.get("winner") or {}
    findings = winner.get("findings") or []
    chunks = [
        (
            "procurement_summary",
            (
                f"Run {run_id} reviewed bid {bid_id}. "
                f"Procurement: {procurement_title}. "
                f"Status: {result.get('status', '')}."
            ),
        ),
        (
            "winning_decision_summary",
            (
                f"Selected quote: {winner.get('quote_id', '')}. "
                f"Vendor: {winner.get('vendor_name', '')}. "
                f"Risk score: {winner.get('risk_score', '')}. "
                f"Risk level: {winner.get('risk_level', '')}. "
                f"Recommendation: {winner.get('recommendation') or result.get('rationale', '')}"
            ),
        ),
        (
            "risk_findings_summary",
            "Risk findings: " + " ".join(str(item) for item in findings),
        ),
        (
            "decision_rationale",
            (
                f"Rationale: {result.get('rationale', '')} "
                f"Feedback: {' '.join(str(item) for item in result.get('feedback') or [])} "
                "Negotiation points: "
                + " ".join(str(item) for item in result.get("negotiation_points") or [])
            ),
        ),
    ]

    return [
        {
            "id": f"{decision_id}:{chunk_type}",
            "chunk_type": chunk_type,
            "content": content[:8000],
            "metadata": {
                "run_id": run_id,
                "bid_id": bid_id,
                "procurement_title": procurement_title,
                "artifact_refs": result.get("artifact_refs") or [],
                "snapshot_keys": list(snapshot.get("artifacts", {}).keys()),
            },
        }
        for chunk_type, content in chunks
        if content.strip()
    ]


def _procurement_title(
    state: dict[str, Any],
    result: dict[str, Any],
    snapshot: dict[str, Any],
) -> str:
    vendor_proposals = snapshot.get("artifacts", {}).get("vendor_proposals", {})
    quotes = vendor_proposals.get("quotes") if isinstance(vendor_proposals, dict) else []
    if quotes:
        fixed = quotes[0].get("fixed_features", {})
        equipment = fixed.get("equipment_type", {}).get("value", "")
        if equipment:
            return str(equipment)
    return str(result.get("bid_id") or state.get("bid_id") or "Procurement review")


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _vector_literal(values: list[float]) -> str:
    return json.dumps(values)
