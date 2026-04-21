"""
Agents — four specialist roles in the research crew.
──────────────────────────────────────────────────────────────
Pipeline:
  1. Researcher    → searches the web, gathers raw intelligence
  2. Writer        → structures research into a clean briefing
  3. Strategist    → personalises the angle to YOUR company's offering
  4. Devil's Adv.  → challenges the briefing, prepares you for pushback
"""

import os
from crewai import Agent, LLM
from .tools import web_search, search_news

llm = LLM(
    model="anthropic/claude-opus-4-5",
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    temperature=0.2,
)


def make_researcher() -> Agent:
    return Agent(
        role="Senior Business Research Analyst",
        goal=(
            "Gather comprehensive, accurate, and business-relevant intelligence "
            "about a company — their business model, recent developments, "
            "key leadership, products, and visible operational challenges."
        ),
        backstory=(
            "You are a senior analyst with 12 years of B2B competitive intelligence "
            "experience. You search multiple angles before drawing conclusions and "
            "always flag uncertainty rather than filling gaps with assumptions. "
            "You write in plain, direct language."
        ),
        tools=[web_search, search_news],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=6,
    )


def make_writer() -> Agent:
    return Agent(
        role="Business Intelligence Report Writer",
        goal=(
            "Transform raw research into a clear, structured, and actionable "
            "company briefing that prepares a professional for a first meeting."
        ),
        backstory=(
            "You specialise in executive briefings and commercial intelligence reports. "
            "You know busy professionals need context first, then what matters now, "
            "then what to do with it. Every sentence earns its place or gets cut."
        ),
        tools=[],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=3,
    )


def make_strategist(company_profile: str = "") -> Agent:
    profile_context = (
        f"The seller's company profile: {company_profile}"
        if company_profile
        else "No specific seller profile provided — give a general strategic recommendation."
    )
    return Agent(
        role="Sales Strategist",
        goal=(
            "Analyse the company briefing and produce a sharp, personalised "
            "sales strategy — how to position the conversation, what angle to lead "
            "with, and why this prospect should care."
        ),
        backstory=(
            f"You are a senior sales strategist with 15 years in B2B enterprise sales. "
            f"You turn research into winning commercial approaches. "
            f"{profile_context} "
            f"You think in terms of buyer psychology, business value, and timing. "
            f"You never recommend generic pitches — every recommendation is specific "
            f"to this company's situation right now."
        ),
        tools=[],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=3,
    )


def make_devil() -> Agent:
    return Agent(
        role="Devil's Advocate",
        goal=(
            "Challenge the briefing and sales strategy. Identify likely objections, "
            "expose assumptions, flag risks, and stress-test the approach so the "
            "seller walks in prepared for the hardest questions."
        ),
        backstory=(
            "You are a seasoned procurement director and former consultant who has "
            "sat on the other side of the table in hundreds of vendor meetings. "
            "You know every deflection tactic, every red flag, and every way a "
            "promising deal falls apart. You are not cynical — you are rigorous. "
            "Your job is to make the seller's preparation bulletproof by exposing "
            "every weak point before the meeting."
        ),
        tools=[],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=3,
    )
