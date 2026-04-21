"""
Research Agent — Backend API
─────────────────────────────────────────────────────────────
4-agent CrewAI pipeline: Researcher → Writer → Strategist → Devil's Advocate
"""

import io
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from crew.research_crew import run_research_crew

load_dotenv()

app = FastAPI(title="RECON — Sales Intelligence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_PATH = Path(__file__).parent.parent / "frontend" / "index.html"


class ResearchRequest(BaseModel):
    company: str
    company_profile: str = ""  # Optional: your company's product/service description


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    if not FRONTEND_PATH.exists():
        raise HTTPException(status_code=404, detail="Frontend not found")
    return HTMLResponse(content=FRONTEND_PATH.read_text(encoding="utf-8"))


@app.post("/api/research")
async def research_company(request: ResearchRequest):
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not set in .env")
    if not os.getenv("TAVILY_API_KEY"):
        raise HTTPException(status_code=500, detail="TAVILY_API_KEY not set in .env")

    company = request.company.strip()
    if not company:
        raise HTTPException(status_code=400, detail="Company name cannot be empty.")
    if len(company) > 200:
        raise HTTPException(status_code=400, detail="Company name too long.")

    try:
        briefing = await run_research_crew(company, request.company_profile.strip())
        return JSONResponse(content=briefing)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Research failed: {str(e)}")


@app.post("/api/extract-text")
async def extract_text(file: UploadFile = File(...)):
    """Extract plain text from uploaded .txt, .pdf, or .docx files."""
    content = await file.read()
    filename = (file.filename or "").lower()

    try:
        if filename.endswith(".pdf"):
            try:
                import pdfplumber
                with pdfplumber.open(io.BytesIO(content)) as pdf:
                    text = "\n\n".join(
                        (page.extract_text() or "") for page in pdf.pages[:10]
                    )
            except ImportError:
                raise HTTPException(status_code=501, detail="pdfplumber not installed. Run: py -3.12 -m pip install pdfplumber")

        elif filename.endswith(".docx") or filename.endswith(".doc"):
            try:
                import docx
                doc = docx.Document(io.BytesIO(content))
                text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
            except ImportError:
                raise HTTPException(status_code=501, detail="python-docx not installed. Run: py -3.12 -m pip install python-docx")

        else:
            text = content.decode("utf-8", errors="ignore")

        return JSONResponse(content={"text": text[:3000]})

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not extract text: {str(e)}")


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "anthropic_key_set": bool(os.getenv("ANTHROPIC_API_KEY")),
        "tavily_key_set": bool(os.getenv("TAVILY_API_KEY")),
    }
