"""
Reddit source — uses the public JSON API (no auth for read-only).
Uses 'new' sorting to ensure recency, then filters by age.
"""

import httpx
import asyncio
import time
from typing import List, Dict

MAX_AGE_HOURS = 24 * 30  # 30 days

# Subreddits chosen for business-relevant AI discussion
SUBREDDITS = [
    "artificial",          # General AI news and discussion — highest signal
    "singularity",         # Big-picture AI industry shifts and impact
    "MachineLearning",     # Major model and research announcements
    "Entrepreneur",        # Business owners discussing real AI adoption
    "business",            # Business community reacting to AI developments
    "technology",          # Broad tech news — filter catches AI stories
    "Futurology",          # Long-term AI impact and industry transformation
    "ChatGPTProTips",      # Real-world AI usage patterns in work contexts
    "AIAssistants",        # Practical AI tool usage and business applications
]

HEADERS = {
    "User-Agent": "AI-Pulse-Dashboard/1.0 (portfolio project)"
}


async def get_subreddit_posts(client: httpx.AsyncClient, sub: str, limit: int = 8) -> List[Dict]:
    try:
        # Use 'new' not 'hot' — hot surfaces days-old posts
        url = f"https://www.reddit.com/r/{sub}/new.json?limit={limit}"
        resp = await client.get(url, headers=HEADERS, timeout=8, follow_redirects=True)
        data = resp.json()
        posts = data.get("data", {}).get("children", [])

        cutoff = time.time() - (MAX_AGE_HOURS * 3600)
        results = []

        for post in posts:
            p = post.get("data", {})
            if p.get("stickied"):
                continue
            if p.get("is_self") and not p.get("selftext"):
                continue
            # Drop posts older than 48 hours
            if p.get("created_utc", 0) < cutoff:
                continue
            results.append({
                "id": p.get("id"),
                "title": p.get("title", ""),
                "url": f"https://reddit.com{p.get('permalink', '')}",
                "score": p.get("score", 0),
                "comments": p.get("num_comments", 0),
                "by": p.get("author", ""),
                "source": f"r/{sub}",
                "selftext": (p.get("selftext") or "")[:400],
            })
        return results
    except Exception:
        return []


async def get_reddit_ai_stories(limit_per_sub: int = 6) -> List[Dict]:
    async with httpx.AsyncClient(trust_env=False) as client:
        tasks = [get_subreddit_posts(client, sub, limit_per_sub) for sub in SUBREDDITS]
        results = await asyncio.gather(*tasks)

    all_posts = []
    seen = set()
    for posts in results:
        for p in posts:
            if p["id"] not in seen:
                seen.add(p["id"])
                all_posts.append(p)

    all_posts.sort(key=lambda x: x["score"], reverse=True)
    return all_posts[:15]
