"""
Unit tests for Deterministic Relationship Engine.
Tests all four mandatory cases: Corroboration, Contradiction, Contextual Difference, and Uncertainty.
"""

import pytest
from core.relationship import RelationshipEngine
from models.fact import Fact, Period
from models.relationship import RelationshipType

@pytest.fixture
def engine():
    return RelationshipEngine(value_tolerance_percent=1.0)

def test_corroboration_within_tolerance(engine):
    fact_a = Fact(
        fact_id="f_a", subject="Delhivery Limited", predicate="revenue from operations",
        object_value="₹8,142 Cr", canonical_value=81420000000.0, canonical_unit="INR", currency="INR",
        period=Period(label="FY2023/24", start_date="2023-04-01", end_date="2024-03-31"),
        business_scope="consolidated", raw_text="Revenue: ₹8,142 Cr",
        evidence_id="ev_a", document_id="doc_a", page_number=6
    )
    fact_b = Fact(
        fact_id="f_b", subject="Delhivery Limited", predicate="revenue from operations",
        object_value="₹ 81,415.38 million", canonical_value=81415380000.0, canonical_unit="INR", currency="INR",
        period=Period(label="FY2023/24", start_date="2023-04-01", end_date="2024-03-31"),
        business_scope="consolidated", raw_text="stood at ₹ 81,415.38 million",
        evidence_id="ev_b", document_id="doc_b", page_number=22
    )

    rel = engine.evaluate_pair(fact_a, fact_b)
    assert rel.relationship_type == RelationshipType.CORROBORATED
    assert rel.comparison_features["value_diff_percent"] < 0.01

def test_genuine_contradiction(engine):
    fact_a = Fact(
        fact_id="f_a", subject="India", predicate="real GDP growth",
        object_value=6.4, canonical_value=6.4, canonical_unit="percent", value_type="percentage",
        period=Period(label="FY2024/25", start_date="2024-04-01", end_date="2025-03-31"),
        raw_text="India’s real GDP is estimated to grow by 6.4 per cent",
        evidence_id="ev_a", document_id="doc_a", page_number=4
    )
    fact_b = Fact(
        fact_id="f_b", subject="India", predicate="real GDP growth",
        object_value=6.5, canonical_value=6.5, canonical_unit="percent", value_type="percentage",
        period=Period(label="FY2024/25", start_date="2024-04-01", end_date="2025-03-31"),
        raw_text="India’s real GDP grew by 6.5 percent in FY2024/25",
        evidence_id="ev_b", document_id="doc_b", page_number=10
    )

    rel = engine.evaluate_pair(fact_a, fact_b)
    assert rel.relationship_type == RelationshipType.CONTRADICTED
    assert rel.comparison_features["value_diff_percent"] > 1.0

def test_contextual_difference_scope(engine):
    fact_sa = Fact(
        fact_id="f_sa", subject="Delhivery Limited", predicate="revenue from operations",
        object_value="₹ 74,540.82 million", canonical_value=74540820000.0, canonical_unit="INR", currency="INR",
        period=Period(label="FY2023/24", start_date="2023-04-01", end_date="2024-03-31"),
        business_scope="standalone", raw_text="standalone basis for FY24 stood at ₹ 74,540.82 million",
        evidence_id="ev_sa", document_id="doc_a", page_number=22
    )
    fact_consol = Fact(
        fact_id="f_consol", subject="Delhivery Limited", predicate="revenue from operations",
        object_value="₹ 81,415.38 million", canonical_value=81415380000.0, canonical_unit="INR", currency="INR",
        period=Period(label="FY2023/24", start_date="2023-04-01", end_date="2024-03-31"),
        business_scope="consolidated", raw_text="consolidated basis for FY24 stood at ₹ 81,415.38 million",
        evidence_id="ev_consol", document_id="doc_a", page_number=22
    )

    rel = engine.evaluate_pair(fact_sa, fact_consol)
    assert rel.relationship_type == RelationshipType.CONTEXTUAL_DIFFERENCE
    assert rel.comparison_features["scope_match"] == "DIFFERENT"

def test_contextual_difference_period(engine):
    fact_q4 = Fact(
        fact_id="f_q4", subject="Delhivery Limited", predicate="revenue from operations",
        object_value="₹2,076 Cr", canonical_value=20760000000.0, canonical_unit="INR", currency="INR",
        period=Period(label="Q4 FY2023/24", period_type="quarter", start_date="2024-01-01", end_date="2024-03-31"),
        business_scope="consolidated", raw_text="Q4 FY24 revenue from services ₹2,076 Cr",
        evidence_id="ev_q4", document_id="doc_a", page_number=7
    )
    fact_fy = Fact(
        fact_id="f_fy", subject="Delhivery Limited", predicate="revenue from operations",
        object_value="₹8,142 Cr", canonical_value=81420000000.0, canonical_unit="INR", currency="INR",
        period=Period(label="FY2023/24", period_type="fiscal_year", start_date="2023-04-01", end_date="2024-03-31"),
        business_scope="consolidated", raw_text="FY24 revenue from services ₹8,142 Cr",
        evidence_id="ev_fy", document_id="doc_a", page_number=6
    )

    rel = engine.evaluate_pair(fact_q4, fact_fy)
    assert rel.relationship_type == RelationshipType.CONTEXTUAL_DIFFERENCE
    assert rel.comparison_features["period_match"] in ("DIFFERENT", "OVERLAPPING")

def test_uncertain_missing_period(engine):
    fact_unknown = Fact(
        fact_id="f_u", subject="India", predicate="real GDP growth",
        object_value=6.5, canonical_value=6.5, canonical_unit="percent", value_type="percentage",
        period=None, raw_text="GDP grew by 6.5%",
        evidence_id="ev_u", document_id="doc_u", page_number=1
    )
    fact_known = Fact(
        fact_id="f_k", subject="India", predicate="real GDP growth",
        object_value=6.4, canonical_value=6.4, canonical_unit="percent", value_type="percentage",
        period=Period(label="FY2024/25", start_date="2024-04-01", end_date="2025-03-31"),
        raw_text="GDP estimated to grow by 6.4%",
        evidence_id="ev_k", document_id="doc_k", page_number=4
    )

    rel = engine.evaluate_pair(fact_unknown, fact_known)
    assert rel.relationship_type == RelationshipType.UNCERTAIN
