"""
Candidate Fact Matcher.
Filters potential fact pairs using entity indexing, predicate compatibility,
and vector similarity to avoid O(N^2) pairwise comparisons.
"""

import logging
from typing import List, Tuple, Dict, Set, Optional
from models.fact import Fact
from core.entity_resolver import EntityResolver
from retrieval.vector_store import VectorStore

logger = logging.getLogger(__name__)

class CandidateMatcher:
    """Discovers plausible fact pairs for deterministic relationship evaluation."""

    def __init__(self, vector_store: Optional[VectorStore] = None):
        self.vector_store = vector_store

    def find_candidate_pairs(
        self,
        new_facts: List[Fact],
        existing_facts: List[Fact],
        similarity_threshold: float = 0.60
    ) -> List[Tuple[Fact, Fact]]:
        """
        Identify candidate pairs between newly ingested facts and existing facts.
        """
        candidate_pairs: List[Tuple[Fact, Fact]] = []
        seen_pairs: Set[Tuple[str, str]] = set()

        # Build lookup table for existing facts
        existing_by_id = {f.fact_id: f for f in existing_facts}

        for f_new in new_facts:
            # 1. Direct Entity & Predicate match pass
            for f_old in existing_facts:
                if f_new.fact_id == f_old.fact_id:
                    continue

                pair_key = tuple(sorted([f_new.fact_id, f_old.fact_id]))
                if pair_key in seen_pairs:
                    continue

                ent_match, _ = EntityResolver.match_entities(f_new.subject, f_old.subject)
                if not ent_match:
                    continue

                pred_match, _ = EntityResolver.match_predicates(f_new.predicate, f_old.predicate)
                if pred_match:
                    candidate_pairs.append((f_new, f_old))
                    seen_pairs.add(pair_key)
                    continue

                # Same entity with related metrics
                if f_new.value_type == f_old.value_type:
                    candidate_pairs.append((f_new, f_old))
                    seen_pairs.add(pair_key)

            # 2. Vector search pass (if vector store available)
            if self.vector_store:
                query = f_new.to_canonical_representation()
                search_results = self.vector_store.search(query, top_k=5, threshold=similarity_threshold)
                for f_id, score in search_results:
                    if f_id == f_new.fact_id or f_id not in existing_by_id:
                        continue
                    pair_key = tuple(sorted([f_new.fact_id, f_id]))
                    if pair_key not in seen_pairs:
                        candidate_pairs.append((f_new, existing_by_id[f_id]))
                        seen_pairs.add(pair_key)

        logger.info(f"Identified {len(candidate_pairs)} candidate pairs from {len(new_facts)} new facts and {len(existing_facts)} existing facts.")
        return candidate_pairs
