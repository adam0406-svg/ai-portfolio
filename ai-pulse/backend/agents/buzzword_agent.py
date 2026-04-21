"""
Buzzword Agent — generates a set of 8 daily AI flashcards.
Terms are seeded to today's date so the same set appears all day,
and a fresh set rotates in every morning.

Each flashcard includes a read_more_url pointing to the best
resource to go deeper on that term.
"""

import anthropic
import json
import hashlib
from datetime import date

CARDS_PER_DAY = 8

TERM_POOL = [
    "Retrieval-Augmented Generation (RAG)", "Vector Database", "Embedding",
    "Fine-tuning", "RLHF", "Constitutional AI", "Chain-of-Thought Prompting",
    "Function Calling", "MCP (Model Context Protocol)", "Agent Loop",
    "Context Window", "Temperature (LLMs)", "Token", "Hallucination",
    "Grounding", "Multimodal", "Mixture of Experts (MoE)", "Quantization",
    "LoRA / QLoRA", "Prompt Injection", "System Prompt",
    "Semantic Search", "Attention Mechanism",
    "Transformer Architecture", "In-Context Learning", "Few-Shot Prompting",
    "Zero-Shot Prompting", "Guardrails", "LLM Orchestration",
    "Knowledge Graph", "Agentic AI", "Tool Use", "ReAct Pattern",
    "Structured Output", "Model Router", "Foundation Model",
    "Model Distillation", "Evals", "Red Teaming",
    "AI Safety", "Alignment", "Emergent Behavior", "Scaling Laws",
    "Prompt Engineering", "Chunking Strategy", "Hybrid Search",
    "Reranking", "AI Agent", "Autonomous AI", "AI Workflow Automation",
    "AI Governance", "Responsible AI", "AI ROI", "AI Strategy",
    "Prompt Chaining", "LangChain", "LangGraph", "CrewAI",
    "Semantic Kernel", "OpenAI API", "Anthropic API", "Inference",
    "Tokenizer", "Benchmark (AI)", "Leaderboard (AI)", "MMLU",
    "GPT-4", "Claude", "Gemini", "Llama", "Mistral",
    "AI Copilot", "AI Assistant", "Knowledge Base (AI)",
    "Document AI", "Multimodal AI", "Vision Language Model",
    "AI in Healthcare", "AI in Legal", "AI in Finance",
    "AI in HR", "AI in Customer Service", "AI in Sales",
    "Process Automation", "Intelligent Automation", "RPA vs AI",
    "AI Pilot", "AI at Scale", "Change Management (AI)",
    "AI Skills Gap", "Prompt Library", "System Design (AI)",
]


def pick_terms_for_today(n: int) -> list:
    """Pick n unique terms seeded to today's date."""
    today_str = date.today().isoformat()
    seed = int(hashlib.md5(today_str.encode()).hexdigest(), 16)
    indices = []
    offset = 0
    while len(indices) < n:
        idx = (seed + offset) % len(TERM_POOL)
        if idx not in indices:
            indices.append(idx)
        offset += 1
    return [TERM_POOL[i] for i in indices]


async def run_buzzword_agent() -> dict:
    terms = pick_terms_for_today(CARDS_PER_DAY)
    client = anthropic.Anthropic()
    today = date.today().strftime("%B %d, %Y")

    terms_list = "\n".join(f"{i+1}. {t}" for i, t in enumerate(terms))

    prompt = f"""You are an AI educator creating daily flashcards for someone becoming an AI generalist — they work with businesses, not as an engineer. Keep explanations practical and business-grounded.

Today's date: {today}
Today's terms to create flashcards for:
{terms_list}

For each term create a flashcard. Be concrete — no jargon without explanation, no corporate fluff.

For read_more_url: provide the single best URL to learn more — prefer official docs, Wikipedia, or a well-known authoritative article. Must be a real, specific URL (not a search query).

Respond with valid JSON only. No markdown. No explanation outside the JSON.

{{
  "flashcards": [
    {{
      "term": "exact term from the list",
      "one_liner": "one sentence — plain English definition someone could repeat in a meeting",
      "example": "one concrete real-world example — name an actual company, product, or industry scenario",
      "why_it_matters": "one sentence — why an AI generalist working with businesses needs to know this",
      "difficulty": "Beginner | Intermediate | Advanced",
      "read_more_url": "https://..."
    }}
  ]
}}"""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    return json.loads(raw)
