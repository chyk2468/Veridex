"""
Abstract LLM Provider Interface.
Decouples the system architecture from specific LLM vendors.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from models.fact import Fact
from models.evidence import Evidence
from models.relationship import ComparisonFeatures

class LLMProvider(ABC):
    """Abstract base class defining LLM operations."""

    @abstractmethod
    def extract_facts(self, context_text: str, evidence: Evidence, document_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Extract structured fact dictionaries grounded strictly in the provided evidence.
        Must return verifiable facts with exact evidence_text.
        """
        pass

    @abstractmethod
    def resolve_entity(self, text: str) -> Dict[str, Any]:
        """
        Interpret ambiguous entities or aliases.
        """
        pass

    @abstractmethod
    def explain_relationship(
        self,
        fact_a: Fact,
        fact_b: Fact,
        relationship_type: str,
        features: ComparisonFeatures,
        evidence_a: Optional[Evidence] = None,
        evidence_b: Optional[Evidence] = None
    ) -> str:
        """
        Generate a grounded, factual explanation of why the two facts have the specified relationship.
        Must use ONLY the structured fields, comparison features, and evidence snippets.
        """
        pass

    def is_available(self) -> bool:
        """Check if provider API client is configured and available."""
        return True

