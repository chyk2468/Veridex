"""
Database configuration and SQLAlchemy ORM models.
"""

from datetime import datetime
from sqlalchemy import create_engine, Column, String, Integer, Float, Text, JSON, DateTime, ForeignKey, Index
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from core.config import settings
from pathlib import Path

Base = declarative_base()

class DocumentORM(Base):
    __tablename__ = "documents"

    document_id = Column(String(64), primary_key=True)
    filename = Column(String(255), nullable=False)
    title = Column(String(255), nullable=True)
    page_count = Column(Integer, nullable=False)
    content_hash = Column(String(64), nullable=False, unique=True, index=True)
    upload_timestamp = Column(DateTime, default=datetime.utcnow)
    processing_status = Column(String(32), default="pending")
    processing_duration = Column(Float, nullable=True)
    extraction_method = Column(String(64), default="pymupdf")
    meta_info = Column("metadata", JSON, default=dict)

    pages = relationship("PageORM", back_populates="document", cascade="all, delete-orphan")
    evidence = relationship("EvidenceORM", back_populates="document", cascade="all, delete-orphan")
    facts = relationship("FactORM", back_populates="document", cascade="all, delete-orphan")

class PageORM(Base):
    __tablename__ = "pages"

    page_id = Column(String(64), primary_key=True)
    document_id = Column(String(64), ForeignKey("documents.document_id", ondelete="CASCADE"), nullable=False)
    page_number = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    extraction_method = Column(String(64), default="pymupdf")
    meta_info = Column("metadata", JSON, default=dict)

    document = relationship("DocumentORM", back_populates="pages")

class EvidenceORM(Base):
    __tablename__ = "evidence"

    evidence_id = Column(String(64), primary_key=True)
    document_id = Column(String(64), ForeignKey("documents.document_id", ondelete="CASCADE"), nullable=False, index=True)
    page_id = Column(String(64), nullable=True)
    page_number = Column(Integer, nullable=False)
    section = Column(String(255), nullable=True)
    text = Column(Text, nullable=False)
    bbox = Column(JSON, nullable=True)
    evidence_type = Column(String(32), default="text")
    extraction_method = Column(String(64), default="pymupdf")
    confidence = Column(Float, default=1.0)
    document_name = Column(String(255), nullable=True)

    document = relationship("DocumentORM", back_populates="evidence")

class FactORM(Base):
    __tablename__ = "facts"

    fact_id = Column(String(64), primary_key=True)
    subject = Column(String(255), nullable=False, index=True)
    predicate = Column(String(255), nullable=False, index=True)
    object_value = Column(Text, nullable=False)
    value_type = Column(String(32), default="numeric")
    numeric_value = Column(Float, nullable=True)
    canonical_value = Column(Float, nullable=True)
    unit = Column(String(64), nullable=True)
    canonical_unit = Column(String(64), nullable=True)
    currency = Column(String(16), nullable=True)
    period_label = Column(String(64), nullable=True, index=True)
    period_type = Column(String(32), nullable=True)
    start_date = Column(String(32), nullable=True)
    end_date = Column(String(32), nullable=True)
    geographic_scope = Column(String(64), default="India")
    population_scope = Column(String(64), nullable=True)
    business_scope = Column(String(64), nullable=True)
    category = Column(String(64), default="general")
    qualifiers = Column(JSON, default=list)
    estimate_status = Column(String(64), nullable=True)
    publication_date = Column(String(64), nullable=True)
    data_vintage = Column(String(64), nullable=True)
    revision_status = Column(String(64), nullable=True)
    upstream_source = Column(String(255), nullable=True)
    raw_text = Column(Text, nullable=False)
    confidence = Column(Float, default=1.0)
    evidence_id = Column(String(64), ForeignKey("evidence.evidence_id", ondelete="CASCADE"), nullable=False)
    document_id = Column(String(64), ForeignKey("documents.document_id", ondelete="CASCADE"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    document_name = Column(String(255), nullable=True)
    extraction_status = Column(String(32), default="valid")
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("DocumentORM", back_populates="facts")

class RelationshipORM(Base):
    __tablename__ = "relationships"

    relationship_id = Column(String(64), primary_key=True)
    fact_a_id = Column(String(64), ForeignKey("facts.fact_id", ondelete="CASCADE"), nullable=False, index=True)
    fact_b_id = Column(String(64), ForeignKey("facts.fact_id", ondelete="CASCADE"), nullable=False, index=True)
    relationship_type = Column(String(32), nullable=False, index=True)
    comparison_features = Column(JSON, default=dict)
    confidence = Column(Float, default=1.0)
    confidence_breakdown = Column(JSON, default=dict)
    explanation = Column(Text, nullable=False)
    evidence_a_id = Column(String(64), nullable=True)
    evidence_b_id = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ProcessingRunORM(Base):
    __tablename__ = "processing_runs"

    run_id = Column(String(64), primary_key=True)
    document_id = Column(String(64), nullable=False)
    facts_extracted = Column(Integer, default=0)
    relationships_found = Column(Integer, default=0)
    duration_seconds = Column(Float, nullable=True)
    status = Column(String(32), default="success")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Database connection helper
Path(settings.DATA_DIR).mkdir(parents=True, exist_ok=True)
engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)
