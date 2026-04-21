"""
RSS source — comprehensive coverage across:
  - Business & consulting (HBR, McKinsey, Deloitte, WEF, MIT Sloan)
  - AI-specific publications (VentureBeat, AI Business, The Batch)
  - Tech news with business lens (Wired, Ars Technica, Fast Company, Axios)
  - AI lab blogs (OpenAI, Anthropic, Google, Meta, Microsoft, HuggingFace)
  - Industry verticals (healthcare, legal, finance, HR)
  - Google News targeted queries (case studies, ROI, agent deployments)
All fetched in parallel — adding more sources doesn't slow things down.
"""

import httpx
import asyncio
from typing import List, Dict
from xml.etree import ElementTree as ET
import re

RSS_FEEDS = [

    # ── BUSINESS & CONSULTING ─────────────────────────────────────────
    {
        "url": "https://feeds.hbr.org/harvardbusiness",
        "source": "Harvard Business Review",
    },
    {
        "url": "https://sloanreview.mit.edu/feed/",
        "source": "MIT Sloan Review",
    },
    {
        "url": "https://www.mckinsey.com/rss/insights.rss",
        "source": "McKinsey Insights",
    },
    {
        "url": "https://www2.deloitte.com/us/en/insights/rss.html",
        "source": "Deloitte Insights",
    },
    {
        "url": "https://www.weforum.org/agenda/artificial-intelligence/rss.xml",
        "source": "World Economic Forum AI",
    },
    {
        "url": "https://www.cio.com/feed/",
        "source": "CIO Magazine",
    },
    {
        "url": "https://www.gartner.com/en/newsroom/rss",
        "source": "Gartner",
    },

    # ── AI-SPECIFIC PUBLICATIONS ──────────────────────────────────────
    {
        "url": "https://venturebeat.com/category/ai/feed/",
        "source": "VentureBeat AI",
    },
    {
        "url": "https://aibusiness.com/feed",
        "source": "AI Business",
    },
    {
        "url": "https://www.artificialintelligence-news.com/feed/",
        "source": "AI News",
    },
    {
        "url": "https://www.therundown.ai/feed",
        "source": "The Rundown AI",
    },
    {
        "url": "https://www.bensbites.com/feed",
        "source": "Ben's Bites",
    },

    # ── TECH & BUSINESS NEWS ──────────────────────────────────────────
    {
        "url": "https://www.wired.com/feed/category/artificial-intelligence/latest/rss",
        "source": "Wired AI",
    },
    {
        "url": "https://feeds.arstechnica.com/arstechnica/technology-lab",
        "source": "Ars Technica",
    },
    {
        "url": "https://www.fastcompany.com/technology/rss",
        "source": "Fast Company Tech",
    },
    {
        "url": "https://api.axios.com/feed/",
        "source": "Axios",
    },
    {
        "url": "https://www.zdnet.com/topic/artificial-intelligence/rss.xml",
        "source": "ZDNet AI",
    },
    {
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "source": "TechCrunch AI",
    },
    {
        "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        "source": "The Verge AI",
    },
    {
        "url": "https://feeds.reuters.com/reuters/technologyNews",
        "source": "Reuters Technology",
    },
    {
        "url": "https://www.technologyreview.com/feed/",
        "source": "MIT Tech Review",
    },

    # ── AI LAB BLOGS (for major releases only — Curator filters the rest) ──
    {
        "url": "https://openai.com/blog/rss.xml",
        "source": "OpenAI Blog",
    },
    {
        "url": "https://www.anthropic.com/rss.xml",
        "source": "Anthropic Blog",
    },
    {
        "url": "https://blog.google/technology/ai/rss/",
        "source": "Google AI Blog",
    },
    {
        "url": "https://ai.meta.com/blog/rss/",
        "source": "Meta AI Blog",
    },
    {
        "url": "https://blogs.microsoft.com/ai/feed/",
        "source": "Microsoft AI Blog",
    },
    {
        "url": "https://huggingface.co/blog/feed.xml",
        "source": "Hugging Face Blog",
    },
    {
        "url": "https://deepmind.google/blog/rss.xml",
        "source": "Google DeepMind Blog",
    },

    # ── INDUSTRY VERTICALS ────────────────────────────────────────────
    {
        "url": "https://www.healthcareitnews.com/feed",
        "source": "Healthcare IT News",
    },
    {
        "url": "https://www.artificiallawyer.com/feed/",
        "source": "Artificial Lawyer",
    },
    {
        "url": "https://www.fintechfutures.com/feed/",
        "source": "FinTech Futures",
    },
    {
        "url": "https://www.shrm.org/rss/pages/rss.aspx",
        "source": "SHRM (HR & Work)",
    },

    # ── GOOGLE NEWS: TARGETED QUERIES ────────────────────────────────
    # These sweep Bloomberg, WSJ, FT, Forbes, Business Insider, etc.
    {
        "url": "https://news.google.com/rss/search?q=%22AI+case+study%22+OR+%22AI+deployment%22&hl=en-US&gl=US&ceid=US:en",
        "source": "Google News: AI Case Studies",
    },
    {
        "url": "https://news.google.com/rss/search?q=%22AI+agent%22+OR+%22agentic+AI%22+company+business&hl=en-US&gl=US&ceid=US:en",
        "source": "Google News: AI Agents",
    },
    {
        "url": "https://news.google.com/rss/search?q=enterprise+AI+%22use+case%22+OR+%22ROI%22+OR+%22saves%22&hl=en-US&gl=US&ceid=US:en",
        "source": "Google News: Enterprise AI ROI",
    },
    {
        "url": "https://news.google.com/rss/search?q=AI+healthcare+OR+legal+OR+finance+OR+HR+deployment&hl=en-US&gl=US&ceid=US:en",
        "source": "Google News: AI by Industry",
    },
    {
        "url": "https://news.google.com/rss/search?q=%22AI+automation%22+OR+%22AI+workflow%22+company+results&hl=en-US&gl=US&ceid=US:en",
        "source": "Google News: AI Automation",
    },
    {
        "url": "https://news.google.com/rss/search?q=AI+strategy+executives+OR+%22chief+AI+officer%22+OR+%22AI+transformation%22&hl=en-US&gl=US&ceid=US:en",
        "source": "Google News: AI Leadership",
    },
    {
        "url": "https://news.google.com/rss/search?q=AI+productivity+%22saves+time%22+OR+%22cuts+costs%22+OR+%22reduces%22+2025&hl=en-US&gl=US&ceid=US:en",
        "source": "Google News: AI Productivity",
    },

]


