"""
Fact Knowledge Layer Pipeline.
Orchestrates end-to-end PDF ingestion, page parsing, candidate detection,
fact extraction, normalization, FAISS indexing, candidate matching,
deterministic relationship classification, grounded explanation, and incremental persistence.
"""

import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from core.parser import PDFParser
from core.table_parser import TableParser
from core.extractor import FactExtractor
from core.matcher import CandidateMatcher
from core.relationship import RelationshipEngine
from core.explanation import ExplanationEngine
from retrieval.vector_store import VectorStore
from providers.base import LLMProvider
from providers.groq_provider import GroqProvider
from storage.database import SessionLocal, init_db, DocumentORM, ProcessingRunORM
from storage.repositories import (
    DocumentRepository,
    EvidenceRepository,
    FactRepository,
    RelationshipRepository
)
from models.document import Document
from models.fact import Fact
from models.relationship import Relationship

logger = logging.getLogger(__name__)

class FactKnowledgePipeline:
    """Unified pipeline for document ingestion, fact indexing, and relationship discovery."""

    def __init__(self, provider: Optional[LLMProvider] = None, vector_store: Optional[VectorStore] = None):
        init_db()
        self.provider = provider or GroqProvider()
        self.parser = PDFParser()
        self.table_parser = TableParser()
        self.extractor = FactExtractor(self.provider)
        self.vector_store = vector_store or VectorStore()
        self.matcher = CandidateMatcher(self.vector_store)
        self.engine = RelationshipEngine()
        self.explainer = ExplanationEngine(self.provider)

    def ingest_document(self, file_path: str, max_pages: Optional[int] = None) -> Dict[str, Any]:
        """
        Incrementally ingest a PDF document without rebuilding existing knowledge.
        """
        start_time = time.time()
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        file_bytes = path.read_bytes()
        content_hash = Document.compute_hash(file_bytes)

        db: Session = SessionLocal()
        doc_repo = DocumentRepository(db)
        ev_repo = EvidenceRepository(db)
        fact_repo = FactRepository(db)
        rel_repo = RelationshipRepository(db)

        # Check for duplicate document
        existing_doc = doc_repo.get_by_hash(content_hash)
        if existing_doc:
            logger.info(f"Document {path.name} already ingested (ID: {existing_doc.document_id}). Skipping re-parse.")
            db.close()
            return {
                "status": "already_indexed",
                "document_id": existing_doc.document_id,
                "filename": existing_doc.filename,
                "message": "Document already ingested."
            }

        # 1. Parse text and blocks
        document, text_evidence = self.parser.parse_document(str(path))
        if max_pages and len(document.pages) > max_pages:
            document.pages = document.pages[:max_pages]
            text_evidence = [e for e in text_evidence if e.page_number <= max_pages]

        # 2. Extract tables
        _, table_evidence = self.table_parser.extract_tables_from_pdf(str(path), document.document_id, max_pages=max_pages)
        all_evidence = text_evidence + table_evidence

        # 3. Save Document and Evidence
        doc_repo.save_document(document)
        ev_repo.save_batch(all_evidence)

        # 4. Extract and normalize facts
        new_facts = self.extractor.extract_facts_from_evidence(all_evidence, document)
        fact_repo.save_batch(new_facts)

        # 5. Index into vector store
        if new_facts:
            self.vector_store.add_facts(new_facts)

        # 6. Retrieve existing facts for cross-document relationship discovery
        all_existing_facts = fact_repo.get_all()
        prior_facts = [f for f in all_existing_facts if f.document_id != document.document_id]

        # 7. Match candidate pairs
        candidate_pairs = self.matcher.find_candidate_pairs(new_facts, prior_facts)

        # Also find intra-document relationships (e.g. standalone vs consolidated on page 22)
        intra_pairs = self.matcher.find_candidate_pairs(new_facts, new_facts)
        for a, b in intra_pairs:
            if a.fact_id != b.fact_id and (a, b) not in candidate_pairs and (b, a) not in candidate_pairs:
                candidate_pairs.append((a, b))

        # 8. Deterministic comparison and grounded explanations
        new_relationships: List[Relationship] = []
        for fact_a, fact_b in candidate_pairs:
            rel = self.engine.evaluate_pair(fact_a, fact_b)
            # Only retain meaningful relationships
            if rel.relationship_type != "RELATED_BUT_DIFFERENT" or rel.confidence >= 0.8:
                self.explainer.explain(rel, fact_a, fact_b)
                new_relationships.append(rel)

        # 9. Save relationships
        rel_repo.save_batch(new_relationships)

        elapsed = time.time() - start_time
        document.processing_status = "completed"
        document.processing_duration = round(elapsed, 2)
        doc_repo.save_document(document)

        # Log processing run
        run_record = ProcessingRunORM(
            run_id=f"run_{document.document_id}",
            document_id=document.document_id,
            facts_extracted=len(new_facts),
            relationships_found=len(new_relationships),
            duration_seconds=elapsed,
            status="completed"
        )
        db.add(run_record)
        db.commit()
        db.close()

        logger.info(f"Ingested {document.filename}: {len(new_facts)} facts, {len(new_relationships)} relationships in {elapsed:.2f}s.")

        return {
            "status": "success",
            "document_id": document.document_id,
            "filename": document.filename,
            "page_count": len(document.pages),
            "facts_extracted": len(new_facts),
            "relationships_discovered": len(new_relationships),
            "processing_duration": round(elapsed, 2)
        }
