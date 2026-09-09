"""
Fact and Period models.
Generalized schema supporting both numerical and semantic facts with full grounding.
"""

from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field

class Period(BaseModel):
    label: str  # e.g., "FY2023-24", "Q1 FY2024-25", "2024"
    period_type: str = "unknown"  # fiscal_year, calendar_year, quarter, month, date, date_range, unknown
    start_date: Optional[str] = None  # ISO format "YYYY-MM-DD"
    end_date: Optional[str] = None    # ISO format "YYYY-MM-DD"

    def overlaps(self, other: "Period") -> bool:
        """Check if two periods overlap in time."""
        if not self.start_date or not self.end_date or not other.start_date or not other.end_date:
            return self.label.lower() == other.label.lower()
        return not (self.end_date < other.start_date or self.start_date > other.end_date)

    def is_exact_match(self, other: "Period") -> bool:
        """Check if two periods represent the same time frame."""
        if self.start_date and self.end_date and other.start_date and other.end_date:
            return self.start_date == other.start_date and self.end_date == other.end_date
        return self.label.strip().lower() == other.label.strip().lower()

class Fact(BaseModel):
    fact_id: str
    subject: str                      # Entity or topic (e.g., "Delhivery Limited", "India")
    predicate: str                    # Metric or relation (e.g., "revenue from operations", "real GDP growth")
    object_value: Any                 # String, float, or structured value
    value_type: str = "numeric"       # "numeric", "semantic", "currency", "percentage"
    
    # Normalized numerical fields
    numeric_value: Optional[float] = None
    canonical_value: Optional[float] = None  # Normalized to standard base units (e.g., base INR, decimal)
    unit: Optional[str] = None               # Original unit (e.g., "Cr", "million", "%")
    canonical_unit: Optional[str] = None     # Normalized unit (e.g., "INR", "percent", "count")
    currency: Optional[str] = None           # e.g., "INR", "USD"
    
    # Temporal & Scope fields
    period: Optional[Period] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    geographic_scope: Optional[str] = "India"
    population_scope: Optional[str] = None
    business_scope: Optional[str] = None     # "consolidated", "standalone", "segment"
    category: Optional[str] = "general"      # "financial", "operational", "macroeconomic", "governance"
    qualifiers: List[str] = Field(default_factory=list)  # e.g., ["pro forma", "adjusted", "advance estimates"]
    
    # Grounding & Traceability
    raw_text: str
    confidence: float = 1.0
    evidence_id: str
    document_id: str
    page_number: int
    document_name: Optional[str] = None
    extraction_status: str = "valid"         # "valid", "uncertain", "review_required"
    
    def to_canonical_representation(self) -> str:
        """Generate a dense text representation for semantic embedding."""
        period_str = self.period.label if self.period else "unspecified period"
        scope_str = f" [{self.business_scope}]" if self.business_scope else ""
        val_str = str(self.canonical_value if self.canonical_value is not None else self.object_value)
        unit_str = f" {self.canonical_unit}" if self.canonical_unit else ""
        return f"{self.subject} {self.predicate}{scope_str} {period_str} {val_str}{unit_str}".strip()
