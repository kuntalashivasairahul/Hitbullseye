"""Zero-shot prompt strategy (v1.0.0).

Minimal baseline: Only task instructions and customer query.
Contains no few-shot demonstrations and no explicit reasoning steps.
"""

from __future__ import annotations

from typing import Any, Dict, List

VERSION = "1.0.0"
AUTHOR = "AI Engineering Team"
STRATEGY_TYPE = "zero_shot"

SYSTEM_PROMPT = (
    "You are a helpful, professional customer support agent for an e-commerce platform. "
    "Provide accurate, concise, and courteous assistance to customer inquiries regarding "
    "orders, shipping, refunds, cancellations, and account security."
)

TEMPLATE = """Customer Query:
{query}

Please provide an appropriate, professional, and helpful response to the customer."""


def format_prompt(query: str, **kwargs: Any) -> str:
    """Format user query into the zero-shot prompt string."""
    return TEMPLATE.format(query=query.strip(), **kwargs)


def format_messages(query: str, **kwargs: Any) -> List[Dict[str, str]]:
    """Format query as standard chat messages (system and user)."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": format_prompt(query, **kwargs)},
    ]


class ZeroShotPromptStrategy:
    """Zero-shot prompt engineering strategy encapsulation."""

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
        }
