"""Prompt Registry for Assignment 3: Prompt Engineering Library.

Provides a unified registry interface for loading, inspecting metadata,
and formatting prompt strategies:
- zero_shot (v1.0.0)
- few_shot (v1.1.0)
- chain_of_thought (v1.2.0)
- structured_template (v1.3.0)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project root is in sys.path so prompts package is importable
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from prompts.chain_of_thought import ChainOfThoughtPromptStrategy
from prompts.few_shot import FewShotPromptStrategy
from prompts.structured_template import StructuredTemplatePromptStrategy
from prompts.zero_shot import ZeroShotPromptStrategy

# Optional Rich console styling
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class PromptRegistry:
    """Central registry managing prompt engineering strategies."""

    _registry: Dict[str, Any] = {}

    @classmethod
    def register(cls, name: str, strategy: Any) -> None:
        """Register a prompt strategy under a unique name."""
        cls._registry[name] = strategy

    @classmethod
    def get(cls, name: str) -> Any:
        """Retrieve a registered prompt strategy by name."""
        if name not in cls._registry:
            valid = list(cls._registry.keys())
            raise KeyError(f"Prompt strategy '{name}' not found. Registered strategies: {valid}")
        return cls._registry[name]

    @classmethod
    def list_prompts(cls) -> List[Dict[str, Any]]:
        """Return metadata summary for all registered prompt strategies."""
        summary = []
        for name, strategy in cls._registry.items():
            meta = strategy.get_metadata()
            summary.append({
                "name": name,
                "version": meta.get("version", "N/A"),
                "author": meta.get("author", "N/A"),
                "strategy_type": meta.get("strategy_type", "N/A"),
                "system_prompt": meta.get("system_prompt", ""),
            })
        return summary

    @classmethod
    def get_metadata(cls, name: str) -> Dict[str, Any]:
        """Return comprehensive metadata for a specific prompt strategy."""
        strategy = cls.get(name)
        meta = strategy.get_metadata()
        meta["name"] = name
        return meta

    @classmethod
    def format_prompt(cls, name: str, query: str, **kwargs: Any) -> str:
        """Format the specified prompt strategy with a customer query."""
        strategy = cls.get(name)
        return strategy.format_prompt(query, **kwargs)

    @classmethod
    def format_messages(cls, name: str, query: str, **kwargs: Any) -> List[Dict[str, str]]:
        """Format query into standard chat completion messages."""
        strategy = cls.get(name)
        return strategy.format_messages(query, **kwargs)


# Initialize default registry with the 4 required strategies
PromptRegistry.register("zero_shot", ZeroShotPromptStrategy)
PromptRegistry.register("few_shot", FewShotPromptStrategy)
PromptRegistry.register("chain_of_thought", ChainOfThoughtPromptStrategy)
PromptRegistry.register("structured_template", StructuredTemplatePromptStrategy)


def preview_prompts(
    target_name: Optional[str] = None,
    sample_query: str = "Hi, I placed order #ORD-84920 yesterday with standard shipping. Can you tell me when it is expected to ship and how I can track the package?",
) -> None:
    """CLI preview of prompt strategies populated with sample data."""
    strategies_to_preview = [target_name] if target_name else list(PromptRegistry._registry.keys())

    if RICH_AVAILABLE:
        console = Console()
        console.print("[bold cyan]======================================================================[/bold cyan]")
        console.print("[bold cyan]Prompt Engineering Library - Strategy Preview[/bold cyan]")
        console.print("[bold cyan]======================================================================[/bold cyan]\n")

        # Metadata Table
        table = Table(title="Registered Prompt Strategies", header_style="bold magenta")
        table.add_column("Strategy Name", style="cyan", justify="left")
        table.add_column("Version", style="green", justify="center")
        table.add_column("Type", style="yellow", justify="left")
        table.add_column("Author", style="white", justify="left")

        for item in PromptRegistry.list_prompts():
            table.add_row(item["name"], item["version"], item["strategy_type"], item["author"])
        console.print(table)
        console.print()

        for name in strategies_to_preview:
            meta = PromptRegistry.get_metadata(name)
            formatted = PromptRegistry.format_prompt(name, sample_query)
            console.print(Panel(
                f"[bold yellow]Version:[/bold yellow] {meta['version']} | "
                f"[bold yellow]Strategy:[/bold yellow] {meta['strategy_type']} | "
                f"[bold yellow]Author:[/bold yellow] {meta['author']}\n\n"
                f"[bold magenta]System Prompt:[/bold magenta]\n{meta['system_prompt']}\n\n"
                f"[bold green]Formatted User Prompt:[/bold green]\n{formatted}",
                title=f"[bold cyan]Strategy: {name}[/bold cyan]",
                border_style="blue",
            ))
            console.print()
    else:
        print("=" * 70)
        print("Prompt Engineering Library - Strategy Preview")
        print("=" * 70)
        print(f"{'Strategy Name':<22} | {'Version':<8} | {'Type':<20} | {'Author'}")
        print("-" * 70)
        for item in PromptRegistry.list_prompts():
            print(f"{item['name']:<22} | {item['version']:<8} | {item['strategy_type']:<20} | {item['author']}")
        print("=" * 70)
        print()

        for name in strategies_to_preview:
            meta = PromptRegistry.get_metadata(name)
            formatted = PromptRegistry.format_prompt(name, sample_query)
            print("-" * 70)
            print(f"STRATEGY: {name.upper()}")
            print(f"Version : {meta['version']} | Author: {meta['author']} | Type: {meta['strategy_type']}")
            print("-" * 70)
            print("[SYSTEM PROMPT]")
            print(meta["system_prompt"])
            print("\n[FORMATTED PROMPT]")
            print(formatted)
            print("\n")


def main() -> None:
    """Command-line interface entry point."""
    parser = argparse.ArgumentParser(
        description="Assignment 3: Prompt Engineering Library Registry & Preview CLI"
    )
    parser.add_argument(
        "--preview",
        nargs="?",
        const="all",
        metavar="STRATEGY",
        help="Preview formatted prompt outputs. Optionally specify a strategy name (zero_shot, few_shot, chain_of_thought, structured_template).",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all registered prompt strategies and versions.",
    )
    parser.add_argument(
        "--query",
        type=str,
        default="Hi, I placed order #ORD-84920 yesterday with standard shipping. Can you tell me when it is expected to ship and how I can track the package?",
        help="Custom customer query to preview.",
    )

    args = parser.parse_args()

    if args.list:
        summary = PromptRegistry.list_prompts()
        print("\nRegistered Prompt Strategies:")
        for item in summary:
            print(f" - {item['name']} ({item['version']}) [{item['strategy_type']}] by {item['author']}")
        print()
        return

    # Default to preview if --preview is provided or run with no arguments
    target = None if (args.preview == "all" or args.preview is None) else args.preview
    preview_prompts(target_name=target, sample_query=args.query)


if __name__ == "__main__":
    main()
