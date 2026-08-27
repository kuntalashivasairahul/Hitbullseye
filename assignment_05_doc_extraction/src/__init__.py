"""Source package for Assignment 5: Document Extraction Pipeline."""

from .schema_validator import SchemaValidator
from .dataset_generator import DatasetGenerator
from .extractor import DocumentExtractor, ExtractionResult
from .cost_model import CostModel, CostAnalysisResult
from .pipeline_evaluator import PipelineEvaluator

__all__ = [
    "SchemaValidator",
    "DatasetGenerator",
    "DocumentExtractor",
    "ExtractionResult",
    "CostModel",
    "CostAnalysisResult",
    "PipelineEvaluator",
]
__version__ = "0.2.0"
