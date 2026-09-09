"""
Fact Extractor Pipeline.
Coordinates candidate context feeding into the LLM provider, applies deterministic normalization
and entity resolution, and links each Fact to verified Evidence records.
"""

import uuid
import logging
from typing import List, Dict, Any, Optional
from models.document import Document
from models.evidence import Evidence
from models.fact import Fact, Period
from providers.base import LLMProvider
from core.normalizer import Normalizer
from core.entity_resolver import EntityResolver
from core.candidate_detector import CandidateDetector
from core.chunker import Chunker

logger = logging.getLogger(__name__)

class FactExtractor:
    """Extracts, normalizes, and grounds facts from document pages and evidence."""

    def __init__(self, provider: LLMProvider):
        self.provider = provider
        self.chunker = Chunker()

    def extract_facts_from_evidence(
        self,
        evidence_list: List[Evidence],
        document: Document,
        max_candidates: Optional[int] = None
    ) -> List[Fact]:
        """
        Process evidence through candidate detection, LLM extraction, and deterministic normalization.
        """
        candidates = CandidateDetector.filter_candidate_evidence(evidence_list)
        if max_candidates:
            candidates = candidates[:max_candidates]

        logger.info(f"Filtered {len(candidates)} candidate evidence blocks from {len(evidence_list)} total blocks.")

        chunks = self.chunker.create_chunks(candidates)
        extracted_facts: List[Fact] = []
        seen_canonical_signatures = set()

        for chunk in chunks:
            raw_fact_dicts = self.provider.extract_facts(
                context_text=chunk.text,
                evidence=chunk.primary_evidence,
                document_name=document.filename
            )

            for item in raw_fact_dicts:
                # 1. Resolve entity & predicate
                raw_subject = item.get("subject") or "Unknown"
                raw_predicate = item.get("predicate") or "unknown"
                canonical_subject, ent_conf = EntityResolver.resolve_entity(raw_subject)
                canonical_predicate, pred_conf = EntityResolver.resolve_predicate(raw_predicate)

                # 2. Normalize period
                raw_period = item.get("period")
                norm_period = Normalizer.normalize_period(raw_period)

                # 3. Normalize value & currency
                raw_val = item.get("value")
                val_type = item.get("value_type", "numeric")
                raw_unit = item.get("unit")

                canonical_val = None
                canonical_unit = raw_unit
                currency = item.get("currency")
                numeric_val = None

                if val_type in ("currency", "numeric"):
                    num = Normalizer.normalize_number(raw_val)
                    numeric_val = num
                    if val_type == "currency" or currency:
                        c_val, curr, c_unit = Normalizer.normalize_currency_and_value(
                            str(raw_val), raw_val=num, raw_unit=raw_unit
                        )
                        canonical_val = c_val
                        currency = curr or currency
                        canonical_unit = c_unit
                    else:
                        canonical_val = num
                elif val_type == "percentage":
                    num = Normalizer.normalize_percentage(raw_val)
                    numeric_val = num
                    canonical_val = num
                    canonical_unit = "percent"

                # 4. Normalize business scope
                b_scope = item.get("business_scope")
                if b_scope:
                    b_scope = b_scope.lower().strip()

                # Deduplicate exact identical facts from same evidence block
                sig = f"{canonical_subject}|{canonical_predicate}|{canonical_val}|{norm_period.label if norm_period else ''}|{chunk.page_number}"
                if sig in seen_canonical_signatures:
                    continue
                seen_canonical_signatures.add(sig)

                fact_id = f"fact_{uuid.uuid4().hex[:10]}"
                ev_id = chunk.primary_evidence.evidence_id

                fact = Fact(
                    fact_id=fact_id,
                    subject=canonical_subject,
                    predicate=canonical_predicate,
                    object_value=raw_val,
                    value_type=val_type,
                    numeric_value=numeric_val,
                    canonical_value=canonical_val,
                    unit=raw_unit,
                    canonical_unit=canonical_unit,
                    currency=currency,
                    period=norm_period,
                    start_date=norm_period.start_date if norm_period else None,
                    end_date=norm_period.end_date if norm_period else None,
                    geographic_scope=item.get("geographic_scope", "India"),
                    business_scope=b_scope,
                    qualifiers=item.get("qualifiers", []),
                    raw_text=item.get("evidence_text") or chunk.primary_evidence.text[:200],
                    confidence=round(float(item.get("confidence", 0.9)) * ent_conf * pred_conf, 2),
                    evidence_id=ev_id,
                    document_id=document.document_id,
                    page_number=chunk.page_number,
                    document_name=document.filename,
                    extraction_status="valid"
                )
                extracted_facts.append(fact)

        return extracted_facts
