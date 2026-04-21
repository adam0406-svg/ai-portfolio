"""
Scorer Agent
─────────────────────────────────────────────────────────────
Takes the Analyst's findings and produces:
  - overall_score:    0–100 risk score (100 = highest risk)
  - risk_level:       Low | Medium | High | Critical
  - executive_summary: 2–3 sentence summary for a non-legal audience
  - negotiate_count:  how many findings are worth negotiating
  - sign_as_is:       boolean — would a lawyer recommend signing as-is?

Design decision — why separate from the Analyst?
  The Analyst's job is to find and explain individual risks in detail.
  The Scorer's job is to synthesise and make a judgment call on the whole.
  These are different cognitive tasks. Keeping them separate also means
  you can tune each prompt independently — the Analyst stays analytical,
  the Scorer stays executive-focused.
"""

import anthropic
import json
from typing import List, Dict

SCORER_SYSTEM_PROMPT = """You are a senior partner at a law firm giving a final verdict on a contract review.
You have just received a list of risk findings from a junior associate. Your job is to:

1. Score the overall risk of this contract from 0-100
   - 0-25: Low risk. Standard terms, minor issues. Generally safe to sign.
   - 26-50: Medium risk. Some concerns worth negotiating. Don't sign without addressing key issues.
   - 51-75: High risk. Multiple significant concerns. Substantial negotiation needed.
   - 76-100: Critical risk. Signing as-is would be inadvisable. Major renegotiation or rejection recommended.

2. Write an executive summary (2-3 sentences) that a CEO could read in 10 seconds.
   Name the top 1-2 risks specifically. No legal jargon.

3. Make a clear recommendation.

Base your score on: number of High findings, severity distribution, and whether risks are concentrated
in deal-critical areas (liability, IP, payment).

Respond with valid JSON only. No markdown.

{
  "overall_score": 0-100,
  "risk_level": "Low | Medium | High | Critical",
  "executive_summary": "2-3 sentences, plain English, names specific risks",
  "top_concern": "single most important issue in one sentence",
  "sign_as_is": false,
  "recommended_action": "Sign as-is | Negotiate key clauses | Major renegotiation required | Do not sign"
}"""


async def run_scorer_agent(analyst_output: dict) -> dict:
    """
    Synthesises analyst findings into an overall risk verdict.
    """
    client = anthropic.Anthropic()

    findings = analyst_output.get("findings", [])
    contract_type = analyst_output.get("contract_type", "Unknown")

    high_count   = sum(1 for f in findings if f.get("severity") == "High")
    medium_count = sum(1 for f in findings if f.get("severity") == "Medium")
    low_count    = sum(1 for f in findings if f.get("severity") == "Low")

    findings_summary = "\n".join([
        f"[{f['severity']}] {f['clause_type']}: {f['explanation']}"
        for f in findings
    ])

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=800,
        temperature=0,
        system=SCORER_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"""Contract type: {contract_type}

Risk findings ({len(findings)} total — {high_count} High, {medium_count} Medium, {low_count} Low):

{findings_summary}

Provide the overall risk verdict as JSON."""
        }]
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    scorer_output = json.loads(raw)

    # Attach finding counts for the frontend
    scorer_output["finding_counts"] = {
        "high": high_count,
        "medium": medium_count,
        "low": low_count,
        "total": len(findings)
    }

    return scorer_output
