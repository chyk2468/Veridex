"""
FastAPI REST API for Fact Knowledge Layer.
Provides endpoints for document ingestion, fact exploration, relationship queries,
grounded evidence inspection, semantic search, and assignment showcase cases.
"""

import os
import shutil
import uuid
from typing import List, Dict, Any, Optional
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel

from core.config import settings
from core.pipeline import FactKnowledgePipeline
from storage.database import SessionLocal, init_db, DocumentORM, FactORM, RelationshipORM, EvidenceORM
from storage.repositories import (
    DocumentRepository,
    EvidenceRepository,
    FactRepository,
    RelationshipRepository
)
from models.fact import Fact
from models.relationship import Relationship, RelationshipType
from evaluation.dataset import get_benchmark_dataset, FAILURE_ANALYSIS_CASES

app = FastAPI(
    title="Fact Knowledge Layer API",
    description="Explainable, generalized knowledge layer for grounding, extracting, normalizing, and comparing facts across documents.",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pipeline singleton
pipeline = FactKnowledgePipeline()

# --- HEALTH & STATS ---

@app.get("/health", tags=["System"])
def health_check():
    """System health check verifying database and provider connectivity."""
    db = SessionLocal()
    try:
        doc_count = db.query(DocumentORM).count()
        db_ok = True
    except Exception:
        db_ok = False
        doc_count = 0
    finally:
        db.close()

    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
        "provider": "groq" if pipeline.provider.is_available() else "offline_heuristic_fallback",
        "model": settings.GROQ_MODEL,
        "embedding_model": settings.EMBEDDING_MODEL,
        "indexed_documents": doc_count
    }

@app.get("/statistics", tags=["System"])
def get_statistics(db: Session = Depends(get_db)):
    """Summary metrics of all ingested knowledge, facts, and discovered relationships."""
    doc_count = db.query(DocumentORM).count()
    fact_count = db.query(FactORM).count()
    rel_count = db.query(RelationshipORM).count()
    ev_count = db.query(EvidenceORM).count()

    # Relationship counts by type
    rel_types = {}
    for r_type in [RelationshipType.CORROBORATED, RelationshipType.CONTRADICTED, RelationshipType.CONTEXTUAL_DIFFERENCE, RelationshipType.RELATED_BUT_DIFFERENT, RelationshipType.UNCERTAIN]:
        c = db.query(RelationshipORM).filter(RelationshipORM.relationship_type == r_type).count()
        rel_types[r_type.value] = c

    return {
        "total_documents": doc_count,
        "total_evidence_blocks": ev_count,
        "total_facts": fact_count,
        "total_relationships": rel_count,
        "relationships_breakdown": rel_types
    }

# --- DOCUMENT ENDPOINTS ---

@app.post("/documents/upload", tags=["Documents"])
async def upload_document(
    file: UploadFile = File(...),
    auto_process: bool = Query(True, description="Immediately run fact extraction pipeline")
):
    """
    Upload a PDF document. Saves to data/uploads and automatically extracts facts
    and discovers cross-document relationships.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF documents are supported.")

    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    file_path = settings.UPLOAD_DIR / f"{uuid.uuid4().hex[:8]}_{file.filename}"
    
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    if auto_process:
        try:
            result = pipeline.ingest_document(str(file_path))
            return {
                "message": "Document uploaded and ingested successfully.",
                "filename": file.filename,
                "ingestion_result": result
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

    return {
        "message": "Document uploaded successfully.",
        "filename": file.filename,
        "file_path": str(file_path),
        "status": "pending_processing"
    }

@app.get("/documents", tags=["Documents"])
def list_documents(db: Session = Depends(get_db)):
    """List all ingested documents and their status."""
    repo = DocumentRepository(db)
    docs = repo.get_all()
    out = []
    for d in docs:
        fact_count = db.query(FactORM).filter(FactORM.document_id == d.document_id).count()
        out.append({
            "document_id": d.document_id,
            "filename": d.filename,
            "page_count": d.page_count,
            "upload_timestamp": d.upload_timestamp.isoformat() if d.upload_timestamp else None,
            "status": d.processing_status,
            "processing_duration": d.processing_duration,
            "facts_extracted": fact_count
        })
    return out

@app.get("/documents/{document_id}", tags=["Documents"])
def get_document(document_id: str, db: Session = Depends(get_db)):
    """Get metadata and pages for a specific document."""
    repo = DocumentRepository(db)
    doc = repo.get_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return doc.model_dump()

# --- FACTS ENDPOINTS ---

@app.get("/facts", tags=["Facts"])
def list_facts(
    subject: Optional[str] = Query(None, description="Filter by canonical subject entity"),
    predicate: Optional[str] = Query(None, description="Filter by metric or predicate"),
    business_scope: Optional[str] = Query(None, description="Filter by scope (e.g. standalone, consolidated)"),
    document_id: Optional[str] = Query(None, description="Filter by document ID"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Retrieve indexed facts with optional filters."""
    query = db.query(FactORM)
    if subject:
        query = query.filter(FactORM.subject.ilike(f"%{subject}%"))
    if predicate:
        query = query.filter(FactORM.predicate.ilike(f"%{predicate}%"))
    if business_scope:
        query = query.filter(FactORM.business_scope.ilike(f"%{business_scope}%"))
    if document_id:
        query = query.filter(FactORM.document_id == document_id)

    total = query.count()
    rows = query.offset(offset).limit(limit).all()
    repo = FactRepository(db)
    facts = [repo._to_model(r).model_dump() for r in rows]

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "facts": facts
    }

