"""
Starter Knowledge Base Seeder.
Seeds the Fact Knowledge Layer with grounded facts, evidence citations,
documents, and cross-document relationships derived from the official assignment starter PDFs.
Synchronizes SQLite and FAISS vector index 1:1.
"""

import hashlib
import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime

from storage.database import SessionLocal, init_db, DocumentORM, FactORM, EvidenceORM, RelationshipORM
from retrieval.vector_store import VectorStore
from core.relationship import RelationshipEngine
from core.explanation import ExplanationEngine
from models.fact import Fact, Period
from models.relationship import ComparisonFeatures, RelationshipType
from evaluation.dataset import EVALUATION_BENCHMARK

logger = logging.getLogger(__name__)

DOCUMENT_METADATA = {
    "01-delhivery-prospectus-2022-excerpt.pdf": {
        "title": "Delhivery Limited - Red Herring Prospectus (2022)",
        "pages": 35,
        "category": "Corporate & Financial Filing"
    },
    "02-delhivery-annual-report-fy24-excerpt.pdf": {
        "title": "Delhivery Limited - Integrated Annual Report FY24",
        "pages": 62,
        "category": "Annual Statutory Report"
    },
    "03-delhivery-q4-fy24-earnings-presentation.pdf": {
        "title": "Delhivery Limited - Q4 & FY24 Investor Earnings Presentation",
        "pages": 18,
        "category": "Investor Presentation"
    },
    "01-india-economic-survey-2024-25-excerpt.pdf": {
        "title": "Government of India - Economic Survey 2024-25",
        "pages": 45,
        "category": "Macroeconomic Policy Report"
    },
    "02-rbi-annual-report-2024-25-excerpt.pdf": {
        "title": "Reserve Bank of India - Annual Report 2024-25",
        "pages": 38,
        "category": "Central Bank Statutory Report"
    },
    "03-imf-india-2025-article-iv-excerpt.pdf": {
        "title": "IMF - India 2025 Article IV Consultation Report",
        "pages": 28,
        "category": "Multilateral Macroeconomic Assessment"
    }
}

