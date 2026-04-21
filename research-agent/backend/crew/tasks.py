"""
Tasks — four sequential assignments, each building on the last.
──────────────────────────────────────────────────────────────
Pipeline:
  1. Research task   → raw intelligence gathering
  2. Briefing task   → structured company brief (uses research)
  3. Strategy task   → personalised sales angle (uses brief)
  4. Challenge task  → devil's advocate stress test (uses brief + strategy)
"""

from crewai import Task


def make_research_task(researcher, company: str) -> Task:
    return Task(
        description=f"""
Research the company "{company}" across five areas:

1. COMPANY OVERVIEW — what they do, business model, market position, size indicators
2. RECENT NEWS — last 6 months: launches, leadership changes, funding, controversies
3. KEY PEOPLE — CEO and relevant C-suite: name, title, one notable fact each
4. PRODUCTS & SERVICES — core offering, differentiators, known tech stack
5. PAIN POINTS — visible challenges: customer complaints, market pressures, strategic risks

Search multiple angles. Flag uncertainty rather than guessing.
        """,
        expected_output="Comprehensive research notes covering all five areas with at least 3 news items, 2 key people, and 3 pain points.",
        agent=researcher,
    )


def make_briefing_task(writer, research_task: Task, company: str) -> Task:
    return Task(
        description=f"""
Using the research provided, write a complete company briefing for "{company}".

Output ONLY a single valid JSON object with this exact structure:

{{
  "company_name": "official company name",
  "tagline": "one sentence capturing what the company does and who for",
  "overview": "2-3 paragraph company overview",
  "recent_news": [
    {{"headline": "brief headline", "summary": "1-2 sentence summary", "significance": "why this matters for a business conversation"}}
  ],
  "key_people": [
    {{"name": "full name", "title": "job title", "note": "1-2 sentences useful before meeting them"}}
  ],
  "products_services": "2-3 sentence summary of core offering and differentiators",
  "pain_points": [
    {{"area": "short label", "description": "1-2 sentence description of the challenge"}}
  ],
  "engagement_angle": "2-3 sentences on how to position a conversation with this company",
  "talking_points": ["point 1", "point 2", "point 3", "point 4", "point 5"]
}}

Rules: output ONLY the JSON. No markdown fences. All fields required.
recent_news: 3+ items. key_people: 2+ items. pain_points: 3+ items. talking_points: exactly 5.
        """,
        expected_output="A single valid JSON object with all required fields populated.",
        agent=writer,
        context=[research_task],
    )


def make_strategy_task(strategist, briefing_task: Task, company: str) -> Task:
    return Task(
        description=f"""
You have received a full company briefing for "{company}".
Analyse it and produce a sharp sales strategy.

Output ONLY a single valid JSON object:

{{
  "strategic_fit": "2-3 sentences: why is this company a strong commercial target right now, given their situation?",
  "tailored_pitch": "The single strongest opening message — specific to their pain points and current moment. One paragraph.",
  "recommended_approach": "Tactical advice: what to lead with, what NOT to say, what tone to strike, which stakeholder to target first.",
  "key_differentiators": [
    "specific differentiator 1 relevant to this company's situation",
    "specific differentiator 2",
    "specific differentiator 3"
  ],
  "best_timing": "Is now a good time to approach? Why or why not? What signals make this the right moment?"
}}

Rules: output ONLY the JSON. No markdown fences. All fields required.
Be specific to this company — no generic sales advice.
        """,
        expected_output="A valid JSON strategy object with all five fields populated and tailored specifically to this company.",
        agent=strategist,
        context=[briefing_task],
    )


def make_challenge_task(devil, briefing_task: Task, strategy_task: Task, company: str) -> Task:
    return Task(
        description=f"""
You have the full briefing and sales strategy for "{company}".
Your job is to stress-test both ruthlessly from the buyer's perspective.

Output ONLY a single valid JSON object:

{{
  "likely_objections": [
    {{
      "objection": "The exact pushback a decision-maker at this company will likely give",
      "counter": "The strongest, most specific response to this objection"
    }}
  ],
  "risk_flags": [
    {{
      "flag": "A specific risk or red flag in this deal or company situation",
      "why_it_matters": "What this could mean for the deal or the relationship"
    }}
  ],
  "intel_gaps": [
    "Area where the research was uncertain or thin — seller should verify before the meeting"
  ],
  "challenge_summary": "2-3 sentences: the single biggest challenge in this sale and what the seller needs to do about it."
}}

Rules: output ONLY the JSON. No markdown fences. All fields required.
likely_objections: 3 items minimum. risk_flags: 2 items minimum. intel_gaps: 2 items minimum.
Be specific — no generic sales objections. Root everything in this company's actual situation.
        """,
        expected_output="A valid JSON challenge object with objections, risk flags, intel gaps, and challenge summary all populated and company-specific.",
        agent=devil,
        context=[briefing_task, strategy_task],
    )
