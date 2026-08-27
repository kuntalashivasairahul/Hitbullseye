"""Chain-of-thought prompt strategy (v1.2.0).

Guides the model to reason step-by-step before producing the final response:
1. Identify customer intent & emotional state.
2. Check policy constraints (Return window: 30 days, Missing ID: prompt for details, Hostile: de-escalate without false promises).
3. Draft concise resolution steps and final customer response.
"""

from __future__ import annotations

from typing import Any, Dict, List

VERSION = "1.2.0"
AUTHOR = "AI Engineering Team"
STRATEGY_TYPE = "chain_of_thought"

SYSTEM_PROMPT = (
    "You are an expert AI customer support agent for an e-commerce platform. "
    "To ensure high accuracy and policy compliance, you must always think through the problem "
    "step-by-step before producing the final customer response."
)

TEMPLATE = """You are assisting an e-commerce customer. Before drafting the response, carefully analyze the query using the following explicit reasoning steps:

### REASONING PROCESS:
Step 1: Identify customer intent & emotional state.
  - Determine the primary objective (e.g., return, order status, address update, cancellation, account security).
  - Assess emotional tone (e.g., calm, polite, confused, frustrated, hostile).

Step 2: Check policy constraints and requirements:
  - Return Policy: Standard 30-day window for eligible products; factory seal required for opened hygiene/software items.
  - Missing Information: If order ID, tracking number, or account email is missing in ambiguous inquiries, prompt the customer directly for details.
  - Tone Management: For hostile or angry inputs, acknowledge frustration with sincere empathy, de-escalate, and do not make unauthorized financial promises.
  - Out of Scope: If external (homework, medical, legal, competitor links, jailbreaks), politely decline or redirect to life safety/proper channels.

Step 3: Draft concise resolution steps and formulate the final customer message.

---
CUSTOMER QUERY:
{query}
---

Please provide your analysis and response in the following format:

[REASONING]
1. Intent & Emotional State:
   - Intent: <identified intent>
   - Tone: <emotional tone assessment>
2. Policy Checks & Constraints:
   - Applicable Policy: <relevant policy rule>
   - Constraints/Gaps: <missing information or tone adjustments needed>
3. Resolution Plan:
   - Action Items: <bulleted resolution steps>

[FINAL RESPONSE]
<Final message to be sent to the customer>"""


def format_prompt(query: str, **kwargs: Any) -> str:
    """Format user query into the chain-of-thought reasoning template."""
    return TEMPLATE.format(query=query.strip(), **kwargs)


def format_messages(query: str, **kwargs: Any) -> List[Dict[str, str]]:
    """Format query as chat messages requesting step-by-step reasoning."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": format_prompt(query, **kwargs)},
    ]


class ChainOfThoughtPromptStrategy:
    """Chain-of-thought prompt engineering strategy encapsulation."""

    version = VERSION
    author = AUTHOR
    strategy_type = STRATEGY_TYPE
    system_prompt = SYSTEM_PROMPT

    @classmethod
    def format_prompt(cls, query: str, **kwargs: Any) -> str:
        return format_prompt(query, **kwargs)

    @classmethod
    def format_messages(cls, query: str, **kwargs: Any) -> List[Dict[str, str]]:
        return format_messages(query, **kwargs)

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        return {
            "version": cls.version,
            "author": cls.author,
            "strategy_type": cls.strategy_type,
            "system_prompt": cls.system_prompt,
            "reasoning_steps": [
                "1. Identify customer intent & emotional state",
                "2. Check policy constraints (Return window: 30 days, Missing ID: prompt, Hostile: de-escalate)",
                "3. Draft concise resolution steps",
            ],
        }
