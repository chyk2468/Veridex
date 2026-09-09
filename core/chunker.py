"""
Contextual Chunker for Fact Extraction.
Aggregates candidate evidence into cohesive contextual windows preserving section and table boundaries.
Merges adjacent blocks on the same page to ensure values and their metric labels remain unified.
"""

from typing import List, Dict, Any, Tuple
from models.evidence import Evidence

class ContextChunk:
    def __init__(self, chunk_id: str, document_id: str, page_number: int, text: str, primary_evidence: Evidence, associated_evidence_ids: List[str] = None):
        self.chunk_id = chunk_id
        self.document_id = document_id
        self.page_number = page_number
        self.text = text
        self.primary_evidence = primary_evidence
        self.associated_evidence_ids = associated_evidence_ids or [primary_evidence.evidence_id]

class Chunker:
    """Groups evidence items into coherent, context-rich windows for fact extraction."""

    def __init__(self, window_size: int = 3):
        self.window_size = window_size

    def create_chunks(self, candidate_evidence: List[Evidence]) -> List[ContextChunk]:
        """
        Creates context chunks by aggregating adjacent candidate blocks on the same page.
        This binds metrics (e.g. '₹8,142 Cr') with their corresponding label (e.g. 'FY24 revenue').
        """
        if not candidate_evidence:
            return []

        # Group by (document_id, page_number)
        page_groups: Dict[Tuple[str, int], List[Evidence]] = {}
        for ev in candidate_evidence:
            key = (ev.document_id, ev.page_number)
            if key not in page_groups:
                page_groups[key] = []
            page_groups[key].append(ev)

        chunks: List[ContextChunk] = []
        chunk_counter = 0

        for (doc_id, page_num), ev_list in page_groups.items():
            # For each evidence item, build a contextual window of adjacent items on same page
            for i, ev in enumerate(ev_list):
                # If table, preserve table evidence directly
                if ev.evidence_type == "table":
                    chunks.append(ContextChunk(
                        chunk_id=f"chunk_{doc_id}_p{page_num}_tbl_{chunk_counter}",
                        document_id=doc_id,
                        page_number=page_num,
                        text=ev.text,
                        primary_evidence=ev
                    ))
                    chunk_counter += 1
                    continue

                # Merge window around ev
                start_idx = max(0, i - 1)
                end_idx = min(len(ev_list), i + 2)
                window_evs = ev_list[start_idx:end_idx]

                merged_text = "\n".join(e.text for e in window_evs)
                chunk_id = f"chunk_{doc_id}_p{page_num}_{chunk_counter}"
                chunk_counter += 1

                chunks.append(ContextChunk(
                    chunk_id=chunk_id,
                    document_id=doc_id,
                    page_number=page_num,
                    text=merged_text,
                    primary_evidence=ev,
                    associated_evidence_ids=[e.evidence_id for e in window_evs]
                ))

        return chunks
