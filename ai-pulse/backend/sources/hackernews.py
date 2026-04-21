"""
Hacker News source — uses the official free HN API.
No auth required. Fetches recent AI stories from the last 48 hours.
"""

import httpx
import asyncio
import time
from typing import List, Dict

HN_BASE = "https://hacker-news.firebaseio.com/v0"
MAX_AGE_HOURS = 24 * 30  # 30 days
CUTOFF = lambda: time.time() - (MAX_AGE_HOURS * 3600)

AI_KEYWORDS = [
    "ai", "llm", "gpt", "claude", "gemini", "openai", "anthropic", "deepmind",
    "machine learning", "agent", "rag", "chatgpt", "copilot",
    "artificial intelligence", "generative", "foundation model",
    "automation", "workflow", "enterprise ai", "ai tool", "ai model",
]


async def fetch_story(client: httpx.AsyncClient, story_id: int, cutoff: float) -> Dict | None:
    try:
        resp = await client.get(f"{HN_BASE}/item/{story_id}.json", timeout=8)
        story = resp.json()
        if not story or story.get("type") != "story" or not story.get("url"):
            return None
        # Drop anything older than 48 hours
        if story.get("time", 0) < cutoff:
            return None
        return {
            "id": story.get("id"),
            "title": story.get("title", ""),
            "url": story.get("url", ""),
            "score": story.get("score", 0),
            "comments": story.get("descendants", 0),
            "by": story.get("by", ""),
            "source": "Hacker News",
        }
    except Exception:
        return None


def is_ai_related(story: Dict) -> bool:
    title_lower = story["title"].lower()
    return any(kw in title_lower for kw in AI_KEYWORDS)


async def get_hn_ai_stories(limit: int = 8) -> List[Dict]:
    cutoff = CUTOFF()
    async with httpx.AsyncClient(trust_env=False) as client:
        # Check top 200 to find enough recent stories
        resp = await client.get(f"{HN_BASE}/topstories.json", timeout=10)
        top_ids = resp.json()[:200]

        tasks = [fetch_story(client, sid, cutoff) for sid in top_ids]
        all_stories = await asyncio.gather(*tasks)

    ai_stories = [s for s in all_stories if s and is_ai_related(s)]
    ai_stories.sort(key=lambda x: x["score"], reverse=True)
    return ai_stories[:limit]
