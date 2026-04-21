"""
Contract Intelligence — Backend API
─────────────────────────────────────────────────────────────
FastAPI server that powers the contract risk analysis tool.

Pipeline:
  Upload PDF → Extract text → Analyst Agent → Scorer Agent → Report

Endpoints:
  POST /api/analyse  — Upload a PDF, get back a full risk report
  GET  /             — Serve the frontend HTML
"""

import os
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from utils.pdf_extractor import extract_pdf_text
from agents.analyst_agent import run_analyst_agent
from agents.scorer_agent import run_scorer_agent

load_dotenv()

app = FastAPI(title="Contract Intelligence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_PATH = Path(__file__).parent.parent / "frontend" / "index.html"
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    if not FRONTEND_PATH.exists():
        raise HTTPException(status_code=404, detail="Frontend not found")
    return HTMLResponse(content=FRONTEND_PATH.read_text(encoding="utf-8"))


@app.post("/api/analyse")
async def analyse_contract(file: UploadFile = File(...)):
    """
    Full pipeline:
      1. Validate the upload
      2. Extract text from PDF
      3. Analyst agent identifies risks
      4. Scorer agent produces overall verdict
      5. Return merged report
    """
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(
            status_code=500,
            detail="ANTHROPIC_API_KEY not set. Add it to your .env file."
        )

    # ── VALIDATE ──────────────────────────────────────────
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_bytes = await file.read()

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 20 MB.")

    if len(file_bytes) < 100:
        raise HTTPException(status_code=400, detail="File appears to be empty.")

    # ── EXTRACT ───────────────────────────────────────────
    try:
        extracted = extract_pdf_text(file_bytes)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not read PDF: {str(e)}")

    if not extracted["text"].strip():
        raise HTTPException(
            status_code=422,
            detail="No text could be extracted from this PDF. It may be a scanned image — try a text-based PDF."
        )

    # ── AGENT 1: ANALYST ──────────────────────────────────
    analyst_output = await run_analyst_agent(extracted["text"])

    # ── AGENT 2: SCORER ───────────────────────────────────
    scorer_output = await run_scorer_agent(analyst_output)

    # ── MERGE AND RETURN ──────────────────────────────────
    return JSONResponse(content={
        "file_name": file.filename,
        "page_count": extracted["page_count"],
        "truncated": extracted["truncated"],
        "contract_type": analyst_output.get("contract_type", "Unknown"),
        "parties": analyst_output.get("parties", ""),
        "findings": analyst_output.get("findings", []),
        "verdict": scorer_output,
    })


@app.get("/api/health")
async def health():
    return {"status": "ok", "anthropic_key_set": bool(os.getenv("ANTHROPIC_API_KEY"))}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8001, reload=True)
