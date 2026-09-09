"""
Relationship model and enumeration.
Represents cross-document relationships determined by deterministic comparison
and explained by grounded LLM synthesis.
"""

from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any, Union
from pydantic import BaseModel, Field, model_validator

class RelationshipType(str, Enum):
    CORROBORATED = "CORROBORATED"
    CONTRADICTED = "CONTRADICTED"
    LIKELY_CONTRADICTION = "LIKELY_CONTRADICTION"
    CONTEXTUAL_DIFFERENCE = "CONTEXTUAL_DIFFERENCE"
    RELATED_BUT_DIFFERENT = "RELATED_BUT_DIFFERENT"
    UNCERTAIN = "UNCERTAIN"

class ComparisonFeatures(BaseModel):
    entity_match: bool = False
    entity_similarity: float = 0.0
    predicate_match: bool = False
    predicate_similarity: float = 0.0
    period_match: str = "UNKNOWN"        # "EXACT", "OVERLAPPING", "DIFFERENT", "UNKNOWN"
    scope_match: str = "UNKNOWN"         # "EXACT", "DIFFERENT", "UNKNOWN"
    unit_match: bool = False
    value_match: str = "UNKNOWN"         # "EXACT_MATCH", "ROUNDING_VARIANCE", "MATERIAL_DIFFERENCE", "NOT_COMPARABLE", "SEMANTIC_EQUAL", "AGREES", "DISAGREES", "TOLERANCE_MATCH"
    numeric_variance_type: Optional[str] = None  # "EXACT_MATCH", "ROUNDING_VARIANCE", "MATERIAL_DIFFERENCE", "NOT_COMPARABLE"
    value_diff_percent: Optional[float] = None
    value_diff_absolute: Optional[float] = None
    estimate_match: str = "EXACT"        # "EXACT", "DIVERGENT", "UNKNOWN" (e.g. advance estimate vs projection)
    source_independence: bool = False    # True if from distinct documents
    upstream_source_match: Optional[bool] = None  # True if both cite identical upstream source

class Relationship(BaseModel):
    relationship_id: str
    fact_a_id: str
    fact_b_id: str
    relationship_type: RelationshipType
    comparison_features: Union[Dict[str, Any], ComparisonFeatures] = Field(default_factory=dict)
    confidence: float = 1.0
    confidence_breakdown: Dict[str, float] = Field(default_factory=dict)
    explanation: str
    evidence_a_id: Optional[str] = None
    evidence_b_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @model_validator(mode="before")
    @classmethod
    def convert_features(cls, data: Any) -> Any:
        if isinstance(data, dict) and "comparison_features" in data:
            if isinstance(data["comparison_features"], ComparisonFeatures):
                data["comparison_features"] = data["comparison_features"].model_dump()
        return data

