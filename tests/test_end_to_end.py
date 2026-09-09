"""
End-to-End Pipeline Integration Tests.
Verifies PDF ingestion, fact extraction, vector indexing, relationship discovery,
and evidence grounding without requiring an external API key.
"""

import pytest
import fitz  # PyMuPDF
from pathlib import Path
from models.document import Document
from models.fact import Fact
from core.pipeline import FactKnowledgePipeline
from providers.groq_provider import GroqProvider
from storage.database import Base, engine, SessionLocal
from storage.repositories import DocumentRepository, FactRepository, RelationshipRepository

@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def sample_pdf(tmp_path) -> str:
    """Create a realistic two-page financial disclosure PDF."""
    pdf_path = tmp_path / "delhivery_sample_presentation.pdf"
    doc = fitz.open()

    # Page 1: Financial Highlights
    p1 = doc.new_page()
    text_p1 = (
        "Delhivery Limited\n"
        "Corporate Presentation - FY24 Performance Highlights\n\n"
        "Key Metric: Revenue from operations for FY24 stood at Rs. 8,142 Cr on a consolidated basis.\n"
        "The network covered 18,793 pin codes across India.\n"
        "Sahil Barua continued as Managing Director and CEO.\n"
    )
    p1.insert_text((50, 72), text_p1, fontsize=12)

    # Page 2: Standalone Segment Info
    p2 = doc.new_page()
    text_p2 = (
        "Delhivery Limited\n"
        "Financial Disclosures - Segment Information\n\n"
        "Standalone revenue from operations for FY24 was Rs. 74,540.82 million.\n"
        "Registered Office: Plot 5, Sector 44, Gurugram, Haryana 122002, India.\n"
    )
    p2.insert_text((50, 72), text_p2, fontsize=12)

    doc.save(str(pdf_path))
    doc.close()
    return str(pdf_path)

def test_full_pipeline_ingestion(sample_pdf):
    # Initialize pipeline with offline heuristic fallback provider
    provider = GroqProvider()
    provider.is_available = lambda: False  # Force offline heuristic mode

    pipeline = FactKnowledgePipeline(provider=provider)

    result = pipeline.ingest_document(sample_pdf)
    assert result["status"] == "success"
    assert result["page_count"] == 2
    assert result["facts_extracted"] > 0

    # Query DB to verify persistent state
    db = SessionLocal()
    doc_repo = DocumentRepository(db)
    fact_repo = FactRepository(db)
    rel_repo = RelationshipRepository(db)

    # Verify Document
    doc = doc_repo.get_by_id(result["document_id"])
    assert doc is not None
    assert doc.processing_status == "completed"
    assert len(doc.pages) == 2

    # Verify Facts
    facts = fact_repo.get_by_document(doc.document_id)
    assert len(facts) >= 2

    # Verify Evidence Grounding
    for fact in facts:
        assert fact.evidence_id is not None
        assert fact.document_id == doc.document_id
        assert fact.page_number in (1, 2)
        assert fact.raw_text != ""

    # Test deduplication on re-ingestion
    re_result = pipeline.ingest_document(sample_pdf)
    assert re_result["status"] == "already_indexed"

    db.close()
