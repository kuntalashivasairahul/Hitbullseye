"""Unit tests for the prompt templates and PromptRegistry."""

import sys
import unittest
from pathlib import Path

# Ensure assignment_03_prompt_library is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from prompts.chain_of_thought import ChainOfThoughtPromptStrategy
from prompts.few_shot import FewShotPromptStrategy
from prompts.structured_template import StructuredTemplatePromptStrategy
from prompts.zero_shot import ZeroShotPromptStrategy
from src.prompt_registry import PromptRegistry


class TestPromptRegistry(unittest.TestCase):
    """Test suite verifying PromptRegistry functionality and metadata."""

    def test_registered_strategies_exist(self):
        """Ensure all 4 required strategies are registered."""
        strategies = PromptRegistry.list_prompts()
        registered_names = {item["name"] for item in strategies}
        expected_names = {"zero_shot", "few_shot", "chain_of_thought", "structured_template"}
        self.assertTrue(expected_names.issubset(registered_names))

    def test_zero_shot_metadata_and_format(self):
        """Verify zero_shot strategy metadata and minimal formatting."""
        meta = PromptRegistry.get_metadata("zero_shot")
        self.assertEqual(meta["version"], "1.0.0")
        self.assertEqual(meta["strategy_type"], "zero_shot")
        self.assertEqual(meta["author"], "AI Engineering Team")
        self.assertTrue(len(meta["system_prompt"]) > 0)

        query = "Can I cancel my order #12345?"
        formatted = PromptRegistry.format_prompt("zero_shot", query)
        self.assertIn(query, formatted)
        self.assertIn("Customer Query:", formatted)

        messages = PromptRegistry.format_messages("zero_shot", query)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[1]["role"], "user")
        self.assertIn(query, messages[1]["content"])

    def test_few_shot_demonstrations_and_format(self):
        """Verify few_shot includes 3 demonstrations with Input/Output patterns."""
        meta = PromptRegistry.get_metadata("few_shot")
        self.assertEqual(meta["version"], "1.1.0")
        self.assertEqual(meta["strategy_type"], "few_shot")
        self.assertEqual(meta["demonstration_count"], 3)

        query = "Where is my delayed package #ORD-999?"
        formatted = PromptRegistry.format_prompt("few_shot", query)
        self.assertIn("Standard Return Inquiry", formatted)
        self.assertIn("Hostile Order Delay Escalation", formatted)
        self.assertIn("Ambiguous Missing Tracking Query", formatted)
        self.assertIn(query, formatted)
        self.assertIn("Support Response:", formatted)

    def test_chain_of_thought_steps_and_format(self):
        """Verify chain_of_thought guides model through 3-step reasoning."""
        meta = PromptRegistry.get_metadata("chain_of_thought")
        self.assertEqual(meta["version"], "1.2.0")
        self.assertEqual(meta["strategy_type"], "chain_of_thought")
        self.assertEqual(len(meta["reasoning_steps"]), 3)

        query = "I want to return an opened pair of earbuds from 40 days ago."
        formatted = PromptRegistry.format_prompt("chain_of_thought", query)
        self.assertIn("Step 1: Identify customer intent & emotional state", formatted)
        self.assertIn("Step 2: Check policy constraints", formatted)
        self.assertIn("Step 3: Draft concise resolution steps", formatted)
        self.assertIn("[REASONING]", formatted)
        self.assertIn("[FINAL RESPONSE]", formatted)
        self.assertIn(query, formatted)

    def test_structured_template_keys_and_format(self):
        """Verify structured_template contains all required JSON keys and sections."""
        meta = PromptRegistry.get_metadata("structured_template")
        self.assertEqual(meta["version"], "1.3.0")
        self.assertEqual(meta["strategy_type"], "structured_template")

        expected_keys = ["intent", "tone_assessment", "actionable_steps", "customer_reply"]
        self.assertEqual(meta["expected_json_keys"], expected_keys)

        query = "Fix my broken laptop delivery right now!"
        formatted = PromptRegistry.format_prompt("structured_template", query)
        self.assertIn("### ROLE", formatted)
        self.assertIn("### CONTEXT", formatted)
        self.assertIn("### CONSTRAINTS", formatted)
        self.assertIn("### TASK", formatted)
        self.assertIn("### OUTPUT FORMAT", formatted)
        self.assertIn("### CUSTOMER QUERY", formatted)
        for key in expected_keys:
            self.assertIn(f'"{key}"', formatted)
        self.assertIn(query, formatted)

    def test_unknown_strategy_raises_key_error(self):
        """Verify requesting non-existent strategy raises KeyError."""
        with self.assertRaises(KeyError):
            PromptRegistry.get("non_existent_strategy")

        with self.assertRaises(KeyError):
            PromptRegistry.format_prompt("non_existent_strategy", "hello")

    def test_custom_strategy_registration(self):
        """Verify custom strategies can be registered dynamically."""
        class DummyStrategy:
            version = "0.0.1"
            author = "Tester"
            strategy_type = "dummy"
            system_prompt = "Dummy system"

            @classmethod
            def format_prompt(cls, query, **kwargs):
                return f"DUMMY: {query}"

            @classmethod
            def format_messages(cls, query, **kwargs):
                return [{"role": "user", "content": query}]

            @classmethod
            def get_metadata(cls):
                return {
                    "version": cls.version,
                    "author": cls.author,
                    "strategy_type": cls.strategy_type,
                    "system_prompt": cls.system_prompt,
                }

        PromptRegistry.register("dummy_test", DummyStrategy)
        self.assertEqual(PromptRegistry.get("dummy_test"), DummyStrategy)
        formatted = PromptRegistry.format_prompt("dummy_test", "test query")
        self.assertEqual(formatted, "DUMMY: test query")


if __name__ == "__main__":
    unittest.main()
