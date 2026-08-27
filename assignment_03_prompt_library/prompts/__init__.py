"""Prompt Engineering Library templates package."""

from .chain_of_thought import ChainOfThoughtPromptStrategy
from .few_shot import FewShotPromptStrategy
from .structured_template import StructuredTemplatePromptStrategy
from .zero_shot import ZeroShotPromptStrategy

__all__ = [
    "ZeroShotPromptStrategy",
    "FewShotPromptStrategy",
    "ChainOfThoughtPromptStrategy",
    "StructuredTemplatePromptStrategy",
]