@app.get("/facts/{fact_id}", tags=["Facts"])
def get_fact(fact_id: str, db: Session = Depends(get_db)):
    """Get a single fact along with its grounded evidence snippet and page coordinates."""
    fact_repo = FactRepository(db)
    ev_repo = EvidenceRepository(db)

    fact = fact_repo.get_by_id(fact_id)
    if not fact:
        raise HTTPException(status_code=404, detail="Fact not found.")

    evidence = ev_repo.get_by_id(fact.evidence_id) if fact.evidence_id else None

    return {
        "fact": fact.model_dump(),
        "evidence": evidence.model_dump() if evidence else None
    }

@app.get("/facts/{fact_id}/relationships", tags=["Facts"])
def get_fact_relationships(fact_id: str, db: Session = Depends(get_db)):
    """Retrieve all relationships (corroborations, contradictions, contextual differences) involving this fact."""
    rel_repo = RelationshipRepository(db)
    fact_repo = FactRepository(db)

    relationships = rel_repo.get_by_fact(fact_id)
    out = []
    for r in relationships:
        counterpart_id = r.fact_b_id if r.fact_a_id == fact_id else r.fact_a_id
        counterpart_fact = fact_repo.get_by_id(counterpart_id)
        out.append({
            "relationship": r.model_dump(),
            "counterpart_fact": counterpart_fact.model_dump() if counterpart_fact else None
        })
    return out

# --- RELATIONSHIPS ENDPOINTS ---

@app.get("/relationships", tags=["Relationships"])
def list_relationships(
    type: Optional[str] = Query(None, description="Filter by relationship type (CORROBORATED, CONTRADICTED, CONTEXTUAL_DIFFERENCE, UNCERTAIN)"),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0),
    document_id: Optional[str] = Query(None, description="Filter by involved document ID"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """List classified relationships between facts with feature breakdown and explanations."""
    query = db.query(RelationshipORM).filter(RelationshipORM.confidence >= min_confidence)
    if type:
        query = query.filter(RelationshipORM.relationship_type == type.upper())
    
    total = query.count()
    rows = query.offset(offset).limit(limit).all()
    rel_repo = RelationshipRepository(db)
    fact_repo = FactRepository(db)

    results = []
    for r in rows:
        rel = rel_repo._to_model(r)
        f_a = fact_repo.get_by_id(rel.fact_a_id)
        f_b = fact_repo.get_by_id(rel.fact_b_id)
        results.append({
            "relationship": rel.model_dump(),
            "fact_a": f_a.model_dump() if f_a else None,
            "fact_b": f_b.model_dump() if f_b else None
        })

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "relationships": results
    }

@app.get("/relationships/{relationship_id}", tags=["Relationships"])
def get_relationship(relationship_id: str, db: Session = Depends(get_db)):
    """Detailed view of a relationship including both facts, comparison features, and explanation."""
    rel_repo = RelationshipRepository(db)
    fact_repo = FactRepository(db)
    ev_repo = EvidenceRepository(db)

    rel = rel_repo.get_by_id(relationship_id)
    if not rel:
        raise HTTPException(status_code=404, detail="Relationship not found.")

    fact_a = fact_repo.get_by_id(rel.fact_a_id)
    fact_b = fact_repo.get_by_id(rel.fact_b_id)
    ev_a = ev_repo.get_by_id(fact_a.evidence_id) if fact_a and fact_a.evidence_id else None
    ev_b = ev_repo.get_by_id(fact_b.evidence_id) if fact_b and fact_b.evidence_id else None

    return {
        "relationship": rel.model_dump(),
        "fact_a": fact_a.model_dump() if fact_a else None,
        "evidence_a": ev_a.model_dump() if ev_a else None,
        "fact_b": fact_b.model_dump() if fact_b else None,
        "evidence_b": ev_b.model_dump() if ev_b else None
    }

