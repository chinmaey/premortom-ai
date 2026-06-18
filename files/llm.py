"""LLM service wrapper (Claude / Anthropic edition).

PreMortem AI runs in two modes:

1.  **Agentic mode** - when ``ANTHROPIC_API_KEY`` is set, each specialist agent
    gets an LLM-authored analysis from Claude.
2.  **Offline mode** - with no key, every agent falls back to its deterministic
    rule-based engine, so the full demo still runs with zero external calls.

This file is a *drop-in* replacement: it exposes the same ``has_api_key()`` and
``run_agent_llm(...)`` functions the agents already call, so nothing else in the
codebase needs to change.
"""
from __future__ import annotations

import json
import os
from typing import Optional

# Model the specialist agents use. Haiku is cheapest/fastest and fine for the
# 5 per-agent passes; bump to claude-sonnet-4-6 if you want stronger reasoning.
#   Haiku 4.5  -> "claude-haiku-4-5-20251001"   (~$1 / $5 per million tokens)
#   Sonnet 4.6 -> "claude-sonnet-4-6"           (~$3 / $15 per million tokens)
MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5-20251001")


def has_api_key() -> bool:
    """True when an Anthropic key is configured (switches on agentic mode)."""
    return bool(os.getenv("ANTHROPIC_API_KEY"))


_client = None


def _get_client():
    """Lazily build and cache the Anthropic client."""
    global _client
    if _client is not None:
        return _client
    try:
        from anthropic import Anthropic

        _client = Anthropic()  # reads ANTHROPIC_API_KEY from the environment
        return _client
    except Exception:
        return None


def run_agent_llm(
    *,
    name: str,
    instructions: str,
    user_payload: str,
    temperature: float = 0.2,
) -> Optional[dict]:
    """Run one agent through Claude.

    Returns a parsed JSON dict (the agent is asked to reply with a single JSON
    object) or ``None`` if the call could not be completed, so callers can fall
    back to their rule-based engine.
    """
    if not has_api_key():
        return None

    client = _get_client()
    if client is None:
        return None

    try:
        resp = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            temperature=temperature,
            system=(
                instructions
                + "\n\nRespond with a SINGLE valid JSON object and nothing "
                "else. No markdown, no code fences, no commentary."
            ),
            messages=[
                {"role": "user", "content": user_payload},
                # Prefill the assistant turn with "{" so Claude is forced to
                # start a JSON object straight away -> much more reliable parsing.
                {"role": "assistant", "content": "{"},
            ],
        )
        # Because we prefilled "{", the model's text continues from there.
        text = "{" + resp.content[0].text
        return _coerce_json(text)
    except Exception:
        return None


def _coerce_json(text) -> Optional[dict]:
    """Best-effort parse of an LLM response into a dict."""
    if text is None:
        return None
    if isinstance(text, dict):
        return text
    text = str(text).strip()
    # Strip code fences if the model added them despite instructions.
    if text.startswith("```"):
        text = text.split("```", 2)[1] if "```" in text else text
        text = text.replace("json", "", 1).strip("` \n")
    try:
        return json.loads(text)
    except Exception:
        # Locate the first {...} block and try again.
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except Exception:
                return None
        return None
