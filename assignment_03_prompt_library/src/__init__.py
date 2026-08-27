"""Assignment 3: Prompt Engineering Library source package."""

from .benchmark_runner import BenchmarkRunner
from .dataset_generator import TestCase, generate_dataset, save_dataset
from .evaluator import EvaluationResult, Evaluator
from .generate_report import build_guide_markdown, load_benchmark_artifacts
from .llm_client import LLMResponse, LiveLLMClient, MockLLMBackend, get_llm_client
from .prompt_registry import PromptRegistry

__all__ = [
    "TestCase",
    "generate_dataset",
    "save_dataset",
    "PromptRegistry",
    "Evaluator",
    "EvaluationResult",
    "BenchmarkRunner",
    "LLMResponse",
    "MockLLMBackend",
    "LiveLLMClient",
    "get_llm_client",
    "load_benchmark_artifacts",
    "build_guide_markdown",
]
__version__ = "0.4.0"
