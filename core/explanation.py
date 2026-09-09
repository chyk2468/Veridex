"""
Grounded Explanation Engine.
Coordinates with the LLM provider to synthesize explanations strictly from
Fact fields, comparison features, and evidence quotes.
"""

import logging
from typing import Optional, Dict
from models.fact import Fact
from models.evidence import Evidence
from models.relationship import Relationship, ComparisonFeatures
from providers.base import LLMProvider

logger = logging.getLogger(__name__)

class ExplanationEngine:
    """Generates grounded natural language explanations for classified relationships."""

    def __init__(self, provider: LLMProvider):
        self.provider = provider

    def explain(
        self,
        relationship: Relationship,
        fact_a: Fact,
        fact_b: Fact,
        evidence_a: Optional[Evidence] = None,
        evidence_b: Optional[Evidence] = None
    ) -> str:
        """
        Generate grounded explanation for a classified relationship.
        """
        features = ComparisonFeatures.model_validate(relationship.comparison_features)
        
        explanation_text = self.provider.explain_relationship(
            fact_a=fact_a,
            fact_b=fact_b,
            relationship_type=relationship.relationship_type.value,
            features=features,
            evidence_a=evidence_a,
            evidence_b=evidence_b
        )

        relationship.explanation = explanation_text
        return explanation_text
