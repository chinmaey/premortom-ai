"""Thin HTTP client for the PreMortem AI backend."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import requests

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dependency is declared for normal installs.
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)

API_BASE = os.getenv("PREMORTEM_API", "http://localhost:8000")
TIMEOUT = 120


def health() -> dict:
    return requests.get(f"{API_BASE}/health", timeout=TIMEOUT).json()


def sample_input() -> dict:
    return requests.get(f"{API_BASE}/sample", timeout=TIMEOUT).json()


def analyze(payload: dict) -> dict:
    r = requests.post(f"{API_BASE}/analyze", json=payload, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def upload(filename: str, content: bytes) -> dict:
    files = {"file": (filename, content)}
    r = requests.post(f"{API_BASE}/upload", files=files, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def export_report(fmt: str, report: dict) -> Optional[bytes]:
    r = requests.post(f"{API_BASE}/report/{fmt}", json=report, timeout=TIMEOUT)
    r.raise_for_status()
    return r.content
