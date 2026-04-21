from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List
import anthropic
import os
from pathlib import Path
from dotenv import load_dotenv
from profile import SYSTEM_PROMPT

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-4-6"


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]


class AnalyseRequest(BaseModel):
    job_description: str


@app.post("/api/chat")
async def chat(request: ChatRequest):
    if not request.messages:
        raise HTTPException(status_code=400, detail="No messages provided")

    def generate():
        with client.messages.stream(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": m.role, "content": m.content} for m in request.messages],
        ) as stream:
            for text in stream.text_stream:
                yield text

    return StreamingResponse(generate(), media_type="text/plain")


@app.post("/api/analyse")
async def analyse_role(request: AnalyseRequest):
    if not request.job_description.strip():
        raise HTTPException(status_code=400, detail="No job description provided")

    prompt = f"""A recruiter or hiring manager has shared a job description. Analyse the fit between this role and Adam's background.

Structure your response exactly as follows:

**Overall fit**
One clear sentence. Be direct — strong, moderate, or limited, and why.

**Strong matches**
Specific evidence from Adam's background that maps to this role's requirements. Cite concrete examples, not generalities.

**Genuine gaps**
Honest assessment of where Adam's background doesn't fully match what's being asked for. Don't spin these.

**The angle to lead with**
What Adam should emphasise in conversation with this company — the thread that makes his application stand out for this specific role.

Job description:
{request.job_description}"""

    def generate():
        with client.messages.stream(
            model=MODEL,
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            for text in stream.text_stream:
                yield text

    return StreamingResponse(generate(), media_type="text/plain")


@app.get("/api/health")
async def health():
    return {"status": "ok", "model": MODEL}


# Serve frontend
FRONTEND = Path(__file__).parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=FRONTEND), name="static")

@app.get("/")
async def root():
    return FileResponse(FRONTEND / "index.html")