def clean_html(text: str) -> str:
    if not text:
        return ""
    clean = re.sub(r'<[^>]+>', '', text)
    clean = re.sub(r'&amp;', '&', clean)
    clean = re.sub(r'&lt;', '<', clean)
    clean = re.sub(r'&gt;', '>', clean)
    clean = re.sub(r'&#\d+;', '', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean[:400]


def parse_feed(xml_text: str, source_name: str) -> List[Dict]:
    stories = []
    try:
        root = ET.fromstring(xml_text)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}

        # RSS format
        items = root.findall('.//item')
        for item in items[:8]:
            title_el = item.find('title')
            link_el = item.find('link')
            desc_el = item.find('description')

            title = clean_html(title_el.text or "") if title_el is not None else ""
            url = (link_el.text or "").strip() if link_el is not None else ""
            desc = clean_html(desc_el.text if desc_el is not None else "")

            if not title or not url or len(title) < 10:
                continue

            stories.append({
                "title": title,
                "url": url,
                "source": source_name,
                "score": 0,
                "comments": 0,
                "selftext": desc,
            })

        # Atom format fallback
        if not stories:
            for entry in root.findall('.//atom:entry', ns)[:8]:
                title_el = entry.find('atom:title', ns)
                link_el = entry.find('atom:link', ns)
                summary_el = entry.find('atom:summary', ns)

                title = clean_html(title_el.text or "") if title_el is not None else ""
                url = link_el.get('href', '') if link_el is not None else ""
                desc = clean_html(summary_el.text if summary_el is not None else "")

                if not title or not url or len(title) < 10:
                    continue

                stories.append({
                    "title": title,
                    "url": url,
                    "source": source_name,
                    "score": 0,
                    "comments": 0,
                    "selftext": desc,
                })

    except ET.ParseError:
        pass

    return stories


async def fetch_feed(client: httpx.AsyncClient, feed: dict) -> List[Dict]:
    try:
        resp = await client.get(
            feed["url"],
            timeout=12,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; AI-Pulse/1.0)"}
        )
        return parse_feed(resp.text, feed["source"])
    except Exception:
        return []


async def get_rss_stories() -> List[Dict]:
    # All feeds fetched simultaneously — parallel means 40 sources
    # takes the same time as 1
    async with httpx.AsyncClient(trust_env=False) as client:
        tasks = [fetch_feed(client, feed) for feed in RSS_FEEDS]
        results = await asyncio.gather(*tasks)

    all_stories = []
    seen = set()
    for stories in results:
        for s in stories:
            key = s["title"].lower()[:60]
            if key not in seen and len(key) > 10:
                seen.add(key)
                all_stories.append(s)

    return all_stories
