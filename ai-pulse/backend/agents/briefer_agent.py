"""
Agent 3: Briefer
─────────────────────────────────────────────────────────────────
WHAT IT DOES:
  Takes the Curator's approved, scored stories and writes
  expert-level briefings. Because the Curator already filtered
  the noise, this agent can focus entirely on depth and clarity.

KEY DESIGN DECISION — Why separate this from the Curator?
  If one agent filters AND writes summaries, it has to split
  its "attention" between two very different tasks. Separation
  means each agent can be optimised independently:
    - Curator: temperature=0, analytical, ruthless filter
    - Briefer: temperature=0.3, educational, precise writer
  You can also swap one out without touching the other.

HOW THE SYSTEM PROMPT DIFFERS:
  The Curator's prompt was about rules and judgment.
  The Briefer's prompt is about voice, depth, and format.
  Same technique (system prompt), different goal.
"""

import anthropic
import json
from typing import List, Dict
from datetime import date


BRIEFER_SYSTEM_PROMPT = """You are an AI strategist writing daily briefings for an AI generalist — someone who works at the intersection of AI and business, advising organisations on how to use AI effectively.

Your reader:
- Understands what AI is and how it works at a conceptual level, but is not an AI engineer
- Is most interested in HOW AI is being used in the real world, by which organisations, to solve what problems
- Wants to be able to walk into any business conversation about AI and contribute confidently
- Cares about practical outcomes: what worked, what didn't, what it cost, what it saved

Your writing rules:
- Lead with the real-world impact, not the technology
- Always ground the story in a concrete example: which company, which industry, what problem, what result
- Explain any technical terms briefly in plain language — assume the reader knows what an LLM is, but not what RAG is
- Connect every story to a business context: who would care about this and why
- Never use filler phrases like "it's worth noting" or "game-changer" or "revolutionary"
- Be direct and specific. Vague insights are worthless.

Format each briefing as exactly 3 sentences:
  Sentence 1: What happened — specific, factual, names the organisation or technology involved
  Sentence 2: The business significance — what problem this solves and who it affects
  Sentence 3: The broader implication — what this means for how organisations should think about or use AI"""


async def run_briefer_agent(curator_output: Dict) -> Dict:
    """
    Takes curator output, writes expert briefings for each story,
    adds a daily digest intro, and identifies the lead story.
    """
    stories = curator_output.get("stories", [])
    if not stories:
        return {"intro": "No high-signal stories found today.", "stories": [], "lead_index": 0}

    client = anthropic.Anthropic()
    today = date.today().strftime("%B %d, %Y")

    # Build a compact representation for the briefer
    # It only gets the accepted, scored stories — not the noise
    stories_text = "\n\n".join([
        f"Story {i+1}:\n"
        f"Title: {s['title']}\n"
        f"Source: {s['source']}\n"
        f"URL: {s['url']}\n"
        f"Category: {s['knowledge_category']}\n"
        f"Why it was selected: {s['signal_reason']}"
        for i, s in enumerate(stories)
    ])

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=3000,
        temperature=0.3,    # Slight creativity for writing quality, still mostly deterministic
        system=BRIEFER_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"""Today is {today}. Write expert briefings for these {len(stories)} curated AI stories.

{stories_text}

Also write:
1. A 2-sentence digest intro that frames the overall theme of today's AI landscape based on these stories
2. Identify which story index (0-based) is the lead — the single most important one for AI practitioners today

Respond with valid JSON only. No markdown outside the JSON.

{{
  "intro": "2-sentence framing of today in AI",
  "lead_index": 0,
  "briefings": [
    {{
      "story_index": 0,
      "briefing": "exactly 3 sentences as instructed"
    }}
  ]
}}"""
        }]
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    briefer_output = json.loads(raw)

    # Merge briefings back into stories
    briefings_map = {b["story_index"]: b["briefing"] for b in briefer_output.get("briefings", [])}
    for i, story in enumerate(stories):
        story["briefing"] = briefings_map.get(i, "")

    return {
        "intro": briefer_output.get("intro", ""),
        "lead_index": briefer_output.get("lead_index", 0),
        "stories": stories,
        # Pass through curator metadata so the UI can show it
        "pipeline_stats": {
            "total_fetched": curator_output.get("total_input", 0),
            "rejected": curator_output.get("rejected_count", 0),
            "accepted": len(stories),
            "rejection_summary": curator_output.get("rejection_summary", ""),
        }
    }