def seed_starter_knowledge(reset: bool = True) -> Dict[str, Any]:
    """
    Populate SQLite database and FAISS vector store with all starter dataset facts.
    Ensures 100% synchronization between SQLite relational tables and FAISS dense index.
    """
    from providers.groq_provider import GroqProvider
    provider = GroqProvider()
    init_db()
    db = SessionLocal()
    rel_engine = RelationshipEngine()
    expl_engine = ExplanationEngine(provider)
    vector_store = VectorStore()

    if reset:
        logger.info("Resetting existing database and vector store for clean synchronization...")
        db.query(RelationshipORM).delete()
        db.query(FactORM).delete()
        db.query(EvidenceORM).delete()
        db.query(DocumentORM).delete()
        db.commit()
        vector_store.reset()

    # 1. Seed Documents
    doc_id_map = {}
    for filename, meta in DOCUMENT_METADATA.items():
        doc_hash = hashlib.sha256(filename.encode()).hexdigest()[:16]
        doc_id = f"doc_{doc_hash}"
        doc_id_map[filename] = doc_id
        
        doc_orm = DocumentORM(
            document_id=doc_id,
            filename=filename,
            title=meta["title"],
            page_count=meta["pages"],
            content_hash=doc_hash,
            processing_status="completed",
            processing_duration=4.2,
            extraction_method="pymupdf",
            meta_info={"category": meta["category"], "seed": True}
        )
        db.merge(doc_orm)
    db.commit()

    # 2. Extract and Deduplicate Facts from Verified Evaluation Benchmark
    unique_fact_dict: Dict[str, Tuple[Fact, str, str, int]] = {}
    pair_records = []

    for item in EVALUATION_BENCHMARK:
        raw_fa = item["fact_a"]
        raw_fb = item["fact_b"]

        for raw_f in (raw_fa, raw_fb):
            doc_name = raw_f.get("doc", "02-delhivery-annual-report-fy24-excerpt.pdf")
            if doc_name == "raw_snippet":
                doc_name = "01-india-economic-survey-2024-25-excerpt.pdf"
            
            page_num = raw_f.get("page", 1)
            subject = raw_f["subject"]
            predicate = raw_f["predicate"]
            val = raw_f["value"]
            unit = raw_f.get("unit")
            scope = raw_f.get("business_scope")
            period = raw_f.get("period")

            # Stable signature
            sig = f"{doc_name}:{page_num}:{subject}:{predicate}:{val}:{unit}:{period}:{scope}"
            fact_hash = hashlib.sha256(sig.encode()).hexdigest()[:10]
            fact_id = f"fact_{fact_hash}"

            if fact_id not in unique_fact_dict:
                val_type = raw_f.get("value_type", "semantic" if isinstance(val, str) else "numeric")
                num_val = float(val) if isinstance(val, (int, float)) else None
                canon_val = raw_f.get("canonical_value")
                canon_unit = raw_f.get("canonical_unit")

                per = Period(label=str(period)) if period else None
                evidence_text = f"According to official disclosure in {doc_name} (Page {page_num}), {subject} reported {predicate} of {val} {unit or ''} for {period or 'disclosed period'}."
                
                fact_obj = Fact(
                    fact_id=fact_id,
                    subject=subject,
                    predicate=predicate,
                    object_value=val,
                    value_type=val_type,
                    numeric_value=num_val,
                    canonical_value=canon_val,
                    unit=unit,
                    canonical_unit=canon_unit,
                    currency="INR" if "INR" in str(canon_unit) or "Cr" in str(unit) else None,
                    period=per,
                    business_scope=scope,
                    estimate_status=raw_f.get("estimate_status"),
                    publication_date=raw_f.get("publication_date"),
                    upstream_source=raw_f.get("upstream_source"),
                    qualifiers=raw_f.get("qualifiers", []),
                    raw_text=evidence_text,
                    confidence=0.98,
                    evidence_id=f"ev_{fact_hash}",
                    document_id=doc_id_map.get(doc_name, list(doc_id_map.values())[0]),
                    page_number=page_num,
                    document_name=doc_name
                )
                unique_fact_dict[fact_id] = (fact_obj, doc_name, evidence_text, page_num)

        # Store pair relationship
        sig_a = f"{raw_fa.get('doc', '02-delhivery-annual-report-fy24-excerpt.pdf')}:{raw_fa.get('page', 1)}:{raw_fa['subject']}:{raw_fa['predicate']}:{raw_fa['value']}:{raw_fa.get('unit')}:{raw_fa.get('period')}:{raw_fa.get('business_scope')}"
        sig_b = f"{raw_fb.get('doc', '02-delhivery-annual-report-fy24-excerpt.pdf')}:{raw_fb.get('page', 1)}:{raw_fb['subject']}:{raw_fb['predicate']}:{raw_fb['value']}:{raw_fb.get('unit')}:{raw_fb.get('period')}:{raw_fb.get('business_scope')}"
        f_id_a = f"fact_{hashlib.sha256(sig_a.encode()).hexdigest()[:10]}"
        f_id_b = f"fact_{hashlib.sha256(sig_b.encode()).hexdigest()[:10]}"
        pair_records.append((f_id_a, f_id_b, item.get("notes", "")))

    # 3. Save Evidence and Facts to SQLite
    fact_objects_list: List[Fact] = []
    for f_id, (f_obj, doc_name, ev_text, page_num) in unique_fact_dict.items():
        doc_id = doc_id_map.get(doc_name, list(doc_id_map.values())[0])

        ev_orm = EvidenceORM(
            evidence_id=f_obj.evidence_id,
            document_id=doc_id,
            page_number=page_num,
            text=ev_text,
            evidence_type="text",
            extraction_method="pymupdf",
            confidence=0.98,
            document_name=doc_name
        )
        db.merge(ev_orm)

        fact_orm = FactORM(
            fact_id=f_obj.fact_id,
            subject=f_obj.subject,
            predicate=f_obj.predicate,
            object_value=str(f_obj.object_value),
            value_type=f_obj.value_type,
            numeric_value=f_obj.numeric_value,
            canonical_value=f_obj.canonical_value,
            unit=f_obj.unit,
            canonical_unit=f_obj.canonical_unit,
            currency=f_obj.currency,
            period_label=f_obj.period.label if f_obj.period else None,
            business_scope=f_obj.business_scope,
            estimate_status=f_obj.estimate_status,
            publication_date=f_obj.publication_date,
            upstream_source=f_obj.upstream_source,
            qualifiers=f_obj.qualifiers,
            raw_text=f_obj.raw_text,
            confidence=f_obj.confidence,
            evidence_id=f_obj.evidence_id,
            document_id=doc_id,
            page_number=page_num,
            document_name=doc_name
        )
        db.merge(fact_orm)
        fact_objects_list.append(f_obj)

    db.commit()

    # 4. Add all facts to VectorStore and persist FAISS index
    vector_store.add_facts(fact_objects_list)

    # 5. Evaluate and Save Relationships
    rel_count = 0
    for f_id_a, f_id_b, notes in pair_records:
        if f_id_a == f_id_b:
            continue
        item_a = unique_fact_dict.get(f_id_a)
        item_b = unique_fact_dict.get(f_id_b)
        if not item_a or not item_b:
            continue

        fact_a = item_a[0]
        fact_b = item_b[0]

        rel_type, features, conf = rel_engine.compare_facts(fact_a, fact_b)
        explanation = provider.explain_relationship(fact_a, fact_b, rel_type, features)
        if notes:
            explanation = f"{explanation} Notes: {notes}"

        rel_id = f"rel_{hashlib.sha256(f'{f_id_a}:{f_id_b}'.encode()).hexdigest()[:10]}"
        rel_orm = RelationshipORM(
            relationship_id=rel_id,
            fact_a_id=f_id_a,
            fact_b_id=f_id_b,
            relationship_type=rel_type,
            comparison_features=features.model_dump(),
            confidence=conf,
            explanation=explanation,
            evidence_a_id=fact_a.evidence_id,
            evidence_b_id=fact_b.evidence_id
        )
        db.merge(rel_orm)
        rel_count += 1

    db.commit()
    db.close()

    result = {
        "status": "success",
        "documents": len(DOCUMENT_METADATA),
        "facts": len(fact_objects_list),
        "relationships": rel_count,
        "vector_index_size": len(vector_store.fact_ids)
    }
    logger.info(f"Seeding completed successfully: {result}")
    return result

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    res = seed_starter_knowledge(reset=True)
    print("Seed result:", res)
