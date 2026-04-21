"""
Tools — what the agents can actually do beyond generating text.
──────────────────────────────────────────────────────────────
The @tool decorator is how CrewAI knows a function is available
for agents to call autonomously. The agent reads the docstring
to decide WHEN and HOW to use each tool — so the docstring is
part of the agent's instructions, not just documentation.

We give the agents two tools:
  1. web_search   — broad search for any query
  2. search_news  — targeted recent news search

Having two separate tools lets agents make a deliberate choice:
"I need general background" vs "I need what happened recently."
That distinction produces better research than a single catch-all search.
"""

import os
from crewai.tools import tool
from tavily import TavilyClient


def get_tavily_client() -> TavilyClient:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY not set in .env")
    return TavilyClient(api_key=api_key)


@tool("Web Search")
def web_search(query: str) -> str:
    """
    Search the web for information about a company, person, product, or topic.
    Use this to find company overviews, product descriptions, key people,
    business model details, and background information.
    Input should be a specific, well-formed search query.
    """
    client = get_tavily_client()
    response = client.search(
        query=query,
        max_results=5,
        include_answer=True,
    )
    # Format results cleanly for the agent to read
    output = []
    if response.get("answer"):
        output.append(f"Summary: {response['answer']}\n")
    for r in response.get("results", []):
        output.append(
            f"Source: {r.get('url', '')}\n"
            f"Title: {r.get('title', '')}\n"
            f"Content: {r.get('content', '')}\n"
        )
    return "\n---\n".join(output) if output else "No results found."


@tool("News Search")
def search_news(query: str) -> str:
    """
    Search for recent news articles about a company or topic.
    Use this to find the latest developments, announcements, product launches,
    leadership changes, financial news, or any events from the past few months.
    Input should be a specific news-focused search query.
    """
    client = get_tavily_client()
    response = client.search(
        query=query,
        max_results=5,
        include_answer=True,
        topic="news",
    )
    output = []
    if response.get("answer"):
        output.append(f"News Summary: {response['answer']}\n")
    for r in response.get("results", []):
        output.append(
            f"Source: {r.get('url', '')}\n"
            f"Title: {r.get('title', '')}\n"
            f"Published: {r.get('published_date', 'Unknown date')}\n"
            f"Content: {r.get('content', '')}\n"
        )
    return "\n---\n".join(output) if output else "No recent news found."
