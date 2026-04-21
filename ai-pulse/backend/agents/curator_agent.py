"""
Agent 2: Curator
─────────────────────────────────────────────────────────────────
WHAT IT DOES:
  Takes raw stories from the Scout (HN + Reddit) and decides
  which ones actually matter for someone building deep AI expertise.

HOW IT'S "TRAINED":
  It isn't trained — Claude is already a foundation model.
  What we do instead is give it a SYSTEM PROMPT that defines:
    - Its role and mindset
    - A knowledge map of topics that matter
    - Explicit rules for what to filter out
    - The exact output format we expect (JSON)

  The system prompt is the core of agent design. It's the
  closest thing to "training" in applied AI work.

WHERE IT LIVES:
  Just a Python function. It calls the Anthropic API, gets
  a response, parses it, and hands clean data to the next agent.

HOW WE OPTIMIZE IT:
  1. System prompt clarity — specific rules outperform vague ones
  2. Model choice — claude-opus for intelligence, haiku for speed
  3. Structured output — JSON schema enforced in the prompt
  4. Temperature=0 — for filtering/scoring we want determinism,
     not creativity. Always 0 for analytical tasks.
"""

import anthropic
import json
from typing import List, Dict

# ─────────────────────────────────────────────
# THE KNOWLEDGE MAP
# This is the reference point the Curator uses to judge relevance.
# It's not magic — it's just a list we've defined.
# The more precise this is, the better the filtering.
# ─────────────────────────────────────────────
AI_KNOWLEDGE_MAP = {
    "Business Use Cases & ROI": [
        "enterprise AI adoption", "AI use case", "business case for AI",
        "AI return on investment", "AI cost savings", "productivity gains",
        "AI implementation", "AI strategy", "AI transformation",
        "workflow automation", "process automation", "AI pilot",
        "AI deployment at scale", "AI in the workplace",
    ],
    "Industry Applications": [
        "AI in healthcare", "AI in finance", "AI in legal", "AI in HR",
        "AI in customer service", "AI in sales", "AI in marketing",
        "AI in supply chain", "AI in education", "AI in retail",
        "AI in manufacturing", "AI in real estate", "AI in consulting",
        "AI in operations", "AI in logistics", "AI in insurance",
    ],
    "AI Tools & Products": [
        "new AI product", "AI assistant", "AI agent", "AI copilot",
        "ChatGPT", "Claude", "Gemini", "Copilot", "Perplexity",
        "AI for business", "SaaS AI", "AI platform", "no-code AI",
        "AI integration", "API release", "model release", "product launch",
    ],
    "Agentic AI & Automation": [
        "AI agent", "agentic AI", "autonomous AI", "AI workflow",
        "AI automation", "multi-agent", "AI assistant", "AI doing tasks",
        "AI replacing jobs", "AI augmenting workers", "human in the loop",
        "AI decision making", "AI operating independently",
    ],
    "AI Leadership & Strategy": [
        "AI strategy", "AI governance", "AI policy", "AI regulation",
        "AI ethics", "responsible AI", "AI risk", "AI leadership",
        "chief AI officer", "AI team structure", "AI roadmap",
        "AI adoption challenges", "change management AI",
        "AI skills gap", "AI talent", "AI investment",
    ],
    "What AI Can & Cannot Do": [
        "AI capabilities", "AI limitations", "AI benchmark", "model comparison",
        "AI performance", "AI reasoning", "AI accuracy", "AI hallucination",
        "when to use AI", "AI best practices", "AI failure cases",
        "AI vs human", "AI reliability", "AI trust",
    ],
}

# Flatten for the prompt
KNOWLEDGE_MAP_TEXT = "\n".join(
    f"  • {category}: {', '.join(topics)}"
    for category, topics in AI_KNOWLEDGE_MAP.items()
)

