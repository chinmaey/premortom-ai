"""PreMortem AI - FastAPI backend.

Endpoints
---------
GET  /health                 - service + mode (agentic/offline) status
POST /analyze                - run the full PreMortem (returns report JSON)
POST /upload                 - parse a document, return extracted text + fields
POST /report/{fmt}           - export report as json | pdf | docx
GET  /sample                 - the AIIMS MRI demo input
"""
from __future__ import annotations

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from .agents import extraction_agent
from .agents.orchestrator import run_premortem
from .models import PreMortemReport, ProcurementInput
from .services import document_parser, report as report_service
from .services.llm import has_api_key

app = FastAPI(
    title="PreMortem AI",
    description="Agentic Procurement Failure Prediction Platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "mode": "agentic" if has_api_key() else "offline (rule-based)",
        "service": "PreMortem AI",
    }


@app.get("/sample", response_model=ProcurementInput)
def sample():
    """AIIMS MRI demo procurement package."""
    return ProcurementInput()


@app.post("/analyze", response_model=PreMortemReport)
def analyze(data: ProcurementInput):
    if data.raw_document_text:
        data, _ = extraction_agent.extract(data.raw_document_text)
    return run_premortem(data)


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    content = await file.read()
    text = document_parser.extract_text(file.filename, content)
    extracted_input, missing = extraction_agent.extract(text)
    return {
        "filename": file.filename,
        "characters": len(text),
        "extracted_fields": extracted_input.model_dump(exclude={"raw_document_text"}),
        "missing_fields": missing,
        "text_preview": text[:2000],
        "raw_document_text": text,
    }


@app.post("/report/{fmt}")
def export_report(fmt: str, report: PreMortemReport):
    fmt = fmt.lower()
    base = report.procurement_name.replace(" ", "_")
    if fmt == "json":
        return Response(
            report_service.to_json_bytes(report),
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="{base}_premortem.json"'
            },
        )
    if fmt == "pdf":
        return Response(
            report_service.to_pdf_bytes(report),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{base}_premortem.pdf"'
            },
        )
    if fmt in ("docx", "word"):
        return Response(
            report_service.to_docx_bytes(report),
            media_type=(
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),
            headers={
                "Content-Disposition": f'attachment; filename="{base}_premortem.docx"'
            },
        )
    return Response(
        '{"error": "unsupported format"}',
        media_type="application/json",
        status_code=400,
    )
