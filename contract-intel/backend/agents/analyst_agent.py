"""
Analyst Agent
─────────────────────────────────────────────────────────────
The core of the system. Reads the contract text and produces
a structured list of risk findings.

Each finding contains:
  - clause_type:   what kind of clause this is (e.g. "Indemnification")
  - severity:      High | Medium | Low
  - quoted_text:   the exact excerpt from the contract that triggered this
  - explanation:   plain-English description of why this is a risk
  - recommendation: what to do about it

Design decision — why one big call rather than many small ones?
  Contracts are highly interconnected. A liability cap in clause 8
  directly affects how risky the indemnity in clause 12 is. A single
  agent reading the whole document can reason holistically in a way
  that chained small calls cannot.
"""

import anthropic
import json

ANALYST_SYSTEM_PROMPT = """You are a senior commercial lawyer reviewing contracts on behalf of a company (the "Client"). Your job is to identify risks — clauses that could expose the Client to financial loss, legal liability, operational disruption, or unfair obligations.

Your reader is a business professional, not a lawyer. Write clearly. Explain legal concepts in plain English. Name the actual risk, not just the clause type.

Risk categories to look for:
- Liability & Indemnification: uncapped liability, one-sided indemnity, consequential damages exposure
- Termination: no termination for convenience, excessive notice periods, automatic renewal traps
- Payment: unfavorable payment terms, late payment penalties, price escalation clauses
- Intellectual Property: IP assignment that's too broad, work-for-hire overreach, license restrictions
- Confidentiality: weak NDA terms, broad disclosure carve-outs, insufficient duration
- Governing Law & Disputes: unfavorable jurisdiction, mandatory arbitration, class action waivers
- Data & Privacy: data ownership ambiguity, inadequate security obligations, GDPR/compliance gaps
- Exclusivity & Non-compete: broad exclusivity, aggressive non-compete, non-solicitation overreach
- SLA & Performance: vague deliverable definitions, unenforceable SLA remedies, acceptance criteria gaps
- Warranties & Representations: broad warranty disclaimers, unilateral warranty changes

Severity guide:
- High: could result in significant financial loss, legal action, or business disruption
- Medium: unfavorable but manageable; worth negotiating
- Low: minor issue or standard clause worth flagging for awareness

Respond with valid JSON only. No markdown. No text outside the JSON.

{
  "contract_type": "detected contract type (e.g. SaaS Agreement, NDA, Employment Contract)",
  "parties": "brief description of the parties if identifiable",
  "findings": [
    {
      "clause_type": "short name of the clause type",
      "severity": "High | Medium | Low",
      "quoted_text": "exact excerpt from the contract — keep it concise, max 200 chars",
      "explanation": "plain-English explanation of why this is a risk for the Client",
      "recommendation": "specific action: accept / reject / negotiate with suggested alternative language"
    }
  ]
}"""


async def run_analyst_agent(contract_text: str) -> dict:
    """
    Reads the contract and returns structured risk findings.
    """
    client = anthropic.Anthropic()

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=4000,
        temperature=0,        # Analytical task — deterministic is better
        system=ANALYST_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"""Review this contract and identify all material risks. Focus on clauses that are unusual, one-sided, or could harm the Client.

CONTRACT TEXT:
{contract_text}

Return only the JSON. No preamble."""
        }]
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    return json.loads(raw)
