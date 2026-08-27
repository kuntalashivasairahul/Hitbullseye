"""Few-shot prompt strategy (v1.1.0).

Includes 3 representative customer support demonstrations:
1. Standard return inquiry (clear policy, RMA steps).
2. Hostile/frustrated order delay escalation (de-escalation, empathy, trace, supervisor escalation).
3. Ambiguous missing tracking query (clarification question asking for order/tracking ID).
"""

from __future__ import annotations

from typing import Any, Dict, List

VERSION = "1.1.0"
AUTHOR = "AI Engineering Team"
STRATEGY_TYPE = "few_shot"

SYSTEM_PROMPT = (
    "You are a helpful, empathetic, and professional customer support agent for an e-commerce platform. "
    "Follow the provided exemplary response patterns to resolve customer queries across orders, shipping, "
    "refunds, cancellations, and account security. Maintain composure, adhere to store policy, and request "
    "missing details when inquiries are ambiguous."
)

DEMONSTRATIONS = [
    {
        "type": "Standard Return Inquiry",
        "input": "What is your return policy for electronics? I purchased a wireless mouse 10 days ago and want to return it.",
        "output": (
            "Hi there! Thanks for reaching out.\n\n"
            "We offer a 30-day return window for all consumer electronics, starting from the delivery date. "
            "Because your purchase was 10 days ago, your wireless mouse is fully eligible for a full refund, "
            "provided it is in its original packaging with all included accessories.\n\n"
            "Here is how to initiate your return:\n"
            "1. Log into your account and navigate to 'Order History'.\n"
            "2. Select your mouse purchase and click 'Start a Return / RMA'.\n"
            "3. Download and print your prepaid return shipping label (or generate a mobile QR code for UPS drop-off).\n\n"
            "Once our warehouse scans the returned package, your refund will be issued to your original payment method within 3-5 business days."
        ),
    },
    {
        "type": "Hostile Order Delay Escalation",
        "input": "THIS IS RIDICULOUS! My order #ORD-88192 is 10 days late! Your automated tracking is stuck on 'In Transit' and hasn't updated in a week. I demand an immediate refund and a real manager on the phone NOW!",
        "output": (
            "Hello, I completely understand why you are so upset. Waiting 10 days past the delivery date with no tracking updates is extremely frustrating, and I sincerely apologize for this experience.\n\n"
            "I have pulled up order #ORD-88192 and can see that the carrier's last tracking ping was 7 days ago at the regional hub. Here is what I am doing immediately to resolve this for you:\n"
            "1. Priority Carrier Trace: I have opened an emergency trace ticket with the logistics team to locate the parcel.\n"
            "2. Manager Escalation: I have flagged this ticket for supervisor review. A senior support lead will review this case and follow up with you within 2 hours.\n"
            "3. Resolution Guarantee: If the carrier cannot verify delivery within 24 hours, we will immediately issue a full refund to your payment card or dispatch a free replacement with overnight express delivery—whichever you prefer.\n\n"
            "You have my personal commitment that we will see this through to your satisfaction."
        ),
    },
    {
        "type": "Ambiguous Missing Tracking Query",
        "input": "Where is my stuff? It never came.",
        "output": (
            "Hello! I am sorry to hear that your package has not arrived yet. I would be more than happy to help track it down for you.\n\n"
            "Could you please reply with:\n"
            "• Your Order Number (e.g., #ORD-12345), or\n"
            "• The email address associated with your purchase?\n\n"
            "As soon as you share either of those details, I will look into the shipment status right away and let you know where your package is!"
        ),
    },
]


def _build_demonstration_text() -> str:
    parts = []
    for idx, demo in enumerate(DEMONSTRATIONS, start=1):
        parts.append(
            f"--- Example {idx} [{demo['type']}] ---\n"
            f"Customer Query: {demo['input']}\n"
            f"Support Response:\n{demo['output']}\n"
        )
    return "\n".join(parts)


TEMPLATE = """Review the following representative examples of customer inquiries and high-quality support responses:

{demonstrations}
--- Current Inquiry ---
Customer Query: {query}
Support Response:"""


def format_prompt(query: str, **kwargs: Any) -> str:
    """Format user query along with few-shot demonstrations."""
    demos_text = _build_demonstration_text()
    return TEMPLATE.format(demonstrations=demos_text, query=query.strip(), **kwargs)


def format_messages(query: str, **kwargs: Any) -> List[Dict[str, str]]:
    """Format query as chat messages incorporating few-shot demonstrations."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": format_prompt(query, **kwargs)},
    ]


class FewShotPromptStrategy:
    """Few-shot prompt engineering strategy encapsulation."""

    version = VERSION
    author = AUTHOR
    strategy_type = STRATEGY_TYPE
    system_prompt = SYSTEM_PROMPT
    demonstrations = DEMONSTRATIONS

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
            "demonstration_count": len(cls.demonstrations),
        }
