"""
Research Crew — 4-agent sequential pipeline.
─────────────────────────────────────────────
Pipeline: Researcher → Writer → Strategist → Devil's Advocate

Each agent's output feeds the next via `context`.
The final merged result includes the briefing, strategy, and challenge sections.
"""

import json
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor
from crewai import Crew, Process

from .agents import make_researcher, make_writer, make_strategist, make_devil
from .tasks import (
    make_research_task,
    make_briefing_task,
    make_strategy_task,
    make_challenge_task,
)

_executor = ThreadPoolExecutor(max_workers=3)


def _strip_json(raw: str) -> str:
    """
    Extract the first JSON object from raw LLM output.
    Handles: plain JSON, ```json...```, text before/after the object.
    """
    raw = raw.strip()
    # Remove any code-fence wrappers first
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"\s*```\s*$", "", raw, flags=re.MULTILINE)
    raw = raw.strip()
    # Grab the first complete {...} block (handles leading/trailing prose)
    match = re.search(r"\{[\s\S]*\}", raw)
    if match:
        return match.group(0)
    return raw


def _safe_parse(raw: str, label: str) -> dict:
    """Parse JSON with a helpful fallback so one bad agent doesn't kill the whole run."""
    try:
        return json.loads(_strip_json(raw))
    except Exception as exc:
        print(f"[WARN] Could not parse {label} JSON ({exc}). Raw snippet: {raw[:300]!r}")
        return {}


def _run_crew_sync(company: str, company_profile: str = "") -> dict:
    researcher  = make_researcher()
    writer      = make_writer()
    strategist  = make_strategist(company_profile)
    devil       = make_devil()

    research_task  = make_research_task(researcher, company)
    briefing_task  = make_briefing_task(writer, research_task, company)
    strategy_task  = make_strategy_task(strategist, briefing_task, company)
    challenge_task = make_challenge_task(devil, briefing_task, strategy_task, company)

    crew = Crew(
        agents=[researcher, writer, strategist, devil],
        tasks=[research_task, briefing_task, strategy_task, challenge_task],
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff()

    # Parse each task output — use _safe_parse so one bad agent doesn't crash everything
    challenge = _safe_parse(result.raw,              "challenge")
    briefing  = _safe_parse(briefing_task.output.raw, "briefing")
    strategy  = _safe_parse(strategy_task.output.raw, "strategy")

    merged = {**briefing, **strategy, **challenge}
    if not merged:
        raise ValueError("All three agents returned unparseable JSON — check verbose logs above.")
    return merged


async def run_research_crew(company: str, company_profile: str = "") -> dict:
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        _executor,
        _run_crew_sync,
        company,
        company_profile,
    )
    return result