# ─────────────────────────────────────────────
# THE SYSTEM PROMPT
# This is what "programs" the Curator agent.
# Notice: it has a clear role, explicit rules, and a strict output format.
# ─────────────────────────────────────────────
CURATOR_SYSTEM_PROMPT = """You are a curator for an AI generalist — someone who advises organisations on how to use AI. Your reader is NOT an AI engineer. They want to understand how AI creates value in the real world, not how it works under the hood.

You have a knowledge map of relevant topics:
{knowledge_map}

PRIORITY SYSTEM — use this exact order when deciding what to accept:

TIER 1 — ALWAYS ACCEPT (these are exactly what the reader needs):
  • A named company or organisation used AI to solve a specific problem — especially if it includes outcomes, metrics, or lessons learned
  • A real AI agent or automation deployed inside a business workflow
  • An industry (healthcare, legal, finance, HR, sales, operations etc.) adopting AI in a concrete way
  • A case study, post-mortem, or "what we learned" story about an AI deployment
  • AI changing jobs, workflows, or team structures inside real organisations

TIER 2 — ACCEPT IF GENUINELY SIGNIFICANT:
  • A major new AI model launch from a top lab (OpenAI, Anthropic, Google, Meta) — only if it represents a meaningful capability leap
  • A new AI tool or platform that business teams would actually use
  • A significant change to how AI agents work (e.g. major new MCP capability, breakthrough in agentic reasoning)
  • AI regulation or governance news that affects how businesses can use AI

TIER 3 — REJECT UNLESS EXCEPTIONAL:
  • Technical AI research with no clear business application mentioned
  • Model architecture papers, training techniques, benchmark results
  • Product updates that are minor features, not capability changes
  • Anything about AI in consumer apps (phone features, gaming, social media)

ALWAYS REJECT:
  • Hype and speculation without concrete examples or named organisations
  • Funding rounds and acquisitions unless the story explains the specific AI product and its real-world use
  • Beginner explainer content ("What is AI?", "How does ChatGPT work?")
  • Duplicate or near-duplicate stories
  • Anything older than 48 hours or clearly outdated

Your goal: return 5-7 stories where at least 4 of them are Tier 1. If you cannot find 4 Tier 1 stories in the batch, return fewer stories — do not pad with Tier 3 content.

For each accepted story assign:
- relevance_score: 1-10 (10 = concrete business use case with outcomes, 5 = major model launch, 3 = general industry commentary)
- knowledge_category: one category from the knowledge map
- signal_reason: one sentence — name the company/industry and state the specific value or lesson"""


def build_stories_text(stories: List[Dict]) -> str:
    lines = []
    for i, s in enumerate(stories, 1):
        lines.append(
            f"{i}. [{s['source']}] {s['title']}\n"
            f"   URL: {s['url']}\n"
            f"   Score: {s.get('score', 0)} | Comments: {s.get('comments', 0)}"
        )
        if s.get("selftext"):
            lines.append(f"   Preview: {s['selftext'][:300]}")
    return "\n\n".join(lines)


async def run_curator_agent(stories: List[Dict]) -> List[Dict]:
    """
    Takes raw stories, returns only the ones worth knowing about.
    Each returned story has relevance_score, knowledge_category, signal_reason added.
    """
    client = anthropic.Anthropic()

    # Notice: system prompt is separate from the user message.
    # This is the correct way to use the API — system = agent instructions,
    # user = the actual data to process.
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=3000,
        temperature=0,          # 0 = deterministic. Right for filtering/scoring tasks.
        system=CURATOR_SYSTEM_PROMPT.format(knowledge_map=KNOWLEDGE_MAP_TEXT),
        messages=[{
            "role": "user",
            "content": f"""Here are {len(stories)} raw stories to curate. Apply your filtering rules and return only the high-signal ones.

{build_stories_text(stories)}

Respond with valid JSON only — no markdown, no explanation outside the JSON.

{{
  "accepted": [
    {{
      "title": "exact original title",
      "url": "exact original url",
      "source": "exact original source",
      "score": original_score_number,
      "comments": original_comments_number,
      "relevance_score": 1-10,
      "knowledge_category": "category from knowledge map",
      "signal_reason": "one sentence: why this matters for AI expertise"
    }}
  ],
  "rejected_count": number_of_rejected_stories,
  "rejection_summary": "one sentence summary of what was filtered out and why"
}}"""
        }]
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    result = json.loads(raw)

    # Sort by relevance score descending
    accepted = result.get("accepted", [])
    accepted.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

    # Attach metadata for the next agent to use
    return {
        "stories": accepted,
        "rejected_count": result.get("rejected_count", 0),
        "rejection_summary": result.get("rejection_summary", ""),
        "total_input": len(stories),
    }
