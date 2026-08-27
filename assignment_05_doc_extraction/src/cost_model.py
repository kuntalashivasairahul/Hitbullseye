"""Cost Model and Economic Analysis for Document Extraction Pipeline (Assignment 5).

Calculates total pipeline costs, Straight-Through Processing (STP) savings,
and comparative ROI against 100% manual data entry.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict


@dataclass
class CostAnalysisResult:
    total_documents: int
    stp_count: int
    human_review_count: int
    rejected_count: int
    stp_rate_pct: float
    human_review_rate_pct: float
    rejection_rate_pct: float
    baseline_manual_cost: float
    ai_extraction_cost: float
    human_review_cost: float
    total_pipeline_cost: float
    cost_per_document: float
    net_savings_dollars: float
    net_savings_pct: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CostModel:
    """Calculates operational economics and labor savings for hybrid AI pipelines."""

    MANUAL_COST_PER_DOC: float = 1.80       # Avg 4.5 minutes human entry labor @ $24/hr
    AI_EXTRACTION_COST_PER_DOC: float = 0.015  # LLM inference + OCR token costs
    HUMAN_REVIEW_COST_PER_DOC: float = 0.60  # Avg 1.5 minutes verification/fix labor @ $24/hr

    @classmethod
    def evaluate(
        cls,
        total_docs: int,
        stp_count: int,
        human_review_count: int,
        rejected_count: int,
    ) -> CostAnalysisResult:
        """Compute complete cost breakdown and ROI savings."""
        if total_docs <= 0:
            raise ValueError("total_docs must be greater than zero.")

        # Baseline: 100% manual data entry
        baseline_manual = round(total_docs * cls.MANUAL_COST_PER_DOC, 2)

        # AI Extraction Cost: Applied to all submitted documents
        ai_cost = round(total_docs * cls.AI_EXTRACTION_COST_PER_DOC, 2)

        # Human Review Cost: Applied strictly to low-confidence / failed documents
        review_cost = round(human_review_count * cls.HUMAN_REVIEW_COST_PER_DOC, 2)

        # Total Pipeline Cost
        total_pipeline = round(ai_cost + review_cost, 2)
        cost_per_doc = round(total_pipeline / total_docs, 3)

        # Savings
        net_savings_dollars = round(baseline_manual - total_pipeline, 2)
        net_savings_pct = round((net_savings_dollars / baseline_manual) * 100.0, 1)

        # Rates
        stp_rate = round((stp_count / total_docs) * 100.0, 1)
        review_rate = round((human_review_count / total_docs) * 100.0, 1)
        rejection_rate = round((rejected_count / total_docs) * 100.0, 1)

        return CostAnalysisResult(
            total_documents=total_docs,
            stp_count=stp_count,
            human_review_count=human_review_count,
            rejected_count=rejected_count,
            stp_rate_pct=stp_rate,
            human_review_rate_pct=review_rate,
            rejection_rate_pct=rejection_rate,
            baseline_manual_cost=baseline_manual,
            ai_extraction_cost=ai_cost,
            human_review_cost=review_cost,
            total_pipeline_cost=total_pipeline,
            cost_per_document=cost_per_doc,
            net_savings_dollars=net_savings_dollars,
            net_savings_pct=net_savings_pct,
        )