# --- SEARCH ENDPOINT ---

@app.get("/search", tags=["Search"])
def search_facts(
    q: str = Query(..., description="Search query string"),
    top_k: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """
    Semantic and keyword search over indexed facts.
    Returns matched facts ranked by semantic similarity and evidence relevance.
    """
    fact_repo = FactRepository(db)
    ev_repo = EvidenceRepository(db)

    # 1. Vector similarity search
    top_fact_ids = pipeline.vector_store.search(q, top_k=top_k)
    results = []

    for fact_id, sim in top_fact_ids:
        fact = fact_repo.get_by_id(fact_id)
        if fact:
            ev = ev_repo.get_by_id(fact.evidence_id) if fact.evidence_id else None
            results.append({
                "similarity_score": round(sim, 4),
                "fact": fact.model_dump(),
                "evidence": ev.model_dump() if ev else None
            })

    # If vector search returned no results, fallback to SQL LIKE search
    if not results:
        terms = q.split()
        query = db.query(FactORM)
        for term in terms:
            query = query.filter(
                (FactORM.subject.ilike(f"%{term}%")) |
                (FactORM.predicate.ilike(f"%{term}%")) |
                (FactORM.raw_text.ilike(f"%{term}%"))
            )
        sql_rows = query.limit(top_k).all()
        for r in sql_rows:
            f = fact_repo._to_model(r)
            ev = ev_repo.get_by_id(f.evidence_id) if f.evidence_id else None
            results.append({
                "similarity_score": 0.50,
                "fact": f.model_dump(),
                "evidence": ev.model_dump() if ev else None
            })

    return {
        "query": q,
        "total_results": len(results),
        "results": results
    }

# --- SHOWCASE CASES ENDPOINT (THE 4 MANDATORY ASSIGNMENT DEMOS) ---

@app.get("/cases", tags=["Showcase"])
def get_showcase_cases():
    """
    Returns the four mandatory demonstration cases required by the Superjoin Assignment:
    1. Corroboration: Delhivery FY24 Consolidated Revenue (₹8,142 Cr vs ₹81,415.38 million).
    2. Genuine Contradiction: India Real GDP Growth FY2024/25 (6.4% Economic Survey vs 6.5% IMF).
    3. Contextual Difference: Delhivery Standalone vs Consolidated, or Q4 vs Full Year.
    4. Failure Analysis: Multi-column table layout cell-to-header misattribution and qualifier omission.
    """
    dataset = get_benchmark_dataset()

    # Case 1: Corroboration
    case_1 = next((c for c in dataset if c["id"] == "corrob_01"), None)
    
    # Case 2: Contradiction
    case_2 = next((c for c in dataset if c["id"] == "contrad_01"), None)

    # Case 3: Contextual Difference
    case_3 = next((c for c in dataset if c["id"] == "context_01"), None)

    # Case 4: Failure Analysis Cases
    case_4 = FAILURE_ANALYSIS_CASES

    return {
        "case_1_corroboration": {
            "title": "Case 1: Cross-Document Numerical Corroboration",
            "summary": "Delhivery FY24 Consolidated Revenue reported in ₹ Crores in Earnings Presentation vs ₹ Millions in Annual Report.",
            "data": case_1
        },
        "case_2_contradiction": {
            "title": "Case 2: Genuine Macroeconomic Contradiction",
            "summary": "India Real GDP Growth for FY2024/25: 6.4% in Economic Survey vs 6.5% in IMF Article IV Consultation.",
            "data": case_2
        },
        "case_3_contextual_difference": {
            "title": "Case 3: Contextual Difference (Not a Contradiction)",
            "summary": "Delhivery FY24 Standalone (₹74,540.82 million) vs Consolidated (₹81,415.38 million) Revenue.",
            "data": case_3
        },
        "case_4_failure_analysis": {
            "title": "Case 4: Extraction & Reasoning Failure Analysis",
            "summary": "Analysis of multi-column table layout misattribution, qualifier omission, and discrete count continuous tolerance failures.",
            "data": case_4
        }
    }
