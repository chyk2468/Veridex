"""
Repository implementations for SQLite/SQLAlchemy data access.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from storage.database import DocumentORM, PageORM, EvidenceORM, FactORM, RelationshipORM, ProcessingRunORM
from models.document import Document, Page
from models.evidence import Evidence
from models.fact import Fact, Period
from models.relationship import Relationship, RelationshipType

class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_document(self, doc: Document) -> DocumentORM:
        orm = DocumentORM(
            document_id=doc.document_id,
            filename=doc.filename,
            title=doc.title,
            page_count=doc.page_count,
            content_hash=doc.content_hash,
            processing_status=doc.processing_status,
            processing_duration=doc.processing_duration,
            extraction_method=doc.extraction_method,
            meta_info=doc.metadata
        )
        self.db.merge(orm)
        
        # Save pages
        for p in doc.pages:
            p_orm = PageORM(
                page_id=p.page_id,
                document_id=doc.document_id,
                page_number=p.page_number,
                text=p.text,
                extraction_method=p.extraction_method,
                meta_info=p.metadata
            )
            self.db.merge(p_orm)

        self.db.commit()
        return orm

    def get_by_id(self, doc_id: str) -> Optional[DocumentORM]:
        return self.db.query(DocumentORM).filter(DocumentORM.document_id == doc_id).first()

    def get_by_hash(self, content_hash: str) -> Optional[DocumentORM]:
        return self.db.query(DocumentORM).filter(DocumentORM.content_hash == content_hash).first()

    def get_all(self) -> List[DocumentORM]:
        return self.db.query(DocumentORM).all()

class EvidenceRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_batch(self, evidence_list: List[Evidence]):
        for ev in evidence_list:
            orm = EvidenceORM(
                evidence_id=ev.evidence_id,
                document_id=ev.document_id,
                page_id=ev.page_id,
                page_number=ev.page_number,
                section=ev.section,
                text=ev.text,
                bbox=ev.bbox,
                evidence_type=ev.evidence_type,
                extraction_method=ev.extraction_method,
                confidence=ev.confidence,
                document_name=ev.document_name
            )
            self.db.merge(orm)
        self.db.commit()

    def get_by_id(self, ev_id: str) -> Optional[EvidenceORM]:
        return self.db.query(EvidenceORM).filter(EvidenceORM.evidence_id == ev_id).first()

    def get_by_document(self, doc_id: str) -> List[EvidenceORM]:
        return self.db.query(EvidenceORM).filter(EvidenceORM.document_id == doc_id).all()

class FactRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_batch(self, facts: List[Fact]):
        for f in facts:
            orm = FactORM(
                fact_id=f.fact_id,
                subject=f.subject,
                predicate=f.predicate,
                object_value=str(f.object_value),
                value_type=f.value_type,
                numeric_value=f.numeric_value,
                canonical_value=f.canonical_value,
                unit=f.unit,
                canonical_unit=f.canonical_unit,
                currency=f.currency,
                period_label=f.period.label if f.period else None,
                period_type=f.period.period_type if f.period else None,
                start_date=f.period.start_date if f.period else None,
                end_date=f.period.end_date if f.period else None,
                geographic_scope=f.geographic_scope,
                population_scope=f.population_scope,
                business_scope=f.business_scope,
                category=f.category,
                qualifiers=f.qualifiers,
                estimate_status=f.estimate_status,
                publication_date=f.publication_date,
                data_vintage=f.data_vintage,
                revision_status=f.revision_status,
                upstream_source=f.upstream_source,
                raw_text=f.raw_text,
                confidence=f.confidence,
                evidence_id=f.evidence_id,
                document_id=f.document_id,
                page_number=f.page_number,
                document_name=f.document_name,
                extraction_status=f.extraction_status
            )
            self.db.merge(orm)
        self.db.commit()

    def get_by_id(self, fact_id: str) -> Optional[Fact]:
        orm = self.db.query(FactORM).filter(FactORM.fact_id == fact_id).first()
        return self._to_model(orm) if orm else None

    def get_all(self) -> List[Fact]:
        orms = self.db.query(FactORM).all()
        return [self._to_model(o) for o in orms]

    def get_by_document(self, doc_id: str) -> List[Fact]:
        orms = self.db.query(FactORM).filter(FactORM.document_id == doc_id).all()
        return [self._to_model(o) for o in orms]

    def _to_model(self, orm: FactORM) -> Fact:
        per = None
        if orm.period_label:
            per = Period(
                label=orm.period_label,
                period_type=orm.period_type or "unknown",
                start_date=orm.start_date,
                end_date=orm.end_date
            )

        return Fact(
            fact_id=orm.fact_id,
            subject=orm.subject,
            predicate=orm.predicate,
            object_value=orm.object_value,
            value_type=orm.value_type,
            numeric_value=orm.numeric_value,
            canonical_value=orm.canonical_value,
            unit=orm.unit,
            canonical_unit=orm.canonical_unit,
            currency=orm.currency,
            period=per,
            start_date=orm.start_date,
            end_date=orm.end_date,
            geographic_scope=orm.geographic_scope,
            population_scope=orm.population_scope,
            business_scope=orm.business_scope,
            category=orm.category,
            qualifiers=orm.qualifiers or [],
            estimate_status=orm.estimate_status,
            publication_date=orm.publication_date,
            data_vintage=orm.data_vintage,
            revision_status=orm.revision_status,
            upstream_source=orm.upstream_source,
            raw_text=orm.raw_text,
            confidence=orm.confidence,
            evidence_id=orm.evidence_id,
            document_id=orm.document_id,
            page_number=orm.page_number,
            document_name=orm.document_name,
            extraction_status=orm.extraction_status
        )

class RelationshipRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_batch(self, relationships: List[Relationship]):
        for rel in relationships:
            orm = RelationshipORM(
                relationship_id=rel.relationship_id,
                fact_a_id=rel.fact_a_id,
                fact_b_id=rel.fact_b_id,
                relationship_type=rel.relationship_type.value,
                comparison_features=rel.comparison_features,
                confidence=rel.confidence,
                confidence_breakdown=rel.confidence_breakdown,
                explanation=rel.explanation,
                evidence_a_id=rel.evidence_a_id,
                evidence_b_id=rel.evidence_b_id
            )
            self.db.merge(orm)
        self.db.commit()

    def get_all(self) -> List[Relationship]:
        orms = self.db.query(RelationshipORM).all()
        return [self._to_model(o) for o in orms]

    def get_by_id(self, relationship_id: str) -> Optional[Relationship]:
        orm = self.db.query(RelationshipORM).filter(RelationshipORM.relationship_id == relationship_id).first()
        return self._to_model(orm) if orm else None


    def get_by_fact(self, fact_id: str) -> List[Relationship]:
        orms = self.db.query(RelationshipORM).filter(
            (RelationshipORM.fact_a_id == fact_id) | (RelationshipORM.fact_b_id == fact_id)
        ).all()
        return [self._to_model(o) for o in orms]

    def get_by_type(self, rel_type: str) -> List[Relationship]:
        orms = self.db.query(RelationshipORM).filter(RelationshipORM.relationship_type == rel_type).all()
        return [self._to_model(o) for o in orms]

    def _to_model(self, orm: RelationshipORM) -> Relationship:
        return Relationship(
            relationship_id=orm.relationship_id,
            fact_a_id=orm.fact_a_id,
            fact_b_id=orm.fact_b_id,
            relationship_type=RelationshipType(orm.relationship_type),
            comparison_features=orm.comparison_features or {},
            confidence=orm.confidence,
            confidence_breakdown=orm.confidence_breakdown or {},
            explanation=orm.explanation,
            evidence_a_id=orm.evidence_a_id,
            evidence_b_id=orm.evidence_b_id
        )
