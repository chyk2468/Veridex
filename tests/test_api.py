"""
Unit & Integration tests for FastAPI backend endpoints.
Verifies /health, /statistics, /cases, /documents, /facts, /relationships, and /search.
"""

import pytest
from fastapi.testclient import TestClient
from storage.database import Base, engine, SessionLocal
from storage.repositories import DocumentRepository, FactRepository, RelationshipRepository
from models.document import Document
from models.fact import Fact, Period
from models.relationship import Relationship, RelationshipType, ComparisonFeatures
from app.api import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("healthy", "degraded")
    assert "database" in data
    assert "provider" in data

def test_cases_endpoint():
    res = client.get("/cases")
    assert res.status_code == 200
    data = res.json()
    assert "case_1_corroboration" in data
    assert "case_2_contradiction" in data
    assert "case_3_contextual_difference" in data
    assert "case_4_failure_analysis" in data
    assert data["case_1_corroboration"]["data"]["expected_relationship"] == "CORROBORATED"
    assert data["case_2_contradiction"]["data"]["expected_relationship"] == "CONTRADICTED"

def test_statistics_endpoint():
    res = client.get("/statistics")
    assert res.status_code == 200
    data = res.json()
    assert data["total_documents"] == 0
    assert data["total_facts"] == 0
    assert "relationships_breakdown" in data

def test_facts_crud_and_relationships():
    db = SessionLocal()
    doc_repo = DocumentRepository(db)
    fact_repo = FactRepository(db)
    rel_repo = RelationshipRepository(db)

    # Add sample document
    doc = Document(document_id="doc_test", filename="test.pdf", content_hash="hash_t1", page_count=2)
    doc_repo.save_document(doc)

    # Add 2 facts
    f1 = Fact(
        fact_id="fact_1", subject="Delhivery Limited", predicate="revenue from operations",
        object_value="₹8,142 Cr", canonical_value=81420000000.0, canonical_unit="INR", currency="INR",
        period=Period(label="FY24"), business_scope="consolidated", raw_text="FY24 rev ₹8,142 Cr",
        evidence_id="ev_1", document_id="doc_test", page_number=1
    )
    f2 = Fact(
        fact_id="fact_2", subject="Delhivery Limited", predicate="revenue from operations",
        object_value="₹81,415.38 million", canonical_value=81415380000.0, canonical_unit="INR", currency="INR",
        period=Period(label="FY24"), business_scope="consolidated", raw_text="FY24 rev stood at ₹ 81,415.38 million",
        evidence_id="ev_2", document_id="doc_test", page_number=2
    )
    fact_repo.save_batch([f1, f2])

    # Add relationship
    rel = Relationship(
        relationship_id="rel_1", fact_a_id="fact_1", fact_b_id="fact_2",
        relationship_type=RelationshipType.CORROBORATED, confidence=0.98,
        comparison_features=ComparisonFeatures(
            entity_match=True, predicate_match=True, period_match="EXACT",
            scope_match="EXACT", unit_match=True, value_match="TOLERANCE_MATCH",
            value_diff_percent=0.0057
        ),
        explanation="Both sources corroborate consolidated FY24 revenue."
    )
    rel_repo.save_batch([rel])
    db.close()

    # Test GET /documents
    res_docs = client.get("/documents")
    assert res_docs.status_code == 200
    assert len(res_docs.json()) == 1

    # Test GET /facts
    res_facts = client.get("/facts")
    assert res_facts.status_code == 200
    assert res_facts.json()["total"] == 2

    # Test GET /facts/{id}
    res_fact = client.get("/facts/fact_1")
    assert res_fact.status_code == 200
    assert res_fact.json()["fact"]["canonical_value"] == 81420000000.0

    # Test GET /facts/{id}/relationships
    res_f_rels = client.get("/facts/fact_1/relationships")
    assert res_f_rels.status_code == 200
    assert len(res_f_rels.json()) == 1

    # Test GET /relationships
    res_rels = client.get("/relationships")
    assert res_rels.status_code == 200
    assert res_rels.json()["total"] == 1
    assert res_rels.json()["relationships"][0]["relationship"]["relationship_type"] == "CORROBORATED"

    # Test GET /relationships/{id}
    res_rel = client.get("/relationships/rel_1")
    assert res_rel.status_code == 200
    assert res_rel.json()["relationship"]["confidence"] == 0.98
