"""
Digest Agent — the core AI layer.
Takes raw stories from multiple sources and uses Claude to:
1. Filter out noise / low-signal stories
2. Write a crisp 2-sentence summary for each
3. Categorize each story (Research, Product, Tooling, Debate, etc.)
4. Pick the single top story as the "Lead"
5. Write a short overall digest intro
"""

import anthropic
import json
from typing import List, Dict
from datetime import date


CATEGORIES = [
    "Research & Papers",
    "New Models",
    "Products & Launches",
    "Tools & Frameworks",
    "Industry & Business",
    "Community & Debate",
    "Tutorials & Learning",
]


def build_stories_text(stories: List[Dict]) -> str:
    lines = []
    for i, s in enumerate(stories, 1):
        lines.append(
            f"{i}. [{s['source']}] {s['title']}\n"
            f"   URL: {s['url']}\n"
            f"   Score: {s.get('score', 0)} | Comments: {s.get('comments', 0)}"
        )
        if s.get("selftext"):
            lines.append(f"   Preview: {s['selftext'][:200]}")
    return "\n".join(lines)


async def run_digest_agent(stories: List[Dict]) -> Dict:
    client = anthropic.Anthropic()
    today = date.today().strftime("%B %d, %Y")
    stories_text = build_stories_text(stories)

    prompt = f"""You are an AI news editor creating a daily digest for a developer who wants to stay current with AI.

Today is {today}.

Here are the raw stories fetched from Hacker News and Reddit:

{stories_text}

Your job:
1. Select the 6 most signal-rich stories (ignore duplicates, hype without substance, or off-topic posts)
2. For each selected story, write a tight 2-sentence summary that captures WHAT happened and WHY it matters
3. Assign each story one category from: {', '.join(CATEGORIES)}
4. Identify the single most important story as the "lead"
5. Write a 2-sentence overall digest intro that frames the day's AI landscape

Respond with valid JSON only. No markdown, no explanation outside the JSON.

{{
  "intro": "string — 2 sentences framing today in AI",
  "lead_index": 0,
  "stories": [
    {{
      "title": "original title from input",
      "url": "original url",
      "source": "original source",
      "summary": "2-sentence summary",
      "category": "one of the categories above",
      "score": original score number,
      "comments": original comments number
    }}
  ]
}}"""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    result = json.loads(raw)
    return result
