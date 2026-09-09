"""
Tests for Incremental Processing and Deduplication.
Ensures that uploading a second PDF adds facts and cross-document relationships
without re-processing or corrupting the first PDF's knowledge.
"""

import pytest
from unittest.mock import MagicMock
from models.document import Document, Page
from models.fact import Fact, Period
from models.relationship import RelationshipType
from storage.database import Base, engine, SessionLocal
from storage.repositories import DocumentRepository, FactRepository, RelationshipRepository
from retrieval.vector_store import VectorStore
from core.matcher import CandidateMatcher
from core.relationship import RelationshipEngine

@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_document_hash_deduplication():
    db = SessionLocal()
    doc_repo = DocumentRepository(db)

    doc1 = Document(
        document_id="doc_1",
        filename="report_v1.pdf",
        content_hash="hash_abc123",
        page_count=1,
        pages=[Page(page_id="p_1", document_id="doc_1", page_number=1, text="Sample text")]
    )
    doc_repo.save_document(doc1)

    # Query by hash
    existing = doc_repo.get_by_hash("hash_abc123")
    assert existing is not None
    assert existing.document_id == "doc_1"

    # Query for non-existent hash
    none_doc = doc_repo.get_by_hash("hash_xyz789")
    assert none_doc is None
    db.close()

def test_incremental_fact_and_relationship_linking():
    db = SessionLocal()
    doc_repo = DocumentRepository(db)
    fact_repo = FactRepository(db)
    rel_repo = RelationshipRepository(db)

    # Ingest Document 1: Earnings Presentation
    doc1 = Document(document_id="doc_ep", filename="earnings_presentation.pdf", content_hash="hash_1", page_count=10)
    doc_repo.save_document(doc1)

    fact1 = Fact(
        fact_id="fact_ep_rev",
        subject="Delhivery Limited",
        predicate="revenue from operations",
        object_value="₹8,142 Cr",
        canonical_value=81420000000.0,
        canonical_unit="INR",
        currency="INR",
        period=Period(label="FY2023/24", period_type="fiscal_year", start_date="2023-04-01", end_date="2024-03-31"),
        business_scope="consolidated",
        raw_text="FY24 revenue from services ₹8,142 Cr",
        evidence_id="ev_1",
        document_id="doc_ep",
        page_number=6
    )
    fact_repo.save_batch([fact1])

    # Assert Doc 1 facts stored
    assert len(fact_repo.get_by_document("doc_ep")) == 1
    assert len(rel_repo.get_all()) == 0

    # Ingest Document 2: Annual Report (Days/Weeks later)
    doc2 = Document(document_id="doc_ar", filename="annual_report.pdf", content_hash="hash_2", page_count=50)
    doc_repo.save_document(doc2)

    fact2 = Fact(
        fact_id="fact_ar_rev",
        subject="Delhivery Limited",
        predicate="revenue from operations",
        object_value="₹81,415.38 million",
        canonical_value=81415380000.0,
        canonical_unit="INR",
        currency="INR",
        period=Period(label="FY2023/24", period_type="fiscal_year", start_date="2023-04-01", end_date="2024-03-31"),
        business_scope="consolidated",
        raw_text="Revenue from operations for FY 2023-24 stood at ₹ 81,415.38 million",
        evidence_id="ev_2",
        document_id="doc_ar",
        page_number=22
    )
    fact_repo.save_batch([fact2])

    # Check that prior facts (from doc_ep) remain intact
    all_facts = fact_repo.get_all()
    assert len(all_facts) == 2
    prior_facts = [f for f in all_facts if f.document_id != "doc_ar"]
    assert len(prior_facts) == 1
    assert prior_facts[0].fact_id == "fact_ep_rev"

    # Perform candidate matching between new facts and prior facts
    matcher = CandidateMatcher(vector_store=MagicMock())
    # Mock vector store search to return prior fact
    matcher.find_candidate_pairs = MagicMock(return_value=[(fact2, prior_facts[0])])
    candidate_pairs = matcher.find_candidate_pairs([fact2], prior_facts)

    # Evaluate relationship
    engine = RelationshipEngine(value_tolerance_percent=1.0)
    relationships = []
    for a, b in candidate_pairs:
        rel = engine.evaluate_pair(a, b)
        relationships.append(rel)

    rel_repo.save_batch(relationships)

    # Verification: Cross-document relationship discovered incrementally
    saved_rels = rel_repo.get_all()
    assert len(saved_rels) == 1
    assert saved_rels[0].relationship_type == RelationshipType.CORROBORATED
    assert saved_rels[0].fact_a_id in ("fact_ar_rev", "fact_ep_rev")
    assert saved_rels[0].fact_b_id in ("fact_ar_rev", "fact_ep_rev")

    # Document 1 facts were never re-written or corrupted
    doc1_facts = fact_repo.get_by_document("doc_ep")
    assert len(doc1_facts) == 1
    assert doc1_facts[0].canonical_value == 81420000000.0

    db.close()
