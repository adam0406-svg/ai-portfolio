"""
AI Pulse — Backend API
FastAPI server that powers the dashboard.

Pipeline:
  Scout (HN + Reddit + RSS Publications) → Curator (filter) → Briefer (summarise) → Dashboard

Sources:
  - Hacker News: top AI stories from the tech community
  - Reddit: business and AI-focused subreddits
  - RSS: VentureBeat, TechCrunch, MIT Tech Review, The Verge, O'Reilly, Google News

Endpoints:
  GET /api/digest   — Run the full 3-agent pipeline
  GET /api/buzzword — Get today's AI buzzword flashcard
  GET /            — Serve the frontend HTML
"""

import asyncio
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from sources.hackernews import get_hn_ai_stories
from sources.reddit import get_reddit_ai_stories
from sources.rss_feeds import get_rss_stories
from agents.curator_agent import run_curator_agent
from agents.briefer_agent import run_briefer_agent
from agents.buzzword_agent import run_buzzword_agent

load_dotenv()

app = FastAPI(title="AI Pulse API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_PATH = Path(__file__).parent.parent / "frontend" / "index.html"


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    if not FRONTEND_PATH.exists():
        raise HTTPException(status_code=404, detail="Frontend not found")
    return HTMLResponse(content=FRONTEND_PATH.read_text(encoding="utf-8"))


@app.get("/api/digest")
async def get_digest():
    """
    Runs the full 3-agent pipeline:
      1. Scout: fetch stories from HN + Reddit in parallel
      2. Curator: filter to high-signal AI knowledge stories
      3. Briefer: write expert-level briefings for approved stories
    """
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(
            status_code=500,
            detail="ANTHROPIC_API_KEY not set. Add it to your .env file."
        )

    # ── AGENT 1: SCOUT ──────────────────────────────
    # return_exceptions=True means a timeout on one source won't crash the others
    results = await asyncio.gather(
        get_hn_ai_stories(limit=12),
        get_reddit_ai_stories(limit_per_sub=4),
        get_rss_stories(),
        return_exceptions=True
    )
    all_stories = []
    for r in results:
        if isinstance(r, list):
            all_stories.extend(r)
        # If it's an exception (timeout, network error), silently skip that source

    if not all_stories:
        raise HTTPException(status_code=503, detail="Could not fetch stories from any source — check your internet connection")

    # ── AGENT 2: CURATOR ─────────────────────────────
    # Filters to only high-signal stories relevant to AI expertise
    curator_output = await run_curator_agent(all_stories)

    if not curator_output["stories"]:
        raise HTTPException(status_code=200, detail="No high-signal stories found today")

    # ── AGENT 3: BRIEFER ─────────────────────────────
    # Writes expert briefings for the curated stories
    digest = await run_briefer_agent(curator_output)

    return JSONResponse(content=digest)


@app.get("/api/buzzword")
async def get_buzzword():
    """
    Returns today's AI buzzword as a flashcard.
    Same term all day, changes at midnight.
    """
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(
            status_code=500,
            detail="ANTHROPIC_API_KEY not set. Add it to your .env file."
        )

    flashcard = await run_buzzword_agent()
    return JSONResponse(content=flashcard)


@app.get("/api/health")
async def health():
    return {"status": "ok", "anthropic_key_set": bool(os.getenv("ANTHROPIC_API_KEY"))}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
